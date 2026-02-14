BOARD_SIZE = 15

EMPTY = 0
PLAYER = 1  # human
AI = 2      # AI


def empty_board(size: int = BOARD_SIZE) -> list[list[int]]:
    return [[EMPTY for _ in range(size)] for _ in range(size)]


def in_bounds(row: int, col: int, size: int = BOARD_SIZE) -> bool:
    return 0 <= row < size and 0 <= col < size


def available_moves(board: list[list[int]]) -> list[tuple[int, int]]:
    moves: list[tuple[int, int]] = []
    for r in range(len(board)):
        for c in range(len(board[r])):
            if board[r][c] == EMPTY:
                moves.append((r, c))
    return moves


def apply_move(board: list[list[int]], row: int, col: int, who: int) -> None:
    board[row][col] = who
