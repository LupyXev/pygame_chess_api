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
    def case_allowed(self, case_pos, board): #returns allowed, collision
        for c in case_pos:
            if c < 0 or c > 7:
                return False, True
        
        if case_pos in board.pieces_pos:
            cur_piece = board.pieces_pos[case_pos]
            if cur_piece.color != self.color and cur_piece.invicible == False:
                return True, True #there is collision
            else:
                return False, True #not allowed and collision
        else:
            return True, False #no collision

    def cases_allowed_around(self, board):
        cases_around_list = []
        for x in range(max(0, self.pos[0]-1), min(8, self.pos[0]+2)):
            for y in range(max(0, self.pos[1]-1), min(8, self.pos[1]+2)):
                if self.case_allowed((x, y), board)[0]:
                    cases_around_list.append((x, y))    
        return cases_around_list
    
    def cases_allowed_in_diagonals(self, board):
        cases_allowed_list = []
        for vector in self.DIAGONALS_VECTORS: #4 directions of diagonals
            cur_pos = tuple([self.pos[i] + vector[i] for i in range(2)])
            allowing = self.case_allowed(cur_pos, board)
            while allowing[0]: #move allowed
                cases_allowed_list.append(cur_pos)
                if allowing[1]: #has been collision last move
                    break
                cur_pos = tuple([cur_pos[i] + vector[i] for i in range(2)])
                allowing = self.case_allowed(cur_pos, board)
        return cases_allowed_list
    
    def cases_allowed_in_line(self, board): #like for rooks
        cases_allowed_list = []
        for vector in self.LINES_VECTORS: #4 directions of lines
            cur_pos = tuple([self.pos[i] + vector[i] for i in range(2)])
            allowing = self.case_allowed(cur_pos, board)
            while allowing[0]: #move allowed
                cases_allowed_list.append(cur_pos)
                if allowing[1]: #has been collision last move
                    break
                cur_pos = tuple([cur_pos[i] + vector[i] for i in range(2)])
                allowing = self.case_allowed(cur_pos, board)
        return cases_allowed_list
    
    def cases_allowed_for_knight(self, board):
        allowed_moves = []
        for vector in self.KNIGHT_VECTOR:
            cur_pos = tuple([self.pos[i] + vector[i] for i in range(2)])
            if self.case_allowed(cur_pos, board)[0]:
                allowed_moves.append(cur_pos)
        return allowed_moves

    @property
    def texture(self):
        return self.WHITE_TEXTURE if self.color == 0 else self.BLACK_TEXTURE

class Check(Piece):
    def __init__(self, color, pos: tuple):
        super().__init__(color, pos)
        self.invicible = True
    
    def get_moves_allowed(self, board): #returns every move allowed
        moves_around = self.cases_allowed_around(board)
        #TODO: must be filtered with check situations
        return moves_around
        

class Queen(Piece):
    def __init__(self, color, pos: tuple):
        super().__init__(color, pos)
    
    def get_moves_allowed(self, board): #returns every move allowed
        return self.cases_allowed_around(board) + self.cases_allowed_in_diagonals(board) + self.cases_allowed_in_line(board) #may be duplications but we don't matter

class Rook(Piece):
    def __init__(self, color, pos: tuple):
        super().__init__(color, pos)
    
    def get_moves_allowed(self, board): #returns every move allowed
        return self.cases_allowed_in_line(board)

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
        in_front_case_pos = (self.pos[0], self.pos[1] + 1*self.color + (self.color - 1))
        in_front_case_allowing = self.case_allowed(in_front_case_pos, board)
        if in_front_case_allowing[0]:
            allowed_moves.append(in_front_case_pos)
            if not in_front_case_allowing[1] and not self.has_already_moved:
                #it could try to go 2 cases in front of itself
                two_cases_in_front = (in_front_case_pos[0], in_front_case_pos[1] + 1*self.color + (self.color - 1))
                if self.case_allowed(two_cases_in_front, board)[0]:
                    allowed_moves.append(two_cases_in_front)
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
    
    def is_allowed_move(self, piece: Piece, future_pos:tuple):
        moves_allowed = piece.get_moves_allowed(self)
        if future_pos in moves_allowed:
            return True
        return False
        
    def move_piece(self, piece, pos:tuple):
        if self.is_allowed_move(piece, pos):
            self.pieces_pos.pop(piece.pos)
            piece.pos = pos
            piece.has_already_moved = True
            if pos in self.pieces_pos:
                print("WARNING: overriding an existing piece pos", pos, "for piece obj", piece)
            self.pieces_pos[pos] = piece
            return pos
        return None