from time import time
from math import sqrt
from warnings import warn

'''
French pieces' name to english:
- Roi: Check
- Dame: Queen
- Tour: Rook
- Fou: Bishop
- Cavalier: Knight
- Pion: Pawn
'''


class Move:
    '''Moves will be initiated when getting piece's allowed moves, they can also be used as argument to move a piece
    There is different types of moves'''
    FORBIDDEN_MOVE = 0
    ''''''
    TO_EMPTY_MOVE = 1 
    '''A move to a empty case'''
    KILL_MOVE = 2
    '''A move that will kill an opponent's piece'''
    SPECIAL_MOVE = 3 #like for castling move
    '''Ex: for a castling move or a Pawn promoting move (in this case you should specify the wanted class as Pawn attribute, please refer to :class:`Pawn`)'''
    OVER_CHECK_MOVE = 4 
    '''Used to detect check situations (move where you'll kill a Check piece)'''
    LEADING_TO_CHECK_SITUATION_MOVE = 5
    '''Used to detect check situations (move that will conduct to a Check of its own color, so it's forbidden)'''
    TEXTURES = {} #will be written by render.py
    CASTLING_TYPE = 1
    '''For SPECIAL_MOVE'''
    EN_PASSANT_TYPE = 2
    '''For SPECIAL_MOVE'''
    TO_PROMOTE_TYPE = 3
    '''special_type if it's a Pawn promotion move. Be careful, the Move type won't be SPECIAL_MOVE for promotions. To specify promotion, refer to :class:`Pawn`'''
    def __init__(self, type: int, piece, target:tuple, special_type=None):
        self.type = type
        '''Move's type (int)'''
        self.piece = piece
        '''Move's piece'''
        self.target = target #will be (-1, -1) if type is FORBIDDEN_MOVE
        '''Move's position target (tuple)'''
        self.special_type = special_type
        '''Special type if type==SPECIAL_MOVE or if it's a Pawn promotion move (value would be TO_PROMOTE_TYPE)'''
    
    def copy(self, new_piece):
        return self.__class__(self.type, new_piece, self.target, self.special_type)

    @property
    def allowed(self):
        return self.type not in (self.FORBIDDEN_MOVE, self.LEADING_TO_CHECK_SITUATION_MOVE)
    
    @property
    def texture(self):
        return self.TEXTURES[self.type]
    
    def __str__(self):
        return f"Move of piece {self.piece} to {self.target} type : {self.type}, special_type: {self.special_type}"


class Piece:
    '''Base class for pieces'''
    WHITE_TEXTURE, BLACK_TEXTURE = None, None #will be used only in childs
    WHITE, BLACK = 0, 1
    INT_COLOR_TO_TEXT = {0: "White", 1: "Black"}
    DIAGONALS_VECTORS = ((-1, -1), (1, -1), (-1, 1), (1, 1))
    LINES_VECTORS = ((0, -1), (0, 1), (-1, 0), (1, 0))
    KNIGHT_VECTOR = ((1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2))
    COLLISION_MOVES = (Move.KILL_MOVE, Move.OVER_CHECK_MOVE, Move.FORBIDDEN_MOVE)
    def __init__(self, color: int, pos: tuple, board):
        self.color = color
        ''''''
        self.pos = pos
        ''''''
        self.board = board
        ''''''
        self.invicible = False #True value will be considered as Check piece
        self.has_already_moved = False
    
    def get_moves_allowed(self, skip_check_verification=False) -> list:
        '''**To get every piece's moves allowed** with the current Board configuration (moves allowed this current turn)'''
        return [] #will be overrided in children
    
    def case_allowed(self, case_pos:tuple, this_move_can_kill=True, skip_check_verification=False) -> Move: #returns move
        '''To test if this specific case is currently allowed for the piece'''
        for c in case_pos:
            if c < 0 or c > 7:
                return Move(Move.FORBIDDEN_MOVE, self, (-1, -1))
        
        def verify_check(skip_check_verification):
            if skip_check_verification: #for hypothesis, to avoid recursive errors
                return None
            #we check for each movement if it will make the piece's color's Check in check
            #print("checking for", self, "target:", case_pos, self.board.cur_color_turn)
            hypo_board = self.board.create_hypothesis_board(pieces_with_pos_to_change={self: case_pos})
            if self.board.check_pieces[self.board.cur_color_turn].in_check_situation(hypothesis=hypo_board):
                return Move(Move.LEADING_TO_CHECK_SITUATION_MOVE, self, (-1, -1)) #not allowed because would be in check situation
            return None
        
        to_promotion_pawn = (isinstance(self, Pawn) and ((self.color == self.WHITE and case_pos[1] == 0) or (self.color == self.BLACK and case_pos[1] == 7)))
        special_type = Move.TO_PROMOTE_TYPE if to_promotion_pawn else None

        if case_pos in self.board.pieces_by_pos:
            cur_piece = self.board.pieces_by_pos[case_pos]
            if cur_piece.color != self.color and this_move_can_kill:
                if cur_piece.invicible == False: #invicible means that this is a Check piece
                    verification = verify_check(skip_check_verification)
                    if verification: return verification
                    return Move(Move.KILL_MOVE, self, case_pos,  special_type=special_type) #there is collision
                else:
                    verification = verify_check(skip_check_verification)
                    if verification: return verification
                    return Move(Move.OVER_CHECK_MOVE, self, case_pos) #over a Check piece (used only in hypothesis)
            else:
                return Move(Move.FORBIDDEN_MOVE, self, (-1, -1)) #not allowed and collision
        else:
            verification = verify_check(skip_check_verification)
            if verification: return verification
            return Move(Move.TO_EMPTY_MOVE, self, case_pos, special_type=special_type) #no collision

    def cases_allowed_around(self, skip_check_verification=False):
        cases_around_list = []
        for x in range(max(0, self.pos[0]-1), min(8, self.pos[0]+2)):
            for y in range(max(0, self.pos[1]-1), min(8, self.pos[1]+2)):
                cur_move = self.case_allowed((x, y), skip_check_verification=skip_check_verification)
                if cur_move.allowed:
                    cases_around_list.append(cur_move)    
        return cases_around_list
    
    def cases_allowed_in_diagonals(self, skip_check_verification=False):
        cases_allowed_list = []
        for vector in self.DIAGONALS_VECTORS: #4 directions of diagonals
            cur_pos = tuple([self.pos[i] + vector[i] for i in range(2)])
            cur_move = self.case_allowed(cur_pos, skip_check_verification=skip_check_verification)
            while cur_move.type not in self.COLLISION_MOVES: #no collision
                if cur_move.allowed: cases_allowed_list.append(cur_move)
                cur_pos = tuple([cur_pos[i] + vector[i] for i in range(2)])
                cur_move = self.case_allowed(cur_pos, skip_check_verification=skip_check_verification)
            if cur_move.allowed: #to detect in check situations and killing
                cases_allowed_list.append(cur_move)
        return cases_allowed_list
    
    def cases_allowed_in_line(self, skip_check_verification=False): #like for rooks
        cases_allowed_list = []
        for vector in self.LINES_VECTORS: #4 directions of lines
            cur_pos = tuple([self.pos[i] + vector[i] for i in range(2)])
            cur_move = self.case_allowed(cur_pos, skip_check_verification=skip_check_verification)
            while cur_move.type not in self.COLLISION_MOVES: #no collision
                if cur_move.allowed: cases_allowed_list.append(cur_move)
                cur_pos = tuple([cur_pos[i] + vector[i] for i in range(2)])
                cur_move = self.case_allowed(cur_pos, skip_check_verification=skip_check_verification)
            if cur_move.allowed: #to detect in check situations and killing
                cases_allowed_list.append(cur_move)
        return cases_allowed_list
    
    def cases_allowed_for_knight(self, skip_check_verification=False):
        allowed_moves = []
        for vector in self.KNIGHT_VECTOR:
            cur_pos = tuple([self.pos[i] + vector[i] for i in range(2)])
            cur_move = self.case_allowed(cur_pos, skip_check_verification=skip_check_verification)
            if cur_move.allowed:
                allowed_moves.append(cur_move)
        return allowed_moves
    
    def move(self, pos_or_move:tuple or Move, skip_allowed_verif=False, call_new_turn=True) -> None or tuple:
        '''To move the piece to a position returns the target position if it worked, otherwise it returns None'''
        return self.board.move_piece(self, pos_or_move, skip_allowed_verif=skip_allowed_verif, call_new_turn=call_new_turn)

    @property
    def texture(self):
        return self.WHITE_TEXTURE if self.color == 0 else self.BLACK_TEXTURE
    
    def copy(self, new_board):
        return self.__class__(self.color, self.pos, new_board)
    
    def __str__(self):
        return f"{self.INT_COLOR_TO_TEXT[self.color]} {self.NAME} at pos {self.pos}"

class Rook(Piece):
    '''Class for Rooks, please refer to :class:`Piece`'''
    NAME = "Rook"
    def __init__(self, color, pos: tuple, board):
        super().__init__(color, pos, board)
    
    def get_moves_allowed(self, skip_check_verification=False): #returns every move allowed
        return self.cases_allowed_in_line(skip_check_verification)

class Check(Piece):
    '''Class for Checks, please refer to :class:`Piece`'''
    NAME = "Check"
    IN_CHECK_TEXTURE = None
    def __init__(self, color, pos: tuple, board):
        super().__init__(color, pos, board)
        self.invicible = True
        self.currently_in_check = False
    
    def in_check_situation(self, hypothesis=None) -> bool:
        '''Detects if this Check is "in check"'''
        if hypothesis:
            #we create hypothesis to know if some piece could "kill" this Check piece, meaning that we would be in a check situation
            board = hypothesis
            self_in_hypothesis = board.check_pieces[self.color]
        else:
            board = self.board
            self_in_hypothesis = self
        
        if self.board.hypothesis_board:print("in_check_situation with self hypothesis board")
        
        for piece in board.pieces_by_pos.values():
            if piece.color != self.color:
                if piece.invicible: #to avoid recursive erros
                    if sqrt((self_in_hypothesis.pos[0] - piece.pos[0])**2 + (self_in_hypothesis.pos[1] - piece.pos[1])**2) < 2:
                        #both Checks are too close, this should be impossible (obviously it will only happen in hypothesis)
                        return True
                else:
                    for move in piece.get_moves_allowed(skip_check_verification=True):
                        if move.type == Move.OVER_CHECK_MOVE:
                            return True

        return False

    def get_moves_allowed(self, skip_check_verification=False): #returns every move allowed
        moves_around = self.cases_allowed_around(skip_check_verification)

        if not self.has_already_moved:
            #little castling
            little_castling_free_pos_needed = [(self.pos[0]+i, self.pos[1]) for i in range(1, 3)]
            pos_little_castling_are_free = True
            for cur_pos in little_castling_free_pos_needed:
                if cur_pos in self.board.pieces_by_pos or (not skip_check_verification and self.in_check_situation(self.board.create_hypothesis_board({self:cur_pos}))):
                    pos_little_castling_are_free = False
            
            piece_at_rook_needed_pos = self.board.pieces_by_pos[(self.pos[0]+3, self.pos[1])] if (self.pos[0]+3, self.pos[1]) in self.board.pieces_by_pos else None
            if pos_little_castling_are_free and type(piece_at_rook_needed_pos) == Rook and not piece_at_rook_needed_pos.has_already_moved:
                if skip_check_verification or not self.in_check_situation(self.board.create_hypothesis_board({self:(self.pos[0]+2, self.pos[1])})):
                    moves_around.append(Move(Move.SPECIAL_MOVE, self, (self.pos[0]+2, self.pos[1]), Move.CASTLING_TYPE))
            
            #big castling
            big_castling_free_pos_needed = [(self.pos[0]-i, self.pos[1]) for i in range(1, 4)]
            pos_big_castling_are_free = True
            for cur_pos in big_castling_free_pos_needed:
                if cur_pos in self.board.pieces_by_pos or (not skip_check_verification and self.in_check_situation(self.board.create_hypothesis_board({self:cur_pos}))):
                    pos_big_castling_are_free = False
            
            piece_at_rook_needed_pos = self.board.pieces_by_pos[(self.pos[0]-4, self.pos[1])] if (self.pos[0]-4, self.pos[1]) in self.board.pieces_by_pos else None
            if pos_big_castling_are_free and type(piece_at_rook_needed_pos) == Rook and not piece_at_rook_needed_pos.has_already_moved:
                if skip_check_verification or not self.in_check_situation(self.board.create_hypothesis_board({self:(self.pos[0]-2, self.pos[1])})):
                    moves_around.append(Move(Move.SPECIAL_MOVE, self, (self.pos[0]-2, self.pos[1]), Move.CASTLING_TYPE))
        #TODO: must be filtered with check situations
        return moves_around   

class Queen(Piece):
    '''Class for Queens, please refer to :class:`Piece`'''
    NAME = "Queen"
    def __init__(self, color, pos: tuple, board):
        super().__init__(color, pos, board)
    
    def get_moves_allowed(self, skip_check_verification=False): #returns every move allowed
        return self.cases_allowed_around(skip_check_verification) + self.cases_allowed_in_diagonals(skip_check_verification) + self.cases_allowed_in_line(skip_check_verification) #may be duplications but we don't matter

class Bishop(Piece):
    '''Class for Bishops, please refer to :class:`Piece`'''
    NAME = "Bishop"
    def __init__(self, color, pos: tuple, board):
        super().__init__(color, pos, board)
    
    def get_moves_allowed(self, skip_check_verification=False): #returns every move allowed
        return self.cases_allowed_in_diagonals(skip_check_verification)
    
class Knight(Piece):
    '''Class for Knights, please refer to :class:`Piece`'''
    NAME = "Knight"
    def __init__(self, color, pos: tuple, board):
        super().__init__(color, pos, board)
    
    def get_moves_allowed(self, skip_check_verification=False): #returns every move allowed
        return self.cases_allowed_for_knight(skip_check_verification)

class Pawn(Piece):
    '''Class for Pawns, please refer to :class:`Piece`'''
    NAME = "Pawn"
    def __init__(self, color, pos: tuple, board):
        super().__init__(color, pos, board)
        self.promote_class_wanted = None
        '''
        | This attribute stores the piece class that will be used if the Pawn promotes
        | It can be changed whenever in the game, if no value is given we'll warn it and use a Queen to promote the Pawn
        '''
    
    def get_moves_allowed(self, skip_check_verification=False): #returns every move allowed
        allowed_moves = []
        in_front_y = self.pos[1] + 1*self.color + (self.color - 1)
        in_front_case_pos = (self.pos[0], in_front_y)
        in_front_move = self.case_allowed(in_front_case_pos, this_move_can_kill=False, skip_check_verification=skip_check_verification)
        
        if in_front_move.allowed:
            allowed_moves.append(in_front_move)

            if not self.has_already_moved:
                #it could try to go 2 cases in front of itself
                two_cases_in_front_pos = (in_front_case_pos[0], in_front_y + 1*self.color + (self.color - 1))
                two_cases_move = self.case_allowed(two_cases_in_front_pos, this_move_can_kill=False, skip_check_verification=skip_check_verification)
                if two_cases_move.allowed:
                    allowed_moves.append(two_cases_move)
        
        for x in range(self.pos[0]-1, self.pos[0]+2, 2):#x-1 and x+1
            cur_move = self.case_allowed((x, in_front_y), skip_check_verification=skip_check_verification)
            if cur_move.type in (cur_move.KILL_MOVE, cur_move.OVER_CHECK_MOVE):
                allowed_moves.append(cur_move)
        
        #En passant move
        if (self.color == self.WHITE and self.pos[1] == 3) or (self.color == self.BLACK and self.pos[1] == 4):
            last_move_history = self.board.move_history[-1]
            piece_of_last_move = last_move_history["piece"]
            en_passant_pos = (piece_of_last_move.pos[0], piece_of_last_move.pos[1] + (last_move_history["ini_pos"][1] - piece_of_last_move.pos[1])//2)
            if type(piece_of_last_move) == __class__ and piece_of_last_move.pos[1] == self.pos[1] and abs(piece_of_last_move.pos[0] - self.pos[0]) == 1 and \
                not last_move_history["has_already_moved"] and self.case_allowed(en_passant_pos, skip_check_verification=skip_check_verification):
                allowed_moves.append(Move(Move.SPECIAL_MOVE, self, en_passant_pos, Move.EN_PASSANT_TYPE))

        return allowed_moves

class Case:
    BLACK_TEXTURE = None
    WHITE_TEXTURE = None
    BLACK = 1
    WHITE = 0
    def __init__(self, square_type, content=None):
        self.content = content
        self.type = square_type

class Board:
    '''Represents the whole game board, containing pieces and data about current and past turns'''
    #we'll always consider that white starts in the bottom screen and black in the upper, so the white knight will be (4, 8) and the black one at (4, 0)
    BACK_LINE_INIT_POSITIONS = {(0, 0): Rook, (1, 0): Knight, (2, 0): Bishop,
        (3, 0): Queen, (4, 0): Check, (5, 0): Bishop,
        (6, 0): Knight, (7, 0): Rook} #uses 0 as y back line
    
    def __init__(self, pieces_by_pos=None, move_history=[], cur_color_turn=Case.WHITE, verbose=1):
        self.verbose = verbose
        self.move_history = move_history
        ''''''
        self.hypothesis_board = False
        self.cur_color_turn = cur_color_turn
        ''''''
        self.cur_color_turn_in_check = False #will be overidden in the hypothesis build if it is a hypothesis
        '''If the current playing color is in check'''
        self.game_ended = False
        ''''''
        self.winner = False
        ''''''

        self.pieces_by_color = [[], []] #will be overidden in _init_vars
        '''2-dimensional list representing pieces by color (self.pieces_by_color[0] for white pieces and self.pieces_by_color[0] for black pieces)'''

        if pieces_by_pos is None:
            self.pieces_by_pos = {}
            '''Dict representing pieces, keys are positions (tuple) and values are pieces (:class:`Piece`)'''
            #inits pieces pos
            for color in range(2):
                #adding the back line
                for pos_vector, type in self.BACK_LINE_INIT_POSITIONS.items():
                    pos = (pos_vector[0], (1-color)*7)
                    self.pieces_by_pos[pos] = type(color, pos, self)
                #adding the front line
                for x in range(8):
                    pos = (x, (1-color)*6 + 1*color)
                    piece = Pawn(color, pos, self)
                    self.pieces_by_pos[pos] = piece

            self._init_vars()

        else:
            self.pieces_by_pos = pieces_by_pos
            self.hypothesis_board = True
    
    def _init_vars(self):
        '''Used to init self.check_pieces and self.pieces_by_color (used when initiating a new obj or hypothesis)'''
        self.check_pieces = [None, None]
        for piece in tuple(self.pieces_by_pos.values()):
            if piece.invicible:
                self.check_pieces[piece.color] = piece
        
        for piece in tuple(self.pieces_by_pos.values()):
            self.pieces_by_color[piece.color].append(piece)

            
    def get_piece_by_pos(self, pos):
        if pos in self.pieces_by_pos:
            return self.pieces_by_pos[pos]
        else:
            return None
    
    def is_allowed_move(self, piece: Piece, future_pos:tuple): #return bool, Move
        moves_allowed = piece.get_moves_allowed()
        for move in moves_allowed:
            if move.target == future_pos:
                return True, move
        return False, None
    
    def _new_turn(self): #returns if there is a checkmate
        self.cur_color_turn = 1 - self.cur_color_turn
        self.cur_color_turn_in_check = self.check_pieces[self.cur_color_turn].in_check_situation()
        if self.cur_color_turn_in_check: print(f"{self.check_pieces[self.cur_color_turn]} is in check situation")
        #we check if it is a checkmate situation
        for piece in tuple(self.pieces_by_pos.values()):
            if piece.color == self.cur_color_turn:
                if len(piece.get_moves_allowed()) > 0:
                    return False
        #no piece can move, this is a checkmate or an ending in a stalemate situation
        self.game_ended = True
        if self.cur_color_turn_in_check:
            self.winner = 1 - self.cur_color_turn
            print(f"Checkmate! color {self.winner} won!")
        else:
            self.winner = None
            print("Pat! Nobody won!")
        return True

    def move_piece(self, piece, pos_or_move:tuple or Move, skip_allowed_verif=False, call_new_turn=True) -> None or tuple:
        '''Enables you to move a piece instead of doing it with the :class:`Piece` obj, returns None if the move isn't allowed'''
        pos = pos_or_move
        if type(pos_or_move) == Move:
            pos = pos_or_move.target
        
        if not skip_allowed_verif:
            allowed, move = self.is_allowed_move(piece, pos)
            if self.cur_color_turn != piece.color:
                allowed = False
        else:
            allowed = True
            move = Move(Move.KILL_MOVE, piece, pos) #to avoid any problem
            #when skip_allowed_verif move_history won't be important so move type doesn't matter

        if allowed:
            ini_pos = piece.pos
            self.move_history.append({"ini_pos": ini_pos, "move": move, "piece": piece, "has_already_moved": piece.has_already_moved})
            self.pieces_by_pos.pop(piece.pos)
            piece.pos = pos
            piece.has_already_moved = True
            if move.special_type == move.CASTLING_TYPE:
                #moving rook
                little_castling = True if pos == (ini_pos[0]+2, ini_pos[1]) else False
                rook = self.pieces_by_pos.pop((pos[0]+1, pos[1])) if little_castling else self.pieces_by_pos.pop((pos[0]-2, pos[1]))
                new_rook_pos = (pos[0]-1, pos[1]) if little_castling else (pos[0]+1, pos[1])
                rook.pos = new_rook_pos
                self.pieces_by_pos[new_rook_pos] = rook
            elif move.special_type == move.EN_PASSANT_TYPE:
                #killing pawn
                self.pieces_by_pos.pop((pos[0], ini_pos[1]))

            if pos in self.pieces_by_pos:
                if move.type == move.TO_EMPTY_MOVE:
                    print("WARNING: overriding an existing piece pos", pos, "for piece obj", piece)
                else:
                    self.pieces_by_color[self.pieces_by_pos[pos].color].remove(self.pieces_by_pos[pos])
                
            self.pieces_by_pos[pos] = piece
            
            if call_new_turn:
                #if we must make a Pawn promote
                if isinstance(piece, Pawn) and ((piece.color == Piece.WHITE and piece.pos[1] == 0) or (piece.color == Piece.BLACK and piece.pos[1] == 7)):
                    if self.verbose >= 1: print(f"{piece} upgrading!")
                    new_piece_class = piece.promote_class_wanted
                    if new_piece_class is None:
                        warn(f"No promote_class_wanted for {piece}, you should set the pawn's attribute promote_class_wanted before moving it\nWe'll use a Queen to promote it")
                        new_piece_class = Queen
                    new_piece = new_piece_class(piece.color, piece.pos, self)
                    self.pieces_by_pos[pos] = new_piece
                    self.pieces_by_color[piece.color].append(new_piece)
                    #deleting the pawn
                    self.pieces_by_color[piece.color].remove(piece)

                is_checkmate = self._new_turn()
            return pos
        else:
            if self.verbose >= 1: print(f"Move of piece {piece} to {pos} isn't allowed")
            return None
    
    def create_hypothesis_board(self, pieces_with_pos_to_change={}):
        '''| Allows you to create hypothesis boards, an independent copy of the current Board
        | Returns another Board obj'''
        if self.hypothesis_board: print("Warning: creating a hypothesis from another hypothesis")

        hypo_board = Board(pieces_by_pos={}, cur_color_turn=self.cur_color_turn, verbose=self.verbose)

        real_piece_to_hypothesis_piece = {}
        #copying pieces_by_pos
        pieces_by_pos = {}
        for pos, piece in self.pieces_by_pos.items():
            piece_copy = piece.copy(hypo_board)
            real_piece_to_hypothesis_piece[piece] = piece_copy
            pieces_by_pos[pos] = piece_copy
        hypo_board.pieces_by_pos = pieces_by_pos

        #copying moves_history
        move_history = []
        for cur_history_point in self.move_history:
            if cur_history_point['piece'] in real_piece_to_hypothesis_piece:
                cur_hypothesis_piece = real_piece_to_hypothesis_piece[cur_history_point['piece']]
            else: #meaning that the piece is dead
                cur_hypothesis_piece = cur_history_point["piece"]
            
            move_history.append({
                "ini_pos": cur_history_point['ini_pos'],
                "move": cur_history_point['move'].copy(cur_hypothesis_piece),
                "piece": cur_hypothesis_piece,
                "has_already_moved": cur_history_point['has_already_moved']
            })
        hypo_board.move_history = move_history
        
        hypo_board._init_vars()
        
        for piece, new_pos in pieces_with_pos_to_change.items():
            hypo_board.move_piece(real_piece_to_hypothesis_piece[piece], new_pos, skip_allowed_verif=True, call_new_turn=False)

        return hypo_board