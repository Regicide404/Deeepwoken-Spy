// =========================================================================
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
