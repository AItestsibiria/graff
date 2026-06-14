# Graff — граф кода + MCP-сервер

**Автор / Author:** NEG · egnovoselov@gmail.com

Standalone-инструмент: индексирует ЛЮБОЙ репозиторий в граф символов и связей,
отдаёт навигацию/impact-анализ как CLI и как MCP-сервер для AI-агентов (Claude
Code, Cursor и т.п.).

> **Лицензия**: [BSL 1.1](LICENSE) — бесплатно для личного и некоммерческого использования.
> Коммерческое SaaS-использование требует лицензии: egnovoselov@gmail.com

## Что делает

- **Парсит** Python (через `ast`, полная точность) + 15+ языков через tree-sitter
  (TS/TSX/JS, Go, Rust, Java, Ruby, PHP, C/C++, C#, Kotlin, Bash и др.).
- **Строит граф** в SQLite (`<repo>/.graff/graph.db`): узлы (File/Class/Function/
  Method) + связи (IMPORTS/CALLS/HAS_METHOD/INHERITS/CONTAINS).
- **Мульти-репо**: глобальный реестр `~/.graff/registry.json`, один MCP-сервер на
  все проекты.

## Инструменты

**Навигация и анализ:**

| Инструмент | Что даёт | Заменяет |
|---|---|---|
| `find`    | поиск символа (BM25) → точный файл+строка | grep + glob |
| `context` | 360°: кто вызывает / что вызывает / родитель / дети | grep→read цепочку |
| `impact`  | blast radius: что сломается при изменении (риск + файлы) | ручное чтение потребителей |
| `flows`   | трассировка CALLS-цепочек | ручной обход вызовов |
| `route-map` | кросс-стек: API-роуты и кто их зовёт с фронта | grep по всему фронту |

**Свежесть и контроль:**

| Инструмент | Что даёт |
|---|---|
| `update`         | инкрементальный реиндекс (только изменённые файлы по mtime) |
| `detect-changes` | git-diff → затронутые символы + blast radius (перед коммитом) |
| `check`          | rule guard: проверка правил проекта (секреты, прокси, .env) |
| `roles`          | роли файлов (паук/пайплайн/роут) + аномалии |

**Аналитика графа:**

| Инструмент | Что даёт |
|---|---|
| `hotspots` | самые зависимые символы (риск изменения) |
| `deadcode` | кандидаты в мёртвый код (Python) |
| `cycles`   | циклические импорты |

MCP-сервер отдаёт все 14 инструментов (`graff_find`, `graff_context`, `graff_impact`,
`graff_flows`, `graff_route_map`, `graff_detect_changes`, `graff_check`, `graff_roles`,
`graff_hotspots`, `graff_deadcode`, `graff_cycles`, `graff_update`, `graff_list_repos`,
`graff_status`).

## Слои (растёт при выявлении паттернов)

1. **Граф** — символы + связи (IMPORTS/CALLS/HAS_METHOD/INHERITS/HTTP_CALL).
2. **Точность** — import-aware резолв вызовов, кросс-стек fetch→route.
3. **Правила** (`rules.py`) — жёсткие правила проекта как граф/контент-проверки;
   новые паттерны добавляются как функции-правила.
4. **Аналитика** — хотспоты/мёртвый код/циклы из топологии графа.

## Установка

```bash
cd tools/graff
python3 -m venv .venv
.venv/bin/python -m pip install -e .
# глобальный лаунчер (опц.):
ln -sf "$PWD/.venv/bin/graff" /usr/local/bin/graff   # или свой шелл-враппер
```

## Использование

```bash
graff analyze /path/to/repo          # проиндексировать (создаёт <repo>/.graff/)
graff list                           # все проиндексированные репо
graff find "process item" --repo myrepo
graff context PgPipeline --repo myrepo
graff impact RealtyItem --repo myrepo --depth 2
graff flows "save offer" --repo myrepo
graff status --repo myrepo
```

Запросы по умолчанию берут единственный репо или текущий каталог; `--repo
<алиас|путь>` выбирает нужный.

## Подключение другого проекта — одна команда

```bash
bash /var/www/biznesmetr/tools/graff/connect-project.sh /путь/к/проекту [алиас]
```

Скрипт автоматически:
1. Индексирует репо (`graff analyze`)
2. Добавляет/создаёт `.mcp.json` с записью graff
3. Печатает статус и инструкцию

После этого — **рестарт Claude Code** в том проекте → 14 `graff_*` инструментов активны.

**Вручную** (если нужно):
```bash
# 1. Проиндексировать
graff analyze /путь/к/проекту --alias мой-проект

# 2. Добавить в .mcp.json проекта
```
```json
{
  "mcpServers": {
    "graff": { "command": "graff", "args": ["mcp"] }
  }
}
```

Один MCP-сервер обслуживает все репо из реестра (`~/.graff/registry.json`).
При запросах без `--repo` берётся текущий каталог или единственный репо в реестре.

## Переиндексация

Граф — снимок на момент `analyze`. После значимых правок:
```bash
graff update /путь/к/проекту   # инкремент по mtime (быстро)
graff analyze /путь/к/проекту  # полный переиндекс
```
