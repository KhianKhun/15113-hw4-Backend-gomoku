from .board import BOARD_SIZE, EMPTY


def _count_dir(board, r, c, dr, dc, who) -> int:
    n = 0
    size = BOARD_SIZE
    rr, cc = r, c
    while 0 <= rr < size and 0 <= cc < size and board[rr][cc] == who:
        n += 1
        rr += dr
        cc += dc
    return n


def check_winner(board: list[list[int]], k: int = 5) -> int | None:
    """
    Returns:
      1 if player wins
      2 if AI wins
      None if no winner yet
    """
    size = BOARD_SIZE
    dirs = [(1, 0), (0, 1), (1, 1), (1, -1)]

    for r in range(size):
        for c in range(size):
            who = board[r][c]
            if who == EMPTY:
                continue
            for dr, dc in dirs:
                # count in both directions, minus 1 to avoid double-counting the origin
                total = _count_dir(board, r, c, dr, dc, who) + _count_dir(board, r, c, -dr, -dc, who) - 1
                if total >= k:
                    return who
    return None


def is_draw(board: list[list[int]]) -> bool:
    return all(cell != EMPTY for row in board for cell in row)
