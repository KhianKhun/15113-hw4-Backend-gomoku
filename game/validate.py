from .board import BOARD_SIZE, EMPTY, in_bounds


def parse_board(payload_board) -> list[list[int]]:
    if not isinstance(payload_board, list) or len(payload_board) != BOARD_SIZE:
        raise ValueError("board must be a 15x15 array")

    board: list[list[int]] = []
    for row in payload_board:
        if not isinstance(row, list) or len(row) != BOARD_SIZE:
            raise ValueError("board must be a 15x15 array")
        new_row: list[int] = []
        for cell in row:
            if not isinstance(cell, int) or cell not in (0, 1, 2):
                raise ValueError("board cells must be integers: 0, 1, or 2")
            new_row.append(cell)
        board.append(new_row)

    return board


def validate_move(board: list[list[int]], row: int, col: int) -> None:
    if not isinstance(row, int) or not isinstance(col, int):
        raise ValueError("row and col must be integers")
    if not in_bounds(row, col, BOARD_SIZE):
        raise ValueError("move out of bounds")
    if board[row][col] != EMPTY:
        raise ValueError("cell is not empty")
