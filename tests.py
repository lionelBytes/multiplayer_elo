from unittest import TestCase
import ranking

# example players
ALICE = 'alice'
BOB = 'bob'
CEVIN = 'cevin'
DOGE = 'doge'

class TestRanking(TestCase):


    def test_calc_expected_score(self):

        self.assertEqual(ranking.calc_expected_score(1000, 1000), (0.5, 0.5))
        self.assertAlmostEquals(ranking.calc_expected_score(1000, 10000)[0], 0.)

    def test_gen_win_pairs_from_result(self):

        self.assertEqual(ranking.gen_win_pairs_from_result(((ALICE, 404), (BOB, 200))), [(ALICE, BOB, 1.)])
        self.assertEqual(ranking.gen_win_pairs_from_result(((ALICE, 404), (BOB, 200), (CEVIN, -100), (DOGE, 1000))),
                         [(DOGE, ALICE, 1.), (ALICE, BOB, 1.), (BOB, CEVIN, 1.)])

        # TODO: No test case for drawing scores, as undefined
