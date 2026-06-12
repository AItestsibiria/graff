"""Graff SaaS landing page — EN/RU, token savings focus."""

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Graff — Stop Burning Tokens on Code Navigation</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0d1117;color:#e6edf3;line-height:1.6}
a{color:#58a6ff;text-decoration:none}

.lang-bar{text-align:right;padding:10px 24px;background:#161b22;border-bottom:1px solid #21262d}
.lang-btn{background:none;border:1px solid #30363d;color:#8b949e;padding:4px 14px;border-radius:20px;cursor:pointer;font-size:.82rem;margin-left:6px}
.lang-btn.active{border-color:#58a6ff;color:#58a6ff}

/* HERO */
.hero{text-align:center;padding:72px 20px 52px;background:linear-gradient(180deg,#161b22 0%,#0d1117 100%)}
.hero h1{font-size:2.9rem;font-weight:800;margin-bottom:14px;line-height:1.15}
.hero h1 em{font-style:normal;background:linear-gradient(135deg,#f85149,#ff8c42);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero h1 strong{background:linear-gradient(135deg,#3fb950,#58a6ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero .tagline{font-size:1.15rem;color:#8b949e;max-width:580px;margin:0 auto 28px}
.pill{display:inline-block;background:#0f3d1a;border:1px solid #3fb950;border-radius:30px;padding:7px 22px;font-size:1rem;color:#3fb950;font-weight:700;margin-bottom:32px}
.pill span{color:#57ff8c;font-size:1.15em}
.btn{display:inline-block;padding:12px 28px;border-radius:8px;font-weight:600;font-size:1rem;cursor:pointer;border:none;transition:.15s;text-decoration:none}
.btn-green{background:#238636;color:#fff}.btn-green:hover{background:#2ea043}
.btn-out{background:transparent;color:#58a6ff;border:1px solid #30363d;margin-left:12px}.btn-out:hover{border-color:#58a6ff}

/* STATS */
.stats{display:flex;justify-content:center;gap:0;background:#161b22;border-top:1px solid #21262d;border-bottom:1px solid #21262d;flex-wrap:wrap}
.stat{text-align:center;padding:28px 40px;border-right:1px solid #21262d}
.stat:last-child{border-right:none}
@media(max-width:600px){.stat{border-right:none;border-bottom:1px solid #21262d;width:50%}}
.stat .n{font-size:2.2rem;font-weight:800;line-height:1}
.stat .n.red{color:#f85149}.stat .n.green{color:#3fb950}.stat .n.blue{color:#58a6ff}.stat .n.yellow{color:#e3b341}
.stat .l{font-size:.78rem;color:#8b949e;margin-top:5px}

/* SECTION */
.sec{padding:64px 20px;max-width:1060px;margin:0 auto}
.sec h2{font-size:1.75rem;font-weight:700;text-align:center;margin-bottom:8px}
.sec .h2s{text-align:center;color:#8b949e;font-size:.92rem;margin-bottom:40px}

/* COMPARE */
.cmp{display:grid;grid-template-columns:1fr auto 1fr;gap:0;align-items:stretch;margin-bottom:8px}
@media(max-width:680px){.cmp{grid-template-columns:1fr;}.vs-col{display:none}}
.cbox{border-radius:12px;overflow:hidden}
.ch{padding:13px 18px;font-weight:700;font-size:.88rem;display:flex;align-items:center;gap:8px}
.cb{padding:16px 18px;font-family:monospace;font-size:.77rem;line-height:1.85;border:1px solid;border-top:none;border-radius:0 0 12px 12px;min-height:240px}
.bad .ch{background:#2d0f0f;color:#f85149}.bad .cb{background:#1a0a0a;border-color:#3d1a1a}
.good .ch{background:#0a2d0a;color:#3fb950}.good .cb{background:#0a1a0a;border-color:#1a3d1a}
.tc{display:flex;justify-content:space-between;padding:1px 0;gap:8px}
.tc .nm{color:#58a6ff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tc .tk{color:#f0883e;white-space:nowrap;flex-shrink:0}
.tc .dim{color:#484f58}
.tr{margin-top:12px;padding-top:10px;border-top:1px solid;display:flex;justify-content:space-between;font-weight:700;font-size:.85rem}
.bad .tr{border-color:#3d1a1a;color:#f85149}.good .tr{border-color:#1a3d1a;color:#3fb950}
.vs-col{display:flex;align-items:center;justify-content:center;padding:0 20px;font-size:2rem;font-weight:800;color:#484f58}
.win{text-align:center;font-size:1.45rem;font-weight:800;color:#3fb950;padding:6px 0 32px}

/* MONEY CALCULATOR */
.calc-wrap{background:#161b22;border:1px solid #30363d;border-radius:16px;padding:36px;max-width:780px;margin:0 auto}
.calc-wrap h3{font-size:1.2rem;font-weight:700;margin-bottom:24px;text-align:center}
.calc-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:24px}
@media(max-width:600px){.calc-row{grid-template-columns:1fr}}
.calc-field label{display:block;font-size:.78rem;color:#8b949e;margin-bottom:6px}
.calc-field select,.calc-field input[type=range]{width:100%;background:#0d1117;border:1px solid #30363d;color:#e6edf3;border-radius:6px;padding:8px 10px;font-size:.88rem;outline:none}
.calc-field input[type=range]{padding:4px;accent-color:#58a6ff;cursor:pointer}
.calc-field .val{font-size:.78rem;color:#58a6ff;margin-top:3px;text-align:right}
.result-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:8px}
@media(max-width:600px){.result-grid{grid-template-columns:1fr}}
.rcard{border-radius:10px;padding:18px;text-align:center}
.rcard.bad{background:#2d0f0f;border:1px solid #5a1a1a}
.rcard.good{background:#0a2d0a;border:1px solid #1a5a1a}
.rcard.save{background:#0a1a2d;border:1px solid #1a3a5a}
.rcard .rtitle{font-size:.75rem;color:#8b949e;margin-bottom:6px}
.rcard .rval{font-size:1.8rem;font-weight:800;line-height:1}
.rcard.bad .rval{color:#f85149}.rcard.good .rval{color:#3fb950}.rcard.save .rval{color:#58a6ff}
.rcard .rsub{font-size:.72rem;color:#8b949e;margin-top:4px}
.payback{text-align:center;margin-top:16px;font-size:.9rem;color:#8b949e}
.payback strong{color:#e3b341}

/* FLOW */
.flow{display:flex;align-items:center;justify-content:center;gap:4px;flex-wrap:wrap;margin:36px 0 12px}
.fn{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:11px 16px;text-align:center;min-width:110px}
.fn .fi{font-size:1.5rem;margin-bottom:3px}
.fn .fl{font-size:.72rem;color:#8b949e}
.fn .fname{font-size:.82rem;font-weight:600}
.fn.hl{border-color:#58a6ff;background:#0d1f38}
.fa{color:#30363d;font-size:1.3rem;padding:0 4px;align-self:center}
.fa.g{color:#3fb950}

/* TOOLS */
.tg{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}
.tool{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:13px}
.tool code{color:#58a6ff;font-size:.83rem}
.tool p{font-size:.77rem;color:#8b949e;margin-top:3px}
.tool .sv{font-size:.7rem;color:#3fb950;margin-top:5px;display:flex;align-items:center;gap:4px}
.tool .sv::before{content:"↓";font-weight:700}

/* PLANS */
.plans{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px}
.plan{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:26px;position:relative}
.plan.pop{border-color:#238636}
.pbadge{position:absolute;top:-11px;left:50%;transform:translateX(-50%);background:#238636;color:#fff;font-size:.72rem;padding:2px 14px;border-radius:20px;font-weight:700}
.plan h3{font-weight:700;margin-bottom:6px}
.plan .pr{font-size:2.3rem;font-weight:800;margin-bottom:2px}
.plan .pr span{font-size:.9rem;font-weight:400;color:#8b949e}
.plan ul{list-style:none;margin:16px 0 20px;font-size:.87rem;color:#8b949e}
.plan ul li{padding:3px 0}.plan ul li::before{content:"✓  ";color:#3fb950}
.plan .btn{width:100%;text-align:center}
.roi-tag{font-size:.75rem;color:#3fb950;margin-top:10px;text-align:center}

/* SIGNUP */
.sbox{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:38px;max-width:500px;margin:0 auto;text-align:center}
.sbox h2{margin-bottom:6px}
.sbox .sub{color:#8b949e;margin-bottom:22px;font-size:.88rem}
.fr{display:flex;gap:8px}
.fr input{flex:1;background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:10px 14px;color:#e6edf3;font-size:.93rem;outline:none}
.fr input:focus{border-color:#58a6ff}
.msg{margin-top:14px;padding:12px;border-radius:8px;font-size:.88rem;display:none}
.ok{background:#0f3d1a;border:1px solid #238636;color:#3fb950}
.er{background:#3d0f0f;border:1px solid #8b0000;color:#f85149}
.kd{font-family:monospace;font-size:.76rem;word-break:break-all;margin-top:8px;padding:9px;background:#0d1117;border-radius:6px;border:1px solid #30363d;text-align:left}
.cb2{background:#0d1117;border:1px solid #21262d;border-radius:6px;padding:12px;font-family:monospace;font-size:.75rem;color:#3fb950;text-align:left;overflow-x:auto;margin-top:10px;white-space:pre}

footer{text-align:center;padding:36px 20px;color:#8b949e;font-size:.82rem;border-top:1px solid #21262d;margin-top:60px}

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
  <h1>
    <span class="en"><em>Stop burning tokens</em><br>on code navigation.<br><strong>Get answers in one call.</strong></span>
    <span class="ru"><em>Хватит сжигать токены</em><br>на навигацию по коду.<br><strong>Ответ — одним вызовом.</strong></span>
  </h1>
  <p class="tagline en">Graff indexes your GitHub repo into a symbol graph. Instead of Claude reading 10+ files, one MCP call returns the exact answer.</p>
  <p class="tagline ru">Graff индексирует GitHub-репо в граф символов. Вместо того чтобы Claude читал 10+ файлов — один MCP-вызов возвращает точный ответ.</p>
  <div class="pill">
    <span class="en">Save up to <span>$300–1600/month</span> per developer</span>
    <span class="ru">Экономия до <span>$300–1600/мес</span> на разработчика</span>
  </div>
  <br>
  <a href="#signup" class="btn btn-green"><span class="en">Get started free</span><span class="ru">Начать бесплатно</span></a>
  <a href="https://github.com/AItestsibiria/graff" class="btn btn-out">GitHub</a>
</div>

<!-- STATS -->
<div class="stats">
  <div class="stat"><div class="n red">~36 000</div><div class="l"><span class="en">tokens: read 8 files manually</span><span class="ru">токенов: прочитать 8 файлов</span></div></div>
  <div class="stat"><div class="n green">~350</div><div class="l"><span class="en">tokens: one graff_context call</span><span class="ru">токенов: один graff_context</span></div></div>
  <div class="stat"><div class="n yellow">100×</div><div class="l"><span class="en">token savings per lookup</span><span class="ru">экономия токенов на запрос</span></div></div>
  <div class="stat"><div class="n blue">14</div><div class="l"><span class="en">MCP tools for any AI agent</span><span class="ru">MCP-инструментов для AI-агентов</span></div></div>
</div>

<!-- BEFORE / AFTER -->
<div class="sec">
  <h2><span class="en">Before vs After Graff</span><span class="ru">До и после Graff</span></h2>
  <p class="h2s en">Task: "What calls processItem and what does it call?" — real token count</p>
  <p class="h2s ru">Задача: «Что вызывает processItem и что она вызывает?» — реальный подсчёт токенов</p>

  <div class="cmp">
    <div class="cbox bad">
      <div class="ch">✗ <span class="en">Without Graff</span><span class="ru">Без Graff</span></div>
      <div class="cb">
        <div class="tc"><span class="nm">Glob("**/*.py")</span><span class="tk dim">312 files</span></div>
        <div class="tc"><span class="nm">Grep("processItem")</span><span class="tk dim">8 files matched</span></div>
        <div class="tc"><span class="nm">Read(pipelines.py)</span><span class="tk">4 200 tok</span></div>
        <div class="tc"><span class="nm">Read(spider_base.py)</span><span class="tk">5 800 tok</span></div>
        <div class="tc"><span class="nm">Read(db_pipeline.py)</span><span class="tk">6 400 tok</span></div>
        <div class="tc"><span class="nm">Read(items.py)</span><span class="tk">2 100 tok</span></div>
        <div class="tc"><span class="nm">Read(export.py)</span><span class="tk">3 700 tok</span></div>
        <div class="tc"><span class="nm">Read(validators.py)</span><span class="tk">4 100 tok</span></div>
        <div class="tc"><span class="nm">Read(middleware.py)</span><span class="tk">7 200 tok</span></div>
        <div class="tc"><span class="nm">Read(settings.py)</span><span class="tk">2 900 tok</span></div>
        <div class="tc dim" style="font-size:.71rem;margin-top:3px">…still incomplete — no caller map</div>
        <div class="tr">
          <span>10 <span class="en">calls</span><span class="ru">вызовов</span></span>
          <span>36 400 <span class="en">tokens</span><span class="ru">токенов</span></span>
        </div>
      </div>
    </div>
    <div class="vs-col">VS</div>
    <div class="cbox good">
      <div class="ch">✓ <span class="en">With Graff</span><span class="ru">С Graff</span></div>
      <div class="cb">
        <div class="tc"><span class="nm" style="color:#3fb950">graff_context("processItem")</span><span class="tk" style="color:#3fb950">1 call</span></div>
        <div style="margin-top:10px;padding:10px;background:#061206;border-radius:6px;line-height:2;font-size:.76rem">
          <div style="color:#3fb950">✓ defined: pipelines.py:47</div>
          <div>callers (3):
  CianSpider.parse
  Ru09Spider.parse
  YandexSpider.parse</div>
          <div>callees (4):
  RealtyItem.validate
  DbPipeline.save
  PhotoPipeline.download
  StatsPipeline.count</div>
          <div style="color:#58a6ff">parent: ScrapyPipeline</div>
        </div>
        <div style="flex:1;min-height:20px"></div>
        <div class="tr" style="margin-top:24px">
          <span>1 <span class="en">call, complete</span><span class="ru">вызов, полная картина</span></span>
          <span>350 <span class="en">tokens</span><span class="ru">токенов</span></span>
        </div>
      </div>
    </div>
  </div>
  <div class="win">→ <span class="en">104× fewer tokens. Same answer. Every time.</span><span class="ru">104× меньше токенов. Тот же ответ. Каждый раз.</span></div>
</div>

<!-- MONEY CALCULATOR -->
<div class="sec" style="padding-top:0">
  <h2><span class="en">Calculate your savings</span><span class="ru">Посчитайте свою экономию</span></h2>
  <p class="h2s en">Based on real Claude API pricing</p>
  <p class="h2s ru">На основе реальных цен Claude API</p>

  <div class="calc-wrap">
    <h3><span class="en">💰 Monthly savings calculator</span><span class="ru">💰 Калькулятор ежемесячной экономии</span></h3>
    <div class="calc-row">
      <div class="calc-field">
        <label><span class="en">Claude model</span><span class="ru">Модель Claude</span></label>
        <select id="model" onchange="calc()">
          <option value="haiku">Claude Haiku ($0.80/MTok)</option>
          <option value="sonnet" selected>Claude Sonnet ($3/MTok)</option>
          <option value="opus">Claude Opus ($15/MTok)</option>
        </select>
      </div>
      <div class="calc-field">
        <label><span class="en">Developers</span><span class="ru">Разработчиков</span></label>
        <input type="range" id="devs" min="1" max="20" value="1" oninput="calc()">
        <div class="val" id="devs-val">1</div>
      </div>
      <div class="calc-field">
        <label><span class="en">Code queries/day</span><span class="ru">Запросов к коду/день</span></label>
        <input type="range" id="queries" min="5" max="100" value="30" step="5" oninput="calc()">
        <div class="val" id="queries-val">30</div>
      </div>
    </div>

    <div class="result-grid">
      <div class="rcard bad">
        <div class="rtitle"><span class="en">Without Graff</span><span class="ru">Без Graff</span></div>
        <div class="rval" id="r-without">$0</div>
        <div class="rsub"><span class="en">per month on navigation tokens</span><span class="ru">в месяц на токены навигации</span></div>
      </div>
      <div class="rcard good">
        <div class="rtitle"><span class="en">With Graff</span><span class="ru">С Graff</span></div>
        <div class="rval" id="r-with">$0</div>
        <div class="rsub"><span class="en">tokens + Graff plan</span><span class="ru">токены + тариф Graff</span></div>
      </div>
      <div class="rcard save">
        <div class="rtitle"><span class="en">You save</span><span class="ru">Вы экономите</span></div>
        <div class="rval" id="r-save">$0</div>
        <div class="rsub"><span class="en">per month</span><span class="ru">в месяц</span></div>
      </div>
    </div>
    <div class="payback" id="payback"></div>
  </div>
</div>

<!-- FLOW DIAGRAM -->
<div class="sec" style="padding-top:0">
  <h2><span class="en">How it works inside</span><span class="ru">Как это работает</span></h2>
  <div class="flow">
    <div class="fn"><div class="fi">🤖</div><div class="fname">Claude</div><div class="fl">AI Agent</div></div>
    <div class="fa g">→</div>
    <div class="fn hl"><div class="fi">🔍</div><div class="fname">graff_*</div><div class="fl">MCP call</div></div>
    <div class="fa g">→</div>
    <div class="fn hl"><div class="fi">🕸</div><div class="fname"><span class="en">Symbol Graph</span><span class="ru">Граф символов</span></div><div class="fl">SQLite index</div></div>
    <div class="fa g">→</div>
    <div class="fn"><div class="fi">⚡</div><div class="fname"><span class="en">Exact answer</span><span class="ru">Точный ответ</span></div><div class="fl">~350 tokens</div></div>
  </div>
  <div style="text-align:center;color:#484f58;font-size:.82rem;margin-top:4px">
    <span class="en">vs: Read → Grep → Read×8 → still incomplete (~36 000 tokens)</span>
    <span class="ru">vs: Read → Grep → Read×8 → всё равно неполная картина (~36 000 токенов)</span>
  </div>
</div>

<!-- TOOLS -->
<div class="sec" style="padding-top:0">
  <h2>14 MCP <span class="en">Tools</span><span class="ru">Инструментов</span></h2>
  <p class="h2s en">Each replaces a chain of file reads — thousands of tokens saved per call</p>
  <p class="h2s ru">Каждый заменяет цепочку чтений файлов — тысячи токенов на каждом вызове</p>
  <div class="tg">
    <div class="tool"><code>graff_find</code><p class="en">Symbol → exact file+line</p><p class="ru">Символ → файл+строка</p><div class="sv en">replaces Glob+Grep+Read×3</div><div class="sv ru">заменяет Glob+Grep+Read×3</div></div>
    <div class="tool"><code>graff_context</code><p class="en">360°: callers/callees/children</p><p class="ru">360°: кто/что вызывает</p><div class="sv en">replaces Read×5–15 files</div><div class="sv ru">заменяет Read×5–15 файлов</div></div>
    <div class="tool"><code>graff_impact</code><p class="en">Blast radius before any change</p><p class="ru">Blast radius перед правкой</p><div class="sv en">replaces reading entire codebase</div><div class="sv ru">заменяет чтение всей базы</div></div>
    <div class="tool"><code>graff_flows</code><p class="en">Trace call chains</p><p class="ru">Цепочки вызовов</p><div class="sv en">replaces manual graph tracing</div><div class="sv ru">заменяет ручной обход</div></div>
    <div class="tool"><code>graff_route_map</code><p class="en">Frontend ↔ API route</p><p class="ru">Фронт ↔ API-роут</p><div class="sv en">replaces Grep across all frontend</div><div class="sv ru">заменяет Grep по всему фронту</div></div>
    <div class="tool"><code>graff_detect_changes</code><p class="en">git diff → affected symbols</p><p class="ru">git-diff → символы + риск</p><div class="sv en">replaces manual diff analysis</div><div class="sv ru">заменяет ручной анализ диффа</div></div>
    <div class="tool"><code>graff_check</code><p class="en">Security rule guard</p><p class="ru">Rule guard: секреты</p><div class="sv en">replaces grep for secret patterns</div><div class="sv ru">заменяет grep по паттернам</div></div>
    <div class="tool"><code>graff_roles</code><p class="en">File roles + anomalies</p><p class="ru">Роли файлов + аномалии</p><div class="sv en">replaces Read all class files</div><div class="sv ru">заменяет Read всех классов</div></div>
    <div class="tool"><code>graff_hotspots</code><p class="en">Riskiest symbols</p><p class="ru">Самые зависимые символы</p><div class="sv en">replaces full dep scan</div><div class="sv ru">заменяет скан зависимостей</div></div>
    <div class="tool"><code>graff_deadcode</code><p class="en">Dead code candidates</p><p class="ru">Кандидаты в мёртвый код</p><div class="sv en">replaces Read+count references</div><div class="sv ru">заменяет Read+подсчёт ссылок</div></div>
    <div class="tool"><code>graff_cycles</code><p class="en">Circular imports</p><p class="ru">Циклические импорты</p><div class="sv en">replaces trace imports by hand</div><div class="sv ru">заменяет ручной обход импортов</div></div>
    <div class="tool"><code>graff_update</code><p class="en">Incremental re-index</p><p class="ru">Инкрементальный реиндекс</p><div class="sv en">keeps graph fresh on every save</div><div class="sv ru">граф всегда актуален</div></div>
    <div class="tool"><code>graff_list_repos</code><p class="en">All indexed repos</p><p class="ru">Все проиндексированные репо</p></div>
    <div class="tool"><code>graff_status</code><p class="en">Graph stats</p><p class="ru">Статистика графа</p></div>
  </div>
</div>

<!-- PLANS -->
<div class="sec" style="padding-top:0">
  <h2><span class="en">Pricing — pays for itself on day one</span><span class="ru">Тарифы — окупается в первый день</span></h2>
  <div class="plans">
    <div class="plan">
      <h3>Free</h3>
      <div class="pr">$0<span>/mo</span></div>
      <ul>
        <li><span class="en">1 repository</span><span class="ru">1 репозиторий</span></li>
        <li>14 MCP tools</li>
        <li>Python + 15 <span class="en">languages</span><span class="ru">языков</span></li>
        <li><span class="en">Public repos</span><span class="ru">Публичные репо</span></li>
      </ul>
      <a href="#signup" class="btn btn-out" style="display:block;text-align:center"><span class="en">Start free</span><span class="ru">Начать</span></a>
    </div>
    <div class="plan pop">
      <div class="pbadge"><span class="en">Popular</span><span class="ru">Популярный</span></div>
      <h3>Pro</h3>
      <div class="pr">$20<span>/mo</span></div>
      <ul>
        <li><span class="en">5 repositories</span><span class="ru">5 репозиториев</span></li>
        <li>14 MCP tools</li>
        <li><span class="en">Private repos (PAT)</span><span class="ru">Приватные репо (PAT)</span></li>
        <li><span class="en">Priority indexing</span><span class="ru">Приоритетная индексация</span></li>
      </ul>
      <a href="#signup" class="btn btn-green" style="display:block;text-align:center"><span class="en">Try Pro</span><span class="ru">Попробовать</span></a>
      <div class="roi-tag en">Saves ~$200+/mo vs Sonnet without Graff</div>
      <div class="roi-tag ru">Экономит ~$200+/мес vs Sonnet без Graff</div>
    </div>
    <div class="plan">
      <h3>Team</h3>
      <div class="pr">$50<span>/mo</span></div>
      <ul>
        <li><span class="en">Unlimited repos</span><span class="ru">Неограниченно репо</span></li>
        <li>14 MCP tools</li>
        <li><span class="en">Private repos</span><span class="ru">Приватные репо</span></li>
        <li><span class="en">Webhook auto-reindex</span><span class="ru">Webhook авто-реиндекс</span></li>
      </ul>
      <a href="#signup" class="btn btn-out" style="display:block;text-align:center"><span class="en">Try Team</span><span class="ru">Попробовать</span></a>
      <div class="roi-tag en">ROI: 10–30× for teams of 3+</div>
      <div class="roi-tag ru">ROI: 10–30× для команды 3+</div>
    </div>
  </div>
</div>

<!-- SIGNUP -->
<div class="sec" id="signup">
  <div class="sbox">
    <h2><span class="en">Get your free API key</span><span class="ru">Получите бесплатный API-ключ</span></h2>
    <p class="sub en">Start saving tokens on your first repo today. No credit card.</p>
    <p class="sub ru">Начните экономить токены прямо сейчас. Карта не нужна.</p>
    <div class="fr">
      <input type="email" id="email" placeholder="you@example.com">
      <button class="btn btn-green" onclick="signup()"><span class="en">Get key</span><span class="ru">Получить</span></button>
    </div>
    <div class="msg ok" id="msg-ok">
      <span class="en">✓ Your API key — save it:</span><span class="ru">✓ Ваш API-ключ — сохраните:</span>
      <div class="kd" id="key-display"></div>
      <div class="cb2" id="curl-example"></div>
    </div>
    <div class="msg er" id="msg-err"></div>
  </div>
</div>

<footer>
  Graff ·
  <a href="https://github.com/AItestsibiria/graff">GitHub</a> ·
  <span class="en">© 2025 BAI. All rights reserved. Commercial use requires a license.</span>
  <span class="ru">© 2025 BAI. Все права защищены. Коммерческое использование требует лицензии.</span>
</footer>

<script>
const BASE = window.location.origin + (window.location.pathname.startsWith('/graff') ? '/graff' : '');

// Claude API pricing: input $/MTok
const PRICE = { haiku: 0.80, sonnet: 3.00, opus: 15.00 };
// tokens per navigation query
const TOK_WITHOUT = 36400;
const TOK_WITH = 350;
const GRAFF_PLAN = 20; // Pro plan cost

function fmt(n) {
  if (n >= 1000) return '$' + Math.round(n).toLocaleString();
  if (n >= 10) return '$' + Math.round(n);
  return '$' + n.toFixed(2);
}

function calc() {
  const model = document.getElementById('model').value;
  const devs = +document.getElementById('devs').value;
  const qpd = +document.getElementById('queries').value;
  document.getElementById('devs-val').textContent = devs + (devs === 1 ? '' : '');
  document.getElementById('queries-val').textContent = qpd;

  const ppm = PRICE[model]; // $ per MTok
  const qpm = qpd * 20 * devs; // queries per month (20 work days)

  const costWithout = qpm * TOK_WITHOUT / 1e6 * ppm;
  const costWith = qpm * TOK_WITH / 1e6 * ppm + GRAFF_PLAN * Math.ceil(devs / 5);
  const saved = costWithout - costWith;

  document.getElementById('r-without').textContent = fmt(costWithout);
  document.getElementById('r-with').textContent = fmt(costWith);
  document.getElementById('r-save').textContent = saved > 0 ? fmt(saved) : '$0';

  const pb = document.getElementById('payback');
  const isEn = document.body.classList.contains('lang-en');
  if (saved > 0) {
    const days = Math.max(1, Math.round(GRAFF_PLAN / (saved / 30)));
    pb.innerHTML = isEn
      ? `<strong>Graff pays for itself in ~${days} day${days>1?'s':''}</strong> · ROI: ${Math.round(saved/GRAFF_PLAN)}×`
      : `<strong>Graff окупается за ~${days} ${days===1?'день':days<5?'дня':'дней'}</strong> · ROI: ${Math.round(saved/GRAFF_PLAN)}×`;
  } else {
    pb.innerHTML = '';
  }
}

function setLang(l) {
  document.body.className = 'lang-' + l;
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.toggle('active', b.textContent === l.toUpperCase()));
  localStorage.setItem('graff_lang', l);
  calc();
}

(function(){
  const s = localStorage.getItem('graff_lang');
  const nav = (navigator.language||'en').toLowerCase().startsWith('ru') ? 'ru' : 'en';
  setLang(s || nav);
  calc();
})();

async function signup() {
  const email = document.getElementById('email').value.trim();
  if (!email) return;
  try {
    const r = await fetch(BASE + '/api/register', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({email, plan:'free'})
    });
    const d = await r.json();
    if (r.ok) {
      document.getElementById('key-display').textContent = d.key;
      document.getElementById('curl-example').textContent =
        `curl -X POST ${window.location.origin}/graff/api/repos \\\n` +
        `  -H "X-Api-Key: ${d.key}" \\\n` +
        `  -H "Content-Type: application/json" \\\n` +
        `  -d '{"url":"https://github.com/your/repo"}'`;
      document.getElementById('msg-ok').style.display = 'block';
      document.getElementById('msg-err').style.display = 'none';
    } else {
      document.getElementById('msg-err').textContent = d.detail || 'Error';
      document.getElementById('msg-err').style.display = 'block';
    }
  } catch(e) {
    document.getElementById('msg-err').textContent = 'Network error';
    document.getElementById('msg-err').style.display = 'block';
  }
}
</script>
</body>
</html>"""
