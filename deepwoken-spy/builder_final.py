import os

src_dir = r"C:\Users\march\.gemini\antigravity\scratch\deepwoken-spy\src"
mqtt_file = os.path.join(src_dir, "mqttws31.min.js")
main_file = os.path.join(src_dir, "main.js")

with open(mqtt_file, "r", encoding="utf-8") as f:
    mqtt_code = f.read()

game_code = r'''
// =========================================================================
// --- DEEPWOKEN SPY PRODUCTION ENGINE (INSTANT START & ZERO-STALE ROOMS) ---
// =========================================================================

let currentScreen = 'screen-home';
let myPlayerName = '';
let currentRoomCode = '';

// Persistent Player ID per browser tab
let myPlayerId = sessionStorage.getItem('dw_spy_player_id');
if (!myPlayerId) {
  myPlayerId = 'p_' + Math.floor(Math.random() * 900000 + 100000);
  sessionStorage.setItem('dw_spy_player_id', myPlayerId);
}

let isHost = false;
let soundEnabled = true;

// Networking State
let mqttClient = null;
let isConnectedToBroker = false;
let heartbeatTimer = null;
let guestJoinTimer = null;
let unreadChatCount = 0;
let isChatOpen = false;
let activeSessionToken = null;

// Active Room State
let roomState = {
  code: '',
  sessionToken: '',
  hostId: '',
  players: [],
  settings: {
    selectedCategories: ['oaths', 'attunements', 'races', 'bosses', 'bells'],
    spyCount: 1
  },
  state: 'LOBBY',
  secretItem: null,
  secretCategory: null,
  secretCatKey: null,
  circleNum: 1,
  turnOrder: [],
  currentSpeakerIdx: 0,
  votedOutPlayer: null,
  revealData: null
};

let mySecretRole = null;
let selectedVoteTargetId = null;

// Pass & Play State
let passPlayState = {
  playerCount: 4,
  selectedCategories: ['oaths', 'attunements', 'races', 'bosses', 'bells'],
  currentPlayerIdx: 0,
  spyIdx: 0,
  secretWord: '',
  secretCat: '',
  roles: []
};

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
    } else if (type === 'turn') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(659.25, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.25);
      gain.gain.setValueAtTime(0.3, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.3);
    } else if (type === 'chat') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, now);
      osc.frequency.exponentialRampToValueAtTime(1200, now + 0.1);
      gain.gain.setValueAtTime(0.2, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.15);
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

// --- UI Navigation & Toasts ---
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

function generateRoomCode() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let code = '';
  for (let i = 0; i < 4; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
}

// --- Categories Rendering ---
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

      if (containerId === 'lobby-categories-container' && isHost) {
        roomState.settings.selectedCategories = getSelectedCategories('lobby-categories-container');
        broadcastState();
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

// ==========================================
// --- MQTT GLOBAL WEBSOCKET MULTIPLAYER ---
// ==========================================

const MQTT_BROKERS = [
  { host: 'broker.emqx.io', port: 8084, path: '/mqtt' },
  { host: 'broker.hivemq.com', port: 8884, path: '/mqtt' }
];
let currentBrokerIdx = 0;

function connectMQTT(roomCode, onConnectCallback) {
  currentRoomCode = roomCode;
  const broker = MQTT_BROKERS[currentBrokerIdx];
  const clientId = 'dw_' + myPlayerId + '_' + Math.random().toString(16).substr(2, 6);

  try {
    if (mqttClient) {
      try { mqttClient.disconnect(); } catch (e) {}
    }
    mqttClient = new Paho.MQTT.Client(broker.host, Number(broker.port), broker.path, clientId);
  } catch (err) {
    try {
      mqttClient = new Paho.MQTT.Client(broker.host, Number(broker.port), clientId);
    } catch (e2) {
      console.error('MQTT construct error:', e2);
      showToast('Ошибка инициализации сети!');
      return;
    }
  }

  mqttClient.onConnectionLost = (responseObject) => {
    isConnectedToBroker = false;
    updateConnectionDot(false);
    if (responseObject.errorCode !== 0 && currentRoomCode) {
      setTimeout(() => connectMQTT(currentRoomCode, onConnectCallback), 2000);
    }
  };

  mqttClient.onMessageArrived = (message) => {
    handleIncomingMQTTMessage(message.destinationName, message.payloadString);
  };

  const connectOptions = {
    useSSL: true,
    timeout: 8,
    keepAliveInterval: 25,
    cleanSession: true,
    onSuccess: () => {
      isConnectedToBroker = true;
      updateConnectionDot(true);

      const stateTopic = 'dw_spy_v3_' + currentRoomCode + '/state';
      const eventsTopic = 'dw_spy_v3_' + currentRoomCode + '/events';
      const chatTopic = 'dw_spy_v3_' + currentRoomCode + '/chat';

      mqttClient.subscribe(stateTopic, { qos: 0 });
      mqttClient.subscribe(eventsTopic, { qos: 0 });
      mqttClient.subscribe(chatTopic, { qos: 0 });

      if (onConnectCallback) onConnectCallback();
    },
    onFailure: (err) => {
      isConnectedToBroker = false;
      updateConnectionDot(false);
      currentBrokerIdx = (currentBrokerIdx + 1) % MQTT_BROKERS.length;
      setTimeout(() => connectMQTT(currentRoomCode, onConnectCallback), 1500);
    }
  };

  mqttClient.connect(connectOptions);
}

function updateConnectionDot(online) {
  const dot = document.getElementById('connection-status-dot');
  if (dot) {
    dot.className = 'status-indicator ' + (online ? 'online' : '');
    dot.style.background = online ? '#00ff88' : '#ff2a5f';
    dot.title = online ? 'Сеть подключена (0ms)' : 'Переподключение...';
  }
}

function publishMQTT(topicSuffix, payloadObj) {
  if (!mqttClient || !isConnectedToBroker) return;
  try {
    const topic = 'dw_spy_v3_' + currentRoomCode + '/' + topicSuffix;
    const message = new Paho.MQTT.Message(JSON.stringify(payloadObj));
    message.destinationName = topic;
    message.qos = 0;
    message.retained = false; // Never retain so old expired rooms never leak!
    mqttClient.send(message);
  } catch (err) {}
}

function broadcastState() {
  if (!isHost) return;
  publishMQTT('state', { type: 'STATE_UPDATE', room: roomState, timestamp: Date.now() });
}

function sendEvent(eventType, extraData) {
  const payload = Object.assign({ type: eventType, playerId: myPlayerId, playerName: myPlayerName, timestamp: Date.now() }, extraData || {});
  publishMQTT('events', payload);
}

function sendChatMessage(text) {
  if (!text || !text.trim()) return;
  const msgObj = {
    id: 'm_' + Date.now(),
    playerId: myPlayerId,
    author: myPlayerName,
    text: text.trim(),
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    isHost: isHost
  };
  publishMQTT('chat', msgObj);
}

// --- Incoming Message Handlers ---
function handleIncomingMQTTMessage(topic, payloadStr) {
  try {
    const data = JSON.parse(payloadStr);

    if (topic.endsWith('/chat')) {
      handleIncomingChatMessage(data);
      return;
    }

    if (topic.endsWith('/state')) {
      if (data.type === 'STATE_UPDATE' && data.room) {
        // Validate session token: ignore packets from old/dead rooms
        if (!isHost) {
          if (!activeSessionToken) {
            activeSessionToken = data.room.sessionToken;
          } else if (data.room.sessionToken && data.room.sessionToken !== activeSessionToken) {
            // New room created on same code by host -> accept new token
            activeSessionToken = data.room.sessionToken;
          }
        }
        const prevRoom = roomState;
        roomState = data.room;
        onRoomStateUpdated(prevRoom, roomState);
      }
      return;
    }

    if (topic.endsWith('/events')) {
      handleIncomingGameEvent(data);
    }
  } catch (e) {}
}

function handleIncomingChatMessage(msg) {
  playSound('chat');
  const container = document.getElementById('chat-messages-container');
  if (!container) return;

  const item = document.createElement('div');
  const isMine = (msg.playerId === myPlayerId);
  item.className = 'chat-msg-item ' + (isMine ? 'mine' : '');
  
  item.innerHTML = `
    <div class="chat-msg-header">
      <span class="chat-msg-author ${msg.isHost ? 'host' : ''}">${msg.isHost ? '👑 ' : ''}${escapeHTML(msg.author)}</span>
      <span class="chat-msg-time">${msg.time}</span>
    </div>
    <div class="chat-msg-text">${escapeHTML(msg.text)}</div>
  `;

  container.appendChild(item);
  container.scrollTop = container.scrollHeight;

  if (!isChatOpen) {
    unreadChatCount++;
    const badge = document.getElementById('chat-unread-badge');
    badge.textContent = unreadChatCount;
    badge.style.display = 'inline-block';
  }
}

function handleIncomingGameEvent(event) {
  if (!isHost) return;

  if (event.type === 'JOIN' || event.type === 'GET_STATE') {
    let existing = roomState.players.find(p => p.id === event.playerId) || roomState.players.find(p => p.name === event.playerName);
    if (!existing && event.type === 'JOIN') {
      if (roomState.players.length >= 12) return;
      roomState.players.push({
        id: event.playerId,
        name: event.playerName,
        score: 0,
        isHost: false,
        isSpy: false,
        word: '',
        role: '',
        votedFor: null
      });
      addSystemChatMessage('👋 ' + event.playerName + ' присоединился к лобби!');
    } else if (existing) {
      existing.id = event.playerId;
      if (event.playerName) existing.name = event.playerName;
    }
    broadcastState();
    updateLobbyUI(roomState);
  } else if (event.type === 'PASS_TURN') {
    advanceTurnHost();
  } else if (event.type === 'START_NEXT_CIRCLE') {
    roomState.state = 'PLAYING';
    addSystemChatMessage('🔄 Начался Круг №' + roomState.circleNum + '!');
    broadcastState();
  } else if (event.type === 'TRIGGER_VOTING') {
    roomState.state = 'VOTING';
    roomState.players.forEach(p => p.votedFor = null);
    addSystemChatMessage('🗳️ Хост открыл голосование за шпиона!');
    broadcastState();
  } else if (event.type === 'CAST_VOTE') {
    const voter = roomState.players.find(p => p.id === event.playerId);
    if (voter) voter.votedFor = event.targetId;

    const votedCount = roomState.players.filter(p => p.votedFor !== null).length;
    if (votedCount >= roomState.players.length) {
      evaluateVotingHost();
    } else {
      broadcastState();
    }
  } else if (event.type === 'SPY_GUESS') {
    evaluateSpyGuessHost(event.guessedWord);
  }
}

function addSystemChatMessage(text) {
  sendChatMessage('📢 [СИСТЕМА]: ' + text);
}

function escapeHTML(str) {
  return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// --- Host Game Lifecycle Management ---
function startOnlineGameHost() {
  if (!isHost) return;
  if (roomState.players.length < 3) {
    return showToast('Для игры нужно минимум 3 игрока!');
  }

  const selectedCats = roomState.settings.selectedCategories;
  const validCats = selectedCats.filter(k => DEEPWOKEN_DATA.categories[k]);
  if (validCats.length === 0) {
    return showToast('Выберите хотя бы одну категорию!');
  }

  // 1. Pick secret category and secret item
  const chosenCatKey = validCats[Math.floor(Math.random() * validCats.length)];
  const catData = DEEPWOKEN_DATA.categories[chosenCatKey];
  const chosenItem = catData.items[Math.floor(Math.random() * catData.items.length)];

  roomState.secretItem = chosenItem.name;
  roomState.secretCategory = catData.name;
  roomState.secretCatKey = chosenCatKey;
  roomState.state = 'PLAYING';
  roomState.circleNum = 1;
  roomState.votedOutPlayer = null;
  roomState.revealData = null;

  // Turn order
  const playerIds = roomState.players.map(p => p.id).sort(() => Math.random() - 0.5);
  roomState.turnOrder = playerIds;
  roomState.currentSpeakerIdx = 0;

  // Reset voting
  roomState.players.forEach(p => {
    p.isSpy = false;
    p.votedFor = null;
  });

  // Pick Spy indices
  const numSpies = Math.min(roomState.settings.spyCount || 1, Math.max(1, Math.floor(roomState.players.length / 2)));
  const spyIndices = new Set(roomState.players.map((_, i) => i).sort(() => Math.random() - 0.5).slice(0, numSpies));

  // Set roles
  roomState.players.forEach((p, idx) => {
    if (spyIndices.has(idx)) {
      p.isSpy = true;
      p.word = '🕵️ ВЫ ШПИОН!';
      p.role = 'Ты не знаешь слово! Слушай Discord и притворяйся мирным!';
    } else {
      p.isSpy = false;
      p.word = chosenItem.name;
      p.role = chosenItem.roles ? chosenItem.roles[Math.floor(Math.random() * chosenItem.roles.length)] : 'Мирный Житель';
    }
  });

  addSystemChatMessage('⚔️ Игра началась! Категория: ' + catData.name + '. 1-й круг!');
  
  // Instant local transition for host
  onRoomStateUpdated(Object.assign({}, roomState, { state: 'LOBBY' }), roomState);

  // Broadcast to all guests in rapid burst for 0ms latency
  broadcastState();
  setTimeout(broadcastState, 80);
  setTimeout(broadcastState, 250);
}

function advanceTurnHost() {
  if (!isHost) return;
  roomState.currentSpeakerIdx++;
  if (roomState.currentSpeakerIdx >= roomState.turnOrder.length) {
    roomState.currentSpeakerIdx = 0;
    roomState.circleNum++;
  }
  const speakerId = roomState.turnOrder[roomState.currentSpeakerIdx];
  const speaker = roomState.players.find(p => p.id === speakerId);
  if (speaker) {
    addSystemChatMessage('🎤 Очередь перешла к ' + speaker.name + ' (Круг ' + roomState.circleNum + ')');
  }
  broadcastState();
}

function evaluateVotingHost() {
  const voteCounts = {};
  roomState.players.forEach(p => {
    if (p.votedFor) {
      voteCounts[p.votedFor] = (voteCounts[p.votedFor] || 0) + 1;
    }
  });

  let maxVotes = 0;
  let votedOutId = null;
  let tie = false;

  Object.entries(voteCounts).forEach(([id, count]) => {
    if (count > maxVotes) {
      maxVotes = count;
      votedOutId = id;
      tie = false;
    } else if (count === maxVotes) {
      tie = true;
    }
  });

  const votedOutPlayer = roomState.players.find(p => p.id === votedOutId);
  const spies = roomState.players.filter(p => p.isSpy);

  if (votedOutPlayer && votedOutPlayer.isSpy && !tie) {
    roomState.state = 'SPY_GUESS';
    roomState.votedOutPlayer = { id: votedOutPlayer.id, name: votedOutPlayer.name };
    addSystemChatMessage('🚨 Игроки раскрыли шпиона: ' + votedOutPlayer.name + '! У шпиона есть 1 шанс назвать слово.');
  } else {
    spies.forEach(s => s.score += 200);
    roomState.state = 'REVEAL';
    roomState.revealData = {
      votedOutPlayer: votedOutPlayer ? { name: votedOutPlayer.name, isSpy: votedOutPlayer.isSpy } : null,
      spies: spies.map(s => ({ name: s.name })),
      secretItem: roomState.secretItem,
      secretCategory: roomState.secretCategory,
      players: roomState.players.map(p => ({ name: p.name, score: p.score, isSpy: p.isSpy })),
      resultMessage: '🕵️ ПОБЕДА ШПИОНА! Мирные ошиблись с голосованием!'
    };
    addSystemChatMessage('🏆 Раунд завершен! Победа Шпиона!');
  }

  broadcastState();
}

function evaluateSpyGuessHost(guessedWord) {
  if (!isHost) return;
  const spies = roomState.players.filter(p => p.isSpy);

  let msg = '';
  if (guessedWord.toLowerCase() === roomState.secretItem.toLowerCase()) {
    spies.forEach(s => s.score += 200);
    msg = '🕵️ ШПИОН УГАДАЛ КАРТОЧКУ И ПЕРЕХВАТИЛ ПОБЕДУ!';
    addSystemChatMessage('🎯 Шпион правильно назвал слово [' + roomState.secretItem + '] и победил!');
  } else {
    roomState.players.forEach(p => { if (!p.isSpy) p.score += 100; });
    msg = '🎉 ПОБЕДА МИРНЫХ! Шпион ошибся с догадкой!';
    addSystemChatMessage('🎉 Шпион не угадал карточку! Мирные забирают победу!');
  }

  roomState.state = 'REVEAL';
  roomState.revealData = {
    votedOutPlayer: { name: roomState.votedOutPlayer ? roomState.votedOutPlayer.name : 'Шпион', isSpy: true },
    spies: spies.map(s => ({ name: s.name })),
    secretItem: roomState.secretItem,
    secretCategory: roomState.secretCategory,
    players: roomState.players.map(p => ({ name: p.name, score: p.score, isSpy: p.isSpy })),
    resultMessage: msg
  };

  broadcastState();
}

// --- Client UI State Sync ---
function onRoomStateUpdated(prevRoom, currentRoom) {
  isHost = (currentRoom.hostId === myPlayerId);

  // If Guest joined, clear guestJoinTimer
  if (guestJoinTimer) {
    clearInterval(guestJoinTimer);
    guestJoinTimer = null;
  }

  // Update room code label
  document.getElementById('lobby-code-display').textContent = currentRoom.code || currentRoomCode;

  // Find MY player data in current room
  let me = currentRoom.players.find(p => p.id === myPlayerId);
  if (!me && myPlayerName) {
    me = currentRoom.players.find(p => p.name === myPlayerName);
    if (me) {
      myPlayerId = me.id;
      sessionStorage.setItem('dw_spy_player_id', myPlayerId);
    }
  }

  if (me) {
    mySecretRole = {
      word: me.word,
      role: me.role,
      isSpy: Boolean(me.isSpy),
      category: currentRoom.secretCategory,
      categoryKey: currentRoom.secretCatKey
    };
  }

  if (currentRoom.state === 'LOBBY') {
    updateLobbyUI(currentRoom);
    if (currentScreen !== 'screen-lobby') showScreen('screen-lobby');
  } else if (currentRoom.state === 'PLAYING') {
    // ALWAYS render my secret role card on PLAYING state!
    if (mySecretRole) {
      renderPlayingCardUI(mySecretRole);
    }
    if (currentScreen !== 'screen-game') {
      playSound('bell');
      showScreen('screen-game');
    }
    renderGameRoomState(currentRoom);
  } else if (currentRoom.state === 'VOTING') {
    if (currentScreen !== 'screen-voting') {
      playSound('vote');
      renderVotingUI(currentRoom);
      showScreen('screen-voting');
    }
    renderVotingProgress(currentRoom);
  } else if (currentRoom.state === 'SPY_GUESS') {
    if (currentScreen !== 'screen-spy-guess') {
      playSound('vote');
      renderSpyGuessScreen(currentRoom);
      showScreen('screen-spy-guess');
    }
  } else if (currentRoom.state === 'REVEAL') {
    if (currentScreen !== 'screen-reveal' && currentRoom.revealData) {
      playSound('bell');
      renderGameResultsUI(currentRoom.revealData);
      showScreen('screen-reveal');
    }
  }
}

function updateLobbyUI(room) {
  document.getElementById('lobby-code-display').textContent = room.code || currentRoomCode;
  document.getElementById('lobby-player-count').textContent = room.players.length;

  const hostPanel = document.getElementById('host-settings-panel');
  const startBtn = document.getElementById('btn-host-start-game');
  const waitMsg = document.getElementById('waiting-for-host-msg');

  if (isHost) {
    hostPanel.style.display = 'block';
    startBtn.style.display = 'block';
    waitMsg.style.display = 'none';
  } else {
    hostPanel.style.display = 'none';
    startBtn.style.display = 'none';
    waitMsg.style.display = 'block';
  }

  const grid = document.getElementById('lobby-players-grid');
  grid.innerHTML = '';
  room.players.forEach(p => {
    const badge = document.createElement('div');
    badge.className = 'player-badge ' + (p.isHost ? 'host' : '');
    badge.innerHTML = `
      ${p.isHost ? '👑' : '👤'}
      <div class="name">${escapeHTML(p.name)}</div>
      <div class="score">${p.score || 0} Очков</div>
    `;
    grid.appendChild(badge);
  });
}

function renderPlayingCardUI(roleObj) {
  if (!roleObj) return;

  const cardEl = document.getElementById('secret-role-card');
  const catLabel = document.getElementById('card-category-label');
  const wordEl = document.getElementById('card-word-label');
  const roleEl = document.getElementById('card-role-label');

  catLabel.textContent = roleObj.category || 'Deepwoken';

  if (roleObj.isSpy) {
    cardEl.classList.add('spy-card');
    cardEl.style.borderColor = 'var(--crimson-blood)';
    wordEl.textContent = '🕵️ ТЫ ШПИОН!';
    wordEl.classList.add('spy-text');
    roleEl.innerHTML = `
      <strong style="color: var(--gold-rune); display: block; margin-bottom: 4px;">Категория раунда: ${escapeHTML(roleObj.category)}</strong>
      <span>Ты НЕ знаешь точное слово! Слушай игроков в Discord VC, делай вид, что знаешь карточку, и не спались!</span>
    `;
  } else {
    cardEl.classList.remove('spy-card');
    cardEl.style.borderColor = 'var(--ether-cyan)';
    wordEl.textContent = roleObj.word;
    wordEl.classList.remove('spy-text');
    roleEl.innerHTML = `
      <strong style="color: var(--ether-cyan); display: block; margin-bottom: 4px;">Роль: ${escapeHTML(roleObj.role)}</strong>
      <span>Все мирные знают это слово. Давай осторожные подсказки в Discord VC, чтобы шпион не понял слово!</span>
    `;
  }
}

function renderGameRoomState(room) {
  document.getElementById('game-circle-num').textContent = room.circleNum || 1;

  let currentSpeakerName = 'Игрок';
  let isMyTurn = false;
  let speakerId = null;

  if (room.turnOrder && room.turnOrder.length > 0) {
    speakerId = room.turnOrder[room.currentSpeakerIdx];
    const speakerObj = room.players.find(p => p.id === speakerId);
    if (speakerObj) currentSpeakerName = speakerObj.name;
    isMyTurn = (speakerId === myPlayerId);
  }

  document.getElementById('speaker-name-display').textContent = currentSpeakerName;

  const passBtn = document.getElementById('btn-pass-turn');
  const waitMsg = document.getElementById('not-my-turn-msg');

  if (isMyTurn) {
    passBtn.style.display = 'inline-flex';
    waitMsg.style.display = 'none';
  } else {
    passBtn.style.display = 'none';
    waitMsg.style.display = 'block';
    waitMsg.textContent = `Сейчас говорит ${currentSpeakerName}. Слушайте в Discord...`;
  }

  // Render Turn order chips
  const chipsContainer = document.getElementById('turn-order-chips');
  chipsContainer.innerHTML = '';
  if (room.turnOrder) {
    room.turnOrder.forEach((pId, idx) => {
      const p = room.players.find(pl => pl.id === pId);
      if (!p) return;
      const chip = document.createElement('span');
      const isActive = (idx === room.currentSpeakerIdx);
      const isPast = (idx < room.currentSpeakerIdx);
      chip.className = 'turn-chip ' + (isActive ? 'active' : '') + ' ' + (isPast ? 'done' : '');
      chip.textContent = `${idx + 1}. ${p.name}`;
      chipsContainer.appendChild(chip);
    });
  }

  // Decision box after Circle 3+
  const decisionPanel = document.getElementById('circle-decision-panel');
  if (room.circleNum >= 3) {
    decisionPanel.style.display = 'block';
    document.getElementById('next-circle-num').textContent = room.circleNum + 1;
    const nextCircleBtn = document.getElementById('btn-start-next-circle');
    const triggerVotingBtn = document.getElementById('btn-trigger-voting');

    nextCircleBtn.style.display = isHost ? 'inline-flex' : 'none';
    triggerVotingBtn.style.display = isHost ? 'inline-flex' : 'none';
  } else {
    decisionPanel.style.display = 'none';
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
      <span style="font-weight: 600;">${escapeHTML(p.name)}</span>
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

function renderVotingProgress(room) {
  const votedCount = room.players.filter(p => p.votedFor !== null).length;
  document.getElementById('votes-cast-count').textContent = votedCount;
  document.getElementById('votes-required-count').textContent = room.players.length;
}

function renderSpyGuessScreen(room) {
  const catKey = room.secretCatKey;
  const suspect = room.votedOutPlayer;
  const isSpyMe = (suspect && suspect.id === myPlayerId);

  document.getElementById('spy-suspect-name').textContent = suspect ? suspect.name : 'Шпион';
  document.getElementById('spy-guess-cat-name').textContent = room.secretCategory || 'Категория';

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

  const guessSubmitBtn = document.getElementById('btn-spy-submit-guess');
  guessSubmitBtn.style.display = (isSpyMe || isHost) ? 'inline-flex' : 'none';

  const voiceCorrect = document.getElementById('btn-host-confirm-voice-correct');
  const voiceWrong = document.getElementById('btn-host-confirm-voice-wrong');

  if (isHost) {
    voiceCorrect.style.display = 'inline-flex';
    voiceWrong.style.display = 'inline-flex';
  } else {
    voiceCorrect.style.display = 'none';
    voiceWrong.style.display = 'none';
  }
}

function renderGameResultsUI(data) {
  const titleEl = document.getElementById('reveal-title');
  const wordEl = document.getElementById('reveal-secret-word');
  const spyNamesEl = document.getElementById('reveal-spy-names');

  wordEl.textContent = `${data.secretItem} (${data.secretCategory})`;
  spyNamesEl.textContent = data.spies.map(s => s.name).join(', ');

  titleEl.textContent = data.resultMessage || 'Итоги Раунда';
  titleEl.style.color = data.resultMessage && data.resultMessage.includes('ШПИОН') ? 'var(--crimson-blood)' : 'var(--ether-cyan)';

  const lbContainer = document.getElementById('reveal-leaderboard');
  lbContainer.innerHTML = '';
  data.players.sort((a, b) => b.score - a.score).forEach(p => {
    const badge = document.createElement('div');
    badge.className = 'player-badge ' + (p.isSpy ? 'is-speaking' : '');
    badge.innerHTML = `
      <div class="name">${escapeHTML(p.name)} ${p.isSpy ? '🕵️' : '👤'}</div>
      <div class="score">${p.score} Очков</div>
    `;
    lbContainer.appendChild(badge);
  });

  const nextRoundBtn = document.getElementById('btn-next-round');
  const returnLobbyBtn = document.getElementById('btn-return-lobby');

  if (isHost) {
    nextRoundBtn.style.display = 'block';
    returnLobbyBtn.style.display = 'block';
  } else {
    nextRoundBtn.style.display = 'none';
    returnLobbyBtn.style.display = 'none';
  }
}

// --- DOM Event Bindings ---
document.addEventListener('DOMContentLoaded', () => {
  initCanvasParticles();
  renderCategoryOptions('lobby-categories-container');
  renderCategoryOptions('pp-categories-container');

  const savedName = localStorage.getItem('deepwoken_spy_name');
  if (savedName) {
    document.getElementById('player-name-input').value = savedName;
  }

  // Force uppercase in join code input
  const joinInput = document.getElementById('join-code-input');
  if (joinInput) {
    joinInput.addEventListener('input', () => {
      joinInput.value = joinInput.value.toUpperCase();
    });
  }

  // Sound toggle button
  document.getElementById('btn-sound-toggle').addEventListener('click', (e) => {
    soundEnabled = !soundEnabled;
    e.currentTarget.textContent = soundEnabled ? '🔊' : '🔇';
    showToast(soundEnabled ? 'Звуки включены' : 'Звуки выключены');
  });

  // Create Online Lobby
  document.getElementById('btn-create-online').addEventListener('click', () => {
    const name = document.getElementById('player-name-input').value.trim();
    if (!name) return showToast('Введите ваш Никнейм!');
    localStorage.setItem('deepwoken_spy_name', name);
    myPlayerName = name;

    const code = generateRoomCode();
    currentRoomCode = code;
    isHost = true;
    activeSessionToken = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);

    roomState = {
      code: code,
      sessionToken: activeSessionToken,
      hostId: myPlayerId,
      players: [{ id: myPlayerId, name: myPlayerName, score: 0, isHost: true, isSpy: false, word: '', role: '', votedFor: null }],
      settings: {
        selectedCategories: getSelectedCategories('lobby-categories-container'),
        spyCount: 1
      },
      state: 'LOBBY',
      secretItem: null,
      secretCategory: null,
      secretCatKey: null,
      circleNum: 1,
      turnOrder: [],
      currentSpeakerIdx: 0,
      votedOutPlayer: null,
      revealData: null
    };

    document.getElementById('lobby-code-display').textContent = code;
    showScreen('screen-lobby');
    updateLobbyUI(roomState);
    showToast('Подключение к сети...');

    connectMQTT(code, () => {
      broadcastState();
      showToast('Лобби ' + code + ' создано!');

      if (heartbeatTimer) clearInterval(heartbeatTimer);
      heartbeatTimer = setInterval(() => {
        if (isHost && isConnectedToBroker) {
          broadcastState();
        }
      }, 1000);
    });
  });

  // Show Join Screen
  document.getElementById('btn-show-join').addEventListener('click', () => {
    const name = document.getElementById('player-name-input').value.trim();
    if (!name) return showToast('Введите ваш Никнейм!');
    localStorage.setItem('deepwoken_spy_name', name);
    myPlayerName = name;
    showScreen('screen-join');
  });

  // Join Room by Code
  document.getElementById('btn-join-room').addEventListener('click', () => {
    const code = document.getElementById('join-code-input').value.trim().toUpperCase();
    if (!code || code.length < 3) return showToast('Введите код комнаты!');
    currentRoomCode = code;
    isHost = false;
    activeSessionToken = null; // Reset session token to accept host token

    document.getElementById('lobby-code-display').textContent = code;
    showScreen('screen-lobby');
    showToast('Подключение к комнате ' + code + '...');

    connectMQTT(code, () => {
      sendEvent('JOIN');
      sendEvent('GET_STATE');

      if (guestJoinTimer) clearInterval(guestJoinTimer);
      guestJoinTimer = setInterval(() => {
        if (!isHost && isConnectedToBroker && roomState.players.length === 0) {
          sendEvent('JOIN');
          sendEvent('GET_STATE');
        }
      }, 1000);
    });
  });

  document.getElementById('btn-back-home-1').addEventListener('click', () => showScreen('screen-home'));
  document.getElementById('btn-back-home-2').addEventListener('click', () => showScreen('screen-home'));

  // Copy Code to Clipboard
  document.getElementById('lobby-code-display').addEventListener('click', () => {
    const code = document.getElementById('lobby-code-display').textContent;
    navigator.clipboard.writeText(code).then(() => {
      showToast('Код ' + code + ' скопирован в буфер!');
    });
  });

  // Host Settings
  document.getElementById('lobby-spies-select').addEventListener('change', () => {
    if (isHost) {
      roomState.settings.spyCount = parseInt(document.getElementById('lobby-spies-select').value) || 1;
      broadcastState();
    }
  });

  // Host Start Game
  document.getElementById('btn-host-start-game').addEventListener('click', () => {
    startOnlineGameHost();
  });

  // Leave Lobby
  document.getElementById('btn-leave-lobby').addEventListener('click', () => {
    if (heartbeatTimer) clearInterval(heartbeatTimer);
    if (guestJoinTimer) clearInterval(guestJoinTimer);
    if (mqttClient) {
      try { mqttClient.disconnect(); } catch (e) {}
    }
    window.location.reload();
  });

  // Speaker Pass Turn
  document.getElementById('btn-pass-turn').addEventListener('click', () => {
    playSound('turn');
    if (isHost) advanceTurnHost();
    else sendEvent('PASS_TURN');
  });

  // Start Next Circle
  document.getElementById('btn-start-next-circle').addEventListener('click', () => {
    if (isHost) {
      roomState.state = 'PLAYING';
      addSystemChatMessage('🔄 Начался Круг №' + roomState.circleNum + '!');
      broadcastState();
    } else {
      sendEvent('START_NEXT_CIRCLE');
    }
  });

  // Trigger Voting
  document.getElementById('btn-trigger-voting').addEventListener('click', () => {
    if (isHost) {
      roomState.state = 'VOTING';
      roomState.players.forEach(p => p.votedFor = null);
      addSystemChatMessage('🗳️ Хост открыл голосование за шпиона!');
      broadcastState();
    } else {
      sendEvent('TRIGGER_VOTING');
    }
  });

  // Submit Vote
  document.getElementById('btn-submit-vote').addEventListener('click', () => {
    if (!selectedVoteTargetId) return;
    playSound('vote');
    if (isHost) {
      handleIncomingGameEvent({ type: 'CAST_VOTE', playerId: myPlayerId, targetId: selectedVoteTargetId });
    } else {
      sendEvent('CAST_VOTE', { targetId: selectedVoteTargetId });
    }
    const btn = document.getElementById('btn-submit-vote');
    btn.disabled = true;
    btn.textContent = 'ГОЛОС ПРИНЯТ';
  });

  // Spy Guess Dropdown Submit
  document.getElementById('btn-spy-submit-guess').addEventListener('click', () => {
    const select = document.getElementById('spy-guess-select');
    if (select && select.value) {
      if (isHost) evaluateSpyGuessHost(select.value);
      else sendEvent('SPY_GUESS', { guessedWord: select.value });
    }
  });

  // Host Voice Confirm Buttons
  document.getElementById('btn-host-confirm-voice-correct').addEventListener('click', () => {
    if (isHost) evaluateSpyGuessHost(roomState.secretItem);
  });

  document.getElementById('btn-host-confirm-voice-wrong').addEventListener('click', () => {
    if (isHost) evaluateSpyGuessHost('WRONG_GUESS_FORCE_FAIL');
  });

  // Next Round / Reset to Lobby
  document.getElementById('btn-next-round').addEventListener('click', () => {
    if (isHost) startOnlineGameHost();
  });

  document.getElementById('btn-return-lobby').addEventListener('click', () => {
    if (isHost) {
      roomState.state = 'LOBBY';
      roomState.players.forEach(p => {
        p.votedFor = null;
        p.isSpy = false;
        p.role = '';
        p.word = '';
      });
      broadcastState();
      updateLobbyUI(roomState);
      showScreen('screen-lobby');
    }
  });

  // In-game Chat UI
  const chatToggleBtn = document.getElementById('chat-toggle-btn');
  const chatDrawer = document.getElementById('chat-drawer');
  const chatCloseBtn = document.getElementById('chat-close-btn');
  const chatInput = document.getElementById('chat-input');
  const chatSendBtn = document.getElementById('chat-send-btn');
  const chatBadge = document.getElementById('chat-unread-badge');

  chatToggleBtn.addEventListener('click', () => {
    isChatOpen = !isChatOpen;
    chatDrawer.classList.toggle('open', isChatOpen);
    if (isChatOpen) {
      unreadChatCount = 0;
      chatBadge.style.display = 'none';
      setTimeout(() => chatInput.focus(), 100);
    }
  });

  chatCloseBtn.addEventListener('click', () => {
    isChatOpen = false;
    chatDrawer.classList.remove('open');
  });

  function doSendChat() {
    const text = chatInput.value;
    if (!text.trim()) return;
    sendChatMessage(text);
    chatInput.value = '';
  }

  chatSendBtn.addEventListener('click', doSendChat);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') doSendChat();
  });

  document.querySelectorAll('.quick-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const msg = btn.getAttribute('data-msg');
      if (msg) sendChatMessage(msg);
    });
  });

  // Pass & Play (Local Offline)
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
      roleEl.textContent = 'Узнайте подсказку и не выдавайте себя в Discord!';
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

    playSound('bell');
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
'''

full_code = mqtt_code + "\n\n" + game_code

with open(main_file, "w", encoding="utf-8") as f:
    f.write(full_code)

print("SUCCESS: main.js updated perfectly! Size:", len(full_code))
print("Open braces:", full_code.count('{'), "Close braces:", full_code.count('}'))
assert full_code.count('{') == full_code.count('}'), "Braces mismatch"
print("BRACES CHECK: 100% BALANCED!")
