import dateutil.parser as dt_parser
import json
import logging
import sys
import traceback

import falcon

import custom_exceptions
from db import DB
from ranking import apply_multiplayer_updates, INITIAL_RATING


logging.basicConfig(level=logging.DEBUG)
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
        self.route_to_method(req, res, 'get_' + resource, *args, **kwargs)

    def on_post(self, req, res, resource, *args, **kwargs):
        self.route_to_method(req, res, 'add_' + resource, *args, **kwargs)

    def deal_with_error(self, e_type, e_status, msg, res):
        logger.error("error (%s): %s", e_type, msg)
        self.db.rollback()
        if self.debug:
            traceb = traceback.format_exception(*sys.exc_info())
            res.body = json.dumps({'error': e_type, 'status': e_status,
                                   'message': msg, 'traceback': traceb})
        res.status = getattr(falcon, 'HTTP_{}'.format(e_status), e_status)

    @params_to_kwargs
    def route_to_method(self, req, res, resource, *args, **kwargs):
        try:
            method = getattr(self, resource, None)
            if not method:
                res.status = falcon.HTTP_404
            else:
                res.body = json.dumps(method(*args, **kwargs))
        except custom_exceptions.ApiException as e:
            self.deal_with_error(type(e).__name__, e.status, ' '.join(e.args),
                                 res)
        except Exception as e:
            self.deal_with_error(type(e).__name__, 500, ' '.join(e.args), res)
        finally:
            self.db.close()

    def get_leagues(self):
        return tuple(self.db.leagues())

    def add_league(self, name):
        return self.db.add_league(name)

    def get_league(self, name):
        return tuple(self.db.leagues(name))

    def get_ratings(self, league):
        return tuple(self.db.ratings(league))

    def get_players(self, league):
        return tuple(self.db.players(league))

    def add_player(self, league, name):
        return self.db.add_player(name, INITIAL_RATING, league)

    def get_games(self, league):
        return tuple(self.db.games(league))

    def add_game(self, league, game_end, scores):
        scores = {s['player']: s['score'] for s in scores}
        game_end = dt_parser.parse(game_end)

        # save the game first
        game = self.db.add_game(game_end, scores, league)

        # compute the new ratings based on the old ratings & this game's score..
        old_ratings = {r["player"]: r["rating"]
                       for r in self.db.ratings(league,
                                                players=scores.keys())}
        updated_ratings = apply_multiplayer_updates(tuple(scores.items()),
                                                    old_ratings)
        # ..and save the new ratings
        for player_name, rating in updated_ratings.items():
            self.db.update_rating(rating, league, player_name)

        return game


def create(db_uri="sqlite:///elo.db"):
    api = falcon.API()
    api.add_route('/{resource}', ApiResource(DB(db_uri)))
    return api
