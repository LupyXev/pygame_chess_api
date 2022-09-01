import pygame
from api import Board, Piece, Bishop
from render import Gui

def random_function_for_ai(board:Board):
    from random import choice
    print("AI turn")
    allowed_moves = None
    while not allowed_moves:
        random_piece = choice(board.pieces_by_color[board.cur_color_turn])
        allowed_moves = random_piece.get_moves_allowed()
    
    random_move = choice(random_piece.get_moves_allowed())
    
    if random_move.special_type == random_move.TO_PROMOTE_TYPE: #if we have to specify a promotion we promote it to a Bishop
        random_piece.promote_class_wanted = Bishop
    
    random_piece.move(random_move)

if __name__ == "__main__":
    pygame.init()
    
    board = Board()
    gui = Gui(board, (Piece.WHITE,))
    gui.run_pygame_loop(random_function_for_ai)