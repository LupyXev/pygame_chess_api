from api import *
from os import listdir
import pygame
from time import time
#from warnings import warn

class Gui:
    PIECE_TYPE_NAME_TO_OBJ = {"check": Check, "queen": Queen, "rook": Rook, "bishop": Bishop, "knight": Knight, "pawn": Pawn}

    def __init__(self, board:Board, colors_managed_by_gui=(Piece.WHITE, Piece.BLACK), window_title="Chess Game", SCREEN_SIZE=(800, 800), FPS=60, verbose=1):
        self.FPS = FPS
        self.SCREEN_SIZE = SCREEN_SIZE
        self.SQUARE_SIZE = tuple([SCREEN_SIZE[i] // 8 for i in range(2)])
        self.window_title = window_title

        self.board = board
        self.mouse_piece_holding = None #Piece
        self.need_screen_update = True #draw_board() will be performed only if it's True
        self.highlighted_moves = []
        self.kill_cases = []
        if type(colors_managed_by_gui) not in (tuple, list):
            raise ValueError("colors_managed_by_gui is not a tuple or a list")
        self.colors_managed = colors_managed_by_gui
        self.verbose = verbose #0, 1, or 2

        self.generate_textures()
    
    def run_pygame_loop(self, function_for_AIs=None):
        '''
        Running the Pygame gui loop to show and interact with the pygame window.
        The function_for_AIs must have one input: the board object
        We'll call it when this is turn for a color that should not be managed by gui

        Obviously the move method called by your AI must be part of the given Board (Board.move_piece or a Piece.move)
        '''
        self.screen = pygame.display.set_mode(self.SCREEN_SIZE)
        pygame.display.set_caption(self.window_title)
        clock = pygame.time.Clock()

        stop_loop = False
        while not stop_loop:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    stop_loop = True
                    break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_presses = pygame.mouse.get_pressed()
                    if mouse_presses[0] == True: #left click
                        self.mouse_left_clicked()
                if event.type == pygame.MOUSEBUTTONUP:
                    self.mouse_released()

            self.draw_board()
            if self.board.cur_color_turn not in self.colors_managed and not self.board.game_ended:
                cur_turn = self.board.cur_color_turn
                if function_for_AIs is None:
                    raise ValueError("You must specify a function_for_AIs when calling Gui.run_pygame_loop because you configured that the Gui object shouln't manage every color")
                external_AI_output = function_for_AIs(self.board)
                if self.board.cur_color_turn == cur_turn:
                    raise BaseException("function_for_AIs didn't changed the turn's color/ended turn, please verify that you're moving a piece with your AI")
                self.need_screen_update = True
            
            clock.tick(self.FPS)
    
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
        for piece in self.board.pieces_by_pos.values():
            if piece is not self.mouse_piece_holding:
                #if it's holded we won't draw it on its static coords
                self.screen.blit(piece.texture, tuple([piece.pos[i]*self.SQUARE_SIZE[i] for i in range(len(piece.pos))]))
        
        #drawing highlighted cases
        for move in self.highlighted_moves:
            self.screen.blit(move.texture, tuple([move.target[i]*self.SQUARE_SIZE[i] for i in range(2)]))
        if self.board.cur_color_turn_in_check:
            check_piece = self.board.check_pieces[self.board.cur_color_turn]
            self.screen.blit(check_piece.IN_CHECK_TEXTURE, tuple([check_piece.pos[i]*self.SQUARE_SIZE[i] for i in range(2)]))

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
            if self.verbose >= 2: print("adding", f_name, "texture")
            if color == "white":
                type.WHITE_TEXTURE = texture
            elif color == "black":
                type.BLACK_TEXTURE = texture
            else:
                print("Warning bad file name piece color", f_name)
        self.need_screen_update = True
        if self.verbose >= 1: print("loaded gui textures")

    def mouse_left_clicked(self):
        if self.board.game_ended:
            print("Game ended, you can close the window")
            return

        mouse_pos = self.get_mouse_pos()
        piece_to_hold = self.board.get_piece_by_pos(mouse_pos)
        if piece_to_hold.color != self.board.cur_color_turn or piece_to_hold.color not in self.colors_managed:
            return

        self.mouse_piece_holding = piece_to_hold
        self.need_screen_update = True
        if self.mouse_piece_holding:
            t_start = time()
            moves_allowed = self.mouse_piece_holding.get_moves_allowed()
            if self.verbose >= 1: print("loaded moves allowed in", round((time() - t_start)*1000, 2), "ms")
            for move in moves_allowed:
                self.highlighted_moves.append(move)

    def mouse_released(self):
        self.highlighted_moves = []
        self.kill_cases = []
        if self.mouse_piece_holding:
            mouse_pos = self.get_mouse_pos()
            self.board.move_piece(self.mouse_piece_holding, mouse_pos) #will perform movement only if allowed
            self.mouse_piece_holding = None

            self.need_screen_update = True