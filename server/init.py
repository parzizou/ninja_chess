# Catalogues d'upgrades définis via la classe Upgrade (conservée)
# NB: on n'importe pas Game ici pour éviter l'import circulaire;
# la classe Upgrade vient de server/classes.py au runtime via server_main.

from classes import Upgrade  # garantit que la classe est bien utilisée

# Silver
upgrades_silver = [
    Upgrade("Extra HP", "Augmente de 2 tes PV"),
    Upgrade("Gold Boost", "Reçois 3 pièces d'or supplémentaires par manche"),
    Upgrade("Regicide", "Réduit de 20% le cd de ta pièce qui capture le roi adverse"),
    Upgrade("pions sprinteurs", "Tes pions peuvent avancer de 3 cases lors de leur premier déplacement"),
    Upgrade("Aspiration d'âme", "Quand tu gagnes une manche tu récupères 0.5 point de vie"),
    Upgrade("Recolte d'ame", "Quand tu captures une pièce adverse, tu récupères 0.1 point de vie"),
]

# Gold
upgrades_gold = [
    # TODO: Les upgrades suivants ne sont pas implémentés et sont temporairement retirés:
    # Upgrade("Fusion calculée", "Si tes deux tours se retrouvent côte à côte, elles fusionnent en Dragon"),
    # Upgrade("Echange de pouvoir", "Capacité active: échanger une fois par partie le roi et la reine"),
    # Upgrade("Psychose passagère", "Deux pions superposés fusionnent en Fou"),
    Upgrade("Marathonien", "Tes pions peuvent se déplacer de 2 cases à chaque coup"),
    Upgrade("Assassinat royal", "Si ton roi capture, il peut rejouer immédiatement (cd annulé)"),
    Upgrade("Marche arrière", "Tes pions peuvent se déplacer en arrière"),
    Upgrade("Force Royale", "Ton roi peut se déplacer d'une case de plus dans toutes les directions"),
    Upgrade("Collection de Couronnes", "Chaque manche gagnée +4 or (cumulable), perdu en cas de défaite"),
]

# Platinium (orthographe d’origine conservée)
upgrades_platinium = [
    Upgrade("Furie des Pions", "Si un de tes pions capture, il annule son cd"),
    Upgrade("Sexo-permutation", "Ton roi obtient les déplacements de la reine"),
    # Tu peux en ajouter d'autres ici
]