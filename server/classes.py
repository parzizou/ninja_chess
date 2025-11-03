from globals import *
import time, random, copy, re

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s

def pos_tuple_to_str(pos):
    return f"{pos[0]}{pos[1]}"

def pos_str_to_tuple(pos_str):
    return (pos_str[0], int(pos_str[1:]))

def owner_for_piece(game, piece):
    for p in game.players:
        if piece in p.pieces:
            return p
    return None

class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]
    
    def case(self, x, y):
        lettres = 'abcdefgh'
        xi = lettres.index(x)
        yi = int(y) - 1
        return self.grid[yi][xi]
    
    def index_case(self, x, y):
        lettres = 'abcdefgh'
        xi = lettres.index(x)
        yi = int(y) - 1
        return (xi, yi)
    
    def to_json_grid(self):
        out = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                piece = self.grid[y][x]
                if piece is None:
                    row.append(None)
                else:
                    d = piece.to_dict()
                    d['pos'] = f"{chr(ord('a') + x)}{y + 1}"
                    row.append(d)
            out.append(row)
        return out

class Upgrade:
    # Reste compatible avec Upgrade(name, description)
    def __init__(self, name: str, description: str = "", uid: str | None = None, rarity: str | None = None, data: dict | None = None):
        self.name = name
        self.description = description or ""
        self.id = uid or slugify(name)
        self.rarity = rarity
        self.data = data or {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'rarity': self.rarity
        }

class Game:
    def __init__(self):
        self.board = Board(8, 8)
        self.players = []  # Player[]
        self.current_time = 0
        self.move_history = []
        self.current_state = 'waiting'  # 'waiting', 'in_game', 'shop', 'game_over'
        self.round_number = 0
        # Boutique
        self.shop_deadline = None
        # {player_id: {rarity: [ {type:'upgrade', 'upgrade': Upgrade, 'price': int, 'oid': str} ]}}
        self.shop_offers = {}
    
    def game_state(self):
        return {
            'board': self.board.to_json_grid(),
            'players': [p.to_dict(i) for i, p in enumerate(self.players)],
            'current_time': self.current_time,
            'move_history': self.move_history,
            'current_state': self.current_state,
            'round_number': self.round_number,
            'shop_deadline': self.shop_deadline
        }
    
    def is_over(self):
        for player in self.players:
            for piece in player.pieces:
                if piece.name == 'king' and not piece.alive:
                    self.current_state = 'shop'
                    return True
        return False
    
    def get_winner(self):
        # roi encore vivant
        for p in self.players:
            for piece in p.pieces:
                if piece.name == 'king' and piece.alive:
                    return p
        return None
    
    def add_player(self, player_name):
        if len(self.players) < MAX_PLAYERS:
            color = 'white' if len(self.players) == 0 else 'black'
            new_player = Player(player_name, color)
            self.players.append(new_player)
            return len(self.players) - 1
        else:
            return None
    
    def default_layout_for(self, color):
        layout = []
        if color == 'white':
            back = ['rook','knight','bishop','queen','king','bishop','knight','rook']
            for x, name in enumerate(back):
                layout.append({'pos': (chr(ord('a')+x), 1), 'name': name})
            for x in range(8):
                layout.append({'pos': (chr(ord('a')+x), 2), 'name': 'pawn'})
        else:
            back = ['rook','knight','bishop','queen','king','bishop','knight','rook']
            for x, name in enumerate(back):
                layout.append({'pos': (chr(ord('a')+x), 8), 'name': name})
            for x in range(8):
                layout.append({'pos': (chr(ord('a')+x), 7), 'name': 'pawn'})
        return layout
    
    def apply_layout(self, player):
        # nettoie pièces du joueur et pose selon desired_layout
        for y in range(self.board.height):
            for x in range(self.board.width):
                piece = self.board.grid[y][x]
                if piece is not None and piece.color == player.color:
                    self.board.grid[y][x] = None
        player.pieces = []
        layout = player.desired_layout or self.default_layout_for(player.color)
        name_to_cls = {
            'pawn': Pawn, 'rook': Rook, 'knight': Knight, 'bishop': Bishop,
            'queen': Queen, 'king': King, 'dragon': Dragon, 'sappeur': Sappeur,
            'archer': Archer, 'fantome': Fantome
        }
        for item in layout:
            cls = name_to_cls.get(item['name'])
            if not cls: continue
            piece = cls(player.color)
            ix, iy = self.board.index_case(item['pos'][0], item['pos'][1])
            self.board.grid[iy][ix] = piece
            piece.position = item['pos']
            player.pieces.append(piece)
    
    def start_round(self):
        self.board = Board(8, 8)
        for p in self.players:
            if p.desired_layout is None:
                p.desired_layout = self.default_layout_for(p.color)
            self.apply_layout(p)
            for piece in p.pieces:
                piece.cd = 0
                piece.history = []
                piece.alive = True
        self.current_state = 'in_game'
        self.round_number += 1
        self.move_history = []
    
    def start_game(self):
        if len(self.players) != 2:
            return False
        for p in self.players:
            p.max_hp = PLAYER_MAX_HP
            # Ajuste max_hp si Extra HP déjà acheté avant
            if p.has_upgrade("Extra HP"):
                p.max_hp += 2
            p.hp = p.max_hp
            p.gold = 0
            p.ready = False
            p.inventory = copy.deepcopy(p.base_inventory())
            if p.desired_layout is None:
                p.desired_layout = self.default_layout_for(p.color)
        self.start_round()
        return True
    
    def start_shop_phase(self):
        self.award_coins_from_round()
        self.current_state = 'shop'
        self.shop_deadline = int(time.time()) + SHOP_DURATION_SECONDS
        # reset ready + vider offres précédentes
        for i, p in enumerate(self.players):
            p.ready = False
            self.shop_offers[i] = {}
    
    def award_coins_from_round(self):
        winner = self.get_winner()
        for i, p in enumerate(self.players):
            captures = sum(1 for m in self.move_history if m.get('player_id') == i and m.get('captured'))
            gain = (BASE_COINS_WINNER if p is winner else BASE_COINS_LOSER) + captures * COINS_PER_CAPTURE
            if p.has_upgrade("Gold Boost"):
                gain += 3
            # Bonus simple pour "Collection de Couronnes" (version non-cumulée pour MVP)
            if p is winner and p.has_upgrade("Collection de Couronnes"):
                gain += 4
            p.gold += gain
        # Soin post-victoire
        if winner and winner.has_upgrade("Aspiration d'âme"):
            winner.hp = min(winner.max_hp, winner.hp + 0.5)
    
    def all_ready_or_timeout(self):
        if self.current_state != 'shop':
            return False
        if all(p.ready for p in self.players):
            return True
        if self.shop_deadline and int(time.time()) >= self.shop_deadline:
            return True
        return False
    
    def try_start_next_round(self):
        if any(p.hp <= 0 for p in self.players):
            self.current_state = 'game_over'
            return
        if self.all_ready_or_timeout():
            self.start_round()
    
    def tick_cooldowns(self):
        if self.current_state == 'in_game':
            for player in self.players:
                for piece in player.pieces:
                    if piece.alive and piece.cd > 0:
                        piece.cd -= 1
        elif self.current_state == 'shop':
            self.try_start_next_round()
    
    def store_offers(self, player_id: int, rarity: str, offers: list):
        # offers: liste de dicts prêts à sérialiser (contiennent Upgrade pour l'achat)
        if player_id not in self.shop_offers:
            self.shop_offers[player_id] = {}
        self.shop_offers[player_id][rarity] = offers
    
    def apply_purchase(self, player_id, oid):
        bucket = self.shop_offers.get(player_id, {})
        for rarity, offers in bucket.items():
            for off in list(offers):
                if off.get('oid') == oid:
                    price = off['price']
                    player = self.players[player_id]
                    if player.gold < price:
                        return False, "not_enough_gold"
                    if off['type'] == 'upgrade':
                        upg: Upgrade = off['upgrade']
                        # Tagger la rareté de l'upgrade au moment de l'achat
                        if not upg.rarity:
                            upg.rarity = rarity
                        player.upgrades.append(upg)
                        # Effet immédiat "Extra HP": on augmente le max et on soigne de +2
                        if upg.name == "Extra HP":
                            player.max_hp += 2
                            player.hp = min(player.max_hp, player.hp + 2)
                        player.gold -= price
                        offers.remove(off)
                        return True, "ok"
                    return False, "unsupported_offer_type"
        return False, "offer_not_found"
    
    def validate_and_set_board(self, player_id, layout_items):
        player = self.players[player_id]
        allowed_ranks = {1,2} if player.color == 'white' else {7,8}
        if len(layout_items) > 16:
            return False, "too_many_pieces"
        kings = [it for it in layout_items if it['name'] == 'king']
        if len(kings) != 1:
            return False, "must_have_one_king"
        seen = set()
        for it in layout_items:
            n = it['name']
            if n not in lst_allowed_pieces:
                return False, "piece_not_allowed"
            pos = it['pos']
            x, y = pos[0], int(pos[1:])
            if y not in allowed_ranks:
                return False, "invalid_rank"
            key = (x, y)
            if key in seen:
                return False, "duplicate_pos"
            seen.add(key)
        available = player.total_available_piece_counts()
        needed = {}
        for it in layout_items:
            needed[it['name']] = needed.get(it['name'], 0) + 1
        for name, count in needed.items():
            if available.get(name, 0) < count:
                return False, "not_owned_enough"
        dl = [{'name': it['name'], 'pos': (it['pos'][0], int(it['pos'][1:]))} for it in layout_items]
        player.desired_layout = dl
        return True, "ok"
    
    def make_move(self, player_id, move):
        if self.current_state != 'in_game':
            return False, "not_in_game"
        player = self.players[player_id]
        from_x, from_y = move['from']
        to_x, to_y = move['to']
        piece_name = move['piece']
        piece = self.board.case(from_x, from_y)
        if piece is None or piece.name != piece_name or piece.color != player.color:
            return False, "invalid_piece"
        if piece.cd > 0:
            return False, "on_cooldown"
        possible = piece.possible_moves(self)
        to_idx = self.board.index_case(to_x, to_y)
        if to_idx not in possible:
            return False, "illegal_move"
        target_piece = self.board.case(to_x, to_y)
        if target_piece is not None and target_piece.color == player.color:
            return False, "friendly_fire"
        fx, fy = self.board.index_case(from_x, from_y)
        tx, ty = to_idx
        self.board.grid[fy][fx] = None
        self.board.grid[ty][tx] = piece
        piece.position = (to_x, to_y)
        piece.history.append(((from_x, from_y), (to_x, to_y)))
        captured_flag = False
        if target_piece is not None:
            target_piece.alive = False
            captured_flag = True
        # Reset CD par défaut
        piece.reset_cooldown()
        # Effets d'upgrades réactifs simples
        if captured_flag:
            # Soin sur capture
            if player.has_upgrade("Recolte d'ame"):
                player.hp = min(player.max_hp, player.hp + 0.1)
            # Roi qui rejoue
            if piece.name == 'king' and player.has_upgrade("Assassinat royal"):
                piece.cancel_cooldown()
            # Pion furie
            if piece.name == 'pawn' and player.has_upgrade("Furie des Pions"):
                piece.cancel_cooldown()
            # Regicide: si on a capturé un roi adverse, réduire cd de 20%
            if isinstance(target_piece, King) and player.has_upgrade("Regicide"):
                piece.cd = max(0, piece.cd - max(1, int(round(0.2 * piece.cd_base))))
        self.move_history.append({
            'player_id': player_id,
            'from': pos_tuple_to_str((from_x, from_y)),
            'to': pos_tuple_to_str((to_x, to_y)),
            'piece': piece_name,
            'captured': captured_flag
        })
        # Fin de manche si roi mort
        if any(p.name == 'king' and not p.alive for p in self.players[0].pieces + self.players[1].pieces):
            winner = self.get_winner()
            if winner:
                for p in self.players:
                    if p is not winner:
                        p.hp -= 1
            self.start_shop_phase()
        return True, "ok"

class Piece:
    def __init__(self, name, color, cd_base):
        if name not in lst_allowed_pieces:
            raise ValueError(f"Invalid piece name: {name}\nAllowed pieces are: {lst_allowed_pieces}")
        self.name = name
        self.color = color
        self.cd_base = cd_base
        self.cd = 0
        self.history = []
        self.alive = True
        self.position = None
    
    def reset_cooldown(self):
        self.cd = self.cd_base
    def cancel_cooldown(self):
        self.cd = 0
    def possible_moves(self, game):
        return []
    def to_dict(self):
        return {'name': self.name, 'color': self.color, 'cd': self.cd, 'alive': self.alive,
                'pos': pos_tuple_to_str(self.position) if self.position else None}
    def __str__(self):
        initials = {'p': 'P', 'r': 'R', 'n': 'N', 'b': 'B', 'q': 'Q', 'k': 'K',
                    'd':'D','s':'S','a':'A','f':'F'}
        ch = initials.get(self.name[0].lower(), '?')
        return ch if self.color == 'white' else ch.lower()

class Knight(Piece):
    def __init__(self, color): super().__init__('knight', color, cd_base=1)
    def possible_moves(self, game):
        moves = []
        x, y = game.board.index_case(self.position[0], self.position[1])
        for dx, dy in [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                t = game.board.grid[ny][nx]
                if t is None or t.color != self.color: moves.append((nx, ny))
        return moves

class Rook(Piece):
    def __init__(self, color): super().__init__('rook', color, cd_base=1)
    def possible_moves(self, game):
        moves = []
        x, y = game.board.index_case(self.position[0], self.position[1])
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x, y
            while True:
                nx += dx; ny += dy
                if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                    t = game.board.grid[ny][nx]
                    if t is None: moves.append((nx, ny))
                    elif t.color != self.color: moves.append((nx, ny)); break
                    else: break
                else: break
        return moves

class Bishop(Piece):
    def __init__(self, color): super().__init__('bishop', color, cd_base=1)
    def possible_moves(self, game):
        moves = []
        x, y = game.board.index_case(self.position[0], self.position[1])
        for dx, dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nx, ny = x, y
            while True:
                nx += dx; ny += dy
                if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                    t = game.board.grid[ny][nx]
                    if t is None: moves.append((nx, ny))
                    elif t.color != self.color: moves.append((nx, ny)); break
                    else: break
                else: break
        return moves

class Queen(Piece):
    def __init__(self, color): super().__init__('queen', color, cd_base=1)
    def possible_moves(self, game):
        moves = []
        x, y = game.board.index_case(self.position[0], self.position[1])
        for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nx, ny = x, y
            while True:
                nx += dx; ny += dy
                if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                    t = game.board.grid[ny][nx]
                    if t is None: moves.append((nx, ny))
                    elif t.color != self.color: moves.append((nx, ny)); break
                    else: break
                else: break
        return moves

class King(Piece):
    def __init__(self, color): super().__init__('king', color, cd_base=1)
    def possible_moves(self, game):
        moves = []
        x, y = game.board.index_case(self.position[0], self.position[1])
        owner = owner_for_piece(game, self)
        # Base: 1 case autour
        deltas = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        # Force Royale: +1 case (donc distance 2)
        extra = owner and owner.has_upgrade("Force Royale")
        for dx, dy in deltas:
            nx, ny = x+dx, y+dy
            if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                t = game.board.grid[ny][nx]
                if t is None or t.color != self.color: moves.append((nx, ny))
            if extra:
                nx2, ny2 = x+2*dx, y+2*dy
                if 0 <= nx2 < game.board.width and 0 <= ny2 < game.board.height:
                    t2 = game.board.grid[ny2][nx2]
                    if t2 is None or t2.color != self.color: moves.append((nx2, ny2))
        # Sexo-permutation: déplacements de reine (ajoutés)
        if owner and owner.has_upgrade("Sexo-permutation"):
            for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                nx, ny = x, y
                while True:
                    nx += dx; ny += dy
                    if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                        t = game.board.grid[ny][nx]
                        if t is None: moves.append((nx, ny))
                        elif t.color != self.color: moves.append((nx, ny)); break
                        else: break
                    else: break
        # Roques simplifiés (inchangés)
        if self.history == []:
            if isinstance(game.board.grid[y][7], Rook) and game.board.grid[y][7].history == []:
                if all(game.board.grid[y][xx] is None for xx in range(x + 1, 7)):
                    moves.append((x + 2, y))
            if isinstance(game.board.grid[y][0], Rook) and game.board.grid[y][0].history == []:
                if all(game.board.grid[y][xx] is None for xx in range(1, x)):
                    moves.append((x - 2, y))
        return moves

class Pawn(Piece):
    def __init__(self, color): super().__init__('pawn', color, cd_base=1)
    def possible_moves(self, game):
        moves = []
        x, y = game.board.index_case(self.position[0], self.position[1])
        direction = 1 if self.color == 'white' else -1
        owner = owner_for_piece(game, self)
        first_rank = (self.color == 'white' and y == 1) or (self.color == 'black' and y == 6)
        # 1 case
        if 0 <= y+direction < game.board.height and game.board.grid[y+direction][x] is None:
            moves.append((x, y+direction))
            # 2 cases: initial OU upgrade "Marathonien"
            if (first_rank or (owner and owner.has_upgrade("Marathonien"))) and game.board.grid[y+2*direction][x] is None:
                moves.append((x, y+2*direction))
            # 3 cases au premier coup si "pions sprinteurs"
            if first_rank and owner and owner.has_upgrade("pions sprinteurs"):
                if 0 <= y+3*direction < game.board.height and game.board.grid[y+3*direction][x] is None:
                    moves.append((x, y+3*direction))
        # captures
        for dx in [-1, 1]:
            nx, ny = x+dx, y+direction
            if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                t = game.board.grid[ny][nx]
                if t is not None and t.color != self.color:
                    moves.append((nx, ny))
        # Optionnel: "Marche arrière" (simple: 1 case en arrière si vide)
        if owner and owner.has_upgrade("Marche arrière"):
            by = y - direction
            if 0 <= by < game.board.height and game.board.grid[by][x] is None:
                moves.append((x, by))
        return moves

class Dragon(Piece):
    def __init__(self, color): super().__init__('dragon', color, cd_base=1)
    def possible_moves(self, game):
        moves = []
        x, y = game.board.index_case(self.position[0], self.position[1])
        for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nx, ny = x, y
            while True:
                nx += dx; ny += dy
                if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                    t = game.board.grid[ny][nx]
                    if t is None: moves.append((nx, ny))
                    elif t.color != self.color: moves.append((nx, ny)); break
                    else: break
                else: break
        for dx, dy in [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                t = game.board.grid[ny][nx]
                if t is None or t.color != self.color: moves.append((nx, ny))
        return moves

class Sappeur(Piece):
    def __init__(self, color): super().__init__('sappeur', color, cd_base=1)
    def possible_moves(self, game):
        # identique au pion (MVP)
        return Pawn.possible_moves(self, game)

class Archer(Piece):
    def __init__(self, color): super().__init__('archer', color, cd_base=2)
    def possible_moves(self, game):
        moves = []
        x, y = game.board.index_case(self.position[0], self.position[1])
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                t = game.board.grid[ny][nx]
                if t is None or t.color != self.color: moves.append((nx, ny))
        # portée fixe 3 (on pourra l'upgrader plus tard)
        max_range = 3
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            for dist in range(1, max_range+1):
                nx, ny = x+dx*dist, y+dy*dist
                if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                    t = game.board.grid[ny][nx]
                    if t is not None and t.color != self.color:
                        moves.append((nx, ny)); break
                else: break
        return moves

class Fantome(Piece):
    def __init__(self, color): super().__init__('fantome', color, cd_base=1)
    def possible_moves(self, game):
        # MVP: base pion permissif à travers alliés non-codé (v1)
        return Pawn.possible_moves(self, game)

class Player:
    def __init__(self, username, color):
        self.username = username
        self.color = color
        self.pieces = []
        self.max_hp = PLAYER_MAX_HP
        self.hp = PLAYER_MAX_HP
        self.upgrades: list[Upgrade] = []
        self.gold = 0
        self.ready = False
        self.inventory = {}
        self.desired_layout = None
    
    def base_inventory(self):
        return {'king':1,'queen':1,'rook':2,'bishop':2,'knight':2,'pawn':8}
    
    def total_available_piece_counts(self):
        base = self.base_inventory()
        inv = self.inventory or {}
        out = {}
        for k in set(base) | set(inv):
            out[k] = base.get(k,0) + inv.get(k,0)
        return out
    
    def has_upgrade(self, name: str) -> bool:
        return any(u.name == name for u in self.upgrades)
    
    def to_dict(self, idx):
        return {
            'id': idx,
            'username': self.username,
            'color': self.color,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'gold': self.gold,
            'ready': self.ready,
            'upgrades': [u.to_dict() for u in self.upgrades],
            'inventory': self.inventory,
            'layout': [{'name': it['name'], 'pos': pos_tuple_to_str(it['pos'])} for it in (self.desired_layout or [])]
        }