"""For testing"""
import main
import pygame
pygame.init()
pygame.display.set_mode((100, 100))
import unittest


def create_board_from_text(text):
    board = main.Board(7, 7)
    for y, line in enumerate(text.split("\n")):
        line = line.strip()
        for x, char in enumerate(line):
            board.grid[x][y] = int(char)
    return board


class TestBoard(unittest.TestCase):

    def test_board_rotate(self):
        sample_boards_rotated = {
            board.replace(' ', '') : rotated.replace(' ', '')
            for board, rotated in [
                ("""0000000
                    0000000
                    0000000
                    0000000
                    0000000
                    0000000
                    1111111""",
                 """0000001
                    0000001
                    0000001
                    0000001
                    0000001
                    0000001
                    0000001"""),

                ("""0000000
                    0000000
                    0000001
                    0000002
                    0000001
                    0010101
                    1111111""",
                 """0012111
                    0000001
                    0000011
                    0000001
                    0000011
                    0000001
                    0000001"""),
            ]}

        for text_board in sample_boards_rotated:
            board = create_board_from_text(text_board)
            board.rotate()
            self.assertEqual(board.get_string(),
                             sample_boards_rotated[text_board])

    def test_make_pieces_fall(self):

        test_boards = {
            board.replace(' ', '') : result.replace(' ', '')
            for board, result in [
                ("""2020202
                    0202020
                    2020202
                    0202020
                    2020202
                    0202020
                    1111111""",
                 """0000000
                    0000000
                    0000000
                    2222222
                    2222222
                    2222222
                    1111111"""),

                ("""1221122
                    2112211
                    0000001
                    0000002
                    0000001
                    0010101
                    1111111""",
                 """0000002
                    0000001
                    0000001
                    0020102
                    1211221
                    2112111
                    1111111"""),
            ]}
        for text_board in test_boards:
            board = create_board_from_text(text_board)
            board.make_pieces_fall()
            self.assertEqual(board.get_string(), test_boards[text_board])

    def test_lowest_in_column(self):
        test_boards = {
            board.replace(' ', '') : result
            for board, result in [
                ("""0000000
                    0000200
                    0000200
                    0010200
                    0112200
                    0112200
                    1111100""",
                 (5, 3, 2, 3, 0, 6, 6)
                )]}
        for text_board in test_boards:
            board = create_board_from_text(text_board)
            for col, lowest in enumerate(test_boards[text_board]):
                self.assertEqual(board.lowest_in_column(col), lowest)
