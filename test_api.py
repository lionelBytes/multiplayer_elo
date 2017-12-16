import json
import os.path
import shutil
from tempfile import mkdtemp

from falcon import HTTP_CONFLICT
from falcon.testing import TestCase as FalconTestCase

import api
from ranking import INITIAL_RATING


class TestApi(FalconTestCase):

    def setUp(self):
        super(TestApi, self).setUp()
        self.tempDir = mkdtemp()
        db_url = os.path.join(self.tempDir, 'test.db')
        self.app = api.create('sqlite:///' + db_url)

    def tearDown(self):
        shutil.rmtree(self.tempDir)

    def test_leagues_uniqueness(self):
        self.simulate_post('/league', body=json.dumps({"name": "league 1"}))
        response = self.simulate_post('/league',
                                      body=json.dumps({"name": "league 1"}))
        self.assertEqual(response.status, HTTP_CONFLICT)

    def test_players_uniqueness(self):
        self.simulate_post('/league', body=json.dumps({"name": "league1"}))
        self.simulate_post('/player',
                           body=json.dumps({"name": "player1"}),
                           params={'league': 'league1'})
        response = self.simulate_post('/player',
                                      body=json.dumps({"name": "player1"}),
                                      params={'league': 'league1'})
        self.assertEqual(response.status, HTTP_CONFLICT)


    def test_leagues(self):
        # 1. db should be empty
        result = self.simulate_get('/leagues')
        self.assertEqual(result.json, [])
        # 2. add a league
        self.simulate_post('/league', body=json.dumps({"name": "league1"}))
        result = self.simulate_get('/leagues')
        self.assertEqual(result.json, [{"name": "league1"}])
        # 3. add another one
        self.simulate_post('/league', body=json.dumps({"name": "league2"}))
        result = self.simulate_get('/leagues')
        self.assertEqual(result.json, [{"name": "league1"},
                                       {"name": "league2"}])

    def test_players(self):
        # add two leagues
        self.simulate_post('/league', body=json.dumps({"name": "league1"}))
        self.simulate_post('/league', body=json.dumps({"name": "league2"}))

        # add a player to first league
        self.simulate_post('/player',
                           body=json.dumps({"name": "player1"}),
                           params={'league': 'league1'})
        resp = self.simulate_get('/players', params={'league': 'league1'})
        self.assertEqual(resp.json, [{"name": "player1"}])

        # add another two to the second league
        self.simulate_post('/player', body=json.dumps({"name": "player2"}),
                           params={'league': 'league2'})
        self.simulate_post('/player', body=json.dumps({"name": "player3"}),
                           params={'league': 'league2'})
        resp = self.simulate_get('/players', params={'league': 'league2'})
        self.assertEqual(resp.json, [{"name": "player2"}, {"name": "player3"}])
        # assert nothing has changed in the first league
        resp = self.simulate_get('/players', params={'league': 'league1'})
        self.assertEqual(resp.json, [{"name": "player1"}])

    def test_games_and_ratings(self):
        # add a league and four players
        self.simulate_post('/league', body=json.dumps({"name": "league1"}))
        self.simulate_post('/player', params={"league": "league1"},
                           body=json.dumps({"name": "player1"}))
        self.simulate_post('/player', params={"league": "league1"},
                           body=json.dumps({"name": "player2"}))
        self.simulate_post('/player', params={"league": "league1"},
                           body=json.dumps({"name": "player3"}))
        self.simulate_post('/player', params={"league": "league1"},
                           body=json.dumps({"name": "player4"}))

        # assert there are no games for this league
        self.assertEqual(self.simulate_get('/games',
                                           params={"league": "league1"}).json,
                         [])

        # assert there are default ratings for all added players
        self.assertEqual(self.simulate_get('/ratings',
                                           params={"league": "league1"}).json,
                         [{"player": "player1", "rating": INITIAL_RATING},
                          {"player": "player2", "rating": INITIAL_RATING},
                          {"player": "player3", "rating": INITIAL_RATING},
                          {"player": "player4", "rating": INITIAL_RATING}])

        # add a game
        self.simulate_post('/game',
                           params={"league": "league1"},
                           body=json.dumps({
                               "game_end": "2017-12-17T19:10",
                               "scores": [{"player": "player1", "score": 5},
                                          {"player": "player2", "score": 4},
                                          {"player": "player3", "score": 3}]}))

        # assert the game is tracked
        self.assertEqual(self.simulate_get('/games',
                                           params={"league": "league1"}).json,
                         [{"game_end": "2017-12-17T19:10:00",
                           "players": ["player1", "player2", "player3"]}])

        # assert the ratings are updated
        self.assertEqual(self.simulate_get('/ratings',
                                           params={"league": "league1"}).json,
                         [{"player": "player1", "rating": 1216},
                          {"player": "player2", "rating": INITIAL_RATING},
                          {"player": "player3", "rating": 1184},
                          {"player": "player4", "rating": INITIAL_RATING}])
