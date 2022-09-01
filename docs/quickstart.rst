================
Quickstart
================

A quick example for a 2-player game (no AI)
====================================================
.. code-block:: python

    import pygame
    from api import Board
    from render import Gui

    pygame.init()

    board = Board()
    gui = Gui(board)

    gui.run_pygame_loop()

A quick example for a 1-player game (with one AI)
====================================================
.. code-block:: python

    def function_for_ai(board:Board):
        #finding the best move to do... Here we will execute a random move for a random piece as an example
        from random import choice
        allowed_moves = None
        while not allowed_moves: #loop until we find some allowed move
            random_piece = choice(board.pieces_by_color[board.cur_color_turn]) #getting a random piece
            allowed_moves = random_piece.get_moves_allowed() #fetching allowed moves for this piece
        
        random_move = choice(random_piece.get_moves_allowed()) #getting one random move from the allowed moves
        random_piece.move(random_move) #executing this move

    
    import pygame
    from api import Board
    from render import Gui

    pygame.init()

    board = Board()
    gui = Gui(board, (Piece.WHITE,))
    '''The White color will be the human one and the Black color will be managed by the AI (by function_for_ai)'''

    gui.run_pygame_loop(function_for_ai)
    '''function_for_ai handles AI turns'''

This is similar for a 0-player game (AI vs AI), the only thing changing is that you must set the Gui parameter `colors_managed_by_gui` to a empty tuple/list (meaning that there is not human player)