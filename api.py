from pygame import image
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
    TEXTURES = {
        TO_EMPTY_MOVE: image.load("./assets/square_of_highlight.png"),
        KILL_MOVE: image.load("./assets/square_of_kill.png"),
        SPECIAL_MOVE: image.load("./assets/square_of_special.png")
    }
    CASTLING_TYPE = 1
    EN_PASSANT_TYPE = 2
    def __init__(self, type: int, target=None, special_type=None):
        self.type = type
        self.target = target
        self.special_type = special_type
    
    @property
    def allowed(self):
        return self.type != self.FORBIDDEN_MOVE
    
    @property
    def texture(self):
        return self.TEXTURES[self.type]

class Piece:
    WHITE_TEXTURE, BLACK_TEXTURE = None, None #will be used only in childs
    WHITE, BLACK = 0, 1
    DIAGONALS_VECTORS = ((-1, -1), (1, -1), (-1, 1), (1, 1))
    LINES_VECTORS = ((0, -1), (0, 1), (-1, 0), (1, 0))
    KNIGHT_VECTOR = ((1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2))
    def __init__(self, color: int, pos: tuple):
        self.color = color
        self.pos = pos
        self.invicible = False #will be true for check pieces
        self.has_already_moved = False
        print("initiated", self.__class__, self.pos)
    
    '''def get_distance(self, pos_to_study:tuple):
        return sqrt((self.pos[0] - pos_to_study[0])**2 + (self.pos[1] - pos_to_study[1])**2)'''
    def case_allowed(self, case_pos, board): #returns move
        for c in case_pos:
            if c < 0 or c > 7:
                return Move(Move.FORBIDDEN_MOVE)
        
        if case_pos in board.pieces_pos:
            cur_piece = board.pieces_pos[case_pos]
            if cur_piece.color != self.color and cur_piece.invicible == False:
                return Move(Move.KILL_MOVE, case_pos) #there is collision
            else:
                return Move(Move.FORBIDDEN_MOVE) #not allowed and collision
        else:
            return Move(Move.TO_EMPTY_MOVE, case_pos) #no collision

    def cases_allowed_around(self, board):
        cases_around_list = []
        for x in range(max(0, self.pos[0]-1), min(8, self.pos[0]+2)):
            for y in range(max(0, self.pos[1]-1), min(8, self.pos[1]+2)):
                cur_move = self.case_allowed((x, y), board)
                if cur_move.allowed:
                    cases_around_list.append(cur_move)    
        return cases_around_list
    
    def cases_allowed_in_diagonals(self, board):
        cases_allowed_list = []
        for vector in self.DIAGONALS_VECTORS: #4 directions of diagonals
            cur_pos = tuple([self.pos[i] + vector[i] for i in range(2)])
            cur_move = self.case_allowed(cur_pos, board)
            while cur_move.allowed: #move allowed
                cases_allowed_list.append(cur_move)
                if cur_move.type == cur_move.KILL_MOVE: #has been collision last move
                    break
                cur_pos = tuple([cur_pos[i] + vector[i] for i in range(2)])
                cur_move = self.case_allowed(cur_pos, board)
        return cases_allowed_list
    
    def cases_allowed_in_line(self, board): #like for rooks
        cases_allowed_list = []
        for vector in self.LINES_VECTORS: #4 directions of lines
            cur_pos = tuple([self.pos[i] + vector[i] for i in range(2)])
            cur_move = self.case_allowed(cur_pos, board)
            while cur_move.allowed: #move allowed
                cases_allowed_list.append(cur_move)
                if cur_move.type == cur_move.KILL_MOVE: #has been collision last move
                    break
                cur_pos = tuple([cur_pos[i] + vector[i] for i in range(2)])
                cur_move = self.case_allowed(cur_pos, board)
        return cases_allowed_list
    
    def cases_allowed_for_knight(self, board):
        allowed_moves = []
        for vector in self.KNIGHT_VECTOR:
            cur_pos = tuple([self.pos[i] + vector[i] for i in range(2)])
            cur_move = self.case_allowed(cur_pos, board)
            if cur_move.allowed:
                allowed_moves.append(cur_move)
        return allowed_moves

    @property
    def texture(self):
        return self.WHITE_TEXTURE if self.color == 0 else self.BLACK_TEXTURE

class Rook(Piece):
    def __init__(self, color, pos: tuple):
        super().__init__(color, pos)
    
    def get_moves_allowed(self, board): #returns every move allowed
        return self.cases_allowed_in_line(board)

class Check(Piece):
    def __init__(self, color, pos: tuple):
        super().__init__(color, pos)
        self.invicible = True
    
    def get_moves_allowed(self, board): #returns every move allowed
        moves_around = self.cases_allowed_around(board)
        if not self.has_already_moved:
            #little castling
            little_castling_free_pos_needed = [(self.pos[0]+i, self.pos[1]) for i in range(1, 3)]
            pos_little_castling_are_free = True
            for cur_pos in little_castling_free_pos_needed:
                if cur_pos in board.pieces_pos: pos_little_castling_are_free = False
            
            piece_at_rook_needed_pos = board.pieces_pos[(self.pos[0]+3, self.pos[1])] if (self.pos[0]+3, self.pos[1]) in board.pieces_pos else None
            if pos_little_castling_are_free and type(piece_at_rook_needed_pos) == Rook and not piece_at_rook_needed_pos.has_already_moved:
                moves_around.append(Move(Move.SPECIAL_MOVE, (self.pos[0]+2, self.pos[1]), Move.CASTLING_TYPE))
            
            #big castling
            big_castling_free_pos_needed = [(self.pos[0]-i, self.pos[1]) for i in range(1, 4)]
            pos_big_castling_are_free = True
            for cur_pos in big_castling_free_pos_needed:
                if cur_pos in board.pieces_pos: pos_big_castling_are_free = False
            
            piece_at_rook_needed_pos = board.pieces_pos[(self.pos[0]-4, self.pos[1])] if (self.pos[0]-4, self.pos[1]) in board.pieces_pos else None
            if pos_big_castling_are_free and type(piece_at_rook_needed_pos) == Rook and not piece_at_rook_needed_pos.has_already_moved:
                moves_around.append(Move(Move.SPECIAL_MOVE, (self.pos[0]-2, self.pos[1]), Move.CASTLING_TYPE))
            
        #TODO: must be filtered with check situations
        return moves_around   

class Queen(Piece):
    def __init__(self, color, pos: tuple):
        super().__init__(color, pos)
    
    def get_moves_allowed(self, board): #returns every move allowed
        return self.cases_allowed_around(board) + self.cases_allowed_in_diagonals(board) + self.cases_allowed_in_line(board) #may be duplications but we don't matter

class Bishop(Piece):
    def __init__(self, color, pos: tuple):
        super().__init__(color, pos)
    
    def get_moves_allowed(self, board): #returns every move allowed
        return self.cases_allowed_in_diagonals(board)
    
class Knight(Piece):
    def __init__(self, color, pos: tuple):
        super().__init__(color, pos)
    
    def get_moves_allowed(self, board): #returns every move allowed
        return self.cases_allowed_for_knight(board)

class Pawn(Piece):
    def __init__(self, color, pos: tuple):
        super().__init__(color, pos)
    
    def get_moves_allowed(self, board): #returns every move allowed
        allowed_moves = []
        in_front_y = self.pos[1] + 1*self.color + (self.color - 1)
        in_front_case_pos = (self.pos[0], in_front_y)
        in_front_move = self.case_allowed(in_front_case_pos, board)
        if in_front_move.allowed and in_front_move.type != in_front_move.KILL_MOVE:
            allowed_moves.append(in_front_move)
            if in_front_move.type != in_front_move.KILL_MOVE and not self.has_already_moved:
                #it could try to go 2 cases in front of itself
                two_cases_in_front_pos = (in_front_case_pos[0], in_front_y + 1*self.color + (self.color - 1))
                two_cases_move = self.case_allowed(two_cases_in_front_pos, board)
                if two_cases_move.allowed:
                    allowed_moves.append(two_cases_move)
        
        for x in range(self.pos[0]-1, self.pos[0]+2, 2):#x-1 and x+1
            cur_move = self.case_allowed((x, in_front_y), board)
            if cur_move.type == cur_move.KILL_MOVE:
                allowed_moves.append(cur_move)
        
        #En passant move
        if (self.color == self.WHITE and self.pos[1] == 3) or (self.color == self.BLACK and self.pos[1] == 4) and \
            len(board.move_history) > 0:
            last_move_history = board.move_history[-1]
            piece_of_last_move = last_move_history["piece"]
            if type(piece_of_last_move) == __class__ and piece_of_last_move.pos[1] == self.pos[1] and abs(piece_of_last_move.pos[0] - self.pos[0]) == 1 and \
                not last_move_history["has_already_moved"]:
                allowed_moves.append(Move(Move.SPECIAL_MOVE, (piece_of_last_move.pos[0], piece_of_last_move.pos[1] + (last_move_history["ini_pos"][1] - piece_of_last_move.pos[1])//2), Move.EN_PASSANT_TYPE))

        return allowed_moves

class Case:
    BLACK_TEXTURE = image.load("assets/black_square.png")
    WHITE_TEXTURE = image.load("assets/white_square.png")
    BLACK = 0
    WHITE = 1
    def __init__(self, square_type, content=None):
        self.content = content
        self.type = square_type

class Board:
    #we'll always consider that white starts in the bottom screen and black in the upper, so the white knight will be (4, 8) and the black one at (4, 0)
    BACK_LINE_INIT_POSITIONS = {(0, 0): Rook, (1, 0): Knight, (2, 0): Bishop,
        (3, 0): Queen, (4, 0): Check, (5, 0): Bishop,
        (6, 0): Knight, (7, 0): Rook} #uses 0 as y back line
    def __init__(self):
        #inits pieces pos
        self.pieces_pos = {}
        self.move_history = []
        for color in range(2):
            #adding the back line
            for pos_vector, type in self.BACK_LINE_INIT_POSITIONS.items():
                pos = (pos_vector[0], (1-color)*7)
                self.pieces_pos[pos] = type(color, pos)
            #adding the front line
            for x in range(8):
                pos = (x, (1-color)*6 + 1*color)
                self.pieces_pos[pos] = Pawn(color, pos)
    
    def get_piece_by_pos(self, pos):
        if pos in self.pieces_pos:
            return self.pieces_pos[pos]
        else:
            return None
    
    def is_allowed_move(self, piece: Piece, future_pos:tuple): #return bool, Move
        moves_allowed = piece.get_moves_allowed(self)
        for move in moves_allowed:
            if move.target == future_pos:
                return True, move
        return False, None
        
    def move_piece(self, piece, pos:tuple):
        allowed, move = self.is_allowed_move(piece, pos)
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