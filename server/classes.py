from globals import *



class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]


    
    
class Piece:
    def __init__(self, name, color, cd_base):
        if name in lst_allowed_pieces:
            self.name = name
            self.color = color
            self.cd_base = cd_base
            self.cd = cd_base
        else:
            raise ValueError(f"Invalid piece name: {name}\nAllowed pieces are: {lst_allowed_pieces}")
        
        
    def reset_cooldown(self):
        self.cd = self.cd_base
        
    def cancel_cooldown(self):
        self.cd = 0
        
    
        
        
        
class Player:
    def __init__(self, username, color):
        self.username = username
        self.color = color
        self.pieces = []
        
    