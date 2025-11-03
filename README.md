# Ninja Chess

Duel d'échecs en temps réel:
- Pas de tours: tu joues dès que la pièce n’est pas en cooldown.
- Capture du Roi = fin de manche.
- Le perdant perd 1 HP (sur 5). Boutique entre les manches.
- Des pièces spéciales existent (`dragon`, `sappeur`, `archer`, `fantome`).

## Structure

- `server/`: serveur Flask qui maintient l’état de la partie et gère les mouvements + phases de boutique.
- `client/`: client Pygame pour se connecter, afficher le board, jouer et gérer la boutique.

## Lancer le serveur

```bash
cd server
python server_main.py
```

Le serveur affiche l’adresse, ex. `http://192.168.X.Y:5000`.

Endpoints principaux:
- `POST /connect` body: `{ "name": "Pseudo" }` -> `{ "player_id": 0|1 }`
- `GET /state` -> état JSON
- `POST /move` body: `{ "player_id": n, "move": { "from": "e2", "to": "e4", "piece": "pawn" } }`

Boutique:
- `GET /shop?player_id=0&rarity=silver` -> offres semi-aléatoires de la rareté (prix selon rareté: silver=4, gold=8, platinium=14)
- `POST /buy` body: `{ "player_id": n, "oid": "silver-reduce_cd_all_1-XXXX" }`
- `POST /set_board` body: `{ "player_id": n, "layout": [ {"pos":"a2","name":"pawn"}, ... ] }`
- `POST /ready` body: `{ "player_id": n, "ready": true }`

## Phases

- `in_game`: partie temps réel (cd décrémentés au tick). Capture du roi -> fin de manche.
- `shop`: timer (45s par défaut) + bouton “prêt”. Quand 2/2 prêts ou timer écoulé -> manche suivante.
- Fin de partie: dès qu’un joueur atteint 0 HP.

## Boutique (MVP)

- Choix par rareté: Silver (Argent), Gold (Or), Platinium (Platine) (3 offres).
- Types d’offres:
  - Upgrades (ex: réduction globale des CD, portée Archer +1/+2).
  - Nouvelles pièces (ajoutées à ton inventaire).
- Éditeur de board de départ entre les manches:
  - Contraintes enforce côté serveur: 2 premières rangées de ton camp (white: rangs 1-2; black: 8-7), max 16 pièces, exactement 1 roi, tu ne peux poser que ce que tu possèdes (set de base + inventaire).
  - Enregistre via `POST /set_board`.

## Client

- Menu: IP:port + pseudo + règles.
- Jeu: affichage de l’échiquier, sélection d’une de tes pièces (cd=0), clic sur case d’arrivée, envoi `/move`.
- Boutique:
  - Boutons de rareté -> récupère 3 offres -> achat `/buy`.
  - Mini éditeur de board simple (palette + clic cases autorisées) -> `/set_board`.
  - Bouton “Je suis prêt”.

## Roadmap next

- UI: vrai drag & drop sur le board, surbrillance des cases autorisées, sprites.
- Gameplay: plus d’upgrades (spécifiques par pièce), équilibrage coûts/gains, effets en profondeur (ex: réactions du sappeur).
- Réseau: multi-salles, reconnexion, tokens d’auth (au lieu de player_id nu).
- Robustesse: verrouillage thread-safe, tests unitaires des mouvements.