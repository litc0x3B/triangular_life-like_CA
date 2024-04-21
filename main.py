import pygame
from enum import Enum
from dataclasses import dataclass
import threading
from typing import List
import copy
import random

class CellDirection(Enum):
    UPWARDS = -1
    DOWNWARDS = 1

@dataclass    
class Rule:
    birth: list
    survival: list

def line_equation(x: float, point1: pygame.Vector2, point2: pygame.Vector2):
        return (x - point1.x) * (point2.y - point1.y) / (point2.x - point1.x) + point1.y

class Cell:
    def __init__(self, pos: pygame.Vector2, neighbors: list, dir: CellDirection = CellDirection.UPWARDS, size : pygame.Vector2 = pygame.Vector2(10, 10)):
        self.pos = pos
        self.is_alive = False
        self.dir = dir
        self.size = size
        self.neighbors = neighbors
        self.points = [ pygame.Vector2(self.pos.x + self.size.x / 2, self.pos.y - self.dir.value * self.size.y / 2), 
                        pygame.Vector2(self.pos.x - self.size.x / 2, self.pos.y - self.dir.value * self.size.y / 2),
                        pygame.Vector2(self.pos.x, self.pos.y + self.dir.value * self.size.y / 2)]
        
    def draw(self, surface): 
        return pygame.draw.polygon(surface, 'white' if self.is_alive else 'black', self.points)
    
    def collidepoint(self, point: pygame.Vector2):
        lines = [(self.points[0], self.points[1]), (self.points[1], self.points[2]), (self.points[2], self.points[0])]
        return  point.y * self.dir.value > line_equation(point.x, *lines[0]) * self.dir.value and\
                point.y * self.dir.value < line_equation(point.x, *lines[1]) * self.dir.value and\
                point.y * self.dir.value < line_equation(point.x, *lines[2]) * self.dir.value
    
    def __str__(self):
        return str(int(self.is_alive))

class Automaton:
    def __init__(   self,
                    rule: Rule,
                    cell_count_x = 50,
                    cell_count_y = 50,
                    offset_x = 0,
                    offset_y = 0,
                    cell_width = 100,
                    cell_height = 30,
                    cell_padding_left = 3,
                    cell_padding_top = 3):
        
        if cell_count_x % 2 != 0:
            raise ValueError('cell_count_x should be even')
        if cell_count_y % 2 != 0:
            raise ValueError('cell_count_y should be even')
        
        self.rule = rule
        self.cells: List[List[Cell]] = []
        
        for i in range(cell_count_x):
            row = []
            for j in range(cell_count_y):
                dir = CellDirection.UPWARDS if (i + j) % 2 == 0 else CellDirection.DOWNWARDS
                neighbors = [((i - 1) % cell_count_x, j), ((i + 1) % cell_count_x, j), (i, (j + (-dir.value)) % cell_count_y) ]
                cell = Cell(pygame.Vector2(i * (cell_width / 2 + cell_padding_left) + offset_x, j * (cell_height + cell_padding_top) + offset_y), 
                            neighbors,
                            dir,
                            pygame.Vector2(cell_width, cell_height))
                row.append(cell)
            self.cells.append(row)
    
    def count_alive_neighbors(self, cell: Cell):
        count = 0
        for i, j in cell.neighbors:
            count += self.cells[i][j].is_alive
        return count
    
    def step(self):
        new_cells = copy.deepcopy(self.cells)
        for i in range(len(self.cells)):
            for j in range(len(self.cells[0])):
                alive_count = self.count_alive_neighbors(self.cells[i][j])
                if not self.cells[i][j].is_alive and alive_count in self.rule.birth or self.cells[i][j].is_alive and alive_count in self.rule.survival:
                    new_cells[i][j].is_alive = True
                    continue
                new_cells[i][j].is_alive = False
        self.cells = new_cells
    
    def draw(self, surface):
        for row in self.cells:
            for cell in row:
                cell.draw(surface)
                
    
    def get_cell_by_coord(self, pos: pygame.Vector2):
        for row in self.cells:
            for cell in row:
                if cell.collidepoint(pos):
                    return cell
        return None
        

def main_loop(automaton: Automaton, screen: pygame.surface.Surface, sim_step_time: float):
    global paused
    global running
    global restarting
    dt = 0
    clock = pygame.time.Clock()
    sim_step_timer = sim_step_time
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if pygame.key.get_focused():
                if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                    paused = not paused 
                if event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
                    automaton.step()
                if event.type == pygame.MOUSEBUTTONUP:
                    cell = automaton.get_cell_by_coord(pygame.Vector2(pygame.mouse.get_pos()))
                    if cell:
                        cell.is_alive = not cell.is_alive
                if event.type == pygame.KEYUP and event.key == pygame.K_r:
                    restarting = True
                    running = False
        
        
        sim_step_timer -= dt / 1000
        if sim_step_timer <= 0:
            if not paused:
                automaton.step()
            sim_step_timer = sim_step_timer
        
        screen.fill("green")
        automaton.draw(screen)
        pygame.display.flip()

        dt = clock.tick(60)
        
running = True
paused = True
restarting = False
CELL_COUNT_X = 30
CELL_COUNT_Y = 60
SIM_STEP_TIME = 0
RULE = Rule(birth=[1], survival=[1, 1])

def int_to_bool_list(num: int, length: int):
    ret = [bool(int(x)) for x in list('{0:0b}'.format(num))]
    return [False] * (length - len(ret)) + ret

def apply_init_state(automaton: Automaton, init_state: list):
    for i in range(CELL_COUNT_X):
        for j in range(CELL_COUNT_Y):
            automaton.cells[i][j].is_alive = init_state[i + j * CELL_COUNT_Y]
            
def bool_list_to_int(lst):
    return int('0b' + ''.join(['1' if x else '0' for x in lst]), base=2)


def main():
    global paused
    global running
    global restarting
    
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    
    
    while True:
        running = True
        
        automaton = Automaton(RULE, CELL_COUNT_X, CELL_COUNT_Y, cell_width=30, cell_height=10, offset_x=15, offset_y=10)
        
        init_state = [False] * (CELL_COUNT_X * CELL_COUNT_Y)
        
        for i in range(int(CELL_COUNT_X / 2) - 3, int(CELL_COUNT_X / 2) + 3):
            for j in range(int(CELL_COUNT_Y / 2) - 3, int(CELL_COUNT_Y / 2) + 3):
                init_state[i + j * CELL_COUNT_Y] = bool(random.randint(0, 1))
                
        apply_init_state(automaton, init_state)
        print("init state:", bool_list_to_int(init_state))
        
        main_loop(automaton, screen, SIM_STEP_TIME)
        if not restarting:
            break
        restarting = False
        
    pygame.quit()

if __name__ == '__main__':    
    main()
