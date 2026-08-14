// --- Deepwoken Spy Client Logic (Production Cloud Server API) ---

let currentScreen = 'screen-home';
let myPlayerName = '';
let currentRoomCode = '';
let myPlayerId = '';
let isHost = false;
let pollInterval = null;
let lastKnownState = '';

let selectedVoteTargetId = null;

// Local Pass & Play State
let passPlayState = {
  playerCount: 4,
  selectedCategories: ['oaths', 'attunements', 'races', 'bosses', 'bells'],
  currentPlayerIdx: 0,
  spyIdx: 0,
  secretWord: '',
  secretCat: '',
  roles: []
};

// --- Web Audio API Synthesizer (Deepwoken Chimes & SFX) ---
let audioCtx = null;
function getAudioContext() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  return audioCtx;
}

function playBellSound() {
  try {
    const ctx = getAudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = 'sine';
    osc.frequency.setValueAtTime(440, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 1.2);
    
    gain.gain.setValueAtTime(0.5, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.5);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    osc.start();
    osc.stop(ctx.currentTime + 1.5);
  } catch (e) {}
}

function playTickSound() {
  try {
    const ctx = getAudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(600, ctx.currentTime);
    gain.gain.setValueAtTime(0.1, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.08);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    osc.start();
    osc.stop(ctx.currentTime + 0.08);
  } catch (e) {}
}

// --- Background Particles ---
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
  for (let i = 0; i < 45; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: Math.random() * 2.5 + 0.5,
      color: Math.random() > 0.3 ? '#00f0ff' : '#d4af37',
      alpha: Math.random() * 0.5 + 0.2,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4
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
      ctx.shadowBlur = 10;
      ctx.shadowColor = p.color;
      ctx.fill();
    });
    requestAnimationFrame(render);
  }
  render();
}

// --- Navigation & Helper Tools ---
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

// --- Category Checkboxes Rendering ---
function renderCategoryOptions(containerId, initialSelected = ['oaths', 'attunements', 'races', 'bosses', 'bells']) {
  const container = document.getElementById(containerId);
  if (!container || typeof DEEPWOKEN_DATA === 'undefined') return;

  container.innerHTML = '';
  Object.entries(DEEPWOKEN_DATA.categories).forEach(([key, cat]) => {
    const isChecked = initialSelected.includes(key);
    const chip = document.createElement('label');
    chip.className = `category-chip ${isChecked ? 'selected' : ''}`;
    
    chip.innerHTML = `
      <input type="checkbox" value="${key}" ${isChecked ? 'checked' : ''}>
      <span>${cat.name}</span>
    `;

    chip.querySelector('input').addEventListener('change', (e) => {
      if (e.target.checked) chip.classList.add('selected');
      else chip.classList.remove('selected');

      if (containerId === 'lobby-categories-container' && isHost) {
        syncSettingsToServer();
      }
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

// --- Online Room Server Communications ---
async function createRoomServer() {
  try {
    const res = await fetch('/api/create_room', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playerName: myPlayerName })
    });
    const data = await res.json();
    if (data.error) return showToast(data.error);

    currentRoomCode = data.roomCode;
    myPlayerId = data.playerId;
    isHost = true;

    showScreen('screen-lobby');
    startRoomPolling();
  } catch (err) {
    showToast('Ошибка подключения к серверу!');
  }
}

async function joinRoomServer(code) {
  try {
    const res = await fetch('/api/join_room', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ roomCode: code, playerName: myPlayerName })
    });
    const data = await res.json();
    if (data.error) return showToast(data.error);

    currentRoomCode = data.roomCode;
    myPlayerId = data.playerId;
    isHost = false;

    showScreen('screen-lobby');
    startRoomPolling();
  } catch (err) {
    showToast('Ошибка при входе в комнату! Проверьте код.');
  }
}

function startRoomPolling() {
  if (pollInterval) clearInterval(pollInterval);
  fetchRoomState();
  pollInterval = setInterval(fetchRoomState, 1000);
}

async function fetchRoomState() {
  if (!currentRoomCode || !myPlayerId) return;
  try {
    const res = await fetch(`/api/room_state?code=${currentRoomCode}&player_id=${myPlayerId}`);
    if (!res.ok) return;
    const room = await res.json();

    isHost = (room.hostId === myPlayerId);

    if (room.state === 'LOBBY') {
      updateLobbyUI(room);
      if (currentScreen !== 'screen-lobby') showScreen('screen-lobby');
    } else if (room.state === 'PLAYING') {
      if (lastKnownState !== 'PLAYING') {
        playBellSound();
        renderPlayingCardUI(room.myRole);
        showScreen('screen-game');
      }

      document.getElementById('game-circle-num').textContent = room.circleNum || 1;
      const speakerName = room.currentSpeaker ? room.currentSpeaker.name : 'Игрок';
      document.getElementById('speaker-name-display').textContent = speakerName;

      const passBtn = document.getElementById('btn-pass-turn');
      const waitMsg = document.getElementById('not-my-turn-msg');

      if (room.isMyTurn) {
        passBtn.style.display = 'inline-flex';
        waitMsg.style.display = 'none';
      } else {
        passBtn.style.display = 'none';
        waitMsg.style.display = 'block';
        waitMsg.textContent = `Сейчас говорит ${speakerName}. Ожидайте свою очередь...`;
      }

      const decisionPanel = document.getElementById('circle-decision-panel');
      if (room.circleNum >= 3) {
        decisionPanel.style.display = 'block';
        document.getElementById('next-circle-num').textContent = room.circleNum + 1;
      } else {
        decisionPanel.style.display = 'none';
      }

    } else if (room.state === 'VOTING') {
      if (lastKnownState !== 'VOTING') {
        renderVotingUI(room);
        showScreen('screen-voting');
      }
      document.getElementById('votes-cast-count').textContent = room.totalVotes || 0;
      document.getElementById('votes-required-count').textContent = room.players.length;

    } else if (room.state === 'SPY_GUESS') {
      if (lastKnownState !== 'SPY_GUESS') {
        renderSpyGuessScreen(room.myRole);
        showScreen('screen-spy-guess');
      }
    } else if (room.state === 'REVEAL') {
      if (lastKnownState !== 'REVEAL' && room.revealData) {
        playBellSound();
        renderGameResultsUI(room.revealData);
        showScreen('screen-reveal');
      }
    }

    lastKnownState = room.state;
  } catch (err) {}
}

async function syncSettingsToServer() {
  if (!isHost || !currentRoomCode) return;
  const spyCount = parseInt(document.getElementById('lobby-spies-select').value) || 1;
  const cats = getSelectedCategories('lobby-categories-container');

  fetch('/api/update_settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      roomCode: currentRoomCode,
      playerId: myPlayerId,
      settings: {
        selectedCategories: cats,
        spyCount: spyCount
      }
    })
  });
}

async function startGameServer() {
  if (!isHost || !currentRoomCode) return;
  try {
    const res = await fetch('/api/start_game', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        roomCode: currentRoomCode,
        playerId: myPlayerId
      })
    });
    const data = await res.json();
    if (data.error) showToast(data.error);
  } catch (err) {
    showToast('Ошибка при запуске игры!');
  }
}

async function passTurnServer() {
  if (!currentRoomCode) return;
  fetch('/api/pass_turn', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ roomCode: currentRoomCode, playerId: myPlayerId })
  });
}

async function startNextCircleServer() {
  if (!currentRoomCode) return;
  fetch('/api/start_next_circle', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ roomCode: currentRoomCode })
  });
}

async function triggerVotingServer() {
  if (!currentRoomCode) return;
  fetch('/api/start_voting', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ roomCode: currentRoomCode })
  });
}

async function submitVoteServer() {
  if (!selectedVoteTargetId || !currentRoomCode) return;
  fetch('/api/cast_vote', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      roomCode: currentRoomCode,
      playerId: myPlayerId,
      targetId: selectedVoteTargetId
    })
  });
  const btn = document.getElementById('btn-submit-vote');
  btn.disabled = true;
  btn.textContent = 'ГОЛОС ПРИНЯТ';
}

async function submitSpyGuessServer(word) {
  if (!currentRoomCode || !word) return;
  fetch('/api/spy_guess', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      roomCode: currentRoomCode,
      playerId: myPlayerId,
      guessedWord: word
    })
  });
}

async function resetToLobbyServer() {
  if (!isHost || !currentRoomCode) return;
  fetch('/api/reset_to_lobby', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ roomCode: currentRoomCode, playerId: myPlayerId })
  });
}

// --- DOM Initialisation ---
document.addEventListener('DOMContentLoaded', () => {
  initCanvasParticles();
  renderCategoryOptions('lobby-categories-container');
  renderCategoryOptions('pp-categories-container');

  const savedName = localStorage.getItem('deepwoken_spy_name');
  if (savedName) {
    document.getElementById('player-name-input').value = savedName;
  }

  document.getElementById('btn-create-online').addEventListener('click', () => {
    const name = document.getElementById('player-name-input').value.trim();
    if (!name) return showToast('Введите ваш Никнейм!');
    localStorage.setItem('deepwoken_spy_name', name);
    myPlayerName = name;
    createRoomServer();
  });

  document.getElementById('btn-show-join').addEventListener('click', () => {
    const name = document.getElementById('player-name-input').value.trim();
    if (!name) return showToast('Введите ваш Никнейм!');
    localStorage.setItem('deepwoken_spy_name', name);
    myPlayerName = name;
    showScreen('screen-join');
  });

  document.getElementById('btn-join-room').addEventListener('click', () => {
    const code = document.getElementById('join-code-input').value.trim().toUpperCase();
    if (!code || code.length < 3) return showToast('Введите код комнаты!');
    joinRoomServer(code);
  });

  document.getElementById('btn-back-home-1').addEventListener('click', () => showScreen('screen-home'));
  document.getElementById('btn-back-home-2').addEventListener('click', () => showScreen('screen-home'));

  document.getElementById('lobby-code-display').addEventListener('click', () => {
    const code = document.getElementById('lobby-code-display').textContent;
    navigator.clipboard.writeText(code).then(() => {
      showToast(`Код ${code} скопирован в буфер!`);
    });
  });

  document.getElementById('lobby-spies-select').addEventListener('change', syncSettingsToServer);

  document.getElementById('btn-host-start-game').addEventListener('click', () => {
    startGameServer();
  });

  document.getElementById('btn-leave-lobby').addEventListener('click', () => {
    if (pollInterval) clearInterval(pollInterval);
    window.location.reload();
  });

  document.getElementById('btn-pass-turn').addEventListener('click', () => {
    passTurnServer();
  });

  document.getElementById('btn-start-next-circle').addEventListener('click', () => {
    startNextCircleServer();
  });

  document.getElementById('btn-trigger-voting').addEventListener('click', () => {
    triggerVotingServer();
  });

  document.getElementById('btn-submit-vote').addEventListener('click', () => {
    submitVoteServer();
  });

  document.getElementById('btn-spy-submit-guess').addEventListener('click', () => {
    const select = document.getElementById('spy-guess-select');
    if (select && select.value) {
      submitSpyGuessServer(select.value);
    }
  });

  document.getElementById('btn-host-confirm-voice-correct').addEventListener('click', () => {
    if (isHost) {
      const select = document.getElementById('spy-guess-select');
      if (select && select.value) submitSpyGuessServer(select.value);
    }
  });

  document.getElementById('btn-host-confirm-voice-wrong').addEventListener('click', () => {
    if (isHost) {
      submitSpyGuessServer('WRONG_GUESS_FORCE_FAIL');
    }
  });

  document.getElementById('btn-return-lobby').addEventListener('click', () => {
    resetToLobbyServer();
  });

  // Pass & Play Mode Setup
  document.getElementById('btn-start-passplay').addEventListener('click', () => {
    showScreen('screen-passplay-setup');
  });

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
      roles: chosenItem.roles || ['Житель']
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
      roleEl.textContent = 'Узнайте место/предмет и не выдавайте себя!';
    } else {
      cardEl.classList.remove('spy-card');
      wordEl.textContent = passPlayState.secretWord;
      wordEl.classList.remove('spy-text');
      const randomRole = passPlayState.roles[Math.floor(Math.random() * passPlayState.roles.length)];
      roleEl.textContent = `Роль: ${randomRole}`;
    }

    const nextBtn = document.getElementById('btn-pp-next-player');
    if (idx + 1 >= passPlayState.playerCount) {
      nextBtn.textContent = 'Завершить раздачу и начать обсуждение';
    } else {
      nextBtn.textContent = `Скрыть и передать Игроку №${idx + 2}`;
    }

    playBellSound();
    showScreen('screen-passplay-card');
  });

  document.getElementById('btn-pp-next-player').addEventListener('click', () => {
    passPlayState.currentPlayerIdx++;
    if (passPlayState.currentPlayerIdx >= passPlayState.playerCount) {
      showToast('Все игроки получили роли! Начинаем обсуждение!');
      showScreen('screen-home');
    } else {
      setupPassPlayPlayerTurn(passPlayState.currentPlayerIdx);
    }
  });
});

function setupPassPlayPlayerTurn(playerIdx) {
  document.getElementById('pp-current-player-num').textContent = playerIdx + 1;
  showScreen('screen-passplay-curtain');
}

function updateLobbyUI(room) {
  document.getElementById('lobby-code-display').textContent = room.code;
  document.getElementById('lobby-player-count').textContent = room.players.length;

  const hostPanel = document.getElementById('host-settings-panel');
  const startBtn = document.getElementById('btn-host-start-game');
  const waitingMsg = document.getElementById('waiting-for-host-msg');

  if (isHost) {
    hostPanel.style.display = 'block';
    startBtn.style.display = 'block';
    waitingMsg.style.display = 'none';
  } else {
    hostPanel.style.display = 'none';
    startBtn.style.display = 'none';
    waitingMsg.style.display = 'block';
  }

  const grid = document.getElementById('lobby-players-grid');
  grid.innerHTML = '';
  room.players.forEach(p => {
    const badge = document.createElement('div');
    badge.className = `player-badge ${p.isHost ? 'host' : ''}`;
    badge.innerHTML = `
      ${p.isHost ? '<span class="host-icon" title="Хост">👑</span>' : ''}
      <div class="name">${p.name}</div>
      <div class="score">${p.score || 0} Очков</div>
    `;
    grid.appendChild(badge);
  });
}

function renderPlayingCardUI(roleObj) {
  if (!roleObj) return;
  document.getElementById('card-category-label').textContent = roleObj.category;
  const cardEl = document.getElementById('secret-role-card');
  const wordEl = document.getElementById('card-word-label');
  const roleEl = document.getElementById('card-role-label');

  if (roleObj.isSpy) {
    cardEl.classList.add('spy-card');
    wordEl.textContent = roleObj.word;
    wordEl.classList.add('spy-text');
    roleEl.textContent = roleObj.role;
  } else {
    cardEl.classList.remove('spy-card');
    wordEl.textContent = roleObj.word;
    wordEl.classList.remove('spy-text');
    roleEl.textContent = `Роль: ${roleObj.role}`;
  }
}

function renderVotingUI(room) {
  const container = document.getElementById('voting-players-list');
  container.innerHTML = '';
  selectedVoteTargetId = null;

  const submitBtn = document.getElementById('btn-submit-vote');
  submitBtn.disabled = true;
  submitBtn.textContent = 'ПОДТВЕРДИТЬ ГОЛОС';

  room.players.forEach(p => {
    if (p.id === myPlayerId) return;

    const option = document.createElement('div');
    option.className = 'vote-option';
    option.innerHTML = `
      <span style="font-weight: 600;">${p.name}</span>
      <span style="font-size: 0.8rem; color: var(--text-muted);">Выбрать</span>
    `;

    option.addEventListener('click', () => {
      document.querySelectorAll('.vote-option').forEach(el => el.classList.remove('selected'));
      option.classList.add('selected');
      selectedVoteTargetId = p.id;
      submitBtn.disabled = false;
    });

    container.appendChild(option);
  });
}

function renderSpyGuessScreen(roleObj) {
  if (!roleObj) return;
  const catKey = roleObj.categoryKey;
  document.getElementById('spy-guess-cat-name').textContent = roleObj.category;
  
  const select = document.getElementById('spy-guess-select');
  select.innerHTML = '';

  if (DEEPWOKEN_DATA.categories[catKey]) {
    const items = DEEPWOKEN_DATA.categories[catKey].items;
    items.forEach(item => {
      const opt = document.createElement('option');
      opt.value = item.name;
      opt.textContent = item.name;
      select.appendChild(opt);
    });
  }

  const voiceConfirmCorrect = document.getElementById('btn-host-confirm-voice-correct');
  const voiceConfirmWrong = document.getElementById('btn-host-confirm-voice-wrong');

  if (isHost) {
    voiceConfirmCorrect.style.display = 'block';
    voiceConfirmWrong.style.display = 'block';
  } else {
    voiceConfirmCorrect.style.display = 'none';
    voiceConfirmWrong.style.display = 'none';
  }
}

function renderGameResultsUI(data) {
  const titleEl = document.getElementById('reveal-title');
  const wordEl = document.getElementById('reveal-secret-word');
  const spyNamesEl = document.getElementById('reveal-spy-names');

  wordEl.textContent = `${data.secretItem} (${data.secretCategory})`;
  spyNamesEl.textContent = data.spies.map(s => s.name).join(', ');

  titleEl.textContent = data.resultMessage || 'Итоги Раунда';
  if (data.resultMessage && data.resultMessage.includes('ШПИОН')) {
    titleEl.style.color = 'var(--crimson-blood)';
  } else {
    titleEl.style.color = 'var(--ether-cyan)';
  }

  const lbContainer = document.getElementById('reveal-leaderboard');
  lbContainer.innerHTML = '';
  data.players.sort((a, b) => b.score - a.score).forEach(p => {
    const badge = document.createElement('div');
    badge.className = 'player-badge';
    badge.innerHTML = `
      <div class="name">${p.name} ${p.isSpy ? '🕵️' : ''}</div>
      <div class="score">${p.score} Очков</div>
    `;
    lbContainer.appendChild(badge);
  });

  const returnBtn = document.getElementById('btn-return-lobby');
  returnBtn.style.display = isHost ? 'block' : 'none';
}
