const express = require('express');
const http = require('http');
const path = require('path');
const DEEPWOKEN_DATA = require('./src/data/deepwokenWords');

const app = express();
const server = http.createServer(app);
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(__dirname));

const ROOMS = {};

function generateRoomCode() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let code = '';
  for (let i = 0; i < 4; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return ROOMS[code] ? generateRoomCode() : code;
}

function generatePlayerId() {
  return 'p_' + Math.floor(Math.random() * 900000 + 100000);
}

// API Endpoints
app.get('/api/room_state', (req, res) => {
  const code = (req.query.code || '').toUpperCase();
  const playerId = req.query.player_id;

  if (!ROOMS[code]) {
    return res.status(404).json({ error: 'Комната не найдена' });
  }

  const room = ROOMS[code];
  const playerInfo = room.players.find(p => p.id === playerId);
  let currentSpeaker = null;

  if (room.turnOrder && room.turnOrder.length > 0) {
    const speakerId = room.turnOrder[room.currentSpeakerIdx];
    const speakerObj = room.players.find(p => p.id === speakerId);
    if (speakerObj) {
      currentSpeaker = { id: speakerObj.id, name: speakerObj.name };
    }
  }

  res.json({
    code: room.code,
    hostId: room.hostId,
    players: room.players.map(p => ({ id: p.id, name: p.name, score: p.score, isHost: p.isHost })),
    settings: room.settings,
    state: room.state,
    circleNum: room.circleNum || 1,
    currentSpeaker,
    isMyTurn: Boolean(currentSpeaker && currentSpeaker.id === playerId),
    totalVotes: room.players.filter(p => p.votedFor !== null).length,
    myRole: ['PLAYING', 'VOTING', 'SPY_GUESS', 'REVEAL'].includes(room.state) ? {
      word: playerInfo ? playerInfo.word : '',
      role: playerInfo ? playerInfo.role : '',
      isSpy: playerInfo ? playerInfo.isSpy : false,
      category: room.secretCategory || '',
      categoryKey: room.secretCatKey || ''
    } : null,
    revealData: room.state === 'REVEAL' ? room.revealData : null
  });
});

app.post('/api/create_room', (req, res) => {
  const name = (req.body.playerName || 'Странник').trim() || 'Странник';
  const code = generateRoomCode();
  const playerId = generatePlayerId();

  const player = {
    id: playerId,
    name,
    score: 0,
    isHost: true,
    isSpy: false,
    role: '',
    word: '',
    votedFor: null
  };

  ROOMS[code] = {
    code,
    hostId: playerId,
    players: [player],
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
    currentSpeakerIdx: 0
  };

  res.json({ roomCode: code, playerId });
});

app.post('/api/join_room', (req, res) => {
  const code = (req.body.roomCode || '').trim().toUpperCase();
  const name = (req.body.playerName || 'Странник').trim() || 'Странник';

  if (!ROOMS[code]) {
    return res.status(404).json({ error: 'Комната не найдена. Проверь код!' });
  }

  const room = ROOMS[code];
  if (room.state !== 'LOBBY') {
    return res.status(400).json({ error: 'Игра в этой комнате уже идёт!' });
  }

  if (room.players.length >= 12) {
    return res.status(400).json({ error: 'Комната переполнена (макс 12 игроков)!' });
  }

  const playerId = generatePlayerId();
  const player = {
    id: playerId,
    name,
    score: 0,
    isHost: false,
    isSpy: false,
    role: '',
    word: '',
    votedFor: null
  };

  room.players.push(player);
  res.json({ roomCode: code, playerId });
});

app.post('/api/update_settings', (req, res) => {
  const code = (req.body.roomCode || '').toUpperCase();
  const playerId = req.body.playerId;
  const settings = req.body.settings || {};

  if (ROOMS[code] && ROOMS[code].hostId === playerId) {
    Object.assign(ROOMS[code].settings, settings);
    return res.json({ success: true });
  }
  res.status(403).json({ error: 'Доступ запрещен' });
});

app.post('/api/start_game', (req, res) => {
  const code = (req.body.roomCode || '').toUpperCase();
  const playerId = req.body.playerId;

  if (!ROOMS[code] || ROOMS[code].hostId !== playerId) {
    return res.status(403).json({ error: 'Доступ запрещен' });
  }

  const room = ROOMS[code];
  if (room.players.length < 3) {
    return res.status(400).json({ error: 'Для начала игры нужно минимум 3 игрока!' });
  }

  const categories = room.settings.selectedCategories;
  const validCats = categories.filter(c => DEEPWOKEN_DATA.categories[c]);
  if (validCats.length === 0) {
    return res.status(400).json({ error: 'Выберите хотя бы одну категорию!' });
  }

  const chosenCatKey = validCats[Math.floor(Math.random() * validCats.length)];
  const catData = DEEPWOKEN_DATA.categories[chosenCatKey];
  const chosenItem = catData.items[Math.floor(Math.random() * catData.items.length)];

  room.secretItem = chosenItem.name;
  room.secretCategory = catData.name;
  room.secretCatKey = chosenCatKey;
  room.state = 'PLAYING';
  room.circleNum = 1;
  room.revealData = null;

  const playerIds = room.players.map(p => p.id);
  playerIds.sort(() => Math.random() - 0.5);
  room.turnOrder = playerIds;
  room.currentSpeakerIdx = 0;

  room.players.forEach(p => {
    p.isSpy = false;
    p.votedFor = null;
  });

  const numSpies = Math.min(room.settings.spyCount || 1, Math.max(1, Math.floor(room.players.length / 2)));
  const spyIndices = new Set(room.players.map((_, i) => i).sort(() => Math.random() - 0.5).slice(0, numSpies));

  room.players.forEach((p, idx) => {
    if (spyIndices.has(idx)) {
      p.isSpy = true;
      p.word = '🕵️ ВЫ ШПИОН!';
      p.role = 'Узнайте подсказку и не выдавайте себя в Discord!';
    } else {
      p.isSpy = false;
      p.word = chosenItem.name;
      p.role = chosenItem.roles ? chosenItem.roles[Math.floor(Math.random() * chosenItem.roles.length)] : 'Житель';
    }
  });

  res.json({ success: true });
});

app.post('/api/pass_turn', (req, res) => {
  const code = (req.body.roomCode || '').toUpperCase();
  const playerId = req.body.playerId;

  if (ROOMS[code] && ROOMS[code].state === 'PLAYING') {
    const room = ROOMS[code];
    const currentSpeakerId = room.turnOrder[room.currentSpeakerIdx];
    if (playerId === currentSpeakerId || playerId === room.hostId) {
      room.currentSpeakerIdx++;
      if (room.currentSpeakerIdx >= room.turnOrder.length) {
        room.currentSpeakerIdx = 0;
        room.circleNum++;
      }
      return res.json({ success: true });
    }
  }
  res.status(400).json({ error: 'Не ваш ход' });
});

app.post('/api/start_next_circle', (req, res) => {
  const code = (req.body.roomCode || '').toUpperCase();
  if (ROOMS[code]) {
    ROOMS[code].state = 'PLAYING';
    return res.json({ success: true });
  }
  res.status(404).json({ error: 'Комната не найдена' });
});

app.post('/api/start_voting', (req, res) => {
  const code = (req.body.roomCode || '').toUpperCase();
  if (ROOMS[code]) {
    ROOMS[code].state = 'VOTING';
    return res.json({ success: true });
  }
  res.status(404).json({ error: 'Комната не найдена' });
});

app.post('/api/cast_vote', (req, res) => {
  const code = (req.body.roomCode || '').toUpperCase();
  const playerId = req.body.playerId;
  const targetId = req.body.targetId;

  if (ROOMS[code] && ROOMS[code].state === 'VOTING') {
    const room = ROOMS[code];
    const voter = room.players.find(p => p.id === playerId);
    if (voter) voter.votedFor = targetId;

    const totalVotes = room.players.filter(p => p.votedFor !== null).length;
    if (totalVotes >= room.players.length) {
      const voteCounts = {};
      room.players.forEach(p => {
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

      const votedOutPlayer = room.players.find(p => p.id === votedOutId);
      const spies = room.players.filter(p => p.isSpy);

      if (votedOutPlayer && votedOutPlayer.isSpy && !tie) {
        room.state = 'SPY_GUESS';
        room.votedOutPlayer = votedOutPlayer;
      } else {
        spies.forEach(s => s.score += 200);
        room.state = 'REVEAL';
        room.revealData = {
          votedOutPlayer: votedOutPlayer ? { name: votedOutPlayer.name, isSpy: votedOutPlayer.isSpy } : null,
          spies: spies.map(s => ({ name: s.name })),
          secretItem: room.secretItem,
          secretCategory: room.secretCategory,
          players: room.players.map(p => ({ name: p.name, score: p.score, isSpy: p.isSpy })),
          resultMessage: '🕵️ ПОБЕДА ШПИОНА! Мирные ошиблись с выбором!'
        };
      }
    }
    return res.json({ success: true });
  }
  res.status(400).json({ error: 'Голосование неактивно' });
});

app.post('/api/spy_guess', (req, res) => {
  const code = (req.body.roomCode || '').toUpperCase();
  const guessedWord = (req.body.guessedWord || '').trim();

  if (ROOMS[code] && ROOMS[code].state === 'SPY_GUESS') {
    const room = ROOMS[code];
    const spies = room.players.filter(p => p.isSpy);

    let msg = '';
    if (guessedWord.toLowerCase() === room.secretItem.toLowerCase()) {
      spies.forEach(s => s.score += 200);
      msg = '🕵️ ШПИОН УГАДАЛ СЛОВО И ПЕРЕХВАТИЛ ПОБЕДУ!';
    } else {
      room.players.forEach(p => { if (!p.isSpy) p.score += 100; });
      msg = '🎉 ПОБЕДА МИРНЫХ! Шпион не угадал карточку!';
    }

    room.state = 'REVEAL';
    room.revealData = {
      votedOutPlayer: { name: room.votedOutPlayer ? room.votedOutPlayer.name : 'Шпион', isSpy: true },
      spies: spies.map(s => ({ name: s.name })),
      secretItem: room.secretItem,
      secretCategory: room.secretCategory,
      players: room.players.map(p => ({ name: p.name, score: p.score, isSpy: p.isSpy })),
      resultMessage: msg
    };
    return res.json({ success: true });
  }
  res.status(400).json({ error: 'Фаза угадывания неактивна' });
});

app.post('/api/reset_to_lobby', (req, res) => {
  const code = (req.body.roomCode || '').toUpperCase();
  const playerId = req.body.playerId;

  if (ROOMS[code] && ROOMS[code].hostId === playerId) {
    const room = ROOMS[code];
    room.state = 'LOBBY';
    room.players.forEach(p => {
      p.votedFor = null;
      p.isSpy = false;
      p.role = '';
      p.word = '';
    });
    return res.json({ success: true });
  }
  res.status(403).json({ error: 'Доступ запрещен' });
});

server.listen(PORT, () => {
  console.log(`Deepwoken Spy Server running on port ${PORT}`);
});
