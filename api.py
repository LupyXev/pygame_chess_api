from pygame import image, Surface
from time import time
from math import sqrt

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
    FORBIDDEN_MOVE = 0
    TO_EMPTY_MOVE = 1 #a move to a empty case
    KILL_MOVE = 2
    SPECIAL_MOVE = 3 #like for castling move
    OVER_CHECK_MOVE = 4 #used to detect check situations (move where you'll kill a Check piece)
    LEADING_TO_CHECK_SITUATION_MOVE = 5
    TEXTURES = {
        TO_EMPTY_MOVE: image.load("./assets/square_of_highlight.png"),
        KILL_MOVE: image.load("./assets/square_of_kill.png"),
        SPECIAL_MOVE: image.load("./assets/square_of_special.png"),
    }
    CASTLING_TYPE = 1
    EN_PASSANT_TYPE = 2
    def __init__(self, type: int, piece, target:tuple, special_type=None):
        self.type = type
        self.piece = piece
        self.target = target #will be (-1, -1) if type is FORBIDDEN_MOVE
        self.special_type = special_type
    
    @property
    def allowed(self):
        return self.type not in (self.FORBIDDEN_MOVE, self.LEADING_TO_CHECK_SITUATION_MOVE)
    
    @property
    def texture(self):
        return self.TEXTURES[self.type]
    
    def __str__(self):
        return f"Move of piece {self.piece} to {self.target} (type : {self.type})"    


class Piece:
    WHITE_TEXTURE, BLACK_TEXTURE = None, None #will be used only in childs
    WHITE, BLACK = 0, 1
    DIAGONALS_VECTORS = ((-1, -1), (1, -1), (-1, 1), (1, 1))
    LINES_VECTORS = ((0, -1), (0, 1), (-1, 0), (1, 0))
    KNIGHT_VECTOR = ((1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2))
    COLLISION_MOVES = (Move.KILL_MOVE, Move.OVER_CHECK_MOVE)
    def __init__(self, color: int, pos: tuple, board):
        self.color = color
        self.pos = pos
        self.board = board
        self.invicible = False #True value will be considered as Check piece
        self.has_already_moved = False
    
    def get_moves_allowed(self):
        return [] #will be overrided in children
    
    def case_allowed(self, case_pos, this_move_can_kill=True): #returns move
        for c in case_pos:
            if c < 0 or c > 7:
                return Move(Move.FORBIDDEN_MOVE, self, (-1, -1))
        
        def verify_check():
            if self.invicible and self.in_check_situation(pos_hypothesis=case_pos):
                return Move(Move.LEADING_TO_CHECK_SITUATION_MOVE, self, (-1, -1)) #not allowed because would be in check situation

        if case_pos in self.board.pieces_pos:
            cur_piece = self.board.pieces_pos[case_pos]
            if cur_piece.color != self.color and this_move_can_kill:
                if cur_piece.invicible == False: #invicible means that this is a Check piece
                    verify_check()
                    return Move(Move.KILL_MOVE, self, case_pos) #there is collision
                else:
                    verify_check()
                    return Move(Move.OVER_CHECK_MOVE, self, case_pos) #over a Check piece (used only in hypothesis)
            else:
                return Move(Move.FORBIDDEN_MOVE, self, (-1, -1)) #not allowed and collision
        else:
            verify_check()
            return Move(Move.TO_EMPTY_MOVE, self, case_pos) #no collision

    def cases_allowed_around(self):
        cases_around_list = []
        for x in range(max(0, self.pos[0]-1), min(8, self.pos[0]+2)):
            for y in range(max(0, self.pos[1]-1), min(8, self.pos[1]+2)):
                cur_move = self.case_allowed((x, y))
                if cur_move.allowed:
                    cases_around_list.append(cur_move)    
        return cases_around_list
    
    def cases_allowed_in_diagonals(self):
        cases_allowed_list = []
        for vector in self.DIAGONALS_VECTORS: #4 directions of diagonals
            cur_pos = tuple([self.pos[i] + vector[i] for i in range(2)])
            cur_move = self.case_allowed(cur_pos)
            while cur_move.allowed: #move allowed
                cases_allowed_list.append(cur_move)
                if cur_move.type in self.COLLISION_MOVES: #has been collision last move
                    break
                cur_pos = tuple([cur_pos[i] + vector[i] for i in range(2)])
                cur_move = self.case_allowed(cur_pos)
        return cases_allowed_list
    
    def cases_allowed_in_line(self): #like for rooks
        cases_allowed_list = []
        for vector in self.LINES_VECTORS: #4 directions of lines
            cur_pos = tuple([self.pos[i] + vector[i] for i in range(2)])
            cur_move = self.case_allowed(cur_pos)
            while cur_move.allowed: #move allowed
                cases_allowed_list.append(cur_move)
                if cur_move.type in self.COLLISION_MOVES: #has been collision last move
                    break
                cur_pos = tuple([cur_pos[i] + vector[i] for i in range(2)])
                cur_move = self.case_allowed(cur_pos)
        return cases_allowed_list
    
    def cases_allowed_for_knight(self):
        allowed_moves = []
        for vector in self.KNIGHT_VECTOR:
            cur_pos = tuple([self.pos[i] + vector[i] for i in range(2)])
            cur_move = self.case_allowed(cur_pos)
            if cur_move.allowed:
                allowed_moves.append(cur_move)
        return allowed_moves

    @property
    def texture(self):
        return self.WHITE_TEXTURE if self.color == 0 else self.BLACK_TEXTURE
    
    def copy(self, new_board):
        return self.__class__(self.color, self.pos, new_board)

class Rook(Piece):
    def __init__(self, color, pos: tuple, board):
        super().__init__(color, pos, board)
    
    def get_moves_allowed(self): #returns every move allowed
        return self.cases_allowed_in_line()

class Check(Piece):
    def __init__(self, color, pos: tuple, board):
        super().__init__(color, pos, board)
        self.invicible = True
        self.currently_in_check = False
    
    def in_check_situation(self, pos_hypothesis=None):
        if pos_hypothesis:
            #we create hypothesis to know if some piece could "kill" this Check piece, meaning that we would be in a check situation
            board = self.board.create_hypothesis_board()
            self_in_hypothesis = board.pieces_pos[self.pos]
            board.move_piece(self_in_hypothesis, pos_hypothesis, skip_allowed_verif=True)
        else:
            board = self.board
            self_in_hypothesis = self
        
        for piece in board.pieces_pos.values():
            if piece.color != self.color: 
                if piece.invicible: #to avoid recursive erros
                    if sqrt((self_in_hypothesis.pos[0] - piece.pos[0])**2 + (self_in_hypothesis.pos[1] - piece.pos[1])**2) < 2:
                        #both Checks are too close, this should be impossible (obviously it will only happen in hypothesis)
                        return True

                else:
                    for move in piece.get_moves_allowed():
                        if move.type == Move.OVER_CHECK_MOVE:
                            return True

        return False

    def get_moves_allowed(self): #returns every move allowed
        moves_around_without_check_verif = self.cases_allowed_around()
        moves_around = [m for m in moves_around_without_check_verif if not self.in_check_situation(m.target)]

        if not self.has_already_moved:
            #little castling
            little_castling_free_pos_needed = [(self.pos[0]+i, self.pos[1]) for i in range(1, 3)]
            pos_little_castling_are_free = True
            for cur_pos in little_castling_free_pos_needed:
                if cur_pos in self.board.pieces_pos or self.in_check_situation(cur_pos): pos_little_castling_are_free = False
            
            piece_at_rook_needed_pos = self.board.pieces_pos[(self.pos[0]+3, self.pos[1])] if (self.pos[0]+3, self.pos[1]) in self.board.pieces_pos else None
            if pos_little_castling_are_free and type(piece_at_rook_needed_pos) == Rook and not piece_at_rook_needed_pos.has_already_moved:
                if not self.in_check_situation((self.pos[0]+2, self.pos[1])):
                    moves_around.append(Move(Move.SPECIAL_MOVE, self, (self.pos[0]+2, self.pos[1]), Move.CASTLING_TYPE))
            
            #big castling
            big_castling_free_pos_needed = [(self.pos[0]-i, self.pos[1]) for i in range(1, 4)]
            pos_big_castling_are_free = True
            for cur_pos in big_castling_free_pos_needed:
                if cur_pos in self.board.pieces_pos or self.in_check_situation(cur_pos): pos_big_castling_are_free = False
            
            piece_at_rook_needed_pos = self.board.pieces_pos[(self.pos[0]-4, self.pos[1])] if (self.pos[0]-4, self.pos[1]) in self.board.pieces_pos else None
            if pos_big_castling_are_free and type(piece_at_rook_needed_pos) == Rook and not piece_at_rook_needed_pos.has_already_moved:
                if not self.in_check_situation((self.pos[0]-2, self.pos[1])):
                    moves_around.append(Move(Move.SPECIAL_MOVE, self, (self.pos[0]-2, self.pos[1]), Move.CASTLING_TYPE))
        #TODO: must be filtered with check situations
        return moves_around   

class Queen(Piece):
    def __init__(self, color, pos: tuple, board):
        super().__init__(color, pos, board)
    
    def get_moves_allowed(self): #returns every move allowed
        return self.cases_allowed_around() + self.cases_allowed_in_diagonals() + self.cases_allowed_in_line() #may be duplications but we don't matter

class Bishop(Piece):
    def __init__(self, color, pos: tuple, board):
        super().__init__(color, pos, board)
    
    def get_moves_allowed(self): #returns every move allowed
        return self.cases_allowed_in_diagonals()
    
class Knight(Piece):
    def __init__(self, color, pos: tuple, board):
        super().__init__(color, pos, board)
    
    def get_moves_allowed(self): #returns every move allowed
        return self.cases_allowed_for_knight()

class Pawn(Piece):
    def __init__(self, color, pos: tuple, board):
        super().__init__(color, pos, board)
    
    def get_moves_allowed(self): #returns every move allowed
        allowed_moves = []
        in_front_y = self.pos[1] + 1*self.color + (self.color - 1)
        in_front_case_pos = (self.pos[0], in_front_y)
        in_front_move = self.case_allowed(in_front_case_pos, this_move_can_kill=False)
        
        if in_front_move.allowed: allowed_moves.append(in_front_move)

        if not self.has_already_moved:
            #it could try to go 2 cases in front of itself
            two_cases_in_front_pos = (in_front_case_pos[0], in_front_y + 1*self.color + (self.color - 1))
            two_cases_move = self.case_allowed(two_cases_in_front_pos, this_move_can_kill=False)
            if two_cases_move.allowed:
                allowed_moves.append(two_cases_move)
        
        for x in range(self.pos[0]-1, self.pos[0]+2, 2):#x-1 and x+1
            cur_move = self.case_allowed((x, in_front_y))
            if cur_move.type in (cur_move.KILL_MOVE, cur_move.OVER_CHECK_MOVE):
                allowed_moves.append(cur_move)
        
        #En passant move
        if (self.color == self.WHITE and self.pos[1] == 3) or (self.color == self.BLACK and self.pos[1] == 4):
            last_move_history = self.board.move_history[-1]
            piece_of_last_move = last_move_history["piece"]
            if type(piece_of_last_move) == __class__ and piece_of_last_move.pos[1] == self.pos[1] and abs(piece_of_last_move.pos[0] - self.pos[0]) == 1 and \
                not last_move_history["has_already_moved"]:
                allowed_moves.append(Move(Move.SPECIAL_MOVE, self, (piece_of_last_move.pos[0], piece_of_last_move.pos[1] + (last_move_history["ini_pos"][1] - piece_of_last_move.pos[1])//2), Move.EN_PASSANT_TYPE))

        return allowed_moves

class Case:
    BLACK_TEXTURE = image.load("assets/black_square.png")
    WHITE_TEXTURE = image.load("assets/white_square.png")
    BLACK = 1
    WHITE = 0
    def __init__(self, square_type, content=None):
        self.content = content
        self.type = square_type

class Board:
    #we'll always consider that white starts in the bottom screen and black in the upper, so the white knight will be (4, 8) and the black one at (4, 0)
    BACK_LINE_INIT_POSITIONS = {(0, 0): Rook, (1, 0): Knight, (2, 0): Bishop,
        (3, 0): Queen, (4, 0): Check, (5, 0): Bishop,
        (6, 0): Knight, (7, 0): Rook} #uses 0 as y back line
    
    def __init__(self, pieces_pos=None):
        self.move_history = [] #warning: not copied when making a hypothesis
        self.hypothesis_board = False
        if pieces_pos is None:
            self.pieces_pos = {}
            #inits pieces pos
            for color in range(2):
                #adding the back line
                for pos_vector, type in self.BACK_LINE_INIT_POSITIONS.items():
                    pos = (pos_vector[0], (1-color)*7)
                    self.pieces_pos[pos] = type(color, pos, self)
                #adding the front line
                for x in range(8):
                    pos = (x, (1-color)*6 + 1*color)
                    piece = Pawn(color, pos, self)
                    self.pieces_pos[pos] = piece
        else:
            self.pieces_pos = pieces_pos
            self.hypothesis_board = True
    
    
    def get_piece_by_pos(self, pos):
        if pos in self.pieces_pos:
            return self.pieces_pos[pos]
        else:
            return None
    
    def is_allowed_move(self, piece: Piece, future_pos:tuple): #return bool, Move
        moves_allowed = piece.get_moves_allowed()
        for move in moves_allowed:
            if move.target == future_pos:
                return True, move
        return False, None
        
    def move_piece(self, piece, pos:tuple, skip_allowed_verif=False):
        if not skip_allowed_verif:
            allowed, move = self.is_allowed_move(piece, pos)
        else:
            allowed = True
            move = Move(Move.KILL_MOVE, piece, pos) #to avoid any problem
            #when skip_allowed_verif move_history won't be important so move type doesn't matter

        if allowed:
            ini_pos = piece.pos
            self.move_history.append({"ini_pos": ini_pos, "move": move, "piece": piece, "has_already_moved": piece.has_already_moved})
            self.pieces_pos.pop(piece.pos)
            piece.pos = pos
            piece.has_already_moved = True
            if move.special_type == move.CASTLING_TYPE:
                #moving rook
                little_castling = True if pos == (ini_pos[0]+2, ini_pos[1]) else False
                rook = self.pieces_pos.pop((pos[0]+1, pos[1])) if little_castling else self.pieces_pos.pop((pos[0]-2, pos[1]))
                new_rook_pos = (pos[0]-1, pos[1]) if little_castling else (pos[0]+1, pos[1])
                rook.pos = new_rook_pos
                self.pieces_pos[new_rook_pos] = rook
            elif move.special_type == move.EN_PASSANT_TYPE:
                #killing pawn
                self.pieces_pos.pop((pos[0], ini_pos[1]))

            if pos in self.pieces_pos and move.type == move.TO_EMPTY_MOVE:
                print("WARNING: overriding an existing piece pos", pos, "for piece obj", piece)
            self.pieces_pos[pos] = piece
            return pos
        return None
    
    def create_hypothesis_board(self):
        hypo_board = Board(pieces_pos={})

        pieces_pos = {}
        for pos, piece in self.pieces_pos.items():
            pieces_pos[pos] = piece.copy(hypo_board)
        
        hypo_board.pieces_pos = pieces_pos
        return hypo_board