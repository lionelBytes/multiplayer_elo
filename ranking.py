""" was made referring to METIN'S MEDIA & MATH: HOW TO CALCULATE THE ELO-RATING """
from collections import defaultdict
from itertools import izip, tee

MATT = 'matt'
LIONEL = 'lionel'
AISTIS = 'aistis'
ALL_PLAYERS = {MATT, LIONEL, AISTIS}

SIGMA = 400.  # type: float

ratings = defaultdict(dict)
ratings[0] = {MATT: 1200, LIONEL: 1200, AISTIS: 1200}

new_result = (MATT, AISTIS, LIONEL)


def transform_rating(elo_score):
    """
    Compute the transformed (exponentiated) rating for each player or team
    :type elo_score: float
    :return: transformed ratings
    """
    return 10. ** (elo_score / SIGMA)


def calc_expected_score(p1_elo_score, p2_elo_score):
    """
    calculate expected results (win probability) for pair of players based on elo score
    :type p1_elo_score: float
    :type p2_elo_score: float
    :return: win probability of the two players
    :rtype: (float, float)
    """
    p1_rating = transform_rating(p1_elo_score)
    p2_rating = transform_rating(p2_elo_score)

    e1 = p1_rating / (p1_rating + p2_rating)
    e2 = p2_rating / (p1_rating + p2_rating)

    return (e1, e2)


def pairwise(iterable):
    """ s -> (s0,s1), (s1,s2), (s2, s3), ...
    recipe from the python itertools docs """
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


def gen_win_pairs_from_result(performances):
    """
    Following Tom Kerrigan's Simple Multiplayer Elo. In a mutliplayer game, the intermediate players,
    (players who did not come top or bottom) are treated to have played two games, one with the
    person right above him/her on the performance list, and another with the person right below him/her.
    A win is 1 point, a draw 0.5 points, and a loss 0. points.
    :param tuple[(str, float | int)] performances:
    :return: k-1 pairs of win results
    """

    perfs_descending = sorted(performances, key=lambda x: x[1], reverse=True)

    two_player_game_results = []

    # iterate through pairs, getting 2-player match results
    for (player1, points1), (player2, points2), in pairwise(perfs_descending):

        if points1 > points2:
            two_player_game_results.append((player1, player2, 1))
        elif points1 == points2:
            two_player_game_results.append((player1, player2, 0.5))
        else:
            raise ValueError("performances weren't in descending order! requires debug")

    return two_player_game_results








