import itertools
from unittest import TestCase

import ranking

if False:
    import collections

# example players
ALICE = 'alice'
BOB = 'bob'
CEVIN = 'cevin'
DOGE = 'doge'

def flatten(list_of_lists):
    """
    flatten function from itertools package - faster than list interpretation
    :type list_of_lists: collections.Iterable[collections.Iterable]
    :return:  chain.from_iterable(['ABC', 'DEF']) --> A B C D E F
    """
    return itertools.chain.from_iterable(list_of_lists)

class TestRanking(TestCase):

    initial_elos = {ALICE: 1350, BOB: 1300, CEVIN: 1200, DOGE: 1600}
    result_2_players = ((ALICE, 404), (BOB, 200))
    result_4_players = ((ALICE, 404), (BOB, 200), (CEVIN, -100), (DOGE, 1000))

    def test_calc_expected_score(self):

        self.assertEqual(ranking.calc_expected_score(1000, 1000), (0.5, 0.5))
        self.assertAlmostEquals(ranking.calc_expected_score(1000, 10000)[0], 0.)

    def test_gen_win_pairs_from_result(self):

        self.assertEqual(
            ranking.gen_win_pairs_from_result(self.result_2_players), [(ALICE, BOB, 1.)])
        self.assertEqual(
            ranking.gen_win_pairs_from_result(self.result_4_players),
            [(DOGE, ALICE, 1.), (ALICE, BOB, 1.), (BOB, CEVIN, 1.)])

        # TODO: No test case for drawing scores, as undefined

    def test_multiplayer_updates(self):

        updates_2_player = ranking.calc_multiplayer_updates(self.result_2_players, self.initial_elos)
        # check number of updates as expected
        self.assertEqual(len(updates_2_player), 2)
        self.assertEqual(len(updates_2_player[ALICE]), 1)
        self.assertEqual(len(updates_2_player[BOB]), 1)
        # updates should sum to zero
        self.assertAlmostEquals(sum(flatten(updates_2_player.values())), 0)

        updates_4_player = ranking.calc_multiplayer_updates(self.result_4_players, self.initial_elos)
        # check number of updates as expected
        self.assertEqual(len(updates_4_player), 4)
        self.assertEqual(len(updates_4_player[DOGE]), 1)
        self.assertEqual(len(updates_4_player[ALICE]), 2)
        self.assertEqual(len(updates_4_player[BOB]), 2)
        self.assertEqual(len(updates_4_player[CEVIN]), 1)
        # updates should sum to zero
        self.assertAlmostEquals(sum(flatten(updates_4_player.values())), 0)

        # apply some updates
        updated_elos = ranking.apply_multiplayer_updates(self.result_4_players, self.initial_elos)
        self.assertEqual(updated_elos[ALICE], self.initial_elos[ALICE] + sum(updates_4_player[ALICE]))
        self.assertEqual(updated_elos[DOGE], self.initial_elos[DOGE] + sum(updates_4_player[DOGE]))
        self.assertAlmostEquals(sum(updated_elos.values()), sum(self.initial_elos.values()))