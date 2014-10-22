#!/usr/bin/env python2
from __future__ import print_function
import pygame
from pygame.locals import *
import sys
import random
import copy

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480

BOARD_WIDTH = 7
BOARD_HEIGHT = 7

ROTATE_TIME = 3

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (250, 0, 0)
GREEN = (0, 255, 0)
BLUE = (50, 50, 155)
YELLOW = (220, 220, 0)
DARK_YELLOW = (200, 200, 0)
DARK_GREEN = (0, 200, 0)

VICTORY_LINE_COLOR = DARK_GREEN
VICTORY_LINE_SIZE = 5

PLAYER_COLORS = [0, BLACK, RED]

BG_COLOR = BLUE

MAX_FPS = 30


class AI:
    def __init__(self, team):
        self.team = team

    def get_move(self, board):
        """Returns the column # to drop the piece in."""

        board = copy.deepcopy(board)

        # see if any team could win by dropping a piece into a column
        line_completions = []
        for x in range(board.width):
            y = board.lowest_in_column(x)
            if y != -1:
                board.drop_piece(x, self.team)
                board.grid[x][y] = self.team
                line_completions.append(list(board.check_victory()))
                board.grid[x][y] = 1
                line_completions[-1].extend(list(board.check_victory()))
                board.grid[x][y] = 0


        # first of all, if we can make a 4-in-a-row, do it!
        for x, c in enumerate(line_completions):
            if self.team in c:
                return x

        # blocking an opponent's 4-in-a-row is the 2nd highest piority
        for x, c in enumerate(line_completions):
            if c:
                return x

        # otherwise, just go in a random spot
        return random.randint(0, board.width - 1)


class Board:
    """Two-dimensional Connect 4 board."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[0 for y in range(BOARD_HEIGHT)]
                     for x in range(BOARD_WIDTH)]
        board_size = min(WINDOW_WIDTH, WINDOW_HEIGHT) * 14 / 16
        x = (WINDOW_WIDTH - board_size) / 2
        y = (WINDOW_HEIGHT - board_size) / 2
        self.rect = Rect((x, y), (board_size, board_size))
        self.image = pygame.Surface(
            (board_size, board_size)).convert()
        self.image.set_colorkey(BG_COLOR)

    def rotate(self):
        old_grid = self.grid
        self.grid = [[old_grid[self.height - y - 1][x]
                      for y in range(BOARD_HEIGHT)]
                     for x in range(BOARD_WIDTH)]

    def make_pieces_fall(self):
        for y in range(self.height - 2, -1, -1):
            for x in range(self.width):
                cy = y
                while cy < self.height - 1 and not self.grid[x][cy + 1] \
                        and self.grid[x][cy]:
                    self.grid[x][cy + 1] = self.grid[x][cy]
                    self.grid[x][cy] = 0
                    cy += 1

    def iterate_pieces_falling(self):
        """Yields the position and destination of each piece falling"""
        for y in range(self.height - 2, -1, -1):
            for x in range(self.width):
                cy = y
                while cy < self.height - 1 and not self.grid[x][cy + 1] \
                        and self.grid[x][cy]:
                    self.grid[x][cy + 1] = self.grid[x][cy]
                    self.grid[x][cy] = 0
                    cy += 1
                if cy != y:
                    yield ((x, y), (x, cy))

    def print_text_board(self):
        printboard = [''] * len(self.grid[0])
        for x in range(self.width):
            for y in range(self.height):
                printboard[y] += str(self.grid[x][y])
        for row in printboard:
            print(row)

    def lowest_in_column(self, column):
        """Returns the y-coordinate for the lowest empty position in the given
        column.
        Returns -1 if the column is full"""
        for y in range(self.height - 1, -1, -1):
            if self.grid[column][y] == 0:
                return y
        return -1

    def drop_piece(self, column, player):
        y = self.lowest_in_column(column)
        self.grid[column][y] = player

    def column_blocked(self, column):
        if self.grid[column][0] != 0:
            return True
        return False

    def get_column_relative_x(self, column_number):
        radius = self.get_circle_radius()
        return column_number * self.rect.width / BOARD_WIDTH + radius + 4

    def get_row_relative_y(self, row_number):
        radius = self.get_circle_radius()
        return row_number * self.rect.height / BOARD_HEIGHT + radius + 2

    def get_circle_radius(self):
        return self.rect.height / BOARD_HEIGHT / 2 - 5

    def clear_image(self):
        self.image.fill(YELLOW)
        radius = self.get_circle_radius()
        for x in range(self.width):
            for y in range(self.height):
                pygame.draw.circle(
                    self.image, BG_COLOR, (
                        self.get_column_relative_x(x),
                        self.get_row_relative_y(y)),
                    radius)

    def update_image(self):
        self.image.fill(YELLOW)
        radius = self.get_circle_radius()
        for x in range(self.width):
            for y in range(self.height):
                if self.grid[x][y] == 0:  # empty spot
                    color = BG_COLOR
                elif self.grid[x][y] == 1:
                    color = BLACK
                elif self.grid[x][y] == 2:
                    color = RED
                pygame.draw.circle(self.image, color, (
                    self.get_column_relative_x(x),
                    self.get_row_relative_y(y)),
                    radius)

    def check_victory(self):
        """
        Yields (winning team, list of positions in 4-in-a-row)
        list of positions is in the form [(x1, y1), (x2, y2), ...]
        """
        # for each position in the grid, checks lines extending from it
        # pointing right, down, down-right, and down-left
        for x in range(self.width):
            for y in range(self.height):
                # ignore positions that are empty
                if self.grid[x][y] == 0:
                    continue

                # based on where the position is, determine which lines can be
                # drawn that fit inside the grid
                lines = []
                if x < self.width - 3:
                    # check horizontal line
                    lines.append([(x1, y) for x1 in range(x, x + 4)])
                if y < self.height - 3:
                    # check vertical line
                    lines.append([(x, y1) for y1 in range(y, y + 4)])
                if x < self.width - 3 and y < self.height - 3:
                    # check diagonal \ line
                    lines.append([(x + d, y + d) for d in range(4)])
                if x >= 3 and y < self.height - 3:
                    # check diagonal / line
                    lines.append([(x - d, y + d) for d in range(4)])

                # go through each line, and, if all pieces in the line match,
                # yield the team who won the line and the line itself
                for line in lines:
                    match = True
                    for (x1, y1) in line[1:]:
                        if self.grid[x][y] != self.grid[x1][y1]:
                            match = False
                            break
                    if match:
                        yield (self.grid[x][y], line)


class Game:
    """Singleton that manages input, rendering, and game logic."""

    def __init__(self, screen, ai=True):
        self.screen = screen
        if ai:
            self.ai = AI(2)
        else:
            self.ai = None
        self.timer = pygame.time.Clock()
        self.board = Board(BOARD_WIDTH, BOARD_HEIGHT)
        self.bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.bg.convert()
        self.bg.fill(BG_COLOR)
        self.board.update_image()
        self.num_pieces_dropped = 0
        self.winner = None
        self.player_points = [0, 0, 0]
        self.victory_lines = []
        self.font = pygame.font.Font(None, 50)

        # make a table image and fill it with squares
        self.table_image = pygame.surface.Surface((1000, 1000))
        self.table_image.fill((0, 128, 200))
        for n in range(100):
            c = random.randint(64, 127)
            x = random.randint(0, 900)
            y = random.randint(0, 900)
            pygame.draw.rect(
                self.table_image, (0, c, c * 2), (x, y, 100, 100), 0)

        self.column_selected = 0

        self.active_player = 1  # player 1 and 2 alternate turns
        draw_circle_window_icon(BLACK)

    def run(self):
        """Runs the game.
        Limits FPS, handles input, and renders, in a loop."""
        while True:
            self.timer.tick(MAX_FPS)
            self.handle_input()
            self.render_all()

    def get_column_clicked(self, position):
        """Takes a mouse position and returns the column of the board that it
        was in."""
        x = position[0]
        width_per_row = self.board.rect.width / BOARD_WIDTH
        x_relative_to_board = x - self.board.rect.left

        return int(round(x_relative_to_board) / width_per_row - 1/2)

    def animate_circle_movement(self, x1, y1, x2, y2, num_seconds=1,
                                color=BLACK):
        """Animates a circle smoothly moving from one position to another."""
        g = self.iterate_circle_movement(x1, y1, x2, y2, num_seconds, color)
        for d in range(int(MAX_FPS * num_seconds)):
            pygame.event.get()
            self.render_background()
            g.next()
            self.render_board()
            pygame.display.flip()
            self.timer.tick(MAX_FPS)

    def iterate_circle_movement(self, x1, y1, x2, y2, num_seconds=1,
                                color=BLACK):
        """Animates a circle smoothly moving from one position to another, one
        iteration at a time."""
        # to be called once per frame
        for d in range(int(MAX_FPS * num_seconds)):
            x = x1 + (x2 - x1) * d / int(MAX_FPS * num_seconds)
            y = y1 + (y2 - y1) * d / int(MAX_FPS * num_seconds)
            pygame.draw.circle(self.screen, color,
                               (x, y), self.board.get_circle_radius())
            yield

    def animate_drop_piece(self):
        """Animates a piece in the selected column falling to the lowest empty
        board position in that column."""
        starting_y = self.board.rect.top - 4
        x = self.board.rect.left + \
            self.board.get_column_relative_x(self.column_selected)
        end_y = self.board.rect.top + \
            self.board.get_row_relative_y(
                self.board.lowest_in_column(self.column_selected))

        time = (end_y - starting_y) / self.board.get_circle_radius() / 50.0
        self.animate_circle_movement(x, starting_y, x, end_y, time,
                                     PLAYER_COLORS[self.active_player])

    def do_ai_turn(self):
        """Gets a move from the AI, and drops its piece."""
        self.column_selected = self.ai.get_move(self.board)
        self.drop_piece()

    def drop_piece(self):
        """Drops a game piece for the active team into the currently-selected
        column, animates it, handles game logic, and immediately does the AI
        turn if needed."""
        if not self.board.column_blocked(self.column_selected):
            self.animate_drop_piece()
            # drop piece
            self.board.drop_piece(
                self.column_selected, self.active_player)
            self.board.update_image()

            # toggle players 1 and 2
            if self.active_player == 1:
                self.active_player = 2
            else:
                self.active_player = 1

            draw_circle_window_icon(
                PLAYER_COLORS[self.active_player])
            self.num_pieces_dropped += 1
            if self.num_pieces_dropped % ROTATE_TIME == 0:
                self.rotate()

            # player could move mouse during animations
            self.update_column_selected()

            self.handle_victory()

            if not self.winner and self.active_player == 2 and self.ai:
                self.do_ai_turn()

    def handle_victory(self):
        """Checks for victory, selects the winner, and draws victory lines."""
        v = list(self.board.check_victory())
        if v:
            for (winner, positions) in v:
                pos1 = self.board_to_screen_pos(positions[0])
                pos2 = self.board_to_screen_pos(positions[-1])
                self.victory_lines.append((pos1, pos2))
                self.player_points[winner] += 1
            if self.player_points[1] > self.player_points[2]:
                winning_player = 1
            elif self.player_points[1] < self.player_points[2]:
                winning_player = 2
            else:
                # TIE...
                winning_player = 3

            self.slowly_draw_lines(self.victory_lines)

            self.winner = winning_player

    def slowly_draw_lines(self, lines):
        """Slowly draws multiple lines at the same time."""
        generators = []
        for (p1, p2) in lines:
            generators.append(self.iterate_slowly_draw_line(p1, p2))
        for d in range(MAX_FPS):
            pygame.event.get()
            self.render_background()
            self.render_board()
            for generator in generators:
                generator.next()
            pygame.display.flip()
            self.timer.tick(MAX_FPS)

    def slowly_draw_line(self, p1, p2):
        """Slowly draws a line."""
        (x1, y1) = p1
        (x2, y2) = p2
        generator = self.iterate_slowly_draw_line(p1, p2)
        for d in range(MAX_FPS):
            pygame.event.get()
            self.render_background()
            self.render_board()
            generator.next()
            pygame.display.flip()
            self.timer.tick(MAX_FPS)

    def iterate_slowly_draw_line(self, p1, p2):
        """Slowly draws a line, one iteration at a time."""
        (x1, y1) = p1
        (x2, y2) = p2
        for d in range(MAX_FPS):
            x = x1 + (x2 - x1) * d / MAX_FPS
            y = y1 + (y2 - y1) * d / MAX_FPS
            pygame.draw.line(self.screen, VICTORY_LINE_COLOR, (x1, y1), (x, y),
                             VICTORY_LINE_SIZE)
            yield

    def rotate(self):
        """Rotates the board and makes the pieces fall. Each part is
        animated as well."""
        centerx = self.board.rect.centerx
        centery = self.board.rect.centery
        for degree in range(1, 90, 10):
            pygame.event.get()
            self.render_background()
            image = pygame.transform.rotate(self.board.image, degree)
            width, height = image.get_size()
            self.screen.blit(pygame.transform.rotate(self.board.image, degree),
                             (centerx - width / 2, centery - height / 2))
            pygame.display.flip()
            self.timer.tick(MAX_FPS)
        self.board.rotate()
        self.board.clear_image()
        positions = self.board.iterate_pieces_falling()
        generators = []
        for (pos, pos2) in positions:
            x1, y1 = self.board_to_screen_pos(pos)
            x2, y2 = self.board_to_screen_pos(pos2)
            (x, y) = pos
            player = self.board.grid[x][y]
            color = PLAYER_COLORS[player]
            generators.append(
                self.iterate_circle_movement(x1, y1, x2, y2, .1, color))
        while generators:
            pygame.event.get()
            self.render_background()
            for g in generators:
                try:
                    g.next()
                except StopIteration:
                    generators.remove(g)
                    self.board.update_image()
            self.render_board()
            pygame.display.flip()
            self.timer.tick(MAX_FPS)
        self.board.update_image()

    def update_column_selected(self):
        """Updates the selected column based on the current mouse position."""
        pos = pygame.mouse.get_pos()
        self.column_selected = self.get_column_clicked(pos)
        if self.column_selected < 0:
            self.column_selected = 0
        elif self.column_selected > BOARD_WIDTH - 1:
            self.column_selected = BOARD_WIDTH - 1

    def handle_input(self):
        for e in pygame.event.get():
            if e.type == MOUSEMOTION:
                self.update_column_selected()
            elif e.type == MOUSEBUTTONDOWN:
                if e.button == 1 and not self.winner:
                    # MOUSE CLICK
                    self.drop_piece()
            elif e.type == KEYDOWN:
                if e.key == K_SPACE:
                    # restart game
                    self.__init__(self.screen)
                elif e.key == K_LEFT:
                    self.column_selected -= 1
                    if self.column_selected < 0:
                        self.column_selected = 0
                elif e.key == K_RIGHT:
                    self.column_selected += 1
                    if self.column_selected > BOARD_WIDTH - 1:
                        self.column_selected = BOARD_WIDTH - 1
                elif e.key == K_RETURN:
                    if not self.board.column_blocked(self.column_selected):
                        if not self.winner:
                            self.drop_piece()
                elif e.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            elif e.type == QUIT:
                pygame.quit()
                sys.exit()

    def render_background(self):
        """Renders the background, including a mode 7 effect for the table."""
        # draw background
        self.screen.blit(self.bg, (0, 0))
        # draw table, mode 7 effect-ish
        stretch_factor = 75.0
        for y in range(300, 600):
            # Take a line from the original & stretch it.
            img_y = (y + 0 - 300) * 2
            line = pygame.surface.Surface((800, 1))
            line.blit(self.table_image, (0, 0), (0, img_y, 800, 1))
            w = 800 * (1.0 + ((y - 300) / stretch_factor))
            x = -(w - 800) / 2  # Draw wide line left of screen's edge
            line = pygame.transform.scale(line, (int(w), 1))
            self.screen.blit(line, (x, y))

    def render_board(self):
        """Draws the board."""
        self.screen.blit(
            self.board.image, (self.board.rect.x, self.board.rect.y))

    def draw_current_piece(self):
        """Draws a piece over the currently-selected column."""
        radius = self.board.get_circle_radius()
        pygame.draw.circle(self.screen, PLAYER_COLORS[self.active_player], (
            self.board.rect.left +
            self.board.get_column_relative_x(self.column_selected),
            self.board.rect.top - radius - 2),
            radius)

    def draw_victory_lines(self):
        """Draws lines over 4-in-a-rows."""
        for (p1, p2) in self.victory_lines:
            pygame.draw.line(
                self.screen, VICTORY_LINE_COLOR, p1, p2, VICTORY_LINE_SIZE)

    def draw_moves_until_rotate(self):
        """Draws the number of moves until the next board rotation to the
        top-left of the screen."""
        moves = ROTATE_TIME - self.num_pieces_dropped % ROTATE_TIME
        if moves == 0:
            moves = ROTATE_TIME
        draw_text(str(moves), self.font, self.screen, 10, 10)

    def render_all(self):
        """Renders everything and updates the display."""
        self.render_background()
        self.render_board()
        if not self.winner:
            self.draw_current_piece()
            self.draw_moves_until_rotate()
        else:
            self.draw_victory_lines()
        pygame.display.flip()

    def board_to_screen_pos(self, pos):
        """Converts the given position in board coordinates into screen
        coordinates."""
        (x, y) = pos
        return (self.board.rect.left + self.board.get_column_relative_x(x),
                self.board.rect.top + self.board.get_row_relative_y(y))


def draw_text(text, font, surface, x, y, color=WHITE, background=None,
              position="topleft"):
    """Draws some text to the surface."""
    textobj = font.render(text, 1, color)
    textrect = textobj.get_rect()
    if position == 'center':
        textrect.center = (x, y)
    elif position == 'bottomright':
        textrect.bottomright = (x, y)
    elif position == 'topleft':
        textrect.topleft = (x, y)
    elif position == 'topright':
        textrect.topright = (x, y)
    if background:
        pygame.draw.rect(screen, background, textrect.inflate(2, 2))
    surface.blit(textobj, textrect)
    return textrect  # for knowing where to redraw the background


def draw_circle_window_icon(color):
    """Draws a circle in the given color and sets it as the window icon."""
    icon = pygame.Surface((32, 32))
    icon.convert()
    icon.fill(BG_COLOR)
    icon.set_colorkey(BG_COLOR)
    pygame.draw.circle(icon, color, (16, 16), 16)
    pygame.display.set_icon(icon)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Grav-Twist Connect 4")
    draw_circle_window_icon(YELLOW)
    game = Game(screen)
    game.run()


if __name__ == '__main__':
    main()
