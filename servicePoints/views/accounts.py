import hashlib
import os
import flask
from flask import render_template
import servicePoints
APP = flask.Flask(__name__)

servicePoints.app.secret_key = b'''\xf4\xb2\x9f\x80\xb1\xef\x01\xc6\x10\xca
    \xdd\x84\xd4\xf3\x0c\x95\xad\xa6\xdc\xaf\xd3\xbeI\xf7'''

@servicePoints.app.route('/accounts/login/', methods=['GET', 'POST'])
def login():
    """Render login page."""
    if 'username' in flask.session:
        return flask.redirect(flask.url_for('index'))
    if flask.request.method == 'POST':
        cursor = servicePoints.model.get_db().cursor()
        pass_user = flask.request.form['password']
        password_1 = cursor.execute('SELECT password FROM users WHERE '
                                    'username =:who',
                                    {"who": flask.request.form['username']})
        password_3 = password_1.fetchall()
        if not password_3:
            flask.abort(403)
        password_2 = password_3[0]['password']
        password_4 = password_2.split('$')
        algorithm = password_4[0]
        salt = password_4[1]
        p2word = password_4[2]
        hash_obj = hashlib.new(algorithm)
        password_salted = salt + pass_user
        hash_obj.update(password_salted.encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        if p2word != password_hash:
            flask.abort(403)
        flask.session['username'] = flask.request.form['username']
        return flask.redirect(flask.url_for('index'))
    context = {}
    return render_template('login.html', **context)

@servicePoints.app.route('/accounts/logout/')
def logout():
    """Render logout page."""
    flask.session.clear()
    return flask.redirect(flask.url_for('login'))


@servicePoints.app.route('/accounts/create/', methods=['GET', 'POST'])
def create():
    """Render create page."""
    # If a user is already logged in, redirect to /accounts/edit/
    if 'username' in flask.session:
        return flask.redirect(flask.url_for('index'))
    if flask.request.method == 'POST':

        # If a user tries to create an account with an existing username in
        # the database, abort(409)
        flask.session['username'] = flask.request.form['username']
        flask.session['fullname'] = flask.request.form['fullname']
        flask.session['orgName'] = flask.request.form['orgName']
        flask.session['email'] = flask.request.form['email']
        flask.session['password'] = flask.request.form['password']
        cursor = servicePoints.model.get_db().cursor()
        name = str(flask.session['username'])

        to_add = (name,)
        cursor.execute('SELECT * FROM users WHERE username=?', to_add)
        if cursor.fetchone() is not None:
            flask.abort(409)

        # If a user tries to create an account with an empty string as the
        # password, abort(400)
        if flask.session['password'] == '':
            flask.abort(400)


        # pw = hash_pass(flask.session['password'])
        data = (flask.session['username'], flask.session['fullname'],
                flask.session['email'], flask.session['orgName'],
                flask.session['password'])
        cur = servicePoints.model.get_db()
        cur.execute("INSERT INTO users(username, fullname, email, orgName, "
                    "password) VALUES (?, ?, ?, ?, ?)", data)

        return flask.redirect(flask.url_for('index'))

    context = {}
    return render_template('create.html', **context)

@servicePoints.app.route('/', methods=['GET', 'POST'])
def index():
    """Render index page."""
    if 'username' in flask.session:
        context = {}
        return render_template('index.html', **context)
    return flask.redirect(flask.url_for('login'))