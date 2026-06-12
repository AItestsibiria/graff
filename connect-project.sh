#!/usr/bin/env bash
# Подключить любой проект к Graff (граф кода + MCP).
# Использование: bash /var/www/biznesmetr/tools/graff/connect-project.sh [путь-к-репо] [алиас]
#
# Что делает:
#  1. Проверяет наличие глобального graff
#  2. Индексирует проект (graff analyze)
#  3. Добавляет/обновляет запись в .mcp.json проекта
#  4. Печатает инструкцию по финишу

set -euo pipefail

GRAFF_BIN="/usr/local/bin/graff"
REPO_PATH="${1:-$(pwd)}"
ALIAS="${2:-}"
REPO_PATH="$(realpath "$REPO_PATH")"

# --- проверки ---
if [[ ! -x "$GRAFF_BIN" ]]; then
    echo "ERROR: $GRAFF_BIN не найден. Установите граф:"
    echo "  ln -sf /var/www/biznesmetr/tools/graff/.venv/bin/graff /usr/local/bin/graff"
    exit 1
fi

if [[ ! -d "$REPO_PATH" ]]; then
    echo "ERROR: каталог не найден: $REPO_PATH"
    exit 1
fi

echo "Graff → подключаю $REPO_PATH …"

# --- индексация ---
ANALYZE_ARGS=("$REPO_PATH")
[[ -n "$ALIAS" ]] && ANALYZE_ARGS+=(--alias "$ALIAS")
"$GRAFF_BIN" analyze "${ANALYZE_ARGS[@]}"

# --- патч .mcp.json ---
MCP_FILE="$REPO_PATH/.mcp.json"
GRAFF_ENTRY='"graff": { "command": "graff", "args": ["mcp"] }'

if [[ ! -f "$MCP_FILE" ]]; then
    # создать с нуля
    cat > "$MCP_FILE" << 'JSON'
{
  "mcpServers": {
    "graff": { "command": "graff", "args": ["mcp"] }
  }
}
JSON
    echo "  создан $MCP_FILE"
else
    # проверить — уже есть?
    if python3 -c "
import json, sys
d = json.load(open('$MCP_FILE'))
srv = d.get('mcpServers', {})
sys.exit(0 if 'graff' in srv else 1)
" 2>/dev/null; then
        echo "  .mcp.json уже содержит graff — пропускаю"
    else
        # влить граф-сервер
        python3 - "$MCP_FILE" << 'PYEOF'
import json, sys
path = sys.argv[1]
with open(path) as f:
    d = json.load(f)
d.setdefault('mcpServers', {})['graff'] = {'command': 'graff', 'args': ['mcp']}
with open(path, 'w') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write('\n')
PYEOF
        echo "  обновлён $MCP_FILE (добавлен graff)"
    fi
fi

# --- статус ---
echo ""
echo "  Граф проиндексирован. Статус:"
"$GRAFF_BIN" status --repo "$REPO_PATH" 2>/dev/null || true

echo ""
echo "  Готово. Следующий шаг:"
echo "  → Откройте проект $REPO_PATH в Claude Code"
echo "  → Рестартуйте сессию (MCP стартует при инициализации)"
echo "  → В сессии будут доступны 14 инструментов: graff_find, graff_context, graff_impact …"
echo ""
echo "  Переиндексация после правок: graff update $REPO_PATH"
