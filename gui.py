import pygame
from api import *
from render import *

pygame.init()
FPS = 60
SCREEN_SIZE = (800, 800)
SQUARE_SIZE = tuple([SCREEN_SIZE[i] // 8 for i in range(2)])

screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("ChessyIA Game")
clock = pygame.time.Clock()

board = Board()
gui = Gui(screen, SQUARE_SIZE, board, clock)
gui.generate_textures()

while True:
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            exit()	
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_presses = pygame.mouse.get_pressed()
            if mouse_presses[0] == True:
                #left click
                gui.mouse_left_clicked()
        if event.type == pygame.MOUSEBUTTONUP:
            gui.mouse_released()

    gui.draw_board()
    #pygame.display.update() is performed in draw_board()
    clock.tick(FPS)

