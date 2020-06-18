import hashlib
import uuid
import os
import flask
import shutil
import tempfile
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
            return flask.redirect(flask.url_for('accountNotFound'))
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
            return flask.redirect(flask.url_for('accountNotFound'))
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
        cursor = servicePoints.model.get_db().cursor()
        name = str(flask.request.form['username'])
        orgName = str(flask.request.form['orgName'])
        password = str(flask.request.form['password'])
        
        to_add = (name,)
        to_join = (orgName,)
        cursor.execute('SELECT * FROM users WHERE username=?', to_add)
        if cursor.fetchone() is not None:
            return flask.redirect(flask.url_for('duplicateUsername', prev='create'))

        cursor.execute('SELECT * FROM orgs WHERE orgName=?', to_join)
        if cursor.fetchone() is None:
            return flask.redirect(flask.url_for('orgNotFound'))

        if len(str(flask.request.form['password'])) is 0 or len(str(flask.request.form['fullname'])) is 0:
            return flask.redirect(flask.url_for('incompleteForm', prev="create")) 

        if len(str(flask.request.form['orgName'])) is 0 or len(str(flask.request.form['email'])) is 0:
            return flask.redirect(flask.url_for('incompleteForm', prev="create")) 
        
        if len(str(flask.request.form['username'])) is 0:
            return flask.redirect(flask.url_for('incompleteForm', prev="create"))

        flask.session['username'] = flask.request.form['username']
        flask.session['fullname'] = flask.request.form['fullname']
        flask.session['orgName'] = flask.request.form['orgName']
        flask.session['email'] = flask.request.form['email']
        flask.session['password'] = flask.request.form['password']

        pw = hash_pass(flask.session['password'])
        data = (flask.session['username'], flask.session['fullname'],
                flask.session['email'], flask.session['orgName'],
                pw, 0)
        cur = servicePoints.model.get_db()
        cur.execute("INSERT INTO users(username, fullname, email, orgName, "
                    "password, hours) VALUES (?, ?, ?, ?, ?, ?)", data)

        return flask.redirect(flask.url_for('index'))

    context = {}
    return render_template('create.html', **context)

@servicePoints.app.route('/accounts/createOrg/', methods=['GET', 'POST'])
def createOrg():
    """Render createOrg page."""
    # If a user is already logged in, redirect to /accounts/edit/
    if 'username' in flask.session:
        return flask.redirect(flask.url_for('index'))
    if flask.request.method == 'POST':

        # If a user tries to create an account with an existing username in
        # the database, abort(409)
        cursor = servicePoints.model.get_db().cursor()
        name = str(flask.request.form['username'])
        orgName = str(flask.request.form['orgName'])

        to_add = (name,)
        to_addOrg = (orgName,)
        cursor.execute('SELECT * FROM users WHERE username=?', to_add)
        if cursor.fetchone() is not None:
            return flask.redirect(flask.url_for('duplicateUsername', prev='createOrg'))

        cursor.execute('SELECT * FROM orgs WHERE orgName=?', to_addOrg)
        if cursor.fetchone() is not None:
            return flask.redirect(flask.url_for('duplicateOrgName', prev='createOrg'))

        # If a user tries to create an account with an empty string as the
        # password, abort(400)
        if len(str(flask.request.form['password'])) is 0 or len(str(flask.request.form['fullname'])) is 0:
            return flask.redirect(flask.url_for('incompleteForm', prev="createOrg")) 

        if len(str(flask.request.form['orgName'])) is 0 or len(str(flask.request.form['email'])) is 0:
            return flask.redirect(flask.url_for('incompleteForm', prev="createOrg")) 
        
        if len(str(flask.request.form['username'])) is 0:
            return flask.redirect(flask.url_for('incompleteForm', prev="createOrg"))

        flask.session['username'] = flask.request.form['username']
        flask.session['fullname'] = flask.request.form['fullname']
        flask.session['orgName'] = flask.request.form['orgName']
        flask.session['email'] = flask.request.form['email']
        flask.session['password'] = flask.request.form['password']

        pw = hash_pass(flask.session['password'])
        data = (flask.session['username'], flask.session['fullname'],
                flask.session['email'], flask.session['orgName'],
                pw, 0)
        orgData = (flask.session['username'], flask.session['orgName'])
        cur = servicePoints.model.get_db()
        cur.execute("INSERT INTO orgs(username, orgName) VALUES (?, ?)", orgData)
        cur.execute("INSERT INTO users(username, fullname, email, orgName, "
                    "password, hours) VALUES (?, ?, ?, ?, ?, ?)", data)

        return flask.redirect(flask.url_for('index'))

    context = {}
    return render_template('createOrg.html', **context)

@servicePoints.app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' in flask.session:
        username = flask.session["username"]
        cursor = servicePoints.model.get_db()
        studentOrgCur = cursor.execute('SELECT orgName, hours FROM users WHERE '
                            'username =:who',
                            {"who": username})
        results = studentOrgCur.fetchone()
        leaderCur = cursor.execute('SELECT orgName FROM orgs WHERE '
                    'username =:who',
                    {"who": username})
        if leaderCur.fetchone() is None:
            leader = 0
        else:
            leader = 1
        context = {'username': username, 'org': results["orgName"], 'hours': results["hours"], 'leader': leader}
        return render_template('index.html', **context)
    return flask.redirect(flask.url_for('login'))

def hash_pass(password_in):
    """Hash passwords."""
    algorithm = 'sha512'
    salt = uuid.uuid4().hex
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password_in
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string

@servicePoints.app.route('/accounts/delete/', methods=['GET', 'POST'])
def delete():
    """Render delete page."""
    if flask.request.method == 'POST':
        name = (flask.session['username'])
        to_add = (name,)
        cur = servicePoints.model.get_db()

        flask.session.clear()
        cur.execute('DELETE FROM users WHERE username=?', to_add)
        return flask.redirect(flask.url_for('login'))
    context = {'username': flask.session['username']}
    return render_template('delete.html', **context)

@servicePoints.app.route('/accounts/orgNotFound/', methods=['GET', 'POST'])
def orgNotFound():
    """Render delete page."""
    if flask.request.method == 'POST':
        if 'login' in flask.request.form:
            return flask.redirect(flask.url_for('login'))
        if 'registerOrg' in flask.request.form:
            return flask.redirect(flask.url_for('createOrg'))
    context = {}
    return render_template('orgNotFound.html', **context)

@servicePoints.app.route('/accounts/accountNotFound/', methods=['GET', 'POST'])
def accountNotFound():
    if flask.request.method == 'POST':
        if 'login' in flask.request.form:
            return flask.redirect(flask.url_for('login'))
        if 'createAccount' in flask.request.form:
            return flask.redirect(flask.url_for('create'))
    context = {}
    return render_template('accountNotFound.html', **context)

@servicePoints.app.route('/accounts/duplicateUsername/<prev>', methods=['GET', 'POST'])
def duplicateUsername(prev):
    if flask.request.method == 'POST':
        return flask.redirect(flask.url_for(prev))
    context = {"prev": prev}
    return render_template('duplicateUsername.html', **context)

@servicePoints.app.route('/accounts/duplicateOrgName/', methods=['GET', 'POST'])
def duplicateOrgName():
    if flask.request.method == 'POST':
        return flask.redirect(flask.url_for('createOrg'))
    context = {}
    return render_template('duplicateOrgName.html', **context)

@servicePoints.app.route('/accounts/duplicateTutor/', methods=['GET', 'POST'])
def duplicateTutor():
    if flask.request.method == 'POST':
        return flask.redirect(flask.url_for('tutor'))
    context = {}
    return render_template('duplicateTutor.html', **context)

@servicePoints.app.route('/accounts/incompleteForm/<prev>', methods=['GET', 'POST'])
def incompleteForm(prev):
    if flask.request.method == 'POST':
        return flask.redirect(flask.url_for(prev))
    context = {"prev": prev}
    return render_template('incompleteForm.html', **context)

@servicePoints.app.route('/accounts/mask/')
def mask():
    context = {}
    return render_template('mask.html', **context)

@servicePoints.app.route('/images/<path:filename>', methods=['GET', 'POST'])
def images(filename):
    if "username" in flask.session:
        return flask.send_from_directory(
            servicePoints.app.config['IMAGES_FOLDER'], filename, as_attachment=True)
    return flask.redirect(flask.url_for('login'))

@servicePoints.app.route('/accounts/tutorsu/', methods=['GET', 'POST'])
def tutorsu():

    if flask.request.method == 'POST':
      
        flask.session['subjects'] = flask.request.form['subjects']
        flask.session['time'] = flask.request.form['time']
        cursor = servicePoints.model.get_db().cursor()
        name = str(flask.session['username'])

        to_add = (name,)
        cursor.execute('SELECT * FROM tutors WHERE username=?', to_add)
        if cursor.fetchone() is not None:
            return flask.redirect(flask.url_for('duplicateTutor'))

        # If a user tries to sign up with any empty fields
        if flask.session['time'] == '':
            return flask.redirect(flask.url_for('incompleteForm', prev="tutorsu")) 
        if flask.session['subjects'] == '':
            return flask.redirect(flask.url_for('incompleteForm', prev="tutorsu")) 

        data = (flask.session['username'], flask.session['subjects'],
                flask.session['time'])
        cur = servicePoints.model.get_db()
        cur.execute("INSERT INTO tutors(username, subject, time) VALUES (?, ?, ?)", data)

        return flask.redirect(flask.url_for('index'))

    context = {}
    return render_template('tutor.html', **context)

@servicePoints.app.route('/accounts/submitPoints/', methods=['GET', 'POST'])
def submitPoints():
    if flask.request.method == 'POST':
        dummy, temp_filename = tempfile.mkstemp()
        file = flask.request.files["file"]
        serviceType = flask.request.form["service"]
        file.save(temp_filename)

        # Compute filename
        hash_txt = sha256sum(temp_filename)
        dummy, suffix = os.path.splitext(file.filename)
        hash_filename_basename = hash_txt + suffix
        hash_filename = os.path.join(
            servicePoints.app.config["IMAGES_FOLDER"],
            hash_filename_basename
        )

        # Move temp file to permanent location
        shutil.move(temp_filename, hash_filename)
        cursor = servicePoints.model.get_db()
        username = flask.session["username"]
        studentOrgCur = cursor.execute('SELECT orgName FROM users WHERE '
                        'username =:who',
                        {"who": username})
        results = studentOrgCur.fetchone()
        orgName = results["orgName"]
        studentOrgLeader = cursor.execute('SELECT username FROM orgs WHERE '
                        'orgName =:who',
                        {"who": orgName})
        results = studentOrgLeader.fetchone()
        leader = results["username"]
        cursor.execute('INSERT INTO requests(member, leader, service, filename) VALUES '
            '(:one,:two,:three,:four)', {"one": username, "two": leader, "three": serviceType, "four": hash_filename_basename})
        return flask.redirect(flask.url_for('confirmSubmission'))
    username = flask.session["username"]
    cursor = servicePoints.model.get_db()
    studentOrgCur = cursor.execute('SELECT orgName, hours FROM users WHERE '
                        'username =:who',
                        {"who": username})
    results = studentOrgCur.fetchone()
    context = {'username': username, 'org': results["orgName"], 'hours': results["hours"]}
    return render_template('submitPoints.html', **context)

@servicePoints.app.route('/accounts/confirmSubmission/', methods=['GET', 'POST'])
def confirmSubmission():
    if flask.request.method == 'POST':
        return flask.redirect(flask.url_for('index'))
    username = flask.session["username"]
    cursor = servicePoints.model.get_db()
    studentOrgCur = cursor.execute('SELECT orgName FROM users WHERE '
                        'username =:who',
                        {"who": username})
    results = studentOrgCur.fetchone()
    orgName = results["orgName"]
    studentOrgLeader = cursor.execute('SELECT username FROM orgs WHERE '
                    'orgName =:who',
                    {"who": orgName})
    results = studentOrgLeader.fetchone()
    leader = results["username"]
    studentOrgLeaderFull = cursor.execute('SELECT fullname FROM users WHERE '
                    'username =:who',
                    {"who": leader})
    results = studentOrgLeaderFull.fetchone()
    context = {"leader": results["fullname"]}
    return render_template('confirmSubmission.html', **context)



def sha256sum(filename):
    """Return sha256 hash of file content, similar to UNIX sha256sum."""
    content = open(filename, 'rb').read()
    sha256_obj = hashlib.sha256(content)
    return sha256_obj.hexdigest()

