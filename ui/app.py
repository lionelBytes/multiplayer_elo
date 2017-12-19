from flask import Flask
from flask_bootstrap import Bootstrap

from frontend import frontend, nav


def create_app():
    app = Flask(__name__)
    app.secret_key = 'A0Zr9vaslfhasnkj,mLWX/,?RT'

    Bootstrap(app)
    app.register_blueprint(frontend)
    nav.init_app(app)
    return app

app = create_app()
