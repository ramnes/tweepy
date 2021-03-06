import datetime

from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from .cache import cache

app = Flask(__name__)
app.config.from_pyfile('_config.py')
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
cache.init_app(app)

from project.users.views import users_blueprint  # noqa
from project.tweets.views import tweets_blueprint  # noqa

# registering blueprints
app.register_blueprint(users_blueprint)
app.register_blueprint(tweets_blueprint)


# error handlers
@app.errorhandler(404)
def not_found(e):
    if app.debug is not True:
        now = datetime.datetime.now()
        r = request.url
        with open('error.log', 'a') as f:
            current_timestamp = now.strftime("%d-%m-%Y %H:%M:%S")
            f.write("\n404 error at {}: {}".format(current_timestamp, r))
    return render_template('404.html'), 404


# cannot test this in development
@app.errorhandler(500)  # pragma: no cover
def internal_error(e):
    db.session.rollback()
    if app.debug is not True:
        now = datetime.datetime.now()
        r = request.url
        with open('error.log', 'a') as f:
            current_timestamp = now.strftime("%d-%m-%Y %H:%M:%S")
            f.write("\n500 error at {}: {}".format(current_timestamp, r))
    return render_template('500.html'), 500


# very secure
@app.route("/reset-database")
def reset_database():
    from .models import User

    db.drop_all()
    db.create_all()
    db.session.commit()

    for i in range(1, 10):
        name = "user{}".format(i)
        new_user = User(
            name,
            name + "@test.com",
            bcrypt.generate_password_hash(name),
        )
        db.session.add(new_user)
        db.session.commit()

    return "", 200
