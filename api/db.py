import logging

from sqlalchemy import desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine, \
    UniqueConstraint, Float, DateTime

import config as cfg
from custom_exceptions import NotFound, Exists

logger = logging.getLogger(__name__)
Base = declarative_base()


class Serializable(object):

    @property
    def serialize_fields(self):
        return self.__table__.columns

    def serialized(self):
        return {c.name: getattr(self, c.name)
                for c in self.serialize_fields if c.name != 'id'}


class League(Base, Serializable):

    __tablename__ = 'leagues'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    games = relationship("Game")

    def serialized(self):
        return {"name": self.name}


class Player(Base, Serializable):

    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    player_ratings = relationship("PlayerRating")
    player_game_scores = relationship("PlayerGameScore")


class PlayerRating(Base):

    __tablename__ = 'player_ratings'
    __table_args__ = (UniqueConstraint('league_id', 'player_id',
                                       name='_league_player_uc'),)

    id = Column(Integer, primary_key=True)
    rating = Column(Float)

    league_id = Column(Integer, ForeignKey('leagues.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)

    league = relationship("League")
    player = relationship("Player", back_populates='player_ratings')


class Game(Base, Serializable):

    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)
    game_end = Column(DateTime, nullable=False)

    league_id = Column(Integer, ForeignKey('leagues.id'), nullable=False)

    league = relationship("League", back_populates="games")
    player_game_scores = relationship("PlayerGameScore")

    def serialized(self):
        return {"game_end": self.game_end.isoformat(),
                "players": sorted(g.player.name
                                  for g in self.player_game_scores)}


class PlayerGameScore(Base):

    __tablename__ = 'player_game_scores'

    id = Column(Integer, primary_key=True)
    score = Column(Float)

    game_id = Column(Integer, ForeignKey('games.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)

    game = relationship("Game", back_populates="player_game_scores")
    player = relationship("Player", back_populates="player_game_scores")


class DB(object):
    """
    To be used to interact with SQLAlchemy's ORM.
    """

    def __init__(self, db_uri=cfg.DB_URI):
        self.engine = create_engine(db_uri, echo=cfg.VERBOSE_SQL)
        Base.metadata.create_all(self.engine)
        self._session = scoped_session(sessionmaker(bind=self.engine))

    def close(self):
        self.session.close()

    def rollback(self):
        self.session.rollback()

    @property
    def session(self):
        return self._session()

    def get_or_create(self, model, commit=True, **kwargs):
        instance = self.session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance, False
        else:
            instance = self.create(model, commit=commit, **kwargs)
            return instance, True

    def create(self, model, commit=True, **kwargs):
        instance = model(**kwargs)
        self.session.add(instance)
        if commit:
            self.session.commit()
        return instance

    def leagues(self, league_name=None):
        scs = self.session.query(League)
        if league_name:
            scs = scs.filter_by(name=league_name)
            if scs.count() == 0:
                raise NotFound("League {} doesn't exist.".format(league_name))
            assert scs.count() == 1
        return (s.serialized() for s in scs)

    def players(self, league_name=None):
        ps = self.session.query(PlayerRating if league_name else Player)
        if league_name:
            ps = (p.player
                  for p in ps.join(PlayerRating.league) \
                    .filter(League.name == league_name))
        return (p.serialized() for p in ps)

    def games(self, league_name):
        games = self.session.query(Game) \
            .join(Game.league) \
            .filter(League.name == league_name)
        return (g.serialized() for g in games)

    def ratings(self, league_name, players=None):
        ratings = self.session.query(PlayerRating) \
            .join(PlayerRating.league) \
            .filter(League.name == league_name) \
            .order_by(desc(PlayerRating.rating))
        if players:
            ratings = ratings.join(PlayerRating.player) \
                    .filter(Player.name.in_(players))
        return ({"player": r.player.name, "rating": r.rating} for r in ratings)

    def update_rating(self, rating, league_name, player_name):
        league, created = self.get_or_create(League, name=league_name)
        assert not created
        player, created = self.get_or_create(Player, name=player_name)
        assert not created
        player_rating, _ = self.get_or_create(PlayerRating, league=league,
                                              player=player)
        player_rating.rating = rating
        self.session.add(player_rating)
        self.session.commit()

    def add_league(self, league_name):
        if self.session.query(League).filter_by(name=league_name).count() > 0:
            raise Exists("league {} already exists!".format(league_name))
        self.create(League, name=league_name)

    def add_player(self, name, rating, league_name=None):
        p, _ = self.get_or_create(Player, name=name)
        if league_name:
            league = self.session.query(League) \
                .filter_by(name=league_name).first()
            assert league
            player_rating_exists = self.session.query(PlayerRating) \
                .filter_by(player=p, league=league).count() > 0
            if player_rating_exists:
                raise Exists("player {} already exists for league {}!".format(
                    name, league_name))
            self.create(PlayerRating, player=p, league=league, rating=rating)

    def add_game(self, game_end, scores, league_name):
        league = self.session.query(League).filter_by(name=league_name).first()

        game = self.create(Game, league=league, game_end=game_end)

        for player_name, score in scores.items():
            player = self.session.query(Player) \
                .filter_by(name=player_name).first()
            score, c = self.get_or_create(PlayerGameScore, game=game,
                                          player=player, score=score)
            assert c
