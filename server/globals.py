# Pièces autorisées
lst_allowed_pieces = [
    'pawn', 'rook', 'knight', 'bishop', 'queen', 'king',
    'dragon', 'sappeur', 'archer', 'fantome'
]

# Temps réel
TICK_INTERVAL_SECONDS = 0.5

# Jeu
PLAYER_MAX_HP = 5
MAX_PLAYERS = 2

# Boutique
SHOP_DURATION_SECONDS = 45
# Raretés/prix en phase boutique (alignées sur ton init.py: silver, gold, platinium)
RARITIES = {
    'silver': {'price': 4},
    'gold': {'price': 8},
    'platinium': {'price': 14},
}

# Gains simples par manche
BASE_COINS_WINNER = 8
BASE_COINS_LOSER = 5
COINS_PER_CAPTURE = 2