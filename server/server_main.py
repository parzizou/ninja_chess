# Serveur: IP/port, connexions, jeu temps réel + boutique (Upgrade objets)

from globals import *
from classes import *
from flask import Flask, request, jsonify
import threading, time, socket, random

# Import du catalogue d'upgrades (objets Upgrade)
from init import upgrades_silver, upgrades_gold, upgrades_platinium

app = Flask(__name__)
game = Game()
state_lock = threading.Lock()

def cooldown_ticker():
    while True:
        with state_lock:
            game.tick_cooldowns()
        time.sleep(TICK_INTERVAL_SECONDS)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]; s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@app.route('/state', methods=['GET'])
def get_game_state():
    return jsonify(game.game_state())

@app.route('/connect', methods=['POST'])
def connect_player():
    data = request.get_json(silent=True) or {}
    player_name = data.get('name')
    if not player_name:
        return jsonify({'status':'error','error':'missing_name'}), 400
    with state_lock:
        player_id = game.add_player(player_name)
        if player_id is not None:
            if len(game.players) == MAX_PLAYERS and game.current_state == 'waiting':
                game.start_game()
            return jsonify({'status':'connected','player_id':player_id})
        else:
            return jsonify({'status':'full'}), 403

def parse_move_payload(data):
    frm = data.get('from'); to = data.get('to'); piece = data.get('piece')
    if isinstance(frm, str): fx, fy = frm[0], int(frm[1:])
    else: fx, fy = frm.get('x'), int(frm.get('y'))
    if isinstance(to, str): tx, ty = to[0], int(to[1:])
    else: tx, ty = to.get('x'), int(to.get('y'))
    # Validation basique des coordonnées
    if fx not in 'abcdefgh' or tx not in 'abcdefgh':
        raise Exception("Invalid column (must be a-h)")
    if fy < 1 or fy > 8 or ty < 1 or ty > 8:
        raise Exception("Invalid row (must be 1-8)")
    return {'from': (fx, fy), 'to': (tx, ty), 'piece': piece}

@app.route('/move', methods=['POST'])
def make_move():
    data = request.get_json(silent=True) or {}
    player_id = data.get('player_id'); move_raw = data.get('move')
    if player_id is None or move_raw is None:
        return jsonify({'success':False,'error':'missing_params'}), 400
    try:
        move = parse_move_payload(move_raw)
    except Exception:
        return jsonify({'success':False,'error':'invalid_move_format'}), 400
    with state_lock:
        ok, reason = game.make_move(int(player_id), move)
        if ok:
            return jsonify({'success':True, 'state': game.game_state()})
        else:
            return jsonify({'success':False, 'error':reason, 'state': game.game_state()}), 400

# ======== Boutique (Upgrade objets + pièces) ========

RARITY_TO_POOL = {
    'silver': upgrades_silver,
    'gold': upgrades_gold,
    'platinium': upgrades_platinium,
}

# Pool de pièces achetables par rareté (MVP)
RARITY_TO_PIECES = {
    'silver': ['archer', 'sappeur', 'fantome'],
    'gold': ['archer', 'sappeur', 'fantome'],
    'platinium': ['dragon'],
}

@app.route('/shop', methods=['GET'])
def get_shop_offers():
    player_id = request.args.get('player_id', type=int)
    rarity = request.args.get('rarity', default='silver', type=str)
    with state_lock:
        if player_id is None or player_id < 0 or player_id >= len(game.players):
            return jsonify({'success':False,'error':'invalid_player'}), 400
        if game.current_state != 'shop':
            return jsonify({'success':False,'error':'not_in_shop', 'state': game.game_state()}), 400
        if rarity not in RARITIES:
            return jsonify({'success':False,'error':'invalid_rarity'}), 400
        # Générer si pas déjà fait
        bucket = game.shop_offers.get(player_id, {}).get(rarity)
        if not bucket:
            priced = []
            # Générer des upgrades
            pool = RARITY_TO_POOL.get(rarity, [])
            upgrade_offers = random.sample(pool, k=min(2, len(pool))) if pool else []
            for upg in upgrade_offers:
                # Clone léger pour annoter la rareté (n'affecte pas le catalogue)
                u = Upgrade(upg.name, upg.description, uid=upg.id, rarity=rarity)
                priced.append({
                    'type': 'upgrade',
                    'upgrade': u,
                    'name': u.name,
                    'desc': u.description,
                    'rarity': rarity,
                    'price': RARITIES[rarity]['price'],
                    'oid': f"{rarity}-{u.id}-{random.randint(1000,9999)}"
                })
            # Générer des pièces
            piece_pool = RARITY_TO_PIECES.get(rarity, [])
            piece_offers = random.sample(piece_pool, k=min(1, len(piece_pool))) if piece_pool else []
            for piece_name in piece_offers:
                priced.append({
                    'type': 'piece',
                    'piece': piece_name,
                    'name': f'Nouvelle pièce : {piece_name.capitalize()}',
                    'desc': f"Ajoute {piece_name.capitalize()} x1 à l'inventaire",
                    'rarity': rarity,
                    'price': RARITIES[rarity]['price'],
                    'oid': f"{rarity}-piece-{piece_name}-{random.randint(1000,9999)}"
                })
            game.store_offers(player_id, rarity, priced)
            bucket = priced
        # Sérialisation pour le client
        resp_offers = [{'name': o['name'], 'desc': o['desc'], 'rarity': o['rarity'],
                        'price': o['price'], 'oid': o['oid']} for o in bucket]
        return jsonify({'success':True, 'rarity':rarity, 'offers':resp_offers,
                        'gold': game.players[player_id].gold, 'deadline': game.shop_deadline})

@app.route('/buy', methods=['POST'])
def buy_offer():
    data = request.get_json(silent=True) or {}
    player_id = data.get('player_id'); oid = data.get('oid')
    if player_id is None or oid is None:
        return jsonify({'success':False,'error':'missing_params'}), 400
    with state_lock:
        if game.current_state != 'shop':
            return jsonify({'success':False,'error':'not_in_shop'}), 400
        ok, msg = game.apply_purchase(int(player_id), oid)
        if ok:
            return jsonify({'success':True, 'gold': game.players[int(player_id)].gold})
        else:
            return jsonify({'success':False, 'error': msg}), 400

@app.route('/set_board', methods=['POST'])
def set_board():
    data = request.get_json(silent=True) or {}
    player_id = data.get('player_id'); layout = data.get('layout', [])
    if player_id is None:
        return jsonify({'success':False,'error':'missing_params'}), 400
    with state_lock:
        if game.current_state != 'shop':
            return jsonify({'success':False,'error':'not_in_shop'}), 400
        ok, msg = game.validate_and_set_board(int(player_id), layout)
        if ok: return jsonify({'success':True})
        return jsonify({'success':False,'error':msg}), 400

@app.route('/ready', methods=['POST'])
def set_ready():
    data = request.get_json(silent=True) or {}
    player_id = data.get('player_id'); ready = bool(data.get('ready', True))
    if player_id is None:
        return jsonify({'success':False,'error':'missing_params'}), 400
    with state_lock:
        if game.current_state != 'shop':
            return jsonify({'success':False,'error':'not_in_shop'}), 400
        pid = int(player_id)
        if pid < 0 or pid >= len(game.players):
            return jsonify({'success':False,'error':'invalid_player'}), 400
        game.players[pid].ready = ready
        game.try_start_next_round()
        return jsonify({'success':True,'ready':ready})

if __name__ == '__main__':
    t = threading.Thread(target=cooldown_ticker, daemon=True); t.start()
    ip = get_local_ip()
    print(f"Server is starting on http://{ip}:5000")
    print("Waiting for players to connect... (state endpoint: /state)")
    app.run(host='0.0.0.0', port=5000, debug=False)