"""Graff SaaS landing page — EN/RU bilingual."""

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Graff — Code Intelligence for AI Agents</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0d1117;color:#e6edf3;line-height:1.6}
a{color:#58a6ff;text-decoration:none}

/* lang switcher */
.lang-bar{text-align:right;padding:12px 24px;background:#161b22;border-bottom:1px solid #21262d}
.lang-btn{background:none;border:1px solid #30363d;color:#8b949e;padding:4px 14px;border-radius:20px;cursor:pointer;font-size:.85rem;margin-left:6px;transition:.2s}
.lang-btn.active,.lang-btn:hover{border-color:#58a6ff;color:#58a6ff}

.hero{text-align:center;padding:80px 20px 60px;background:linear-gradient(180deg,#161b22 0%,#0d1117 100%)}
.hero h1{font-size:3rem;font-weight:700;margin-bottom:16px;background:linear-gradient(135deg,#58a6ff,#3fb950);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero p{font-size:1.2rem;color:#8b949e;max-width:620px;margin:0 auto 32px}
.badge{display:inline-block;background:#21262d;border:1px solid #30363d;border-radius:6px;padding:4px 12px;font-size:.85rem;color:#8b949e;margin-bottom:24px}
.btn{display:inline-block;padding:12px 28px;border-radius:8px;font-weight:600;font-size:1rem;cursor:pointer;border:none;transition:.2s}
.btn-primary{background:#238636;color:#fff}
.btn-primary:hover{background:#2ea043}
.btn-outline{background:transparent;color:#58a6ff;border:1px solid #30363d;margin-left:12px}
.btn-outline:hover{border-color:#58a6ff}

.section{padding:60px 20px;max-width:1040px;margin:0 auto}
.section h2{font-size:1.8rem;font-weight:700;margin-bottom:32px;text-align:center}

.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px}
.step{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:24px}
.step .num{font-size:2rem;font-weight:700;color:#58a6ff;margin-bottom:8px}
.step h3{font-size:1rem;font-weight:600;margin-bottom:8px}
.step p{font-size:.9rem;color:#8b949e}
.step code{background:#0d1117;padding:2px 6px;border-radius:4px;font-size:.8rem;color:#3fb950}

.tools-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px}
.tool{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px}
.tool code{color:#58a6ff;font-size:.85rem}
.tool p{font-size:.8rem;color:#8b949e;margin-top:4px}

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

.signup-box{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:40px;max-width:500px;margin:0 auto;text-align:center}
.signup-box h2{margin-bottom:8px}
.signup-box .sub{color:#8b949e;margin-bottom:24px;font-size:.9rem}
.form-row{display:flex;gap:8px}
.form-row input{flex:1;background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:10px 14px;color:#e6edf3;font-size:.95rem;outline:none}
.form-row input:focus{border-color:#58a6ff}
.msg{margin-top:16px;padding:12px;border-radius:8px;font-size:.9rem;display:none}
.msg.ok{background:#0f3d1a;border:1px solid #238636;color:#3fb950}
.msg.err{background:#3d0f0f;border:1px solid #8b0000;color:#f85149}
.key-display{font-family:monospace;font-size:.8rem;word-break:break-all;margin-top:8px;padding:8px;background:#0d1117;border-radius:6px;border:1px solid #30363d}

.code-block{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;font-family:monospace;font-size:.85rem;color:#3fb950;text-align:left;overflow-x:auto;margin-top:8px}

footer{text-align:center;padding:40px 20px;color:#8b949e;font-size:.85rem;border-top:1px solid #21262d}

/* hide/show lang layers */
.en,.ru{display:none}
body.lang-en .en{display:revert}
body.lang-ru .ru{display:revert}
/* inline spans */
span.en,span.ru{display:none}
body.lang-en span.en{display:inline}
body.lang-ru span.ru{display:inline}
</style>
</head>
<body class="lang-en">

<!-- lang switcher -->
<div class="lang-bar">
  <button class="lang-btn active" onclick="setLang('en')">EN</button>
  <button class="lang-btn" onclick="setLang('ru')">RU</button>
</div>

<!-- HERO -->
<div class="hero">
  <div class="badge">🔍 Code Graph + MCP Server</div>
  <h1>Graff</h1>
  <p class="en">Symbol graph of your codebase as an MCP server — 14 tools for Claude Code, Cursor, and any AI agent. No installation required.</p>
  <p class="ru">Граф символов вашего кода как MCP-сервер — 14 инструментов для Claude Code, Cursor и любых AI-агентов. Без установки.</p>
  <a href="#signup" class="btn btn-primary"><span class="en">Get started free</span><span class="ru">Начать бесплатно</span></a>
  <a href="https://github.com/AItestsibiria/graff" class="btn btn-outline">GitHub</a>
</div>

<!-- HOW IT WORKS -->
<div class="section">
  <h2><span class="en">How it works</span><span class="ru">Как это работает</span></h2>
  <div class="steps">
    <div class="step">
      <div class="num">1</div>
      <h3><span class="en">Get an API key</span><span class="ru">Получите API-ключ</span></h3>
      <p class="en">Sign up with your email — free for 1 repo.</p>
      <p class="ru">Введите email — ключ сразу. Бесплатно для 1 репо.</p>
    </div>
    <div class="step">
      <div class="num">2</div>
      <h3><span class="en">Submit your repo</span><span class="ru">Отправьте репозиторий</span></h3>
      <p class="en"><code>POST /api/repos</code><br>Graff clones and indexes your GitHub repo into a symbol graph.</p>
      <p class="ru"><code>POST /api/repos</code><br>Graff клонирует и строит граф символов вашего репозитория.</p>
    </div>
    <div class="step">
      <div class="num">3</div>
      <h3><span class="en">Add to .mcp.json</span><span class="ru">Добавьте в .mcp.json</span></h3>
      <p class="en"><code>"url": "https://.../mcp/TOKEN"</code><br>Restart Claude Code — 14 tools are ready.</p>
      <p class="ru"><code>"url": "https://.../mcp/TOKEN"</code><br>Рестарт Claude Code — 14 инструментов активны.</p>
    </div>
    <div class="step">
      <div class="num">4</div>
      <h3><span class="en">Analyze your code</span><span class="ru">Анализируйте код</span></h3>
      <p class="en">Blast radius, symbol search, cross-stack tracing, dead code — right in chat.</p>
      <p class="ru">Blast radius, поиск символов, кросс-стек, мёртвый код — прямо в чате.</p>
    </div>
  </div>
</div>

<!-- TOOLS -->
<div class="section">
  <h2>14 MCP <span class="en">Tools</span><span class="ru">Инструментов</span></h2>
  <div class="tools-grid">
    <div class="tool"><code>graff_find</code>
      <p class="en">Search symbol → exact file + line</p>
      <p class="ru">Поиск символа → файл + строка</p></div>
    <div class="tool"><code>graff_context</code>
      <p class="en">360°: callers / callees / parent / children</p>
      <p class="ru">360°: кто вызывает / что вызывает / дети</p></div>
    <div class="tool"><code>graff_impact</code>
      <p class="en">Blast radius: what breaks if you change this</p>
      <p class="ru">Blast radius: что сломается при изменении</p></div>
    <div class="tool"><code>graff_flows</code>
      <p class="en">Trace call chains from any symbol</p>
      <p class="ru">Трассировка цепочек вызовов</p></div>
    <div class="tool"><code>graff_route_map</code>
      <p class="en">Cross-stack: frontend fetch ↔ API route</p>
      <p class="ru">Кросс-стек: фронт-fetch ↔ API-роут</p></div>
    <div class="tool"><code>graff_detect_changes</code>
      <p class="en">git diff → affected symbols + risk</p>
      <p class="ru">git-diff → затронутые символы + риск</p></div>
    <div class="tool"><code>graff_check</code>
      <p class="en">Rule guard: secrets, vulnerabilities</p>
      <p class="ru">Rule guard: секреты, уязвимости</p></div>
    <div class="tool"><code>graff_roles</code>
      <p class="en">File roles (spider/pipeline/route) + anomalies</p>
      <p class="ru">Роли файлов (паук/пайплайн/роут) + аномалии</p></div>
    <div class="tool"><code>graff_hotspots</code>
      <p class="en">Most depended-on symbols (change risk)</p>
      <p class="ru">Самые зависимые символы (риск изменения)</p></div>
    <div class="tool"><code>graff_deadcode</code>
      <p class="en">Dead code candidates (no incoming calls)</p>
      <p class="ru">Кандидаты в мёртвый код</p></div>
    <div class="tool"><code>graff_cycles</code>
      <p class="en">Circular imports detection</p>
      <p class="ru">Циклические импорты</p></div>
    <div class="tool"><code>graff_update</code>
      <p class="en">Incremental re-index (mtime-based)</p>
      <p class="ru">Инкрементальный реиндекс</p></div>
    <div class="tool"><code>graff_list_repos</code>
      <p class="en">List all indexed repositories</p>
      <p class="ru">Все проиндексированные репо</p></div>
    <div class="tool"><code>graff_status</code>
      <p class="en">Nodes / edges / languages / index time</p>
      <p class="ru">Узлы / связи / языки / время индексации</p></div>
  </div>
</div>

<!-- PLANS -->
<div class="section">
  <h2><span class="en">Pricing</span><span class="ru">Тарифы</span></h2>
  <div class="plans">
    <div class="plan">
      <h3>Free</h3>
      <div class="price">$0 <span>/ <span class="en">mo</span><span class="ru">мес</span></span></div>
      <ul>
        <li><span class="en">1 repository</span><span class="ru">1 репозиторий</span></li>
        <li><span class="en">14 MCP tools</span><span class="ru">14 MCP-инструментов</span></li>
        <li><span class="en">Python + 15 languages</span><span class="ru">Python + 15 языков</span></li>
        <li><span class="en">Public repos</span><span class="ru">Публичные репо</span></li>
      </ul>
      <a href="#signup" class="btn btn-outline"><span class="en">Start free</span><span class="ru">Начать</span></a>
    </div>
    <div class="plan popular">
      <div class="popular-badge"><span class="en">Popular</span><span class="ru">Популярный</span></div>
      <h3>Pro</h3>
      <div class="price">$20 <span>/ <span class="en">mo</span><span class="ru">мес</span></span></div>
      <ul>
        <li><span class="en">5 repositories</span><span class="ru">5 репозиториев</span></li>
        <li><span class="en">14 MCP tools</span><span class="ru">14 MCP-инструментов</span></li>
        <li><span class="en">Private repos (PAT)</span><span class="ru">Приватные репо (PAT)</span></li>
        <li><span class="en">Priority indexing</span><span class="ru">Приоритетная индексация</span></li>
      </ul>
      <a href="#signup" class="btn btn-primary"><span class="en">Try Pro</span><span class="ru">Попробовать</span></a>
    </div>
    <div class="plan">
      <h3>Team</h3>
      <div class="price">$50 <span>/ <span class="en">mo</span><span class="ru">мес</span></span></div>
      <ul>
        <li><span class="en">Unlimited repos</span><span class="ru">Неограниченно репо</span></li>
        <li><span class="en">14 MCP tools</span><span class="ru">14 MCP-инструментов</span></li>
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
    <h2><span class="en">Get started free</span><span class="ru">Начать бесплатно</span></h2>
    <p class="sub en">Enter your email — we'll send your API key instantly.</p>
    <p class="sub ru">Введите email — ключ придёт сразу.</p>
    <div class="form-row">
      <input type="email" id="email" placeholder="you@example.com">
      <button class="btn btn-primary" onclick="signup()">
        <span class="en">Get key</span><span class="ru">Получить ключ</span>
      </button>
    </div>
    <div class="msg ok" id="msg-ok">
      <span class="en">Your API key (save it):</span>
      <span class="ru">Ваш API-ключ (сохраните):</span>
      <div class="key-display" id="key-display"></div>
      <div style="margin-top:12px;font-size:.85rem;color:#8b949e">
        <span class="en">Add your repo:</span><span class="ru">Добавьте репо:</span>
        <div class="code-block" id="curl-example"></div>
      </div>
    </div>
    <div class="msg err" id="msg-err"></div>
  </div>
</div>

<footer>
  Graff — open source ·
  <a href="https://github.com/AItestsibiria/graff">GitHub</a> ·
  <span class="en">Built for AI-first development</span>
  <span class="ru">Создан для AI-разработки</span>
</footer>

<script>
const BASE = window.location.origin + '/graff';

function setLang(l) {
  document.body.className = 'lang-' + l;
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.toggle('active', b.textContent === l.toUpperCase()));
  localStorage.setItem('graff_lang', l);
}

(function(){
  const saved = localStorage.getItem('graff_lang');
  const nav = (navigator.language || 'en').toLowerCase().startsWith('ru') ? 'ru' : 'en';
  setLang(saved || nav);
})();

async function signup() {
  const email = document.getElementById('email').value.trim();
  if (!email) return;
  try {
    const r = await fetch(BASE + '/api/register', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({email, plan:'free'})
    });
    const d = await r.json();
    if (r.ok) {
      document.getElementById('key-display').textContent = d.key;
      document.getElementById('curl-example').textContent =
        `curl -X POST ${BASE}/api/repos \\\n  -H "X-Api-Key: ${d.key}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"url":"https://github.com/your/repo"}'`;
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
