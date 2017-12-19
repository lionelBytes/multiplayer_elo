from flask_wtf import FlaskForm

from wtforms import StringField, DateTimeField, IntegerField, HiddenField
from wtforms.validators import DataRequired


class LeagueForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])


class PlayerForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])


class GameForm(FlaskForm):

    game_end = DateTimeField('game_end', validators=[DataRequired()])


class PlayerScoreForm(FlaskForm):

    score = IntegerField('score', validators=[DataRequired()])
    player = HiddenField('player', validators=[DataRequired()])


def validate_score_forms(forms):
    for form in forms:
        if form.validate_on_submit():
            yield {k: v for k, v in form.data.items() if k != "csrf_token"}
