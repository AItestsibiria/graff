"""Graff SaaS landing page — EN/RU bilingual."""

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Graff — Save 90% of AI tokens on code navigation</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0d1117;color:#e6edf3;line-height:1.6}
a{color:#58a6ff;text-decoration:none}

.lang-bar{text-align:right;padding:10px 24px;background:#161b22;border-bottom:1px solid #21262d}
.lang-btn{background:none;border:1px solid #30363d;color:#8b949e;padding:4px 14px;border-radius:20px;cursor:pointer;font-size:.82rem;margin-left:6px;transition:.15s}
.lang-btn.active,.lang-btn:hover{border-color:#58a6ff;color:#58a6ff}

/* hero */
.hero{text-align:center;padding:72px 20px 52px;background:linear-gradient(180deg,#161b22 0%,#0d1117 100%)}
.hero h1{font-size:2.8rem;font-weight:800;margin-bottom:16px;background:linear-gradient(135deg,#58a6ff,#3fb950);-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.2}
.hero .sub{font-size:1.15rem;color:#8b949e;max-width:600px;margin:0 auto 12px}
.savings-pill{display:inline-block;background:linear-gradient(135deg,#1a3d1a,#0f3d0f);border:1px solid #3fb950;border-radius:30px;padding:6px 20px;font-size:1rem;color:#3fb950;font-weight:700;margin:16px 0 32px;letter-spacing:.5px}
.savings-pill span{color:#57ff8c}
.btn{display:inline-block;padding:12px 28px;border-radius:8px;font-weight:600;font-size:1rem;cursor:pointer;border:none;transition:.2s}
.btn-primary{background:#238636;color:#fff}
.btn-primary:hover{background:#2ea043}
.btn-outline{background:transparent;color:#58a6ff;border:1px solid #30363d;margin-left:12px}
.btn-outline:hover{border-color:#58a6ff}

/* stats bar */
.stats{display:flex;justify-content:center;gap:48px;padding:32px 20px;background:#161b22;border-top:1px solid #21262d;border-bottom:1px solid #21262d;flex-wrap:wrap}
.stat{text-align:center}
.stat .num{font-size:2.4rem;font-weight:800;background:linear-gradient(135deg,#58a6ff,#3fb950);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.stat .label{font-size:.82rem;color:#8b949e;margin-top:2px}

/* comparison */
.section{padding:60px 20px;max-width:1060px;margin:0 auto}
.section h2{font-size:1.8rem;font-weight:700;margin-bottom:8px;text-align:center}
.section .h2-sub{text-align:center;color:#8b949e;margin-bottom:40px;font-size:.95rem}

.compare{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:16px}
@media(max-width:700px){.compare{grid-template-columns:1fr}}
.cbox{border-radius:12px;overflow:hidden}
.cbox-header{padding:12px 16px;font-weight:700;font-size:.9rem;display:flex;align-items:center;gap:8px}
.cbox.bad .cbox-header{background:#3d1a1a;color:#f85149}
.cbox.good .cbox-header{background:#0f3d1a;color:#3fb950}
.cbox-body{padding:16px;font-family:monospace;font-size:.78rem;line-height:1.7;border:1px solid;border-top:none;border-radius:0 0 12px 12px}
.cbox.bad .cbox-body{background:#1a0d0d;border-color:#3d1a1a;color:#e6edf3}
.cbox.good .cbox-body{background:#0d1a0d;border-color:#1a3d1a;color:#e6edf3}
.tool-call{display:flex;align-items:baseline;gap:6px;padding:3px 0}
.tool-call .tc-name{color:#58a6ff;white-space:nowrap}
.tool-call .tc-tokens{color:#f0883e;font-size:.72rem;margin-left:auto;white-space:nowrap}
.tool-call .tc-gray{color:#484f58}
.divider{text-align:center;padding:12px 0;color:#8b949e;font-size:.85rem}
.total-row{margin-top:12px;padding-top:10px;border-top:1px solid;display:flex;justify-content:space-between;font-weight:700;font-size:.85rem}
.cbox.bad .total-row{border-color:#3d1a1a;color:#f85149}
.cbox.good .total-row{border-color:#1a3d1a;color:#3fb950}
.savings-tag{text-align:center;font-size:1.4rem;font-weight:800;color:#3fb950;padding:4px 0 24px}

/* animated counter */
.counter{font-variant-numeric:tabular-nums}

/* flow diagram */
.flow{display:flex;align-items:center;justify-content:center;gap:0;flex-wrap:wrap;margin:40px 0 16px}
.flow-node{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:12px 18px;text-align:center;min-width:120px}
.flow-node .fn-icon{font-size:1.6rem;margin-bottom:4px}
.flow-node .fn-label{font-size:.78rem;color:#8b949e}
.flow-node .fn-name{font-size:.88rem;font-weight:600}
.flow-node.highlight{border-color:#58a6ff;background:#0d1f38}
.flow-arrow{color:#30363d;font-size:1.4rem;padding:0 6px;align-self:center}
.flow-arrow.green{color:#3fb950}

/* tools */
.tools-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px}
.tool{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px;transition:.15s}
.tool:hover{border-color:#30363d80;background:#1a2030}
.tool code{color:#58a6ff;font-size:.85rem}
.tool p{font-size:.8rem;color:#8b949e;margin-top:4px}
.tool .saving{font-size:.72rem;color:#3fb950;margin-top:6px}

/* plans */
.plans{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:24px}
.plan{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:28px;position:relative}
.plan.popular{border-color:#238636}
.popular-badge{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:#238636;color:#fff;font-size:.75rem;padding:2px 14px;border-radius:20px;font-weight:600}
.plan h3{font-size:1.1rem;font-weight:600;margin-bottom:8px}
.plan .price{font-size:2.5rem;font-weight:700;margin-bottom:4px}
.plan .price span{font-size:1rem;font-weight:400;color:#8b949e}
.plan ul{list-style:none;margin:20px 0 24px;color:#8b949e;font-size:.9rem}
.plan ul li{padding:4px 0}
.plan ul li::before{content:"✓  ";color:#3fb950}
.plan .btn{width:100%;text-align:center}

/* signup */
.signup-box{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:40px;max-width:520px;margin:0 auto;text-align:center}
.signup-box h2{margin-bottom:8px}
.signup-box .sub{color:#8b949e;margin-bottom:24px;font-size:.9rem}
.form-row{display:flex;gap:8px}
.form-row input{flex:1;background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:10px 14px;color:#e6edf3;font-size:.95rem;outline:none}
.form-row input:focus{border-color:#58a6ff}
.msg{margin-top:16px;padding:12px;border-radius:8px;font-size:.9rem;display:none}
.msg.ok{background:#0f3d1a;border:1px solid #238636;color:#3fb950}
.msg.err{background:#3d0f0f;border:1px solid #8b0000;color:#f85149}
.key-display{font-family:monospace;font-size:.78rem;word-break:break-all;margin-top:8px;padding:10px;background:#0d1117;border-radius:6px;border:1px solid #30363d;text-align:left}
.code-block{background:#0d1117;border:1px solid #21262d;border-radius:6px;padding:14px;font-family:monospace;font-size:.78rem;color:#3fb950;text-align:left;overflow-x:auto;margin-top:10px}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:20px}
.step{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:22px}
.step .num{font-size:2rem;font-weight:700;color:#58a6ff;margin-bottom:8px}
.step h3{font-size:.95rem;font-weight:600;margin-bottom:6px}
.step p,.step code{font-size:.85rem;color:#8b949e}
.step code{color:#3fb950;background:#0d1117;padding:1px 5px;border-radius:3px}

footer{text-align:center;padding:40px 20px;color:#8b949e;font-size:.85rem;border-top:1px solid #21262d;margin-top:60px}

.en,.ru{display:none}
body.lang-en .en{display:revert}
body.lang-ru .ru{display:revert}
span.en,span.ru{display:none}
body.lang-en span.en{display:inline}
body.lang-ru span.ru{display:inline}
</style>
</head>
<body class="lang-en">

<div class="lang-bar">
  <button class="lang-btn active" onclick="setLang('en')">EN</button>
  <button class="lang-btn" onclick="setLang('ru')">RU</button>
</div>

<!-- HERO -->
<div class="hero">
  <h1><span class="en">Stop wasting tokens<br>on code navigation</span><span class="ru">Хватит сжигать токены<br>на поиск по коду</span></h1>
  <p class="sub en">Graff indexes your repo into a symbol graph. AI gets precise answers in one call — instead of reading dozens of files.</p>
  <p class="sub ru">Graff индексирует репо в граф символов. AI получает точный ответ одним вызовом — вместо чтения десятков файлов.</p>
  <div class="savings-pill">
    <span class="en">Up to <span>10–50×</span> fewer tokens on code tasks</span>
    <span class="ru">До <span>10–50×</span> меньше токенов на задачи с кодом</span>
  </div>
  <br>
  <a href="#signup" class="btn btn-primary"><span class="en">Get started free</span><span class="ru">Начать бесплатно</span></a>
  <a href="https://github.com/AItestsibiria/graff" class="btn btn-outline">GitHub</a>
</div>

<!-- STATS -->
<div class="stats">
  <div class="stat"><div class="num">~50k</div><div class="label"><span class="en">tokens: read 10 files manually</span><span class="ru">токенов: прочитать 10 файлов вручную</span></div></div>
  <div class="stat"><div class="num" style="color:#3fb950">~500</div><div class="label"><span class="en">tokens: one graff_context call</span><span class="ru">токенов: один graff_context</span></div></div>
  <div class="stat"><div class="num">100×</div><div class="label"><span class="en">savings on context lookup</span><span class="ru">экономия при поиске контекста</span></div></div>
  <div class="stat"><div class="num">14</div><div class="label"><span class="en">MCP tools for AI agents</span><span class="ru">MCP-инструментов для AI-агентов</span></div></div>
</div>

<!-- COMPARISON -->
<div class="section">
  <h2><span class="en">Before vs After Graff</span><span class="ru">До и после Graff</span></h2>
  <p class="h2-sub en">Real example: "Find what calls processItem and what it calls"</p>
  <p class="h2-sub ru">Реальный пример: «Найди что вызывает processItem и что она вызывает»</p>

  <div class="compare">
    <!-- WITHOUT -->
    <div class="cbox bad">
      <div class="cbox-header">
        ✗ <span class="en">Without Graff — Claude reads files</span><span class="ru">Без Graff — Claude читает файлы</span>
      </div>
      <div class="cbox-body">
        <div class="tool-call"><span class="tc-name">Glob("**/*.py")</span><span class="tc-tokens">↳ 312 files listed</span></div>
        <div class="tool-call"><span class="tc-name">Grep("processItem")</span><span class="tc-tokens tc-gray">↳ 18 matches, 8 files</span></div>
        <div class="tool-call"><span class="tc-name">Read(pipelines.py)</span><span class="tc-tokens">~4 200 tok</span></div>
        <div class="tool-call"><span class="tc-name">Read(spider_base.py)</span><span class="tc-tokens">~5 800 tok</span></div>
        <div class="tool-call"><span class="tc-name">Read(items.py)</span><span class="tc-tokens">~2 100 tok</span></div>
        <div class="tool-call"><span class="tc-name">Read(db_pipeline.py)</span><span class="tc-tokens">~6 400 tok</span></div>
        <div class="tool-call"><span class="tc-name">Read(export.py)</span><span class="tc-tokens">~3 700 tok</span></div>
        <div class="tool-call"><span class="tc-name">Read(validators.py)</span><span class="tc-tokens">~4 100 tok</span></div>
        <div class="tool-call"><span class="tc-name">Read(middleware.py)</span><span class="tc-tokens">~7 200 tok</span></div>
        <div class="tool-call"><span class="tc-name">Read(settings.py)</span><span class="tc-tokens">~2 900 tok</span></div>
        <div class="tool-call tc-gray" style="margin-top:4px;font-size:.72rem">… still no full picture of callers</div>
        <div class="total-row">
          <span><span class="en">10 tool calls, incomplete</span><span class="ru">10 вызовов, неполная картина</span></span>
          <span>~36 400 <span class="en">tokens</span><span class="ru">токенов</span></span>
        </div>
      </div>
    </div>

    <!-- WITH -->
    <div class="cbox good">
      <div class="cbox-header">
        ✓ <span class="en">With Graff — one MCP call</span><span class="ru">С Graff — один MCP-вызов</span>
      </div>
      <div class="cbox-body">
        <div class="tool-call"><span class="tc-name" style="color:#3fb950">graff_context("processItem")</span></div>
        <div style="margin-top:10px;padding:10px;background:#0d1a0d;border-radius:6px;font-size:.76rem;line-height:1.9">
          <div style="color:#3fb950">✓ defined: pipelines.py:47</div>
          <div style="color:#e6edf3">callers (3):
  CianSpider.parse → pipelines.py
  Ru09Spider.parse → spiders/ru09.py
  YandexSpider.parse → spiders/yandex.py</div>
          <div style="color:#e6edf3">callees (4):
  RealtyItem.validate
  DbPipeline.save
  PhotoPipeline.download
  StatsPipeline.count</div>
          <div style="color:#58a6ff">parent: ScrapyPipeline (class)</div>
        </div>
        <div style="height:82px"></div>
        <div class="total-row">
          <span><span class="en">1 tool call, complete graph</span><span class="ru">1 вызов, полная картина</span></span>
          <span>~380 <span class="en">tokens</span><span class="ru">токенов</span></span>
        </div>
      </div>
    </div>
  </div>

  <div class="savings-tag">
    → <span class="en">96× less tokens. Same answer. Every time.</span>
       <span class="ru">96× меньше токенов. Тот же ответ. Каждый раз.</span>
  </div>
</div>

<!-- FLOW DIAGRAM -->
<div class="section" style="padding-top:0">
  <h2><span class="en">How AI navigates your code</span><span class="ru">Как AI ориентируется в коде</span></h2>
  <p class="h2-sub en">One indexed graph replaces endless file reading</p>
  <p class="h2-sub ru">Один индексированный граф заменяет бесконечное чтение файлов</p>
  <div class="flow">
    <div class="flow-node"><div class="fn-icon">🤖</div><div class="fn-name">Claude</div><div class="fn-label"><span class="en">AI Agent</span><span class="ru">AI-агент</span></div></div>
    <div class="flow-arrow green">→</div>
    <div class="flow-node highlight"><div class="fn-icon">🔍</div><div class="fn-name">graff_impact</div><div class="fn-label">MCP call</div></div>
    <div class="flow-arrow green">→</div>
    <div class="flow-node highlight"><div class="fn-icon">🕸</div><div class="fn-name"><span class="en">Symbol Graph</span><span class="ru">Граф символов</span></div><div class="fn-label">SQLite</div></div>
    <div class="flow-arrow green">→</div>
    <div class="flow-node"><div class="fn-icon">⚡</div><div class="fn-name"><span class="en">Precise answer</span><span class="ru">Точный ответ</span></div><div class="fn-label">~400 tok</div></div>
  </div>
  <div style="text-align:center;color:#484f58;font-size:.85rem">
    <span class="en">vs: Read → Grep → Read → Read → Read → Read … (~40k tokens)</span>
    <span class="ru">vs: Read → Grep → Read → Read → Read → Read … (~40k токенов)</span>
  </div>
</div>

<!-- TOOLS -->
<div class="section">
  <h2>14 MCP <span class="en">Tools</span><span class="ru">Инструментов</span></h2>
  <p class="h2-sub en">Each replaces a chain of file reads — saving thousands of tokens</p>
  <p class="h2-sub ru">Каждый заменяет цепочку чтений файлов — экономя тысячи токенов</p>
  <div class="tools-grid">
    <div class="tool"><code>graff_find</code><p class="en">Symbol search → exact file + line</p><p class="ru">Поиск символа → файл + строка</p><div class="saving"><span class="en">replaces: Glob + Grep + Read ×3</span><span class="ru">заменяет: Glob + Grep + Read ×3</span></div></div>
    <div class="tool"><code>graff_context</code><p class="en">360°: callers / callees / children</p><p class="ru">360°: кто вызывает / что вызывает</p><div class="saving"><span class="en">replaces: Read ×5–15 files</span><span class="ru">заменяет: Read ×5–15 файлов</span></div></div>
    <div class="tool"><code>graff_impact</code><p class="en">Blast radius before any change</p><p class="ru">Blast radius до любой правки</p><div class="saving"><span class="en">replaces: Read entire codebase</span><span class="ru">заменяет: чтение всей базы</span></div></div>
    <div class="tool"><code>graff_flows</code><p class="en">Trace call chains</p><p class="ru">Цепочки вызовов</p><div class="saving"><span class="en">replaces: manual graph tracing</span><span class="ru">заменяет: ручной обход графа</span></div></div>
    <div class="tool"><code>graff_route_map</code><p class="en">Frontend fetch ↔ API route</p><p class="ru">Фронт-fetch ↔ API-роут</p><div class="saving"><span class="en">replaces: Grep across all frontend</span><span class="ru">заменяет: Grep по всему фронту</span></div></div>
    <div class="tool"><code>graff_detect_changes</code><p class="en">git diff → affected symbols</p><p class="ru">git-diff → затронутые символы</p><div class="saving"><span class="en">replaces: manual diff analysis</span><span class="ru">заменяет: ручной анализ диффа</span></div></div>
    <div class="tool"><code>graff_check</code><p class="en">Security rules guard</p><p class="ru">Rule guard: секреты, уязвимости</p><div class="saving"><span class="en">replaces: grep for secret patterns</span><span class="ru">заменяет: grep по паттернам</span></div></div>
    <div class="tool"><code>graff_roles</code><p class="en">File roles + anomalies</p><p class="ru">Роли файлов + аномалии</p><div class="saving"><span class="en">replaces: Read all class files</span><span class="ru">заменяет: Read всех классов</span></div></div>
    <div class="tool"><code>graff_hotspots</code><p class="en">Most critical symbols</p><p class="ru">Самые зависимые символы</p><div class="saving"><span class="en">replaces: full dependency scan</span><span class="ru">заменяет: полный скан зависимостей</span></div></div>
    <div class="tool"><code>graff_deadcode</code><p class="en">Dead code candidates</p><p class="ru">Кандидаты в мёртвый код</p><div class="saving"><span class="en">replaces: Read + count references</span><span class="ru">заменяет: Read + подсчёт ссылок</span></div></div>
    <div class="tool"><code>graff_cycles</code><p class="en">Circular imports</p><p class="ru">Циклические импорты</p><div class="saving"><span class="en">replaces: trace imports by hand</span><span class="ru">заменяет: ручной обход импортов</span></div></div>
    <div class="tool"><code>graff_update</code><p class="en">Incremental re-index</p><p class="ru">Инкрементальный реиндекс</p><div class="saving"><span class="en">keeps graph fresh automatically</span><span class="ru">держит граф актуальным</span></div></div>
    <div class="tool"><code>graff_list_repos</code><p class="en">All indexed repos</p><p class="ru">Все проиндексированные репо</p></div>
    <div class="tool"><code>graff_status</code><p class="en">Graph stats</p><p class="ru">Статистика графа</p></div>
  </div>
</div>

<!-- HOW TO START -->
<div class="section">
  <h2><span class="en">Start in 3 minutes</span><span class="ru">Начать за 3 минуты</span></h2>
  <div class="steps">
    <div class="step"><div class="num">1</div>
      <h3><span class="en">Get API key (free)</span><span class="ru">Получите ключ (бесплатно)</span></h3>
      <p class="en">Sign up below — instant key, no credit card.</p>
      <p class="ru">Форма ниже — ключ сразу, карта не нужна.</p>
    </div>
    <div class="step"><div class="num">2</div>
      <h3><span class="en">Submit your repo</span><span class="ru">Отправьте репозиторий</span></h3>
      <p><code>POST /api/repos</code><br><span class="en">Graff clones + indexes in ~30s</span><span class="ru">Graff клонирует + индексирует ~30с</span></p>
    </div>
    <div class="step"><div class="num">3</div>
      <h3><span class="en">Add to .mcp.json</span><span class="ru">Добавьте в .mcp.json</span></h3>
      <p><code>"url": ".../mcp/TOKEN"</code><br><span class="en">Restart Claude Code → 14 tools active</span><span class="ru">Рестарт Claude Code → 14 инструментов</span></p>
    </div>
    <div class="step"><div class="num">4</div>
      <h3><span class="en">Save tokens. Ship faster.</span><span class="ru">Экономьте токены. Быстрее делайте.</span></h3>
      <p class="en">Every code navigation task costs 10–100× less. Your AI agent becomes smarter.</p>
      <p class="ru">Каждая задача по коду стоит в 10–100× дешевле. Ваш AI-агент работает умнее.</p>
    </div>
  </div>
</div>

<!-- PLANS -->
<div class="section">
  <h2><span class="en">Pricing</span><span class="ru">Тарифы</span></h2>
  <div class="plans">
    <div class="plan">
      <h3>Free</h3>
      <div class="price">$0<span> / <span class="en">mo</span><span class="ru">мес</span></span></div>
      <ul>
        <li><span class="en">1 repository</span><span class="ru">1 репозиторий</span></li>
        <li>14 MCP tools</li>
        <li>Python + 15 languages</li>
        <li><span class="en">Public repos</span><span class="ru">Публичные репо</span></li>
      </ul>
      <a href="#signup" class="btn btn-outline"><span class="en">Start free</span><span class="ru">Начать</span></a>
    </div>
    <div class="plan popular">
      <div class="popular-badge"><span class="en">Popular</span><span class="ru">Популярный</span></div>
      <h3>Pro</h3>
      <div class="price">$20<span> / <span class="en">mo</span><span class="ru">мес</span></span></div>
      <ul>
        <li><span class="en">5 repositories</span><span class="ru">5 репозиториев</span></li>
        <li>14 MCP tools</li>
        <li><span class="en">Private repos (PAT)</span><span class="ru">Приватные репо (PAT)</span></li>
        <li><span class="en">Priority indexing</span><span class="ru">Приоритетная индексация</span></li>
      </ul>
      <a href="#signup" class="btn btn-primary"><span class="en">Try Pro</span><span class="ru">Попробовать</span></a>
    </div>
    <div class="plan">
      <h3>Team</h3>
      <div class="price">$50<span> / <span class="en">mo</span><span class="ru">мес</span></span></div>
      <ul>
        <li><span class="en">Unlimited repos</span><span class="ru">Неограниченно репо</span></li>
        <li>14 MCP tools</li>
        <li><span class="en">Private repos</span><span class="ru">Приватные репо</span></li>
        <li><span class="en">Webhook auto-reindex</span><span class="ru">Webhook авто-реиндекс</span></li>
      </ul>
      <a href="#signup" class="btn btn-outline"><span class="en">Try Team</span><span class="ru">Попробовать</span></a>
    </div>
  </div>
</div>

<!-- SIGNUP -->
<div class="section" id="signup">
  <div class="signup-box">
    <h2><span class="en">Get your free API key</span><span class="ru">Получите бесплатный API-ключ</span></h2>
    <p class="sub en">Start saving tokens on your first repo today.</p>
    <p class="sub ru">Начните экономить токены на первом репо прямо сейчас.</p>
    <div class="form-row">
      <input type="email" id="email" placeholder="you@example.com">
      <button class="btn btn-primary" onclick="signup()">
        <span class="en">Get key</span><span class="ru">Получить</span>
      </button>
    </div>
    <div class="msg ok" id="msg-ok">
      <span class="en">✓ Your API key — save it:</span>
      <span class="ru">✓ Ваш API-ключ — сохраните:</span>
      <div class="key-display" id="key-display"></div>
      <div class="code-block" id="curl-example"></div>
    </div>
    <div class="msg err" id="msg-err"></div>
  </div>
</div>

<footer>
  Graff — open source ·
  <a href="https://github.com/AItestsibiria/graff">GitHub</a> ·
  <span class="en">Stop burning tokens. Start navigating.</span>
  <span class="ru">Хватит сжигать токены. Начните навигацию.</span>
</footer>

<script>
const BASE = window.location.origin + (window.location.pathname.startsWith('/graff') ? '/graff' : '');

function setLang(l){
  document.body.className='lang-'+l;
  document.querySelectorAll('.lang-btn').forEach(b=>b.classList.toggle('active',b.textContent===l.toUpperCase()));
  localStorage.setItem('graff_lang',l);
}
(function(){
  const s=localStorage.getItem('graff_lang');
  const nav=(navigator.language||'en').toLowerCase().startsWith('ru')?'ru':'en';
  setLang(s||nav);
})();

async function signup(){
  const email=document.getElementById('email').value.trim();
  if(!email)return;
  try{
    const r=await fetch(BASE+'/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,plan:'free'})});
    const d=await r.json();
    if(r.ok){
      document.getElementById('key-display').textContent=d.key;
      document.getElementById('curl-example').textContent=
        `curl -X POST ${window.location.origin}/graff/api/repos \\\n`+
        `  -H "X-Api-Key: ${d.key}" \\\n`+
        `  -H "Content-Type: application/json" \\\n`+
        `  -d '{"url":"https://github.com/your/repo"}'`;
      document.getElementById('msg-ok').style.display='block';
      document.getElementById('msg-err').style.display='none';
    }else{
      document.getElementById('msg-err').textContent=d.detail||'Error';
      document.getElementById('msg-err').style.display='block';
    }
  }catch(e){
    document.getElementById('msg-err').textContent='Network error';
    document.getElementById('msg-err').style.display='block';
  }
}
</script>
</body>
</html>"""
