import os

src_dir = r"C:\Users\march\.gemini\antigravity\scratch\deepwoken-spy\src"
main_file = os.path.join(src_dir, "main.js")
index_file = r"C:\Users\march\.gemini\antigravity\scratch\deepwoken-spy\index.html"

index_html = r'''<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Deepwoken Spy — 100% БЕЗ ЛАГОВ</title>
  <link rel="stylesheet" href="./src/style.css">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🕵️</text></svg>">
</head>
<body>
  <!-- Canvas background particle effects -->
  <canvas id="bgCanvas" class="bg-decor"></canvas>

  <div class="container">
    <!-- Header -->
    <header class="app-header">
      <div class="header-top">
        <h1 class="app-title">DEEPWOKEN SPY</h1>
        <button id="btn-sound-toggle" class="icon-btn" title="Звуки игры">🔊</button>
      </div>
      <p class="app-subtitle">Шпионская игра в сеттинге Глубин & Островов</p>
    </header>

    <!-- SCREEN 1: Home / Main Menu -->
    <div id="screen-home" class="screen active">
      <div class="glass-card text-center">
        <h2 class="section-heading" style="color: var(--gold-rune);">Выбор Режима</h2>
        <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 20px;">
          Сервера больше не нужны! Игра работает 100% без лагов и отключений.
        </p>

        <button id="btn-show-discord" class="btn btn-primary" style="margin-bottom: 12px; height: 60px;">
          <span>🎮 ИГРА С ДРУЗЬЯМИ (Discord)</span>
        </button>

        <button id="btn-start-passplay" class="btn btn-secondary" style="height: 60px;">
          <span>📱 ПЕРЕДАЙ ТЕЛЕФОН (1 устройство)</span>
        </button>
      </div>
    </div>

    <!-- SCREEN 2: Discord Sync Setup -->
    <div id="screen-discord-setup" class="screen">
      <div class="glass-card">
        <h2 class="section-heading" style="color: var(--ether-cyan);">Настройка Комнаты</h2>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 20px;">
          Договоритесь в Discord о коде и ваших номерах. Все, кто введёт одинаковые данные, получат одинаковую игру!
        </p>

        <div class="form-group">
          <label class="form-label" for="ds-room-code">1. Придумайте любой код комнаты:</label>
          <input type="text" id="ds-room-code" class="form-input code-input" placeholder="НАПРИМЕР: 1234" maxlength="6" autocomplete="off" style="letter-spacing: 4px;">
        </div>

        <div class="grid-2col">
          <div class="form-group">
            <label class="form-label" for="ds-player-total">2. Сколько вас всего?</label>
            <input type="number" id="ds-player-total" class="form-input" min="3" max="15" value="4">
          </div>
          <div class="form-group">
            <label class="form-label" for="ds-spies-count">Кол-во шпионов:</label>
            <select id="ds-spies-count" class="form-input">
              <option value="1">1 Шпион</option>
              <option value="2">2 Шпиона</option>
            </select>
          </div>
        </div>

        <div class="form-group" style="margin-top: 10px;">
          <label class="form-label" for="ds-my-number" style="color: var(--gold-rune);">3. ТВОЙ личный номер (от 1 до <span id="ds-total-display">4</span>):</label>
          <input type="number" id="ds-my-number" class="form-input" min="1" max="15" value="1" style="border-color: var(--gold-rune); box-shadow: 0 0 10px rgba(212, 175, 55, 0.2);">
        </div>

        <div class="form-group" style="margin-top: 15px;">
          <label class="form-label">4. Категории карточек (у всех должны быть одинаковые!)</label>
          <div id="ds-categories-container" class="categories-grid"></div>
        </div>

        <button id="btn-ds-start" class="btn btn-primary" style="margin-top: 10px; height: 60px;">🚀 ВОЙТИ И ПОЛУЧИТЬ КАРТОЧКУ</button>
        <button id="btn-back-home-1" class="btn btn-secondary">Назад</button>
      </div>
    </div>

    <!-- SCREEN 3: Playing Game (Discord Sync Mode) -->
    <div id="screen-game" class="screen">
      <div class="glass-card">
        <!-- Circle & Speaker Status HUD -->
        <div class="circle-hud">
          <div class="circle-top-row">
            <span class="circle-badge">КОД: <strong id="game-code-display" style="color: white;">1234</strong></span>
            <span id="circle-status-text" class="circle-status">Игра в процессе</span>
          </div>

          <div id="speaker-box" class="speaker-banner">
            <span class="mic-icon pulse-mic">🎤</span>
            <div class="speaker-text-wrap">
              <span class="speaker-label">ОБЩАЙТЕСЬ В DISCORD!</span>
              <strong id="speaker-name-display" class="speaker-name">Твой номер: Игрок <span id="my-number-display">1</span></strong>
            </div>
          </div>
        </div>

        <!-- Secret Card -->
        <div class="card-wrapper">
          <div id="secret-role-card" class="secret-card">
            <span id="card-category-label" class="card-category">DEEPWOKEN</span>
            <h3 id="card-word-label" class="card-word">Загрузка карточки...</h3>
            <div id="card-role-label" class="card-role">Слушайте игроков в Discord...</div>
          </div>
        </div>

        <div class="turn-order-container">
          <span class="turn-order-title">Список Игроков (договоритесь, кто говорит первым):</span>
          <div id="turn-order-chips" class="turn-chips-list"></div>
        </div>

        <div class="decision-box" style="margin-top: 20px;">
          <p class="decision-title">Как играть?</p>
          <p class="decision-desc">Каждый по кругу называет ассоциацию к слову. Когда пройдете 3 круга, проведите голосование в Discord и нажмите кнопку ниже, чтобы узнать правду!</p>
          <button id="btn-reveal-spies" class="btn btn-crimson" style="margin-top: 15px;">👁️ ПОКАЗАТЬ, КТО БЫЛ ШПИОНОМ</button>
        </div>
      </div>
    </div>

    <!-- SCREEN 4: Reveal / Results -->
    <div id="screen-reveal" class="screen">
      <div class="glass-card text-center">
        <h2 id="reveal-title" class="reveal-title" style="color: var(--ether-cyan);">ИТОГИ ИГРЫ</h2>
        
        <div class="reveal-info-box">
          <span class="reveal-meta-label">Секретная карточка Deepwoken:</span>
          <h3 id="reveal-secret-word" class="reveal-word">Blindseer</h3>
          
          <div style="margin-top: 15px;">
            <span class="reveal-meta-label" style="color: var(--crimson-blood);">Шпионом был:</span>
            <h3 id="reveal-spy-names" class="reveal-spies" style="font-size: 1.8rem; margin-top: 5px; color: var(--crimson-blood);">Игрок 3</h3>
          </div>
        </div>

        <div class="decision-box" style="margin-top: 20px;">
          <p class="decision-desc">Если вы угадали шпиона — победили мирные! Если нет, или шпион назвал ваше слово — победил шпион!</p>
        </div>

        <button id="btn-next-round" class="btn btn-primary" style="margin-top: 20px; height: 50px;">🔄 НАЧАТЬ НОВЫЙ РАУНД</button>
        <button id="btn-return-lobby" class="btn btn-secondary" style="margin-top: 10px;">🚪 Вернуться в Главное Меню</button>
      </div>
    </div>

    <!-- SCREEN 5: Pass & Play Mode (Local Offline) -->
    <div id="screen-passplay-setup" class="screen">
      <div class="glass-card">
        <h2 class="section-heading" style="color: var(--gold-rune);">Настройка "Передай Телефон"</h2>
        
        <div class="form-group">
          <label class="form-label" for="pp-player-count">Количество игроков</label>
          <input type="number" id="pp-player-count" class="form-input" min="3" max="15" value="4">
        </div>

        <div class="form-group">
          <label class="form-label">Категории</label>
          <div id="pp-categories-container" class="categories-grid"></div>
        </div>

        <button id="btn-pp-start" class="btn btn-primary" style="height: 60px; margin-top: 10px;">Начать Игру</button>
        <button id="btn-back-home-2" class="btn btn-secondary">Назад</button>
      </div>
    </div>

    <div id="screen-passplay-curtain" class="screen">
      <div class="glass-card text-center">
        <h3 class="section-heading" style="color: var(--gold-rune); margin-bottom: 12px;">Передайте телефон игроку №<span id="pp-current-player-num">1</span></h3>
        
        <div id="pp-reveal-trigger" class="privacy-curtain">
          <span style="font-size: 2.5rem; display: block; margin-bottom: 10px;">👁️</span>
          <span style="font-weight: 700; color: var(--ether-cyan);">НАЖМИТЕ, ЧТОБЫ ПОСМОТРЕТЬ КАРТОЧКУ</span>
        </div>
      </div>
    </div>

    <div id="screen-passplay-card" class="screen">
      <div class="glass-card text-center">
        <h4 style="color: var(--text-muted); margin-bottom: 10px;">Игрок №<span id="pp-card-player-num">1</span></h4>
        
        <div class="card-wrapper">
          <div id="pp-secret-card" class="secret-card">
            <span id="pp-card-cat" class="card-category">📜 КЛЯТВЫ</span>
            <h3 id="pp-card-word" class="card-word">Blindseer</h3>
            <span id="pp-card-role" class="card-role">Роль: Игрок</span>
          </div>
        </div>

        <button id="btn-pp-next-player" class="btn btn-primary" style="height: 60px; margin-top: 15px;">Скрыть и Передать Игроку №<span id="pp-next-player-num">2</span></button>
      </div>
    </div>
  </div>

  <!-- Deepwoken Dataset -->
  <script src="./src/data/deepwokenWords.js"></script>
  <!-- Main Game Client Script (100% Offline Deterministic Engine) -->
  <script src="./src/main.js"></script>
</body>
</html>
'''

js_code = r'''// =========================================================================
// --- DEEPWOKEN SPY: DETERMINISTIC OFFLINE ENGINE (100% ZERO NETWORK BUGS) ---
// =========================================================================

let currentScreen = 'screen-home';
let soundEnabled = true;

// Active Deterministic State
let gameState = {
  mode: null, // 'discord' or 'passplay'
  roomCode: '',
  totalPlayers: 4,
  myNumber: 1,
  spiesCount: 1,
  categories: [],
  secretWord: '',
  secretCat: '',
  spyIndices: [],
  roundSeed: 1
};

// --- Seeded PRNG (Mulberry32) ---
// Ensures that if everyone enters the same code and settings, they get the EXACT same result!
function cyrb128(str) {
    let h1 = 1779033703, h2 = 3144134277,
        h3 = 1013904242, h4 = 2773480762;
    for (let i = 0, k; i < str.length; i++) {
        k = str.charCodeAt(i);
        h1 = h2 ^ Math.imul(h1 ^ k, 597399067);
        h2 = h3 ^ Math.imul(h2 ^ k, 2869860233);
        h3 = h4 ^ Math.imul(h3 ^ k, 951274213);
        h4 = h1 ^ Math.imul(h4 ^ k, 2716044179);
    }
    h1 = Math.imul(h3 ^ (h1 >>> 18), 597399067);
    h2 = Math.imul(h4 ^ (h2 >>> 22), 2869860233);
    h3 = Math.imul(h1 ^ (h3 >>> 17), 951274213);
    h4 = Math.imul(h2 ^ (h4 >>> 19), 2716044179);
    return [(h1^h2^h3^h4)>>>0, (h2^h1)>>>0, (h3^h1)>>>0, (h4^h1)>>>0];
}

function mulberry32(a) {
    return function() {
      var t = a += 0x6D2B79F5;
      t = Math.imul(t ^ t >>> 15, t | 1);
      t ^= t + Math.imul(t ^ t >>> 7, t | 61);
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    }
}

// --- Web Audio Synthesizer (Deepwoken SFX) ---
let audioCtx = null;
function getAudioContext() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  return audioCtx;
}

function playSound(type) {
  if (!soundEnabled) return;
  try {
    const ctx = getAudioContext();
    if (ctx.state === 'suspended') ctx.resume();

    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    if (type === 'bell') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(523.25, now);
      osc.frequency.exponentialRampToValueAtTime(1046.5, now + 1.2);
      gain.gain.setValueAtTime(0.4, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 1.5);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 1.5);
    } else if (type === 'vote') {
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(300, now);
      osc.frequency.exponentialRampToValueAtTime(150, now + 0.4);
      gain.gain.setValueAtTime(0.25, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.4);
    }
  } catch (e) {}
}

// --- Background Particles Animation ---
function initCanvasParticles() {
  const canvas = document.getElementById('bgCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  
  let width = canvas.width = window.innerWidth;
  let height = canvas.height = window.innerHeight;

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const particles = [];
  for (let i = 0; i < 50; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: Math.random() * 2.2 + 0.6,
      color: Math.random() > 0.35 ? '#00f0ff' : '#d4af37',
      alpha: Math.random() * 0.45 + 0.2,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35
    });
  }

  function render() {
    ctx.clearRect(0, 0, width, height);
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = p.alpha;
      ctx.shadowBlur = 12;
      ctx.shadowColor = p.color;
      ctx.fill();
    });
    requestAnimationFrame(render);
  }
  render();
}

// --- UI Navigation ---
function showScreen(screenId) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const target = document.getElementById(screenId);
  if (target) {
    target.classList.add('active');
    currentScreen = screenId;
  }
}

function showToast(msg) {
  const toast = document.createElement('div');
  toast.className = 'error-toast';
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

function escapeHTML(str) {
  return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// --- Categories ---
function renderCategoryOptions(containerId, initialSelected) {
  const selected = initialSelected || ['oaths', 'attunements', 'races', 'bosses', 'bells'];
  const container = document.getElementById(containerId);
  if (!container || typeof DEEPWOKEN_DATA === 'undefined') return;

  container.innerHTML = '';
  Object.entries(DEEPWOKEN_DATA.categories).forEach(([key, cat]) => {
    const isChecked = selected.includes(key);
    const chip = document.createElement('label');
    chip.className = 'category-chip ' + (isChecked ? 'selected' : '');
    chip.innerHTML = `
      <input type="checkbox" value="${key}" ${isChecked ? 'checked' : ''}>
      <span>${cat.name}</span>
    `;

    chip.querySelector('input').addEventListener('change', (e) => {
      if (e.target.checked) chip.classList.add('selected');
      else chip.classList.remove('selected');
    });

    container.appendChild(chip);
  });
}

function getSelectedCategories(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return ['oaths'];
  const checked = container.querySelectorAll('input:checked');
  return Array.from(checked).map(input => input.value);
}

// =========================================================================
// --- GAME LOGIC (DETERMINISTIC GENERATION) ---
// =========================================================================

function generateDeterministicGame() {
  const seedString = `${gameState.roomCode}_${gameState.totalPlayers}_${gameState.spiesCount}_${gameState.categories.sort().join('')}_R${gameState.roundSeed}`;
  const seed = cyrb128(seedString)[0];
  const rand = mulberry32(seed);

  // 1. Pick Category
  const catKey = gameState.categories[Math.floor(rand() * gameState.categories.length)];
  const catData = DEEPWOKEN_DATA.categories[catKey];
  
  // 2. Pick Word
  const chosenItem = catData.items[Math.floor(rand() * catData.items.length)];
  
  // 3. Pick Spies
  let availableIndices = [];
  for (let i = 1; i <= gameState.totalPlayers; i++) availableIndices.push(i);
  
  gameState.spyIndices = [];
  for (let i = 0; i < gameState.spiesCount; i++) {
    if (availableIndices.length === 0) break;
    const rIdx = Math.floor(rand() * availableIndices.length);
    gameState.spyIndices.push(availableIndices.splice(rIdx, 1)[0]);
  }

  gameState.secretWord = chosenItem.name;
  gameState.secretCat = catData.name;
  gameState.roles = chosenItem.roles || ['Мирный Житель'];
}

function startDiscordSyncGame() {
  const code = document.getElementById('ds-room-code').value.trim().toUpperCase();
  const total = parseInt(document.getElementById('ds-player-total').value);
  const myNum = parseInt(document.getElementById('ds-my-number').value);
  const spies = parseInt(document.getElementById('ds-spies-count').value);
  const cats = getSelectedCategories('ds-categories-container');

  if (!code) return showToast('Введите код комнаты!');
  if (cats.length === 0) return showToast('Выберите категории!');
  if (myNum > total) return showToast('Твой номер не может быть больше количества игроков!');

  gameState.mode = 'discord';
  gameState.roomCode = code;
  gameState.totalPlayers = total;
  gameState.myNumber = myNum;
  gameState.spiesCount = spies;
  gameState.categories = cats;
  
  generateDeterministicGame();
  
  // Render Game Screen
  document.getElementById('game-code-display').textContent = code;
  document.getElementById('my-number-display').textContent = myNum;

  const isSpy = gameState.spyIndices.includes(myNum);
  
  const cardEl = document.getElementById('secret-role-card');
  const catLabel = document.getElementById('card-category-label');
  const wordEl = document.getElementById('card-word-label');
  const roleEl = document.getElementById('card-role-label');

  catLabel.textContent = gameState.secretCat;

  if (isSpy) {
    cardEl.classList.add('spy-card');
    cardEl.style.borderColor = 'var(--crimson-blood)';
    wordEl.textContent = '🕵️ ТЫ ШПИОН!';
    wordEl.classList.add('spy-text');
    roleEl.innerHTML = `
      <strong style="color: var(--gold-rune); display: block; margin-bottom: 4px;">Категория раунда: ${escapeHTML(gameState.secretCat)}</strong>
      <span>Ты НЕ знаешь слово! Внимательно слушай других игроков в Discord и притворяйся мирным!</span>
    `;
  } else {
    cardEl.classList.remove('spy-card');
    cardEl.style.borderColor = 'var(--ether-cyan)';
    wordEl.textContent = gameState.secretWord;
    wordEl.classList.remove('spy-text');
    roleEl.innerHTML = `
      <strong style="color: var(--ether-cyan); display: block; margin-bottom: 4px;">Роль: Мирный</strong>
      <span>Давай ассоциации в Discord так, чтобы поняли свои, но не догадался шпион!</span>
    `;
  }

  // Render player list
  const chipsContainer = document.getElementById('turn-order-chips');
  chipsContainer.innerHTML = '';
  for (let i = 1; i <= total; i++) {
    const chip = document.createElement('span');
    chip.className = 'turn-chip ' + (i === myNum ? 'active' : '');
    chip.textContent = (i === myNum) ? `Игрок ${i} (Ты)` : `Игрок ${i}`;
    chipsContainer.appendChild(chip);
  }

  playSound('bell');
  showScreen('screen-game');
}

// --- DOM Bindings ---
document.addEventListener('DOMContentLoaded', () => {
  initCanvasParticles();
  renderCategoryOptions('ds-categories-container');
  renderCategoryOptions('pp-categories-container');

  // Sound toggle
  document.getElementById('btn-sound-toggle').addEventListener('click', (e) => {
    soundEnabled = !soundEnabled;
    e.currentTarget.textContent = soundEnabled ? '🔊' : '🔇';
    showToast(soundEnabled ? 'Звуки включены' : 'Звуки выключены');
  });

  // Flow Navigation
  document.getElementById('btn-show-discord').addEventListener('click', () => {
    // Generate a random code to suggest
    document.getElementById('ds-room-code').value = Math.floor(1000 + Math.random() * 9000).toString();
    showScreen('screen-discord-setup');
  });

  document.getElementById('btn-start-passplay').addEventListener('click', () => {
    showScreen('screen-passplay-setup');
  });

  document.getElementById('btn-back-home-1').addEventListener('click', () => showScreen('screen-home'));
  document.getElementById('btn-back-home-2').addEventListener('click', () => showScreen('screen-home'));

  // Player Total change -> update max for my number
  document.getElementById('ds-player-total').addEventListener('input', (e) => {
    const total = parseInt(e.target.value) || 4;
    document.getElementById('ds-total-display').textContent = total;
    document.getElementById('ds-my-number').max = total;
  });

  // Start Discord Sync
  document.getElementById('btn-ds-start').addEventListener('click', startDiscordSyncGame);

  // Reveal Spies
  document.getElementById('btn-reveal-spies').addEventListener('click', () => {
    playSound('vote');
    document.getElementById('reveal-secret-word').textContent = `${gameState.secretWord} (${gameState.secretCat})`;
    
    const spiesText = gameState.spyIndices.map(i => `Игрок ${i}`).join(', ');
    document.getElementById('reveal-spy-names').textContent = spiesText;
    
    showScreen('screen-reveal');
  });

  // Next Round
  document.getElementById('btn-next-round').addEventListener('click', () => {
    gameState.roundSeed++;
    startDiscordSyncGame(); // Regenerate with new round seed
  });

  document.getElementById('btn-return-lobby').addEventListener('click', () => {
    showScreen('screen-discord-setup');
  });


  // ==========================================
  // PASS & PLAY (1 DEVICE)
  // ==========================================
  document.getElementById('btn-pp-start').addEventListener('click', () => {
    const count = parseInt(document.getElementById('pp-player-count').value) || 4;
    const cats = getSelectedCategories('pp-categories-container');
    if (cats.length === 0) return showToast('Выберите хотя бы одну категорию!');
    if (count < 3) return showToast('Минимум 3 игрока!');

    const catKey = cats[Math.floor(Math.random() * cats.length)];
    const catData = DEEPWOKEN_DATA.categories[catKey];
    const chosenItem = catData.items[Math.floor(Math.random() * catData.items.length)];
    const spyIdx = Math.floor(Math.random() * count);

    passPlayState = {
      playerCount: count,
      currentPlayerIdx: 0,
      spyIdx: spyIdx,
      secretWord: chosenItem.name,
      secretCat: catData.name,
      roles: chosenItem.roles || ['Мирный Житель']
    };

    setupPassPlayPlayerTurn(0);
  });

  document.getElementById('pp-reveal-trigger').addEventListener('click', () => {
    const idx = passPlayState.currentPlayerIdx;
    const isSpy = (idx === passPlayState.spyIdx);

    document.getElementById('pp-card-player-num').textContent = idx + 1;
    document.getElementById('pp-card-cat').textContent = passPlayState.secretCat;
    
    const cardEl = document.getElementById('pp-secret-card');
    const wordEl = document.getElementById('pp-card-word');
    const roleEl = document.getElementById('pp-card-role');

    if (isSpy) {
      cardEl.classList.add('spy-card');
      wordEl.textContent = '🕵️ ВЫ ШПИОН!';
      wordEl.classList.add('spy-text');
      roleEl.textContent = 'Запомните категорию и не выдавайте себя при обсуждении!';
    } else {
      cardEl.classList.remove('spy-card');
      wordEl.textContent = passPlayState.secretWord;
      wordEl.classList.remove('spy-text');
      const randomRole = passPlayState.roles[Math.floor(Math.random() * passPlayState.roles.length)];
      roleEl.textContent = `Роль: ${randomRole}`;
    }

    const nextBtn = document.getElementById('btn-pp-next-player');
    if (idx + 1 >= passPlayState.playerCount) {
      nextBtn.textContent = 'Завершить раздачу и узнать шпиона';
    } else {
      nextBtn.textContent = `Скрыть и передать Игроку №${idx + 2}`;
    }

    playSound('bell');
    showScreen('screen-passplay-card');
  });

  document.getElementById('btn-pp-next-player').addEventListener('click', () => {
    passPlayState.currentPlayerIdx++;
    if (passPlayState.currentPlayerIdx >= passPlayState.playerCount) {
      
      // Show reveal screen for pass and play
      gameState.secretWord = passPlayState.secretWord;
      gameState.secretCat = passPlayState.secretCat;
      gameState.spyIndices = [passPlayState.spyIdx + 1];
      
      document.getElementById('reveal-secret-word').textContent = `${gameState.secretWord} (${gameState.secretCat})`;
      document.getElementById('reveal-spy-names').textContent = `Игрок ${passPlayState.spyIdx + 1}`;
      
      showScreen('screen-reveal');

    } else {
      setupPassPlayPlayerTurn(passPlayState.currentPlayerIdx);
    }
  });
});

function setupPassPlayPlayerTurn(playerIdx) {
  document.getElementById('pp-current-player-num').textContent = playerIdx + 1;
  showScreen('screen-passplay-curtain');
}
'''

with open(index_file, "w", encoding="utf-8") as f:
    f.write(index_html)

with open(main_file, "w", encoding="utf-8") as f:
    f.write(js_code)

print("SUCCESS: Discord Sync mode built! index.html and main.js updated.")
