# dans ce script console on vois apparaitre l'ip et le port réseau ouvert du serveur, puis l'attente de la connexion des deux joueurs
# on expose en permanace l'etat du jeu

from globals import *
from classes import *
from flask import Flask, request, jsonify

app = Flask(__name__)
game = Game()


@app.route('/state', methods=['GET'])
def get_game_state():
    return jsonify(game.game_state())

#route pour que les joueurs puissent se connecter
@app.route('/connect', methods=['POST'])
def connect_player():
    # obtenir le nom du joueur depuis la requete
    player_name = request.json.get('name')
    player_id = game.add_player(player_name)
    if player_id is not None:
        return jsonify({'status': 'connected', 'player_id': player_id})
    else:
        return jsonify({'status': 'full'}), 403
    

@app.route('/move', methods=['POST'])
def make_move():
    # obtenir le id du joueur et le mouvement depuis la requete
    player_id = request.json.get('player_id')
    move = request.json.get('move')
    game.make_move(player_id, move)


if __name__ == '__main__':
    app.run(host='http://localhost', port=5000)
    print("Server is running on http://localhost:5000")
    print("Waiting for players to connect...")
    
    while len(game.players) < 2:
        pass  # attendre que les joueurs se connectent
    
    print("Both players connected. Starting the game...")
    
    game.start_game()
    
    # boucle principale du jeu
    # ici on a simplement un serveur web qui attend les requetes des joueurs
    # les joueurs envoient leurs mouvements via des requetes POST
    # le serveur traite les mouvements et met a jour l'etat du jeu
    # le serveur envoie l'etat du jeu aux joueurs via des requetes GET
    while not game.is_over():
        pass  # le serveur attend les mouvements des joueurs
    print("Game over!")
    print(f"Winner: {game.get_winner().name}")
    