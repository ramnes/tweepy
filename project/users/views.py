# imports
from functools import wraps
from flask import (flash, redirect, render_template,
                   request, session, url_for, Blueprint)
from sqlalchemy.exc import IntegrityError

from .forms import RegisterForm, LoginForm
from project import db, bcrypt
from project.models import User

# config
users_blueprint = Blueprint('users', __name__)


# helper functions
def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first')
            return (redirect(url_for('users.ui_login')))
    return wrap


# routes
@users_blueprint.route('/logout/')
@login_required
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('name', None)
    session.pop('role', None)
    flash('You have been logged out')
    return redirect(url_for('users.index'))


@users_blueprint.route('/', methods=['GET'])
def index():
    form = LoginForm(request.form)
    return render_template('index.html', form=form, error=None)


def login(form):
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.name.data).first()
        if (user is not None
            and bcrypt.check_password_hash(user.password, form.password.data)):
            session['logged_in'] = True
            session['user_id'] = user.id
            session['name'] = user.name
            session['role'] = user.role
            return user


@users_blueprint.route('/', methods=['POST'])
def ui_login():
    form = LoginForm(request.form)
    if login(form):
        flash('Welcome')
        return redirect(url_for('tweets.tweet'))
    error = 'Invalid username or password.'
    return render_template('index.html', form=form, error=error)


@users_blueprint.route('/api/login', methods=['POST'])
def api_login():
    form = LoginForm(request.form)
    if login(form):
        return "", 200
    return "", 403


@users_blueprint.route('/register/', methods=['GET', 'POST'])
def register():
    error = None
    form = RegisterForm(request.form)
    if 'logged_in' in session:
        return redirect(url_for('tweets.tweet'))
    if request.method == 'POST':
        if form.validate_on_submit():
            new_user = User(
                form.name.data,
                form.email.data,
                bcrypt.generate_password_hash(form.password.data),
            )
            try:
                db.session.add(new_user)
                db.session.commit()
                flash('Thanks for registering. Plese login.')
                return redirect(url_for('users.ui_login'))
            except IntegrityError:
                error = 'That username and/or email already exists.'
                return render_template('register.html', form=form, error=error)
    return render_template('register.html', form=form, error=error)


@users_blueprint.route('/users/')
@login_required
def all_users():
    users = db.session.query(User).all()
    return render_template('users.html', users=users)
