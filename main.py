import pygame
from enum import Enum
from dataclasses import dataclass
from typing import List
import copy
import random
import pygame.gfxdraw
from abc import ABC, abstractmethod

class CellDirection(Enum):
    UPWARDS = -1
    DOWNWARDS = 1

class Rule(ABC):
    @abstractmethod
    def get_new_state(self, automaton, cell) -> bool:
        pass

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
        pygame.gfxdraw.filled_trigon(surface, 
                                    int(self.points[0].x), int(self.points[0].y), 
                                    int(self.points[1].x), int(self.points[1].y),  
                                    int(self.points[2].x), int(self.points[2].y), 
                                    (70, 70, 70) if self.is_alive else (255, 255, 255))
        return pygame.gfxdraw.aatrigon(surface, 
                                    int(self.points[0].x), int(self.points[0].y), 
                                    int(self.points[1].x), int(self.points[1].y),  
                                    int(self.points[2].x), int(self.points[2].y), 
                                    (70, 70, 70) if self.is_alive else (255, 255, 255))
    
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
        
        self.turn = 0
        self.rule = rule
        self.cells: List[List[Cell]] = []
        self.cell_count_x = cell_count_x
        self.cell_count_y = cell_count_y
        
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
    
    def step(self):
        new_cells = [[copy.copy(cell) for cell in row] for row in self.cells]
        for i in range(len(self.cells)):
            for j in range(len(self.cells[0])):
                new_cells[i][j].is_alive = self.rule.get_new_state(self, self.cells[i][j])
        self.cells = new_cells
        self.turn += 1
    
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

def int_to_bool_list(num: int, length: int):
    ret = [bool(int(x)) for x in list('{0:0b}'.format(num))]
    return [False] * (length - len(ret)) + ret

def bool_list_to_int(lst):
    return int('0b' + ''.join(['1' if x else '0' for x in lst]), base=2)
        
class WolframRule(Rule):
    def __init__(self, rule_num: int):
        self.rule_num = rule_num
    
    def get_new_state(self, automaton: Automaton, cell: Cell) -> bool:
        return int_to_bool_list(self.rule_num, 2**len(cell.neighbors))[-bool_list_to_int([automaton.cells[i][j].is_alive for i, j in cell.neighbors])]
    
    def __str__(self) -> str:
        return str(self.rule_num)

class LifelikeRule(Rule):
    def __init__(self, birth: set, survival: set) -> None:
        self.birth = birth
        self.survival = survival
    
    def get_new_state(self, automaton: Automaton, cell: Cell) -> bool:
        alive_count = 0
        for i, j in cell.neighbors:
            alive_count += automaton.cells[i][j].is_alive
            
        if not cell.is_alive and alive_count in self.birth or cell.is_alive and alive_count in self.survival:
            return True
        return False
        
    def __str__(self):
        return f"B{''.join(str(num) for num in self.birth)}/S{''.join(str(num) for num in self.survival)}"

def main_loop(automaton: Automaton, screen: pygame.surface.Surface, sim_step_time: float):
    global paused
    global running
    global restarting
    global show_text
    dt = 0
    clock = pygame.time.Clock()
    sim_step_timer = sim_step_time
    
    font = pygame.font.SysFont("monospace", 30, True)
    text = [font.render('Paused', True, 'black'),
            font.render('t = 0', True, 'black'),
            font.render(f'Rule: {automaton.rule}', True, 'black'),
            font.render('R - restart', True, 'black'), 
            font.render('SPACE - pause/resume', True, 'black'), 
            font.render('ENTER - next turn', True, 'black'),
            font.render('H - show/hide this text', True, 'black')]
    text_pos = (20, 20)
    
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
                if event.type == pygame.KEYUP and event.key == pygame.K_h:
                    show_text = not show_text
        
        
        sim_step_timer -= dt / 1000
        if sim_step_timer <= 0:
            if not paused:
                automaton.step()
            sim_step_timer = sim_step_time
        
        screen.fill((30, 30, 30))
        automaton.draw(screen)
        
        if show_text:
            text[0] = font.render("Paused" if paused else "Simulating", True, 'Black')
            text[1] = font.render(f't = {automaton.turn}', True, 'Black')
            
            pygame.gfxdraw.box(screen, 
                                pygame.Rect(text_pos[0], text_pos[1], max(text, key=lambda line: line.get_width()).get_width(), text[0].get_height() * len(text)), 
                                (70, 70, 70, 200))
            for i in range(len(text)):
                screen.blit(text[i], (text_pos[0], text_pos[1] + i * text[0].get_height()))
        
        
        pygame.display.flip()

        dt = clock.tick(60)
        

def apply_init_state(automaton: Automaton, init_state: list):
    for i in range(automaton.cell_count_x):
        for j in range(automaton.cell_count_y):
            automaton.cells[i][j].is_alive = init_state[i + j * automaton.cell_count_x]

def gen_random_state(filling_range_halved: tuple, filling_center: tuple, whole_range: tuple):
    init_state = [False] * (whole_range[0] * whole_range[1])
    for i in range(filling_center[0] - filling_range_halved[0], filling_center[0] + filling_range_halved[0]):
        for j in range(filling_center[1] - filling_range_halved[1], filling_center[1] + filling_range_halved[1]):
            init_state[i + j * whole_range[0]] = bool(random.randint(0, 1))
    return init_state

running = True
paused = True
restarting = False
show_text = True



def main():
    global paused
    global running
    global restarting
    
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    
    
    while True:
        running = True
        
        ############################## parameters (maybe you want to change these) #####################
        SIM_STEP_TIME = 0.05
        CELL_COUNT_X = 100
        CELL_COUNT_Y = 60
        PADDING = 3
        # rule = LifelikeRule(birth={1}, survival={2})
        # rule=LifelikeRule(  {random.randint(0, 3) for _ in range(random.randint(0, 3))}, 
        #                     {random.randint(0, 3) for _ in range(random.randint(0, 3))})
        rule=WolframRule(random.randint(0, 2**(2**3)))
        # rule = WolframRule(255)
        init_state = gen_random_state(  filling_center=(int(CELL_COUNT_X/ 2), int(CELL_COUNT_Y / 2)), 
                                        filling_range_halved=(int(CELL_COUNT_X / 2), int(CELL_COUNT_Y / 2)),
                                        whole_range=(CELL_COUNT_X, CELL_COUNT_Y)
                                        )
        # init_state = int_to_bool_list(0, CELL_COUNT_X * CELL_COUNT_Y)
        ##################################################################################################
        
        CELL_WIDTH = 2 * (screen.get_width()) / CELL_COUNT_X - PADDING * 2
        CELL_HEIGHT = (screen.get_height()) / CELL_COUNT_Y - PADDING
        
        automaton = Automaton( 
                                rule=rule, 
                                cell_count_x=CELL_COUNT_X, 
                                cell_count_y=CELL_COUNT_Y, 
                                cell_width=CELL_WIDTH, 
                                cell_height=CELL_HEIGHT,
                                offset_x=CELL_WIDTH / 3,
                                offset_y=CELL_HEIGHT / 2,
                                cell_padding_left=PADDING,
                                cell_padding_top=PADDING          
                            )  
        
        apply_init_state(automaton, init_state)
        print( "cell_count_x:", automaton.cell_count_x, 
                "cell_count_y:", automaton.cell_count_y,
                "rule:", automaton.rule)
        print(  "init_state:", bool_list_to_int(init_state))
        main_loop(automaton, screen, SIM_STEP_TIME)
        if not restarting:
            break
        restarting = False
        
    pygame.quit()

if __name__ == '__main__':    
    main()
