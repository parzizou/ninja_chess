import pygame
import sys
import requests
import threading
import time

# Config Pygame
WIDTH, HEIGHT = 960, 8 * 80 + 160  # élargi pour la boutique
TILE = 80
FPS = 60

# Couleurs
WHITE = (240, 240, 240)
BLACK = (30, 30, 30)
LIGHT = (200, 200, 200)
DARK = (90, 90, 90)
GREEN = (50, 180, 90)
RED = (200, 60, 60)
BLUE = (60, 120, 220)
YELLOW = (230, 200, 40)
PURPLE = (150, 80, 180)
BG = (25, 25, 25)
GREY = (120, 120, 120)

# Helpers
def to_alg(col, row):
    return f"{chr(ord('a')+col)}{row+1}"

def from_alg(s):
    return ord(s[0]) - ord('a'), int(s[1:]) - 1

class Client:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Ninja Chess")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 20)
        self.bigfont = pygame.font.SysFont("consolas", 32, bold=True)
        self.running = True

        # UI state
        self.view = 'menu'  # 'menu', 'game', 'rules', 'shop', 'waiting', 'game_over'
        self.server_addr = "http://127.0.0.1:5000"
        self.player_name = "player"
        self.player_id = None
        self.player_color = None

        # Game state
        self.state = None
        self.selected = None
        self.last_error = ""
        self.poll_thread = None
        self.polling = False

        # Shop UI
        self.shop_offers = []  # last fetched offers
        self.shop_rarity = 'silver'
        self.palette_choice = None  # piece name selected to place
        self.local_layout = []  # [{'name':'pawn','pos':'a2'}, ...]

    def draw_text(self, txt, x, y, color=WHITE, font=None):
        if font is None: font = self.font
        surf = font.render(txt, True, color)
        self.screen.blit(surf, (x, y))

    def draw_menu(self):
        self.screen.fill(BG)
        self.draw_text("Ninja Chess - Menu", 20, 20, YELLOW, self.bigfont)
        self.draw_text("Adresse du serveur (ex: http://127.0.0.1:5000):", 20, 80)
        pygame.draw.rect(self.screen, DARK, (20, 110, 500, 32), border_radius=6)
        self.draw_text(self.server_addr, 26, 115)

        self.draw_text("Ton pseudo:", 20, 160)
        pygame.draw.rect(self.screen, DARK, (20, 190, 300, 32), border_radius=6)
        self.draw_text(self.player_name, 26, 195)

        join_rect = pygame.Rect(20, 240, 150, 40)
        rules_rect = pygame.Rect(190, 240, 150, 40)
        pygame.draw.rect(self.screen, BLUE, join_rect, border_radius=6)
        pygame.draw.rect(self.screen, LIGHT, rules_rect, border_radius=6)
        self.draw_text("Rejoindre", join_rect.x+20, join_rect.y+10)
        self.draw_text("Règles", rules_rect.x+40, rules_rect.y+10, BLACK)

        if self.last_error:
            self.draw_text(f"Erreur: {self.last_error}", 20, 300, RED)

        return join_rect, rules_rect

    def draw_rules(self):
        self.screen.fill(BG)
        self.draw_text("Règles (version rapide):", 20, 20, YELLOW, self.bigfont)
        lines = [
            "- Pas de tours: tu joues dès que ta pièce n'est pas en cooldown.",
            "- Si le Roi est capturé, la manche s'arrête.",
            "- Le perdant perd 1 HP (sur 5).",
            "- Boutique entre les manches: upgrades et nouvelles pièces.",
            "- Clique une de tes pièces (cd=0), puis la case d'arrivée.",
        ]
        y = 80
        for l in lines:
            self.draw_text(l, 20, y); y += 28
        back_rect = pygame.Rect(20, HEIGHT-60, 160, 40)
        pygame.draw.rect(self.screen, BLUE, back_rect, border_radius=6)
        self.draw_text("Retour", back_rect.x+40, back_rect.y+10)
        return back_rect

    def draw_waiting(self):
        self.screen.fill(BG)
        self.draw_text("En attente d'un adversaire...", WIDTH//2 - 200, HEIGHT//2 - 40, YELLOW, self.bigfont)
        if self.state:
            pl = self.state['players']
            self.draw_text(f"Joueurs connectés: {len(pl)}/2", WIDTH//2 - 120, HEIGHT//2 + 20, WHITE)

    def draw_game_over(self):
        self.screen.fill(BG)
        self.draw_text("Partie Terminée!", WIDTH//2 - 150, HEIGHT//2 - 80, YELLOW, self.bigfont)
        if self.state:
            pl = self.state['players']
            winner = None
            for p in pl:
                if p['hp'] > 0:
                    winner = p
                    break
            if winner:
                self.draw_text(f"Gagnant: {winner['username']} ({winner['color']})", WIDTH//2 - 180, HEIGHT//2 - 20, GREEN, self.bigfont)
            else:
                self.draw_text("Match nul!", WIDTH//2 - 80, HEIGHT//2 - 20, WHITE, self.bigfont)
        quit_rect = pygame.Rect(WIDTH//2 - 80, HEIGHT//2 + 60, 160, 40)
        pygame.draw.rect(self.screen, RED, quit_rect, border_radius=6)
        self.draw_text("Quitter", quit_rect.x+50, quit_rect.y+10)
        return quit_rect

    def connect(self):
        try:
            r = requests.post(f"{self.server_addr}/connect", json={'name': self.player_name}, timeout=5)
            if r.status_code == 200:
                data = r.json()
                self.player_id = data['player_id']
                st = requests.get(f"{self.server_addr}/state", timeout=5).json()
                self.state = st
                for p in st['players']:
                    if p['id'] == self.player_id:
                        self.player_color = p['color']
                self.start_polling()
                # Définir la vue selon l'état du serveur
                current_state = self.state['current_state']
                if current_state == 'waiting':
                    self.view = 'waiting'
                elif current_state == 'in_game':
                    self.view = 'game'
                elif current_state == 'shop':
                    self.view = 'shop'
                elif current_state == 'game_over':
                    self.view = 'game_over'
                self.last_error = ""
            else:
                self.last_error = r.json().get('status', 'erreur_connexion')
        except Exception as e:
            self.last_error = str(e)

    def start_polling(self):
        if self.poll_thread and self.poll_thread.is_alive():
            return
        self.polling = True
        self.poll_thread = threading.Thread(target=self.poll_loop, daemon=True)
        self.poll_thread.start()

    def poll_loop(self):
        while self.polling:
            try:
                st = requests.get(f"{self.server_addr}/state", timeout=5).json()
                self.state = st
                # switch view selon phase
                current_state = st['current_state']
                if current_state == 'waiting' and self.view != 'waiting':
                    self.view = 'waiting'
                elif current_state == 'in_game' and self.view != 'game':
                    self.view = 'game'
                elif current_state == 'shop' and self.view != 'shop':
                    self.view = 'shop'
                    self.fetch_offers(self.shop_rarity)
                elif current_state == 'game_over' and self.view != 'game_over':
                    self.view = 'game_over'
            except Exception:
                pass
            time.sleep(0.25)

    def stop_polling(self):
        self.polling = False

    def piece_label(self, name, color):
        mapping = {
            'pawn':'P', 'rook':'R', 'knight':'N', 'bishop':'B', 'queen':'Q', 'king':'K',
            'dragon':'D', 'sappeur':'S', 'archer':'A', 'fantome':'F'
        }
        ch = mapping.get(name, '?')
        return ch if color=='white' else ch.lower()

    # ============ Ecran Jeu ============
    def draw_board(self):
        for row in range(8):
            for col in range(8):
                rect = pygame.Rect(col*TILE, row*TILE, TILE, TILE)
                color = LIGHT if (row+col) % 2 == 0 else DARK
                pygame.draw.rect(self.screen, color, rect)
                if self.selected:
                    fx, fy = from_alg(self.selected)
                    if fx == col and fy == row:
                        pygame.draw.rect(self.screen, YELLOW, rect, 4)

        if self.state:
            board = self.state['board']
            for row in range(8):
                for col in range(8):
                    cell = board[row][col]
                    if cell:
                        name = cell['name']
                        color = cell['color']
                        cd = cell['cd']
                        cx, cy = col*TILE + TILE//2, row*TILE + TILE//2
                        lbl = self.piece_label(name, color)
                        self.draw_centered_text(lbl, cx, cy, WHITE if color=='white' else BLACK, bold=True)
                        if cd > 0:
                            self.draw_text(f"{cd}", col*TILE + TILE-20, row*TILE + 5, RED)

        pygame.draw.rect(self.screen, BLACK, (0, 8*TILE, WIDTH, 160))
        if self.state:
            cs = self.state['current_state']
            pl = self.state['players']
            you = next((p for p in pl if p['id'] == self.player_id), None)
            opp = next((p for p in pl if p['id'] != self.player_id), None)
            self.draw_text(f"Etat: {cs} | Manche #{self.state.get('round_number',0)}", 10, 8*TILE+10, WHITE)
            if you:
                self.draw_text(f"Toi ({you['color']}): {you['username']} HP:{you['hp']}", 10, 8*TILE+40, GREEN)
            if opp:
                self.draw_text(f"Adversaire ({opp['color']}): {opp['username']} HP:{opp['hp']}", 10, 8*TILE+70, RED)
            if self.last_error:
                self.draw_text(f"Erreur: {self.last_error}", WIDTH//2, 8*TILE+10, RED)

    def draw_centered_text(self, txt, x, y, color=WHITE, bold=False):
        font = self.bigfont if bold else self.font
        surf = font.render(txt, True, color)
        rect = surf.get_rect(center=(x, y))
        self.screen.blit(surf, rect)

    def handle_game_click(self, pos):
        x, y = pos
        if y >= 8*TILE:
            return
        col = x // TILE
        row = y // TILE
        cell_alg = to_alg(col, row)

        if not self.state: return
        board = self.state['board']
        cell = board[row][col]

        if self.selected is None:
            if cell and cell['color'] == self.player_color and cell['cd'] == 0:
                self.selected = cell_alg
                self.last_error = ""
        else:
            frm = self.selected
            piece = None
            fx, fy = from_alg(frm)
            if board[fy][fx]:
                piece = board[fy][fx]['name']
            if piece is None:
                self.selected = None
                return
            payload = {
                'player_id': self.player_id,
                'move': {
                    'from': frm,
                    'to': cell_alg,
                    'piece': piece
                }
            }
            try:
                r = requests.post(f"{self.server_addr}/move", json=payload, timeout=5)
                if r.status_code == 200:
                    self.state = r.json()['state']
                    self.last_error = ""
                else:
                    jr = r.json()
                    self.last_error = jr.get('error', f"HTTP {r.status_code}")
            except Exception as e:
                self.last_error = str(e)
            self.selected = None

    # ============ Ecran Boutique ============
    def fetch_offers(self, rarity):
        try:
            r = requests.get(f"{self.server_addr}/shop", params={'player_id': self.player_id, 'rarity': rarity}, timeout=5)
            if r.status_code == 200:
                jr = r.json()
                self.shop_rarity = rarity
                self.shop_offers = jr.get('offers', [])
                self.last_error = ""
            else:
                self.last_error = r.json().get('error', 'shop_error')
        except Exception as e:
            self.last_error = str(e)

    def buy_offer(self, oid):
        try:
            r = requests.post(f"{self.server_addr}/buy", json={'player_id': self.player_id, 'oid': oid}, timeout=5)
            if r.status_code == 200:
                self.fetch_offers(self.shop_rarity)
                # refresh state (gold/inventory)
                self.state = requests.get(f"{self.server_addr}/state", timeout=5).json()
                self.last_error = ""
            else:
                self.last_error = r.json().get('error', 'buy_error')
        except Exception as e:
            self.last_error = str(e)

    def submit_layout(self):
        try:
            r = requests.post(f"{self.server_addr}/set_board", json={'player_id': self.player_id, 'layout': self.local_layout}, timeout=5)
            if r.status_code == 200:
                self.last_error = ""
            else:
                self.last_error = r.json().get('error', 'layout_error')
        except Exception as e:
            self.last_error = str(e)

    def set_ready(self):
        try:
            r = requests.post(f"{self.server_addr}/ready", json={'player_id': self.player_id, 'ready': True}, timeout=5)
            if r.status_code == 200:
                self.last_error = ""
            else:
                self.last_error = r.json().get('error', 'ready_error')
        except Exception as e:
            self.last_error = str(e)

    def draw_shop(self):
        self.screen.fill(BG)
        self.draw_text("Boutique", 20, 10, YELLOW, self.bigfont)
        you = next((p for p in self.state['players'] if p['id'] == self.player_id), None) if self.state else None
        gold = you['gold'] if you else 0
        deadline = self.state.get('shop_deadline') if self.state else None
        rem = max(0, deadline - int(time.time())) if deadline else 0
        self.draw_text(f"Or: {gold} | Temps restant: {rem}s", 20, 50, WHITE)

        # boutons rareté (silver, gold, platinium)
        rarities = [('silver', GREY, 'Argent'), ('gold', YELLOW, 'Or'), ('platinium', PURPLE, 'Platine')]
        rrects = []
        x = 20
        for r, col, label in rarities:
            rect = pygame.Rect(x, 80, 140, 36)
            pygame.draw.rect(self.screen, col if self.shop_rarity==r else DARK, rect, border_radius=6)
            self.draw_text(label, rect.x+10, rect.y+8, BLACK if self.shop_rarity==r else WHITE)
            rrects.append((r, rect))
            x += 150

        # Offres (2 colonnes sur la gauche)
        ox = 20
        oy = 130
        orects = []
        for i, off in enumerate(self.shop_offers):
            if i >= 4:  # Maximum 4 offres visibles
                break
            if i > 0 and i % 2 == 0:
                ox = 20
                oy += 110
            rect = pygame.Rect(ox, oy, 280, 100)
            pygame.draw.rect(self.screen, DARK, rect, border_radius=8)
            self.draw_text(off['name'][:30], rect.x+10, rect.y+8, WHITE)
            self.draw_text(off['desc'][:35], rect.x+10, rect.y+36, LIGHT)
            self.draw_text(f"Prix: {off['price']}", rect.x+10, rect.y+64, YELLOW)
            buy_btn = pygame.Rect(rect.right-80, rect.y+68, 70, 26)
            pygame.draw.rect(self.screen, BLUE, buy_btn, border_radius=6)
            self.draw_text("Acheter", buy_btn.x+4, buy_btn.y+4)
            orects.append((off['oid'], buy_btn))
            ox += 300

        # Editeur de board simplifié (partie droite)
        board_left = 640
        self.draw_text("Editeur de board:", board_left, 130, WHITE)
        board_top = 160
        for row in range(8):
            for col in range(8):
                rect = pygame.Rect(board_left + col*35, board_top + row*35, 35, 35)
                color = LIGHT if (row+col) % 2 == 0 else DARK
                pygame.draw.rect(self.screen, color, rect)
        
        # palette (inventaire) - partie droite
        inv = you.get('inventory', {}) if you else {}
        base_counts = {'king':1,'queen':1,'rook':2,'bishop':2,'knight':2,'pawn':8}
        total_counts = {k: base_counts.get(k,0)+inv.get(k,0) for k in set(base_counts)|set(inv)}
        px = board_left
        py = board_top + 8*35 + 20
        self.draw_text("Palette:", px, py, WHITE); py += 26
        palette_rects = []
        for name, count in sorted(total_counts.items()):
            if py > HEIGHT - 80:
                break
            rect = pygame.Rect(px, py, 140, 28)
            pygame.draw.rect(self.screen, DARK if self.palette_choice != name else BLUE, rect, border_radius=6)
            self.draw_text(f"{name} x{count}", rect.x+6, rect.y+6)
            palette_rects.append((name, rect))
            py += 34

        # boutons (partie droite)
        ready_rect = pygame.Rect(board_left, HEIGHT - 60, 140, 40)
        save_rect = pygame.Rect(board_left + 160, HEIGHT - 60, 140, 40)
        pygame.draw.rect(self.screen, GREEN, ready_rect, border_radius=6)
        pygame.draw.rect(self.screen, YELLOW, save_rect, border_radius=6)
        self.draw_text("Je suis prêt", ready_rect.x+15, ready_rect.y+10, BLACK)
        self.draw_text("Sauvegarder", save_rect.x+15, save_rect.y+10, BLACK)

        # infos / erreurs
        if self.last_error:
            self.draw_text(f"Erreur: {self.last_error}", 20, HEIGHT - 30, RED)

        return {'rarities': rrects, 'offers': orects, 'palette': palette_rects,
                'ready': ready_rect, 'save': save_rect, 'board_top': board_top, 'board_left': board_left}

    def handle_shop_click(self, pos, ui):
        # cliquer rareté
        for r, rect in ui['rarities']:
            if rect.collidepoint(pos):
                self.fetch_offers(r)
                return
        # cliquer acheter
        for oid, rect in ui['offers']:
            if rect.collidepoint(pos):
                self.buy_offer(oid)
                return
        # cliquer palette
        for name, rect in ui['palette']:
            if rect.collidepoint(pos):
                self.palette_choice = name
                return
        # cliquer board mini (placement/remove)
        x, y = pos
        bt = ui['board_top']
        bl = ui['board_left']
        if y >= bt and y < bt + 8*35 and x >= bl and x < bl + 8*35:
            col = (x - bl) // 35
            row = (y - bt) // 35
            alg = to_alg(col, row)  # rang 1 en haut (même conv.)
            # contrainte rangs autorisés localement
            allowed = {'white': {0,1}, 'black': {6,7}}[self.player_color]
            if row not in allowed:
                self.last_error = "Case non autorisée"
                return
            # toggle: si même case déjà présente -> remove; sinon place si palette choisie
            found_idx = next((i for i, it in enumerate(self.local_layout) if it['pos'] == alg), None)
            if found_idx is not None:
                self.local_layout.pop(found_idx)
            else:
                if not self.palette_choice:
                    self.last_error = "Choisis une pièce dans la palette"
                    return
                self.local_layout.append({'name': self.palette_choice, 'pos': alg})
            return
        # prêt / sauvegarder
        if ui['ready'].collidepoint(pos):
            self.set_ready()
            return
        if ui['save'].collidepoint(pos):
            self.submit_layout()
            return

    def run(self):
        input_focus = None
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.view == 'menu':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        join_rect, rules_rect = self.draw_menu()
                        if join_rect.collidepoint(event.pos):
                            self.connect()
                        elif rules_rect.collidepoint(event.pos):
                            self.view = 'rules'
                        else:
                            if pygame.Rect(20, 110, 500, 32).collidepoint(event.pos):
                                input_focus = 'server'
                            elif pygame.Rect(20, 190, 300, 32).collidepoint(event.pos):
                                input_focus = 'name'
                            else:
                                input_focus = None
                    elif event.type == pygame.KEYDOWN and input_focus:
                        if event.key == pygame.K_BACKSPACE:
                            if input_focus == 'server':
                                self.server_addr = self.server_addr[:-1]
                            else:
                                self.player_name = self.player_name[:-1]
                        elif event.key == pygame.K_RETURN:
                            if input_focus == 'server':
                                input_focus = 'name'
                            else:
                                self.connect()
                        else:
                            ch = event.unicode
                            if ch.isprintable():
                                if input_focus == 'server':
                                    self.server_addr += ch
                                else:
                                    self.player_name += ch
                elif self.view == 'rules':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        back_rect = self.draw_rules()
                        if back_rect.collidepoint(event.pos):
                            self.view = 'menu'
                elif self.view == 'game':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.handle_game_click(event.pos)
                elif self.view == 'shop':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        ui = self.draw_shop()  # pour les rects courants
                        self.handle_shop_click(event.pos, ui)
                elif self.view == 'game_over':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        quit_rect = self.draw_game_over()
                        if quit_rect.collidepoint(event.pos):
                            self.running = False

            # draw
            if self.view == 'menu':
                self.draw_menu()
            elif self.view == 'rules':
                self.draw_rules()
            elif self.view == 'waiting':
                self.draw_waiting()
            elif self.view == 'game':
                self.screen.fill(BG)
                self.draw_board()
            elif self.view == 'shop':
                self.draw_shop()
            elif self.view == 'game_over':
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)

        self.stop_polling()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    Client().run()