"""Milestone 2: the independent-points model, written by you.

Every point is independent. Player A wins a point on their own serve with probability p_a,
and player B with probability p_b, for the whole match. Build each level from the one below,
as https://livetennisapi.com/tools/win-probability describes it: game, tie-break, set, match.

Conventions the tests rely on:

- Probabilities are floats between 0 and 1, never percentages.
- Every function returns player A's chance.
- In tiebreak() and set_win(), player A serves first. In a tie-break, the first point has one
  server, and after that each player serves two points in turn.
- final_tiebreak is the tie-break played at six games all in the final set: 7 or 10.

Run `pytest tests/test_model.py` to check your work. A test is skipped while its function
still raises NotImplementedError.
"""
from __future__ import annotations


def hold(p: float) -> float:
    """The chance the server holds a game, when they win each point on serve with chance p."""
    raise NotImplementedError('Milestone 2: write hold()')


def tiebreak(p_a: float, p_b: float, target: int = 7) -> float:
    """The chance A wins a tie-break to `target` points, by two clear, with A serving first."""
    raise NotImplementedError('Milestone 2: write tiebreak()')


def set_win(p_a: float, p_b: float, tiebreak_target: int = 7) -> float:
    """The chance A wins a set with a tie-break at six games all, with A serving first."""
    raise NotImplementedError('Milestone 2: write set_win()')


def match_win(p_a: float, p_b: float, best_of: int = 3, final_tiebreak: int = 7) -> float:
    """The chance A wins a match of `best_of` sets, from the first point."""
    raise NotImplementedError('Milestone 2: write match_win()')


def match_win_from(p_a: float, p_b: float, *, sets: tuple[int, int] = (0, 0),
                   games: tuple[int, int] = (0, 0), points: tuple[int, int] = (0, 0),
                   a_serving: bool = True, best_of: int = 3, final_tiebreak: int = 7) -> float:
    """The chance A wins the match from any score.

    sets: sets won by A and B. games: games won by A and B in the current set.
    points: points won by A and B in the current game, as counts (0, 1, 2, 3 for 0, 15, 30,
    40), or in the tie-break when games is (6, 6). After deuce keep counting: (4, 3) is
    advantage A, and (4, 4) is deuce again. a_serving: A serves the next point.
    From the first point, match_win_from(p_a, p_b) must equal match_win(p_a, p_b).
    """
    raise NotImplementedError('Milestone 2: write match_win_from()')
