from globals import *



class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]
    
    def case(self, x, y):
        # retourne l'objet contenu de la case (lettre et chiffre)
        lettres = 'abcdefgh'
        x = lettres.index(x)
        y = int(y) - 1
        return self.grid[y][x]
    
    def index_case(self, x, y):
        # retourne l'index de la case (lettre et chiffre)
        lettres = 'abcdefgh'
        x = lettres.index(x)
        y = int(y) - 1
        return (x, y)
    
    def liste_lignes(self):
        return self.grid
    
    def liste_colonnes(self):
        return [[self.grid[y][x] for y in range(self.height)] for x in range(self.width)]
    
    def liste_diagonales(self):
        diagonales = []
        for p in range(self.width + self.height - 1):
            diag1 = []
            diag2 = []
            for q in range(max(p - self.height + 1, 0), min(p + 1, self.width)):
                diag1.append(self.grid[p - q][q])
                diag2.append(self.grid[self.height - 1 - (p - q)][q])
            diagonales.append(diag1)
            diagonales.append(diag2)
        return diagonales
    
    def afficher(self):
        for row in self.grid:
            print(' | '.join([str(cell) if cell is not None else '.' for cell in row]))
        print('\n')
    
class Game:
    def __init__(self, player1, player2):
        self.board = Board(8, 8)
        self.players = [player1, player2]
        self.current_time = 0
        self.move_history = []
        self.current_state = 'waiting'  # 'waiting', 'in_game', 'game_over'
        
    def game_state(self):
        # retourne l'etat actuel du jeu
        state = {
            'board': self.board,
            'players': self.players,
            'current_time': self.current_time,
            'move_history': self.move_history,
            'current_state': self.current_state
        }
        return state   
    
    def is_over(self):
        #vérifie si le jeu est terminé en regardant si un roi est mort
        for player in self.players:
            for piece in player.pieces:
                if piece.name == 'king' and not piece.alive:
                    self.current_state = 'game_over'
                    return True
                
        return False
    
    def get_winner(self):
        for player in self.players:
            for piece in player.pieces:
                if piece.name == 'king' and piece.alive:
                    return player
        return None
    
    def add_player(self, player_name):
        if len(self.players) < 2:
            color = 'white' if len(self.players) == 0 else 'black'
            new_player = Player(player_name, color)
            self.players.append(new_player)
            return len(self.players) - 1  # retourne l'id du joueur
        else:
            return None  # le jeu est plein
        
        
    def start_game(self):
        # initialiser les pieces sur le board pour chaque joueur
        for player in self.players:
            if player.color == 'white':
                back_row = [Rook('white'), Knight('white'), Bishop('white'), Queen('white'),
                            King('white'), Bishop('white'), Knight('white'), Rook('white')]
                pawn_row = [Pawn('white') for _ in range(8)]
                for x in range(8):
                    self.board.grid[0][x] = back_row[x]
                    back_row[x].position = (chr(ord('a') + x), 1)
                    player.pieces.append(back_row[x])
                    self.board.grid[1][x] = pawn_row[x]
                    pawn_row[x].position = (chr(ord('a') + x), 2)
                    player.pieces.append(pawn_row[x])
            else:
                back_row = [Rook('black'), Knight('black'), Bishop('black'), Queen('black'),
                            King('black'), Bishop('black'), Knight('black'), Rook('black')]
                pawn_row = [Pawn('black') for _ in range(8)]
                for x in range(8):
                    self.board.grid[7][x] = back_row[x]
                    back_row[x].position = (chr(ord('a') + x), 8)
                    player.pieces.append(back_row[x])
                    self.board.grid[6][x] = pawn_row[x]
                    pawn_row[x].position = (chr(ord('a') + x), 7)
                    player.pieces.append(pawn_row[x])
                    
            self.current_state = 'in_game'
    
    def make_move(self, player_id, move):
        # le move est un dico contenant 'from': (x1, y1), 'to': (x2, y2), 'piece': piece_name , 'promotion': piece_name (optionnel) , 'roque': 'king_side'/'queen_side' (optionnel)
        player = self.players[player_id]
        from_x, from_y = move['from']
        to_x, to_y = move['to']
        piece_name = move['piece']
        piece = self.board.case(from_x, from_y)
        
        # verifier que le mouvement est valide
        # verifier que la piece a un cd de 0
        # verifier que la case d'arrivé est soit vide, soit il faut capturer une piece adverse
        if piece is None or piece.name != piece_name or piece.color != player.color:
            return False  # mouvement invalide
        
        possible_moves = piece.possible_moves(self)
        if (self.board.index_case(to_x, to_y)) not in possible_moves:
            return False  # mouvement invalide
        
        if piece.cd > 0:
            return False  # piece en cooldown
        
        target_piece = self.board.case(to_x, to_y)
        if target_piece is not None and target_piece.color == player.color:
            return False  # ne peut pas capturer une piece alliée
        
        # effectuer le mouvement
        self.board.grid[self.board.index_case(from_x, from_y)[1]][self.board.index_case(from_x, from_y)[0]] = None
        self.board.grid[self.board.index_case(to_x, to_y)[1]][self.board.index_case(to_x, to_y)[0]] = piece
        piece.position = (to_x, to_y)
        piece.history.append(((from_x, from_y), (to_x, to_y)))
        piece.reset_cooldown()
        if target_piece is not None:
            target_piece.alive = False  # capturer la piece adverse
            
        self.move_history.append({'player_id': player_id, 'from': (from_x, from_y), 'to': (to_x, to_y), 'piece': piece_name})
        return True  # mouvement réussi
    
class Piece:
    def __init__(self, name, color, cd_base):
        if name in lst_allowed_pieces:
            self.name = name
            self.color = color
            self.cd_base = cd_base
            self.cd = cd_base
            self.history = []
            self.alive = True
            self.position = None
        else:
            raise ValueError(f"Invalid piece name: {name}\nAllowed pieces are: {lst_allowed_pieces}")
        
        
    def reset_cooldown(self):
        self.cd = self.cd_base
        
    def cancel_cooldown(self):
        self.cd = 0
        
    def possible_moves(self, game):
        # fonction a overrider dans les sous-classes
        return []
    
    def __str__(self):
        # retourne une representation textuelle de la piece en une lettre
        initials = {'p': 'P', 'r': 'R', 'n': 'N', 'b': 'B', 'q': 'Q', 'k': 'K'}
        return initials[self.name[0].lower()] if self.color == 'white' else initials[self.name[0].lower()].lower()
    
    

class Knight(Piece):
    def __init__(self, color):
        super().__init__('knight', color, cd_base=1)
        
    # override les mouvements possibles
    def possible_moves(self, game):
        moves = []
        x, y = game.board.index_case(self.position[0], self.position[1])
        knight_moves = [(2, 1), (1, 2), (-1, 2), (-2, 1),
                        (-2, -1), (-1, -2), (1, -2), (2, -1)]
        for dx, dy in knight_moves:
            nx, ny = x + dx, y + dy
            if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                target = game.board.grid[ny][nx]
                if target is None or target.color != self.color:
                    moves.append((nx, ny))
        return moves
    

class Rook(Piece):
    def __init__(self, color):
        super().__init__('rook', color, cd_base=1)
        
    # override les mouvements possibles
    def possible_moves(self, game):
        moves = []
        x, y = game.board.index_case(self.position[0], self.position[1])
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dx, dy in directions:
            nx, ny = x, y
            while True:
                nx += dx
                ny += dy
                if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                    target = game.board.grid[ny][nx]
                    if target is None:
                        moves.append((nx, ny))
                    elif target.color != self.color:
                        moves.append((nx, ny))
                        break
                    else:
                        break
                else:
                    break
        return moves
    
    
class Bishop(Piece):
    def __init__(self, color):
        super().__init__('bishop', color, cd_base=1)
        
    # override les mouvements possibles
    def possible_moves(self, game):
        moves = []
        x, y = game.board.index_case(self.position[0], self.position[1])
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dx, dy in directions:
            nx, ny = x, y
            while True:
                nx += dx
                ny += dy
                if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                    target = game.board.grid[ny][nx]
                    if target is None:
                        moves.append((nx, ny))
                    elif target.color != self.color:
                        moves.append((nx, ny))
                        break
                    else:
                        break
                else:
                    break
        return moves
    

class Queen(Piece):
    def __init__(self, color):
        super().__init__('queen', color, cd_base=1)
        
    # override les mouvements possibles
    def possible_moves(self, game):
        moves = []
        x, y = game.board.index_case(self.position[0], self.position[1])
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),          (0, 1),
                      (1, -1), (1, 0), (1, 1)]
        for dx, dy in directions:
            nx, ny = x, y
            while True:
                nx += dx
                ny += dy
                if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                    target = game.board.grid[ny][nx]
                    if target is None:
                        moves.append((nx, ny))
                    elif target.color != self.color:
                        moves.append((nx, ny))
                        break
                    else:
                        break
                else:
                    break
        return moves
    
    
class King(Piece):
    def __init__(self, color):
        super().__init__('king', color, cd_base=1)
        
    # override les mouvements possibles
    def possible_moves(self, game):
        moves = []
        x, y = game.board.index_case(self.position[0], self.position[1])
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),          (0, 1),
                      (1, -1), (1, 0), (1, 1)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                target = game.board.grid[ny][nx]
                if target is None or target.color != self.color:
                    moves.append((nx, ny))
                    
        # ajouter les mouvements de roque ici si necessaire en regardant l'historique des mouvements du roi et de la tour, et si les cases entre le roi et la tour sont libres

        if self.history == []:
            # roque du cote roi
            if isinstance(game.board.grid[y][7], Rook) and game.board.grid[y][7].history == []:
                if all(game.board.grid[y][x] is None for x in range(x + 1, 7)):
                    moves.append((x + 2, y))
            # roque du cote dame
            if isinstance(game.board.grid[y][0], Rook) and game.board.grid[y][0].history == []:
                if all(game.board.grid[y][x] is None for x in range(1, x)):
                    moves.append((x - 2, y))
        
        return moves
    
class Pawn(Piece):
    def __init__(self, color):
        super().__init__('pawn', color, cd_base=1)
        
    # override les mouvements possibles
    def possible_moves(self, game):
        moves = []
        x, y = game.board.index_case(self.position[0], self.position[1])
        direction = 1 if self.color == 'white' else -1
        
        # mouvement en avant
        if 0 <= y + direction < game.board.height and game.board.grid[y + direction][x] is None:
            moves.append((x, y + direction))
            # mouvement initial de deux cases
            if (self.color == 'white' and y == 1) or (self.color == 'black' and y == 6):
                if game.board.grid[y + 2 * direction][x] is None:
                    moves.append((x, y + 2 * direction))
        
        # captures diagonales
        for dx in [-1, 1]:
            nx = x + dx
            ny = y + direction
            if 0 <= nx < game.board.width and 0 <= ny < game.board.height:
                target = game.board.grid[ny][nx]
                if target is not None and target.color != self.color:
                    moves.append((nx, ny))
        
        
        return moves
        
class Player:
    def __init__(self, username, color):
        self.username = username
        self.color = color
        self.pieces = []
        
    

    
        
        

    
    
    
# tests

test_board = Board(8, 8)
# remplir le board avec des chiffres pour tester
for y in range(8):
    for x in range(8):
        test_board.grid[y][x] = y * 8 + x
        

test_board.afficher()
print(test_board.liste_lignes())
print(test_board.liste_colonnes())
print(test_board.liste_diagonales())

