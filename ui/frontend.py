from datetime import datetime
import os
import requests
from flask import flash, Blueprint, render_template
from flask_nav import Nav
from flask_nav.elements import Text, Link, Subgroup, View, Navbar
from slugify import slugify
from werkzeug.utils import redirect

import config as cfg
from forms import LeagueForm, PlayerForm, GameForm, PlayerScoreForm, \
    validate_score_forms

nav = Nav()

frontend = Blueprint('frontend', __name__)


nav.register_element('frontend_top', Navbar(
    View('ELO Multiplayer Leagues', '.leagues'),
    Link('TODO: Games history', '#'),
    Subgroup(
        'Docs',
        View('Overview', '.readme'),
    ),
    Text('A simple web interface that queries an api under the hood'),
))


def json_or_flash(resp, good_status=200, empty_response_default=True):
    if resp.status_code == good_status:
        return resp.json() or empty_response_default
    else:
        try:
            err = resp.json()
            flash("{} - {}".format(err['error'], err['message']))
        except:
            # we know there is an issue, but can't parse the error from the api,
            #  let's at least report the status code.
            flash("error: {}".format(resp.status_code))


@frontend.route('/', methods=('GET', 'POST'))
def leagues():
    lgs = json_or_flash(requests.get(cfg.API_URL + "/leagues"),
                        empty_response_default=[])
    form = LeagueForm()
    if form.validate_on_submit():
        data = {k: slugify(v)
                for k, v in form.data.items() if k != 'csrf_token'}
        requests.post(cfg.API_URL + "/league", json=data)
        return redirect('/')
    return render_template('leagues.html', leagues=lgs, form=form)


@frontend.route('/<name>', methods=('GET', 'POST'))
def league(name):
    resp = requests.get(cfg.API_URL + "/league", params={"name": name})
    ratings = json_or_flash(resp, empty_response_default=())
    player_form = PlayerForm()
    game_form = GameForm(game_end=datetime.now())
    score_forms = tuple(PlayerScoreForm(player=r['player'], prefix=r['player'])
                        for r in ratings)
    if player_form.validate_on_submit():
        data = {k: slugify(v)
                for k, v in player_form.data.items() if k != 'csrf_token'}
        resp = requests.post(cfg.API_URL + "/player", params={"league": name},
                             json=data)
        no_error = json_or_flash(resp, good_status=201)
        if no_error:
            return redirect('/{}'.format(name))
    score_data = tuple(validate_score_forms(score_forms))
    if score_data and game_form.validate_on_submit():
        # TODO: game_end is set to datetime.now(), make FE configurable
        game_end = game_form.data['game_end'].isoformat()
        resp = requests.post(cfg.API_URL + "/game", params={"league": name},
                             json={"game_end": game_end, "scores": score_data})
        if json_or_flash(resp, good_status=201):
            return redirect('/{}'.format(name))
    return render_template('league.html', league=name, player_form=player_form,
                           ratings={r['player']: r for r in ratings},
                           score_forms=score_forms)


@frontend.route('/readme', methods=('GET',))
def readme():
    with open(os.path.join(os.getcwd(), "README.md")) as f:
        return render_template('readme.html', readme=f.read())
