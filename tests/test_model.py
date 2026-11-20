"""Checks for milestone 2. Each test skips while its function still raises NotImplementedError.

The numbers come from https://livetennisapi.com/tools/win-probability with its default inputs:
player A wins 64% of points on serve and player B 62%. The page rounds to one decimal place,
so a check passes when your value rounds to the page's figure.
"""
from __future__ import annotations

import math

import pytest

from capstone import model

A, B = 0.64, 0.62


def call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except NotImplementedError as exc:
        pytest.skip(str(exc))


def close_to_page(value: float, page_percent: float) -> bool:
    """True when `value` shows as `page_percent` on the page (one decimal place)."""
    return abs(value * 100 - page_percent) <= 0.05 + 1e-9


@pytest.mark.parametrize(('p', 'page'), [(A, 81.3), (B, 77.6)])
def test_hold_matches_the_calculator(p, page):
    assert close_to_page(call(model.hold, p), page)


def test_hold_is_even_at_half_and_follows_the_formula_the_page_prints():
    assert math.isclose(call(model.hold, 0.5), 0.5, abs_tol=1e-12)
    for p in (0.3, 0.55, 0.7, 0.9):
        q = 1 - p
        formula = p ** 4 * (15 - 4 * p - 10 * p ** 2 / (1 - 2 * p * q))
        assert math.isclose(call(model.hold, p), formula, rel_tol=1e-9)


@pytest.mark.parametrize(('target', 'page'), [(7, 53.3), (10, 53.9)])
def test_tiebreak_matches_the_calculator(target, page):
    assert close_to_page(call(model.tiebreak, A, B, target), page)


def test_tiebreak_is_even_between_equal_servers():
    for target in (7, 10):
        assert math.isclose(call(model.tiebreak, 0.6, 0.6, target), 0.5, abs_tol=1e-12)


def test_set_matches_the_calculator():
    assert close_to_page(call(model.set_win, A, B), 56.7)


def test_set_does_not_depend_on_who_serves_first():
    """Newton and Keller (2005): swapping the players gives the other side of the same set."""
    for a, b in ((0.64, 0.62), (0.7, 0.55), (0.58, 0.66)):
        assert math.isclose(call(model.set_win, a, b) + call(model.set_win, b, a), 1,
                            abs_tol=1e-12)


@pytest.mark.parametrize(('best_of', 'page'), [(3, 59.9), (5, 62.4)])
def test_match_matches_the_calculator(best_of, page):
    assert close_to_page(call(model.match_win, A, B, best_of=best_of), page)


def test_match_from_the_first_point_is_the_whole_match():
    for best_of in (3, 5):
        for final in (7, 10):
            whole = call(model.match_win, A, B, best_of=best_of, final_tiebreak=final)
            start = call(model.match_win_from, A, B, best_of=best_of, final_tiebreak=final)
            assert math.isclose(start, whole, abs_tol=1e-12)


def test_match_from_one_set_all_is_the_final_set():
    final_set = call(model.set_win, A, B, tiebreak_target=10)
    from_one_all = call(model.match_win_from, A, B, sets=(1, 1), final_tiebreak=10)
    assert math.isclose(from_one_all, final_set, abs_tol=1e-12)


def test_match_from_six_all_in_the_final_set_is_the_tiebreak():
    tb = call(model.tiebreak, A, B, 10)
    assert math.isclose(call(model.match_win_from, A, B, sets=(1, 1), games=(6, 6),
                             final_tiebreak=10), tb, abs_tol=1e-12)


def test_match_from_a_set_up_uses_the_next_sets():
    s = call(model.set_win, A, B)
    expected = s + (1 - s) * s
    assert math.isclose(call(model.match_win_from, A, B, sets=(1, 0)), expected, abs_tol=1e-12)


def test_each_point_moves_the_chance_the_right_way():
    """At 4-4 in the final set with A serving, the next point is p_a for A and 1 - p_a for B."""
    here = dict(sets=(1, 1), games=(4, 4))
    now = call(model.match_win_from, A, B, **here, points=(1, 1))
    won = call(model.match_win_from, A, B, **here, points=(2, 1))
    lost = call(model.match_win_from, A, B, **here, points=(1, 2))
    assert lost < now < won
    assert math.isclose(now, A * won + (1 - A) * lost, abs_tol=1e-12)


def test_deuce_and_advantage_count_on():
    here = dict(sets=(1, 1), games=(4, 4))
    deuce = call(model.match_win_from, A, B, **here, points=(3, 3))
    assert math.isclose(deuce, call(model.match_win_from, A, B, **here, points=(5, 5)),
                        abs_tol=1e-12)
    adv = call(model.match_win_from, A, B, **here, points=(4, 3))
    assert adv > deuce


def test_match_from_a_won_match_is_certain():
    assert math.isclose(call(model.match_win_from, A, B, sets=(2, 0)), 1, abs_tol=1e-12)
    assert math.isclose(call(model.match_win_from, A, B, sets=(1, 3), best_of=5), 0,
                        abs_tol=1e-12)


@pytest.mark.parametrize('score', [
    dict(sets=(1, 1), games=(4, 5), points=(0, 0)),
    dict(sets=(0, 1), games=(2, 3), points=(1, 3)),
    dict(sets=(1, 0), games=(4, 4), points=(0, 3)),
    dict(sets=(1, 1), games=(6, 6), points=(5, 2)),
    dict(sets=(1, 1), games=(6, 6), points=(8, 9)),
], ids=str)
def test_swapping_the_players_mirrors_the_chance(score):
    """From any score with B serving, A's chance is 1 minus B's chance with the players, the
    score and the serve swapped. A model that ignores a_serving, or reads the points the wrong
    way round when B serves, fails this."""
    flip = {k: v[::-1] for k, v in score.items()}
    b_serving = call(model.match_win_from, A, B, **score, a_serving=False, final_tiebreak=10)
    mirrored = call(model.match_win_from, B, A, **flip, a_serving=True, final_tiebreak=10)
    assert math.isclose(b_serving, 1 - mirrored, abs_tol=1e-12)


def _next_server_in_tiebreak(points: tuple[int, int], a_serving: bool) -> bool:
    """Who serves the point after this one: one point for the first server, then two each."""
    return (not a_serving) if sum(points) % 2 == 0 else a_serving


@pytest.mark.parametrize('points', [(0, 0), (3, 2), (5, 1), (5, 2), (8, 8)], ids=str)
@pytest.mark.parametrize('a_serving', [True, False])
def test_each_tiebreak_point_moves_the_chance_the_right_way(points, a_serving):
    """Inside the final-set tie-break to 10, the chance now is the chance of winning the
    point times the chance after it, plus the same for losing it."""
    here = dict(sets=(1, 1), games=(6, 6), final_tiebreak=10)
    nxt = _next_server_in_tiebreak(points, a_serving)
    now = call(model.match_win_from, A, B, **here, points=points, a_serving=a_serving)
    won = call(model.match_win_from, A, B, **here, points=(points[0] + 1, points[1]),
               a_serving=nxt)
    lost = call(model.match_win_from, A, B, **here, points=(points[0], points[1] + 1),
                a_serving=nxt)
    w = A if a_serving else 1 - B
    assert math.isclose(now, w * won + (1 - w) * lost, abs_tol=1e-12)
    assert lost < now < won


def test_a_ten_point_tiebreak_is_played_in_the_final_set_only():
    s7 = call(model.set_win, A, B, tiebreak_target=7)
    s10 = call(model.set_win, A, B, tiebreak_target=10)
    expected = s7 * s7 + 2 * s7 * (1 - s7) * s10
    assert math.isclose(call(model.match_win, A, B, best_of=3, final_tiebreak=10), expected,
                        abs_tol=1e-12)
