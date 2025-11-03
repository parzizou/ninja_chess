from classes import *
from globals import *


# initialisation des upgrades
# silver upgrades

upgrades_silver = [
    Upgrade("Extra HP", "Augmente de 2 tes PV"),
    Upgrade("Gold Boost", "Reçois 3 pièces d'or supplémentaires par manche"),
    Upgrade("Regicide","réduit de 20% le cd de votre pièce qui capture le roi adverse"),
    Upgrade("pions sprinteurs","vos pions peuvent avancer de 3 cases lors de leur premier déplacement"),
    Upgrade("Aspiration d'âme","Lorsque vous gagnez une manche vous récupérez 0.5 point de vie"),
    Upgrade("Recolte d'ame","Lorsque vous capturez une pièce adverse, vous récupérez 0.1 point de vie"),
]

upgrades_gold = [
    Upgrade("Fusion calculée","Si vos deux tours se retrouvent cote a cote, elles fusionnent pour donner un dragon"),
    Upgrade("Echange de pouvoir","Capacité active : échanger la position du roi et de la reine une fois par partie"),
    Upgrade("Marathonien","Vos pions peuvent se déplacer de 2 cases à chaque tour"),
    Upgrade("Assassinat royal","Si votre roi capture une pièce adverse, il peut rejouer immédiatement"),
    Upgrade("Marche arrière","Vos pions peuvent se déplacer en arrière comme les autres pièces"),
    Upgrade("Force Royale","Votre roi peut se déplacer d'une case de plus dans toutes les directions"),
    Upgrade("Psychose passagère","Si deux de vos pions se trouvent l'un au dessus de l'autre (pions passés), ils fuisonnent pour devenir un fou"),
    Upgrade("Collection de Couronnes","Chaque manche gagnée vous rapporte 4 pièces (cumulable), Mais vous perdez l'effet de cet item en cas de défaite")
]


upgrades_platinium = [
    Upgrade("Furie des Pions", "Si un de tes pions capture une pièce adverse, il annule son cd"),
    Upgrade("Sexo-permutation","Votre roi obtient les déplacements de la reine"),
    Upgrade("")
]