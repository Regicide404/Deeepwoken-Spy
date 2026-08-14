import http.server
import socketserver
import json
import os
import random
import urllib.parse
import sys

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

ROOMS = {}

def generate_room_code():
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    while True:
        code = ''.join(random.choice(chars) for _ in range(4))
        if code not in ROOMS:
            return code

def generate_player_id():
    return 'p_' + str(random.randint(100000, 999999))

class GameHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/room_state':
            query = urllib.parse.parse_qs(parsed.query)
            code = query.get('code', [''])[0].upper()
            player_id = query.get('player_id', [''])[0]

            if code in ROOMS:
                room = ROOMS[code]
                player_info = next((p for p in room['players'] if p['id'] == player_id), None)
                current_speaker = None
                if room.get('turnOrder') and len(room['turnOrder']) > 0:
                    speaker_id = room['turnOrder'][room['currentSpeakerIdx']]
                    speaker_obj = next((p for p in room['players'] if p['id'] == speaker_id), None)
                    if speaker_obj:
                        current_speaker = {'id': speaker_obj['id'], 'name': speaker_obj['name']}

                resp_data = {
                    'code': room['code'],
                    'hostId': room['hostId'],
                    'players': [{'id': p['id'], 'name': p['name'], 'score': p['score'], 'isHost': p['isHost']} for p in room['players']],
                    'settings': room['settings'],
                    'state': room['state'],
                    'circleNum': room.get('circleNum', 1),
                    'currentSpeaker': current_speaker,
                    'isMyTurn': (current_speaker and current_speaker['id'] == player_id),
                    'totalVotes': len([p for p in room['players'] if p.get('votedFor') is not None]),
                    'myRole': {
                        'word': player_info['word'] if player_info else '',
                        'role': player_info['role'] if player_info else '',
                        'isSpy': player_info['isSpy'] if player_info else False,
                        'category': room.get('secretCategory', ''),
                        'categoryKey': room.get('secretCatKey', '')
                    } if room['state'] in ['PLAYING', 'VOTING', 'SPY_GUESS', 'REVEAL'] else None,
                    'revealData': room.get('revealData') if room['state'] == 'REVEAL' else None
                }
                self.send_json(resp_data)
            else:
                self.send_json({'error': 'Комната не найдена'}, status=404)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        try:
            data = json.loads(body)
        except:
            data = {}

        if parsed.path == '/api/create_room':
            name = data.get('playerName', 'Странник').strip() or 'Странник'
            code = generate_room_code()
            player_id = generate_player_id()

            player = {
                'id': player_id,
                'name': name,
                'score': 0,
                'isHost': True,
                'isSpy': False,
                'role': '',
                'word': '',
                'votedFor': None
            }

            room = {
                'code': code,
                'hostId': player_id,
                'players': [player],
                'settings': {
                    'selectedCategories': ['oaths', 'attunements', 'races', 'bosses', 'bells'],
                    'spyCount': 1
                },
                'state': 'LOBBY',
                'secretItem': None,
                'secretCategory': None,
                'secretCatKey': None,
                'circleNum': 1,
                'turnOrder': [],
                'currentSpeakerIdx': 0
            }

            ROOMS[code] = room
            self.send_json({'roomCode': code, 'playerId': player_id})

        elif parsed.path == '/api/join_room':
            code = data.get('roomCode', '').strip().upper()
            name = data.get('playerName', 'Странник').strip() or 'Странник'

            if code not in ROOMS:
                return self.send_json({'error': 'Комната не найдена. Проверь код!'}, status=404)

            room = ROOMS[code]
            if room['state'] != 'LOBBY':
                return self.send_json({'error': 'Игра в этой комнате уже идёт!'}, status=400)

            if len(room['players']) >= 12:
                return self.send_json({'error': 'Комната переполнена (макс 12 игроков)!'}, status=400)

            player_id = generate_player_id()
            player = {
                'id': player_id,
                'name': name,
                'score': 0,
                'isHost': False,
                'isSpy': False,
                'role': '',
                'word': '',
                'votedFor': None
            }

            room['players'].append(player)
            self.send_json({'roomCode': code, 'playerId': player_id})

        elif parsed.path == '/api/update_settings':
            code = data.get('roomCode', '').upper()
            player_id = data.get('playerId')
            settings = data.get('settings', {})

            if code in ROOMS and ROOMS[code]['hostId'] == player_id:
                ROOMS[code]['settings'].update(settings)
                self.send_json({'success': True})

        elif parsed.path == '/api/start_game':
            code = data.get('roomCode', '').upper()
            player_id = data.get('playerId')
            words_db = data.get('wordsDb', {})

            if code not in ROOMS or ROOMS[code]['hostId'] != player_id:
                return self.send_json({'error': 'Доступ запрещен'}, status=403)

            room = ROOMS[code]
            if len(room['players']) < 3:
                return self.send_json({'error': 'Для начала игры нужно минимум 3 игрока!'}, status=400)

            categories = room['settings']['selectedCategories']
            valid_cats = [c for c in categories if c in words_db]
            if not valid_cats:
                return self.send_json({'error': 'Выберите хотя бы одну категорию!'}, status=400)

            chosen_cat_key = random.choice(valid_cats)
            cat_data = words_db[chosen_cat_key]
            chosen_item = random.choice(cat_data['items'])

            room['secretItem'] = chosen_item['name']
            room['secretCategory'] = cat_data['name']
            room['secretCatKey'] = chosen_cat_key
            room['state'] = 'PLAYING'
            room['circleNum'] = 1
            room['revealData'] = None

            # Establish Circle turn order
            player_ids = [p['id'] for p in room['players']]
            random.shuffle(player_ids)
            room['turnOrder'] = player_ids
            room['currentSpeakerIdx'] = 0

            # Assign spies
            for p in room['players']:
                p['isSpy'] = False
                p['votedFor'] = None

            num_spies = min(room['settings'].get('spyCount', 1), max(1, len(room['players']) // 2))
            spy_indices = set(random.sample(range(len(room['players'])), num_spies))

            for idx, p in enumerate(room['players']):
                if idx in spy_indices:
                    p['isSpy'] = True
                    p['word'] = '🕵️ ВЫ ШПИОН!'
                    p['role'] = 'Узнайте подсказку и не выдавайте себя в Discord!'
                else:
                    p['isSpy'] = False
                    p['word'] = chosen_item['name']
                    p['role'] = random.choice(chosen_item.get('roles', ['Житель']))

            self.send_json({'success': True})

        elif parsed.path == '/api/pass_turn':
            code = data.get('roomCode', '').upper()
            player_id = data.get('playerId')

            if code in ROOMS and ROOMS[code]['state'] == 'PLAYING':
                room = ROOMS[code]
                current_speaker_id = room['turnOrder'][room['currentSpeakerIdx']]
                if player_id == current_speaker_id or player_id == room['hostId']:
                    room['currentSpeakerIdx'] += 1
                    if room['currentSpeakerIdx'] >= len(room['turnOrder']):
                        room['currentSpeakerIdx'] = 0
                        room['circleNum'] += 1
                    self.send_json({'success': True})

        elif parsed.path == '/api/start_next_circle':
            code = data.get('roomCode', '').upper()
            if code in ROOMS:
                room = ROOMS[code]
                room['state'] = 'PLAYING'
                self.send_json({'success': True})

        elif parsed.path == '/api/start_voting':
            code = data.get('roomCode', '').upper()
            if code in ROOMS:
                ROOMS[code]['state'] = 'VOTING'
                self.send_json({'success': True})

        elif parsed.path == '/api/cast_vote':
            code = data.get('roomCode', '').upper()
            player_id = data.get('playerId')
            target_id = data.get('targetId')

            if code in ROOMS and ROOMS[code]['state'] == 'VOTING':
                room = ROOMS[code]
                voter = next((p for p in room['players'] if p['id'] == player_id), None)
                if voter:
                    voter['votedFor'] = target_id

                total_votes = len([p for p in room['players'] if p.get('votedFor') is not None])
                if total_votes >= len(room['players']):
                    # Calculate who was voted out
                    vote_counts = {}
                    for p in room['players']:
                        if p.get('votedFor'):
                            vote_counts[p['votedFor']] = vote_counts.get(p['votedFor'], 0) + 1

                    max_votes = 0
                    voted_out_id = None
                    tie = False

                    for pid, count in vote_counts.items():
                        if count > max_votes:
                            max_votes = count
                            voted_out_id = pid
                            tie = False
                        elif count == max_votes:
                            tie = True

                    voted_out_player = next((p for p in room['players'] if p['id'] == voted_out_id), None)
                    spies = [p for p in room['players'] if p['isSpy']]

                    if voted_out_player and voted_out_player['isSpy'] and not tie:
                        # Accused player is SPY -> Give Spy 1 chance to guess the secret word!
                        room['state'] = 'SPY_GUESS'
                        room['votedOutPlayer'] = voted_out_player
                    else:
                        # Accused player is NOT spy -> Spy wins instantly!
                        for s in spies: s['score'] += 200
                        room['state'] = 'REVEAL'
                        room['revealData'] = {
                            'votedOutPlayer': {'name': voted_out_player['name'], 'isSpy': voted_out_player['isSpy']} if voted_out_player else None,
                            'tie': tie,
                            'spies': [{'name': s['name']} for s in spies],
                            'secretItem': room['secretItem'],
                            'secretCategory': room['secretCategory'],
                            'players': [{'name': p['name'], 'score': p['score'], 'isSpy': p['isSpy']} for p in room['players']],
                            'resultMessage': '🕵️ ПОБЕДА ШПИОНА! Мирные ошиблись с выбором!'
                        }

                self.send_json({'success': True})

        elif parsed.path == '/api/spy_guess':
            code = data.get('roomCode', '').upper()
            player_id = data.get('playerId')
            guessed_word = data.get('guessedWord', '').strip()

            if code in ROOMS and ROOMS[code]['state'] == 'SPY_GUESS':
                room = ROOMS[code]
                spies = [p for p in room['players'] if p['isSpy']]
                
                if guessed_word.lower() == room['secretItem'].lower():
                    # Spy guessed correctly -> Spy steals win!
                    for s in spies: s['score'] += 200
                    msg = '🕵️ ШПИОН УГАДАЛ СЛОВО И ПЕРЕХВАТИЛ ПОБЕДУ!'
                else:
                    # Spy failed -> Non-spies win!
                    for p in room['players']:
                        if not p['isSpy']: p['score'] += 100
                    msg = '🎉 ПОБЕДА МИРНЫХ! Шпион не угадал карточку!'

                room['state'] = 'REVEAL'
                room['revealData'] = {
                    'votedOutPlayer': {'name': room['votedOutPlayer']['name'], 'isSpy': True},
                    'spies': [{'name': s['name']} for s in spies],
                    'secretItem': room['secretItem'],
                    'secretCategory': room['secretCategory'],
                    'players': [{'name': p['name'], 'score': p['score'], 'isSpy': p['isSpy']} for p in room['players']],
                    'resultMessage': msg
                }
                self.send_json({'success': True})

        elif parsed.path == '/api/reset_to_lobby':
            code = data.get('roomCode', '').upper()
            player_id = data.get('playerId')
            if code in ROOMS and ROOMS[code]['hostId'] == player_id:
                room = ROOMS[code]
                room['state'] = 'LOBBY'
                for p in room['players']:
                    p['votedFor'] = None
                    p['isSpy'] = False
                    p['role'] = ''
                    p['word'] = ''
                self.send_json({'success': True})

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("==================================================")
    print(" DEEPWOKEN SPY SERVER (DISCORD VC + CIRCLES) READY!")
    print(f" Open in browser: http://localhost:{PORT}")
    print("==================================================")
    class ThreadingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        daemon_threads = True
        allow_reuse_address = True

    with ThreadingServer(("", PORT), GameHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
