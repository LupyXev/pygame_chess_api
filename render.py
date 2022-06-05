from api import *
from os import listdir
import pygame

class Gui:
    PIECE_TYPE_NAME_TO_OBJ = {"check": Check, "queen": Queen, "rook": Rook, "bishop": Bishop, "knight": Knight, "pawn": Pawn}

    def __init__(self, screen: pygame.Surface, SQUARE_SIZE, board:Board, clock:pygame.time.Clock):
        self.screen = screen
        self.SQUARE_SIZE = SQUARE_SIZE
        self.board = board
        self.mouse_piece_holding = None #Piece
        self.need_screen_update = True #draw_board() will be performed only if it's True
        self.clock = clock
        self.highlighted_moves = []
        self.kill_cases = []
    
    def get_mouse_pos(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pos = tuple([mouse_pos[i]//self.SQUARE_SIZE[i] for i in range(2)])
        return mouse_pos

    def draw_board(self):
        if not self.need_screen_update:
            return
        #drawing cases
        for x in range(0, self.SQUARE_SIZE[0]*8, self.SQUARE_SIZE[0]):
            for y in range(0, self.SQUARE_SIZE[1]*8, self.SQUARE_SIZE[1]):
                texture = None
                if x / self.SQUARE_SIZE[0] % 2 == 0:
                    if y / self.SQUARE_SIZE[1] % 2 == 0:
                        texture = Case.WHITE_TEXTURE
                    else:
                        texture = Case.BLACK_TEXTURE
                else:
                    if y / self.SQUARE_SIZE[1] % 2 == 1:
                        texture = Case.WHITE_TEXTURE
                    else:
                        texture = Case.BLACK_TEXTURE
                self.screen.blit(texture, (x, y))
        #drawing pieces
        for piece in self.board.pieces_pos.values():
            if piece is not self.mouse_piece_holding:
                #if it's holded we won't draw it on its static coords
                self.screen.blit(piece.texture, tuple([piece.pos[i]*self.SQUARE_SIZE[i] for i in range(len(piece.pos))]))
        
        #drawing highlighted cases
        for move in self.highlighted_moves:
            self.screen.blit(move.texture, tuple([move.target[i]*self.SQUARE_SIZE[i] for i in range(2)]))
        
        #drawing holded piece
        if self.mouse_piece_holding:
            mouse_pos = pygame.mouse.get_pos()
            self.screen.blit(self.mouse_piece_holding.texture, tuple([mouse_pos[i] - self.SQUARE_SIZE[i]/2 for i in range(2)]))
        else:
            self.need_screen_update = False #if we are holding something we will update next tick
        pygame.display.update()

    def generate_textures(self):
        pieces_dir_path = "./assets/pieces/"
        files = listdir(pieces_dir_path)
        for f_name in files:
            color = f_name[:5]
            type_name = f_name[6:-4] #-4 bc .png has a len of 4
            type = self.PIECE_TYPE_NAME_TO_OBJ[type_name]
            texture = image.load(pieces_dir_path + f_name)
            texture = pygame.transform.smoothscale(texture, self.SQUARE_SIZE)
            print("adding", f_name, "texture")
            if color == "white":
                type.WHITE_TEXTURE = texture
            elif color == "black":
                type.BLACK_TEXTURE = texture
            else:
                print("Warning bad file name piece color", f_name)
        self.need_screen_update = True

    def mouse_left_clicked(self):
        mouse_pos = self.get_mouse_pos()
        self.mouse_piece_holding = self.board.get_piece_by_pos(mouse_pos)
        print("holding piece", self.mouse_piece_holding)
        self.need_screen_update = True
        if self.mouse_piece_holding:
            for move in self.mouse_piece_holding.get_moves_allowed(self.board):
                self.highlighted_moves.append(move)

    def mouse_released(self):
        self.highlighted_moves = []
        self.kill_cases = []
        if self.mouse_piece_holding:
            mouse_pos = self.get_mouse_pos()
            self.board.move_piece(self.mouse_piece_holding, mouse_pos) #will perform movement only if allowed
            self.mouse_piece_holding = None

            self.need_screen_update = True