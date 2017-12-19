import json
import logging
import sys
import traceback

import dateutil.parser as dt_parser
import falcon

import config as cfg
import custom_exceptions
from db import DB
from ranking import apply_multiplayer_updates, INITIAL_RATING

logging.basicConfig(level=logging.DEBUG if cfg.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


def params_to_kwargs(func):
    """
    Simple decorator for a falcon api method to pass on query parameters
     and json content of the request body to the api method as kwargs
    :param func: the decorated api method 
    :return: a kwargs dictionary, updated with converted query parameters 
    """

    def wrapper(resource_instance, req, *args, **kwargs):
        kwargs.update(req.params)
        if req.content_length:
            kwargs.update(json.load(req.stream))
        return func(resource_instance, req, *args, **kwargs)

    return wrapper


class ApiResource(object):
    """
    Express-style API, which routes GET and POST requests to its methods
     corresponding to the <resource> parameter. Query parameters and the json
     body of a request (if exists) are added to the keyword arguments and
     forwarded to the methods.

    The persistence logic is passed on to an injected db object, business logic
     (a.k.a. ELO rating computations) is forwarded to the ranking module, and
     hidden from the persistence layer.
    """

    def __init__(self, db, debug=False):
        self.db = db
        self.debug = debug

    def on_get(self, req, res, resource, *args, **kwargs):
        """
        Deal with get requests
        """
        self.route_to_method(req, res, 'get_' + resource, *args, **kwargs)

    def on_post(self, req, res, resource, *args, **kwargs):
        """
        Deal with post requests
        """
        self.route_to_method(req, res, 'add_' + resource, *args, **kwargs)

    def deal_with_error(self, e_type, e_status, msg, res):
        """
        In case of a caught exception, populate the response body with details
        of the exception (in DEBUG mode), in any case set the correct status.
        """
        logger.error("error (%s): %s", e_type, msg)
        self.db.rollback()
        if self.debug:
            traceb = traceback.format_exception(*sys.exc_info())
            res.body = json.dumps({'error': e_type, 'status': e_status,
                                   'message': msg, 'traceback': traceb})
        res.status = getattr(falcon, 'HTTP_{}'.format(e_status), e_status)

    @params_to_kwargs
    def route_to_method(self, req, res, resource, *args, **kwargs):
        """
        The central request - method - routing. Tries to call the correct method
        for a specific resource, returns appropriate error messages (DEBUG
        mode) and status in case.
        :return:
        """
        try:
            method = getattr(self, resource, None)
            if not method:
                res.status = falcon.HTTP_404
            else:
                result, default_status = method(*args, **kwargs)
                res.body = json.dumps(result)
                res.status = default_status
        except custom_exceptions.ApiException as e:
            self.deal_with_error(type(e).__name__, e.status, ' '.join(e.args),
                                 res)
        except Exception as e:
            self.deal_with_error(type(e).__name__, 500, ' '.join(e.args), res)
        finally:
            self.db.close()

    def get_leagues(self):
        """
        :return: a sequence of leagues, e.g.
            [
              {
                "name": "myleague"
              },
              ..
            ], and the default status message (if successful)
        """
        return tuple(self.db.leagues()), falcon.HTTP_200

    def add_league(self, name):
        """
        Adds a league with name <name>.
        :return: None, and the default CREATED status message (if successful)
        """
        return self.db.add_league(name), falcon.HTTP_CREATED

    def get_league(self, name):
        """
        :param name: a string representing the league's name
        :return: The ratings of the players of the league, see `get_ratings`
        """
        return self.get_ratings(name)

    def get_ratings(self, league):
        """
        :param league: a string representing the league's name
        :return: a sequence of players, sorted by their rating
            [
              {
                "player": "1",
                "rating": 1216
              },
              {
                "player": "2",
                "rating": 1200
              },
              {
                "player": "4",
                "rating": 1200
              },
              {
                "player": "3",
                "rating": 1184
              }
            ], and the default status code (if successful)
        """
        return tuple(self.db.ratings(league)), falcon.HTTP_200

    def get_players(self, league):
        """
        :param league: a string representing the league's name
        :return: a sequence of the players in this league
            [
              {
                "name": "1"
              },
              {
                "name": "2"
              },
              {
                "name": "3"
              },
              {
                "name": "4"
              }
            ], and the default status code (if successful)
        """
        return tuple(self.db.players(league)), falcon.HTTP_200

    def add_player(self, league, name):
        """
        :param league: a string representing the league's name
        :param name: a string representing the name of the player to create
        :return: None, and the default CREATED status message (if successful)
        """
        return (self.db.add_player(name, INITIAL_RATING, league),
                falcon.HTTP_CREATED)

    def get_games(self, league):
        """
        :param league: a string representing the league's name
        :return: a sequence of games, e.g.
            [
              {
                "players": [
                  "1",
                  "2",
                  "3"
                ],
                "game_end": "2017-01-02T12:34:00"
              },
              ..
            ], and the default status code (if successful)
        """
        return tuple(self.db.games(league)), falcon.HTTP_200

    def add_game(self, league, game_end, scores):
        """
        :param league: a string representing the league's name
        :param game_end: a timestamp in isoformat
        :param scores: a sequence of dictionaries mapping player names to
            scores, e.g. [{"1": 10, "2": 8, "3": 6}]
        :return: None, and the default CREATED status message (if successful)
        """
        scores = {s['player']: s['score'] for s in scores}
        players = scores.keys()
        not_found = set(players).difference({p['name']
                                             for p in self.db.players()})
        if not_found:
            raise custom_exceptions.NotAllowed(
                "Players unknown in this league: {}".format(not_found))
        game_end = dt_parser.parse(game_end)

        # save the game first
        self.db.add_game(game_end, scores, league)

        # compute the new ratings based on the old ratings & this game's score..
        old_ratings = {r["player"]: r["rating"]
                       for r in self.db.ratings(league,
                                                players=scores.keys())}
        updated_ratings = apply_multiplayer_updates(tuple(scores.items()),
                                                    old_ratings)
        # ..and save the new ratings
        for player_name, rating in updated_ratings.items():
            self.db.update_rating(rating, league, player_name)

        return None, falcon.HTTP_CREATED


def create(db_uri=None):
    api = falcon.API()
    api.add_route('/{resource}',
                  ApiResource(DB(db_uri or cfg.DB_URI), debug=cfg.DEBUG))
    return api
