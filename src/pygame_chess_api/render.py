import os
import sys
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
sys.path.append(os.path.dirname(__location__))

from pygame_chess_api.api import *
import pygame
from pygame import image
from time import time

class Gui:
    '''Class for the pygame's gui, it will enable you to display the game and human players to move pieces'''
    PIECE_TYPE_NAME_TO_OBJ = {"check": Check, "queen": Queen, "rook": Rook, "bishop": Bishop, "knight": Knight, "pawn": Pawn}
    ASSETS_FOLDER = os.path.join(__location__, 'assets')

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
        '''
        | Tuple containing the colors managed by human moves with the gui.
        | The color(s) not in this tuple/list must be managed by AI with the parameter function `function_for_AIs` in method :meth:`run_pygame_loop`'''
        self.verbose = verbose #0, 1, or 2

        self.generate_textures()
    
    def run_pygame_loop(self, function_for_AIs=None):
        '''
        Run the Pygame gui loop to show and interact with the pygame window.
        The function_for_AIs must have one input: the board object
        We'll call it when this is turn for a color that should not be managed by gui (an AI)

        Obviously the move method called by your AI must be part of the given Board (Board.move_piece or a Piece.move)
        '''
        self.screen = pygame.display.set_mode(self.SCREEN_SIZE)
        pygame.display.set_caption(self.window_title)
        self.clock = pygame.time.Clock()

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
            
            self.clock.tick(self.FPS)
    
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
        #moves textures
        Move.TEXTURES = {
            Move.TO_EMPTY_MOVE: image.load(os.path.join(self.ASSETS_FOLDER, "square_of_highlight.png")),
            Move.KILL_MOVE: image.load(os.path.join(self.ASSETS_FOLDER, "square_of_kill.png")),
            Move.SPECIAL_MOVE: image.load(os.path.join(self.ASSETS_FOLDER, "square_of_special.png"))
        }
        #check
        Check.IN_CHECK_TEXTURE = image.load(os.path.join(self.ASSETS_FOLDER, "square_of_in_check.png"))

        #cases textures
        Case.BLACK_TEXTURE = image.load(os.path.join(self.ASSETS_FOLDER, "black_square.png"))
        Case.WHITE_TEXTURE = image.load(os.path.join(self.ASSETS_FOLDER, "white_square.png"))

        #pieces textures
        pieces_dir_path = self.ASSETS_FOLDER
        for cur_class_name, cur_class in self.PIECE_TYPE_NAME_TO_OBJ.items():
            for color in (Piece.WHITE, Piece.BLACK):
                f_name = Piece.INT_COLOR_TO_TEXT[color].lower() + "_" + cur_class_name + ".png"
                texture = image.load(os.path.join(pieces_dir_path, f_name))
                texture = pygame.transform.smoothscale(texture, self.SQUARE_SIZE)
                if self.verbose >= 2: print("adding", f_name, "texture")
                if color == Piece.WHITE:
                    cur_class.WHITE_TEXTURE = texture
                else:
                    cur_class.BLACK_TEXTURE = texture
        self.need_screen_update = True
        if self.verbose >= 1: print("loaded gui textures")
    
    def choose_a_pawn_promote(self, color:int):
        print("Please choose the Piece to promote the Pawn")
        #drawing promote pieces
        classes_name = ("queen", "rook", "bishop", "knight")
        classes = (Queen, Rook, Bishop, Knight)
        textures = []
        for c in classes_name:
            if color == Piece.WHITE:
                cur_texture = image.load(os.path.join(self.ASSETS_FOLDER, f"pieces/white_{c}.png"))
            else:
                cur_texture = image.load(os.path.join(self.ASSETS_FOLDER, f"pieces/white_{c}.png"))
            cur_texture = pygame.transform.smoothscale(cur_texture, tuple([s*2 for s in self.SQUARE_SIZE]))
            textures.append(cur_texture)

        for i in range(len(textures)):
            self.screen.blit(textures[i], (0 + i*2*self.SQUARE_SIZE[0], self.SQUARE_SIZE[1]*3))
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_presses = pygame.mouse.get_pressed()
                    if mouse_presses[0] == True: #left click
                        mouse_pos = self.get_mouse_pos()
                        if 3 <= mouse_pos[1] <= 4:
                            return classes[mouse_pos[0]//2]
                
            pygame.display.update()
            self.clock.tick(self.FPS)

    def mouse_left_clicked(self):
        if self.board.game_ended:
            print("Game ended, you can close the window")
            return

        mouse_pos = self.get_mouse_pos()
        piece_to_hold = self.board.get_piece_by_pos(mouse_pos)
        if not piece_to_hold or piece_to_hold.color != self.board.cur_color_turn or piece_to_hold.color not in self.colors_managed:
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
            if isinstance(self.mouse_piece_holding, Pawn) and ((self.mouse_piece_holding.color == Piece.WHITE and mouse_pos[1] == 0) or (self.mouse_piece_holding.color == Piece.BLACK and mouse_pos[1] == 7)):
                allowed = self.board.is_allowed_move(self.mouse_piece_holding, mouse_pos)
                if allowed:
                    wanted_class = self.choose_a_pawn_promote(self.mouse_piece_holding.color)
                    self.mouse_piece_holding.promote_class_wanted = wanted_class

            self.board.move_piece(self.mouse_piece_holding, mouse_pos) #will perform movement only if allowed
            self.mouse_piece_holding = None

            self.need_screen_update = True