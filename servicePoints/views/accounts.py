import hashlib
import uuid
import os
import flask
import shutil
import tempfile
from flask import render_template
from flask import flash
from flask import request
from flask import Flask
from flask_mail import Mail
from flask_mail import Message
import servicePoints
APP = flask.Flask(__name__)

APP.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = 'servicePnts@gmail.com',
    MAIL_PASSWORD = 'SrvcPnts-2020',
))

mail = Mail(APP)
APP.config['MAX_IMAGE_FILESIZE'] = 1024 * 1024
APP.config['ALLOWED_IMAGE_EXTENSIONS'] = ["JPEG", "JPG", "PNG", "GIF"]

servicePoints.app.secret_key = b'''\xf4\xb2\x9f\x80\xb1\xef\x01\xc6\x10\xca
    \xdd\x84\xd4\xf3\x0c\x95\xad\xa6\xdc\xaf\xd3\xbeI\xf7'''

@servicePoints.app.route('/accounts/login/', methods=['GET', 'POST'])
def login():
    """Render login page."""
    context = {}
    msg = ''
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
            msg = 'Incorrect login credentials'
        else:
            password_2 = password_3[0]['password']
            password_4 = password_2.split('$')
            algorithm = password_4[0]
            salt = password_4[1]
            p2word = password_4[2]
            hash_obj = hashlib.new(algorithm)
            password_salted = salt + pass_user
            hash_obj.update(password_salted.encode('utf-8'))
            password_hash = hash_obj.hexdigest()
            # if the password does not exist
            if p2word != password_hash:
                msg = 'Incorrect login credentials'
            else:
                flask.session['username'] = flask.request.form['username']
                return flask.redirect(flask.url_for('index'))
    return render_template('login.html', **context, msg=msg)

@servicePoints.app.route('/accounts/logout/')
def logout():
    """Render logout page."""
    flask.session.clear()
    return flask.redirect(flask.url_for('login'))


@servicePoints.app.route('/accounts/create/', methods=['GET', 'POST'])
def create():
    """Render create page."""

    msg = ''
    # If a user is already logged in, redirect to /accounts/edit/
    if 'username' in flask.session:
        return flask.redirect(flask.url_for('index'))
    if flask.request.method == 'POST':
        cursor = servicePoints.model.get_db().cursor()
        name = str(flask.request.form['username'])
        
        to_add = (name,)
        cursor.execute('SELECT * FROM users WHERE username=?', to_add)

        # If the chosen name is already taken
        if cursor.fetchone() is not None or name == "pending":
            msg = 'Username is already taken.'

        if msg == '':

            flask.session['username'] = flask.request.form['username']
            flask.session['fullname'] = flask.request.form['fullname']
            flask.session['orgName'] = flask.request.form['orgName']
            flask.session['email'] = flask.request.form['email']
            flask.session['password'] = flask.request.form['password']

            pw = hash_pass(flask.session['password'])
            cur = servicePoints.model.get_db()
            data = (flask.session['username'], flask.session['fullname'],
                    flask.session['email'], 'NONE',
                    pw, 0)
            cur.execute("INSERT INTO users(username, fullname, email, orgName, "
                        "password, hours) VALUES (?, ?, ?, ?, ?, ?)", data)
            if flask.session['orgName'] != 'NONE':
                pendingData = (flask.session['username'], flask.session['fullname'],
                               flask.session['email'], flask.session['orgName'], 0)
                cur.execute("INSERT INTO pendingOrgs(username, fullname, email, orgName, "
                            "hours) VALUES (?, ?, ?, ?, ?)", pendingData)
                leaderCur = cursor.execute('SELECT username, newMember FROM orgs WHERE '
                                'orgName =:who',
                                {"who": flask.session['orgName']})
                results = leaderCur.fetchone()
                leader = results["username"]
                memberS = results["newMember"]   
                if memberS:
                    leaderEmailCur = cursor.execute('SELECT email, fullname FROM users WHERE '
                                    'username =:who',
                                    {"who": leader})
                    results = leaderEmailCur.fetchone()
                    leaderEmail = results["email"] 
                    leaderName = results["fullname"]                
                    emsg = Message("New Request to Join " + flask.session['orgName'],
                        sender=("ServicePoints", "servicePnts@gmail.com"),
                        recipients=[leaderEmail])
                    emsg.body = "Hi " + leaderName + "! " + flask.session['username'] + " is requesting to join " + flask.session['orgName']
                    mail.send(emsg)

            return flask.redirect(flask.url_for('index'))

    cursor = servicePoints.model.get_db()

    cur = cursor.execute("SELECT * FROM orgs")
    orgs = cur.fetchall()
    context = {"orgs": orgs}
    return render_template('create.html', **context, msg=msg)

@servicePoints.app.route('/accounts/createOrg/', methods=['GET', 'POST'])
def createOrg():
    """Render createOrg page."""

    msg = ''
    if 'username' in flask.session:
        return flask.redirect(flask.url_for('index'))
    if flask.request.method == 'POST':

        cursor = servicePoints.model.get_db().cursor()
        name = str(flask.request.form['username'])
        orgName = str(flask.request.form['orgName'])

        to_add = (name,)
        to_addOrg = (orgName,)

        cursor.execute('SELECT * FROM users WHERE username=?', to_add)
        if cursor.fetchone() is not None or name == "pending":
            msg = 'Username is already taken.'

        cursor.execute('SELECT * FROM orgs WHERE orgName=?', to_addOrg)
        if cursor.fetchone() is not None or orgName == "NONE":
            msg = 'Organization name is already taken.'
        if msg == '':
            flask.session['username'] = flask.request.form['username']
            flask.session['fullname'] = flask.request.form['fullname']
            flask.session['orgName'] = flask.request.form['orgName']
            flask.session['email'] = flask.request.form['email']
            flask.session['password'] = flask.request.form['password']

            pw = hash_pass(flask.session['password'])
            data = (flask.session['username'], flask.session['fullname'],
                    flask.session['email'], flask.session['orgName'],
                    pw, 0)
            orgData = (flask.session['username'], flask.session['orgName'], 1, 1)
            cur = servicePoints.model.get_db()
            cur.execute("INSERT INTO orgs(username, orgName, newMember, pointReq) VALUES (?, ?, ?, ?)", orgData)
            cur.execute("INSERT INTO users(username, fullname, email, orgName, "
                        "password, hours) VALUES (?, ?, ?, ?, ?, ?)", data)

            return flask.redirect(flask.url_for('index'))

    context = {}
    return render_template('createOrg.html', **context, msg=msg)

@servicePoints.app.route('/accounts/viewMemberPoints/', methods=['GET'])
def viewMemberPoints():
    if 'username' in flask.session:
        username = flask.session["username"]
        cursor = servicePoints.model.get_db()
        leaderCur = cursor.execute('SELECT orgName FROM orgs WHERE '
                    'username =:who',
                    {"who": username})
        results = leaderCur.fetchone()
        usersCur = cursor.execute('SELECT username, fullname, hours FROM users WHERE '
                    'orgName =:who',
                    {"who": results["orgName"]})
        hoursResults = usersCur.fetchall()
        context = {'org': results["orgName"], 'hours': hoursResults}
        return render_template('viewMemberPoints.html', **context)
    return flask.redirect(flask.url_for('login'))

@servicePoints.app.route('/accounts/viewRequests/', methods=['GET', 'POST'])
def viewRequests():

    if 'username' in flask.session:
        cursor = servicePoints.model.get_db()
        username = flask.session["username"]

        if flask.request.method == 'POST':
            if 'deny' in flask.request.form:
                post = flask.request.form["postid"]
                file = flask.request.form["filename"]
                serviceType = flask.request.form["service"]
                description = flask.request.form["reason"]
                cursor.execute('INSERT INTO pastRequests(member, service, points, description) VALUES '
                               '(:one,:two,:three,:four)', {"one": username, "two": serviceType, "three": 0, "four": description})
                cursor.execute('DELETE FROM requests WHERE postid =:one ', 
                {"one": post})
            if 'confirm' in flask.request.form:
                numHours = int(flask.request.form["numHours"])
                post = flask.request.form["postid"]
                user = flask.request.form["user"]
                file = flask.request.form["filename"]
                serviceType = flask.request.form["service"]
                hours = servicePoints.model.get_db().execute('SELECT hours FROM users WHERE username =:one ', 
                {"one": user})
                dbHours = hours.fetchone()
                dbHours["hours"] += numHours

                cursor.execute('UPDATE users SET hours =:one WHERE username =:two ', 
                             {"one": dbHours["hours"], "two": user})
                cursor.execute('INSERT INTO pastRequests(member, service, points, description) VALUES '
                               '(:one,:two,:three,:four)', {"one": username, "two": serviceType, "three": numHours, "four": ''})
                cursor.execute('DELETE FROM requests WHERE postid =:one ', {"one": post})

            if file != '':
                os.remove(os.path.join(servicePoints.app.config["IMAGES_FOLDER"], file))
                

        leaderCur = cursor.execute('SELECT postid, member, service, description, filename FROM requests WHERE '
                    'leader =:who',
                    {"who": username})
        results = leaderCur.fetchall()
        context = {'requests': results,'username': username, 'org': flask.session["orgName"], 'hours': flask.session["hours"]}
        return render_template('viewRequests.html', **context)
    return flask.redirect(flask.url_for('login'))

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
        tryfetch = leaderCur.fetchone()
        if tryfetch is None or tryfetch["orgName"] == "NONE":
            leader = 0
        else:
            leader = 1
        flask.session["leader"] = leader
        flask.session["hours"] = results["hours"]
        flask.session["orgName"] = results["orgName"]

        context = {'username': username, 'org': results["orgName"], 'hours': results["hours"], 
                   'leader': leader}
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
    # Delete Account
    username = (flask.session['username'])
    to_add = (username,)
    cur = servicePoints.model.get_db()

    if flask.session["leader"] == 1:
        leaderCur = cur.execute('SELECT orgName FROM orgs WHERE '
        'username =:who', {"who": username})
        results = leaderCur.fetchone()
        orgName = results["orgName"]
        cur.execute("DELETE from orgs WHERE orgName = ?", (orgName,))
        cur.execute("UPDATE users SET orgName = 'NONE' WHERE orgName = ?", (orgName,))
        cur.execute("UPDATE requests SET leader = 'pending' WHERE leader = ?", (username,))

    flask.session.clear()
    cur.execute('DELETE FROM users WHERE username=?', to_add)
    return flask.redirect(flask.url_for('login'))

@servicePoints.app.route('/accounts/deleteOrg/', methods=['GET', 'POST'])
def deleteOrg():
    # Delete Organization
    username = flask.session["username"]
    cursor = servicePoints.model.get_db()
    leaderCur = cursor.execute('SELECT orgName FROM orgs WHERE '
        'username =:who',
        {"who": username})
    results = leaderCur.fetchone()
    orgName = results["orgName"]
    cursor.execute("DELETE from orgs WHERE orgName = ?", (orgName,))
    cursor.execute("UPDATE users SET orgName = 'NONE' WHERE orgName = ?", (orgName,))
    cursor.execute("UPDATE requests SET leader = 'pending' WHERE leader = ?",
                            (username,))
    return flask.redirect(flask.url_for('index'))

@servicePoints.app.route('/accounts/mask/')
def mask():
    username = flask.session["username"]
    cursor = servicePoints.model.get_db()
    studentOrgCur = cursor.execute('SELECT orgName, hours FROM users WHERE '
                            'username =:who',
                            {"who": username})
    results = studentOrgCur.fetchone()
    context = {'username': username, 'org': results["orgName"], 'hours': results["hours"], 'leader': flask.session["leader"]}
    return render_template('mask.html', **context)

@servicePoints.app.route('/accounts/blood/')
def blood():
    username = flask.session["username"]
    cursor = servicePoints.model.get_db()
    studentOrgCur = cursor.execute('SELECT orgName, hours FROM users WHERE '
                            'username =:who',
                            {"who": username})
    results = studentOrgCur.fetchone()

    bloodDrives = cursor.execute('SELECT postid, poster, name, description, link FROM posts WHERE '
                            'service =:who',
                            {"who": 'blood'})
    bloodDs = bloodDrives.fetchall()

    # Add database info to context
    context = {'username': username, 'org': results["orgName"], 'hours': results["hours"], 
               'bloodDs': bloodDs, 'leader': flask.session["leader"]}

    return render_template('blood.html', **context)

@servicePoints.app.route('/accounts/food/')
def food():
    username = flask.session["username"]
    cursor = servicePoints.model.get_db()
    studentOrgCur = cursor.execute('SELECT orgName, hours FROM users WHERE '
                            'username =:who',
                            {"who": username})
    results = studentOrgCur.fetchone()

    foodDrives = cursor.execute('SELECT postid, poster, name, description, link FROM posts WHERE '
                            'service =:who',
                            {"who": 'food'})
    foodDs = foodDrives.fetchall()

    # Add database info to context
    context = {'username': username, 'org': results["orgName"], 'hours': results["hours"], 
               'foodDs': foodDs, 'leader': flask.session["leader"]}
    return render_template('food.html', **context)

@servicePoints.app.route('/accounts/profile/', methods=['GET', 'POST'])
def profile():
    msg = ''
    cursor = servicePoints.model.get_db()
    cur = cursor.execute("SELECT * FROM orgs")
    username = flask.session['username']
    orgs = cur.fetchall()
    cur = cursor.execute("SELECT fullname, email, orgName, hours from users WHERE username = ?", (username,))
    user = cur.fetchone()
    studentOrgCur = cursor.execute('SELECT orgName, hours FROM users WHERE '
                            'username =:who',
                            {"who": username})
    orgResults = studentOrgCur.fetchone()
    leaderCur = cursor.execute('SELECT orgName, newMember, pointReq FROM orgs WHERE '
                    'username =:who',
                    {"who": username})
    tryfetch = leaderCur.fetchone()
    if tryfetch is None or tryfetch["orgName"] == "NONE":
        leader = 0
        members = 0
        reqs = 0
    else:
        leader = 1
        members = tryfetch["newMember"]
        reqs = tryfetch["pointReq"]

    if flask.request.method == 'POST':
        #Join a new org
        if 'Notifications' in flask.request.form:
            memberBox = request.form.get('membersBox')
            reqsBox = request.form.get('reqsBox')
            if memberBox and members == 0:
                cur = servicePoints.model.get_db()
                members = 1
                cur.execute("UPDATE orgs SET newMember = 1")
                msg = 'Your email notification settings have been updated.'
                flash(msg)
            elif members == 1 and not memberBox:
                cur = servicePoints.model.get_db()
                members = 0
                cur.execute("UPDATE orgs SET newMember = 0")
                msg = 'Your email notification settings have been updated.'
                flash(msg)
            if reqsBox and reqs == 0:
                cur = servicePoints.model.get_db()
                reqs = 1
                cur.execute("UPDATE orgs SET pointReq = 1")
                msg = 'Your email notification settings have been updated.'
                flash(msg)
            elif reqs == 1 and not reqsBox:
                cur = servicePoints.model.get_db()
                reqs = 0
                cur.execute("UPDATE orgs SET pointReq = 0")
                msg = 'Your email notification settings have been updated.'
                flash(msg)
                
        if 'orgName' in flask.request.form:
            orgName = str(flask.request.form['orgName'])
            username = str(flask.session['username'])
            cur = servicePoints.model.get_db()
            curOrg = cur.execute('SELECT orgName FROM users WHERE username = ?',
                                        (username,))
            org = curOrg.fetchone()
            curOrg = cur.execute('SELECT fullname, email, hours FROM users WHERE username = ?',
                                        (username,))  
            userInfo = curOrg.fetchone()          
            pendingData = (flask.session['username'], userInfo['fullname'],
                userInfo['email'], orgName, userInfo['hours'])
            cursor = cur.execute('SELECT * FROM pendingOrgs WHERE username =:who', {"who": username})
            tryfetch = cursor.fetchone()
            if tryfetch is not None:
                cur.execute("DELETE from pendingOrgs WHERE username = ?", (username,))
            cur.execute("INSERT INTO pendingOrgs(username, fullname, email, orgName, "
                    "hours) VALUES (?, ?, ?, ?, ?)", pendingData)
            leaderCur = cursor.execute('SELECT username, newMember FROM orgs WHERE '
                                'orgName =:who',
                                {"who": orgName})
            results = leaderCur.fetchone()
            leader = results["username"]  
            memberS = results["newMember"] 
            if memberS:
                leaderEmailCur = cursor.execute('SELECT email, fullname FROM users WHERE '
                                    'username =:who',
                                    {"who": leader})
                results = leaderEmailCur.fetchone()
                leaderEmail = results["email"]  
                leaderName = results["fullname"]                
                emsg = Message("New Request to Join " + orgName,
                        sender=("ServicePoints", "servicePnts@gmail.com"),
                        recipients=[leaderEmail])
                emsg.body = "Hi " + leaderName + "! " + flask.session['username'] + " is requesting to join " + orgName
                mail.send(emsg)
            if org == "NONE":
                cur.execute('DELETE from orgs WHERE username = ?',
                                            (username,))
        # Leave current org and do not join new one
        elif 'noOrg' in flask.request.form:
            username = str(flask.session['username'])
            cur = servicePoints.model.get_db()
            cursor = cur.execute('SELECT * FROM pendingOrgs WHERE username =:who', {"who": username})
            tryfetch = cursor.fetchone()
            if tryfetch is not None:
                cur.execute("DELETE from pendingOrgs WHERE username = ?", (username,))
            cur.execute("UPDATE users SET orgName = 'NONE' WHERE username = ?",
                                        (username,))
            cur.execute("UPDATE requests SET leader = 'pending' WHERE member = ?",
                                        (username,))
            # Change name
        elif 'fullname' in flask.request.form: 
            fullName = str(flask.request.form['fullname'])
            username = str(flask.session['username'])
            cur = servicePoints.model.get_db()
            cur.execute('UPDATE users SET fullname = ? WHERE username = ?',
                                        (fullName, username,))
            # Change email
        elif 'email' in flask.request.form: 
            email = str(flask.request.form['email'])
            username = str(flask.session['username'])
            cur = servicePoints.model.get_db()
            cur.execute('UPDATE users SET email = ? WHERE username = ?',
                                        (email, username,))                           

    cur = cursor.execute('SELECT * FROM pendingOrgs WHERE username =:who', {"who": username})
    trypending = cur.fetchone()
    if trypending is None:
        pending = ''
    else:
        pending = trypending["orgName"]

        
    pendingReq = cursor.execute('SELECT service, description FROM requests WHERE '
                        'member =:who',
                        {"who": username})
    requests = pendingReq.fetchall()

    pastReq = cursor.execute('SELECT * FROM pastRequests WHERE '
                        'member =:who ORDER BY postid DESC',
                        {"who": username})
    pastRequests = pastReq.fetchmany(5)

    context = {"members": members, "reqs": reqs, "orgs": orgs, "fullname": user["fullname"], "email": user["email"], "username": username, "hours": orgResults["hours"],
        "org": user["orgName"], "leader": leader, "pending": pending, 'requests':requests, 'pastReq':pastRequests}
    return render_template('userProfile.html', **context, msg=msg)

@servicePoints.app.route('/images/<path:filename>', methods=['GET', 'POST'])
def images(filename):
    if "username" in flask.session:
        return flask.send_from_directory(servicePoints.app.config['IMAGES_FOLDER'], filename, as_attachment=True)
    return flask.redirect(flask.url_for('login'))

@servicePoints.app.route('/accounts/deleteTutor/', methods=['GET', 'POST'])
def deleteTutor():
    # Delete Tutor Account
    cur = servicePoints.model.get_db()
    cur.execute("DELETE from tutors WHERE username = ?", (flask.session['username'],))

    return flask.redirect(flask.url_for('tutorsu'))

@servicePoints.app.route('/accounts/updateTutor/', methods=['GET', 'POST'])
def updateTutor():
    flask.session['subjects'] = flask.request.form['subjects']
    flask.session['time'] = flask.request.form['time']

    data2 = (flask.session['subjects'], flask.session['time'],
            flask.session['username'])

    cur = servicePoints.model.get_db()
    cur.execute("UPDATE tutors SET subject=?, time=? WHERE username = ?", data2)

    return flask.redirect(flask.url_for('tutorsu'))

@servicePoints.app.route('/accounts/tutorsu/', methods=['GET', 'POST'])
def tutorsu():

    if flask.request.method == 'POST':
        flask.session['subjects'] = flask.request.form['subjects']
        flask.session['time'] = flask.request.form['time']

        data = (flask.session['username'], flask.session['subjects'],
                flask.session['time'])

        cur = servicePoints.model.get_db()
        cur.execute("INSERT INTO tutors(username, subject, time) VALUES (?, ?, ?)", data)

        return flask.redirect(flask.url_for('tutorsu'))

    cursor = servicePoints.model.get_db().cursor()
    username = flask.session["username"]

    cur = cursor.execute("SELECT subject, time FROM tutors")
    tutors = cur.fetchall()

    cur2 = cursor.execute('SELECT fullname, email FROM users WHERE username IN (SELECT username FROM tutors)')
    tutorsN = cur2.fetchall()

    studentOrgCur = cursor.execute('SELECT orgName, hours FROM users WHERE username =:who',
                            {"who": username})
    results = studentOrgCur.fetchone()

    # Add database info to context
    cur3 = cursor.execute('SELECT subject, time FROM tutors WHERE username =:who',
                            {"who": username})
    tutorInfo = cur3.fetchone()
    if not tutorInfo:
        registered = 0
        context = {"tutors": tutors, "tutorsN": tutorsN, 'username': username, 'org': results["orgName"], 
                   'hours': results["hours"], "registered": registered, 'leader': flask.session["leader"]}
    else:
        registered = 1
        context = {"tutors": tutors, "tutorsN": tutorsN, 'userSubjects': tutorInfo["subject"], "userTimes": tutorInfo["time"], 
               'username': username, 'org': results["orgName"], 'hours': results["hours"], 
               "registered": registered, 'leader': flask.session["leader"]}

    return flask.render_template("tutor.html", **context,zip=zip)

def allowed_image(filename):

    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in APP.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False


def allowed_image_filesize(filesize):

    if int(filesize) <= APP.config["MAX_IMAGE_FILESIZE"]:
        return True
    else:
        return False

@servicePoints.app.route('/accounts/submitPoints/', methods=['GET', 'POST'])
def submitPoints():
    if flask.request.method == 'POST':
        dummy, temp_filename = tempfile.mkstemp()
        file = flask.request.files["file"]
        serviceType = flask.request.form["service"]
        description = flask.request.form["description"]
        hash_filename_basename = ''
        msg = ''

        #Checks if a file has been submitted
        if "filesize" in request.cookies:

            # Checks if the photo is not too big
            if not allowed_image_filesize(request.cookies["filesize"]):
                msg = 'photo'

            else:
                # Checks if the file is an image 
                if allowed_image(file.filename):
                    file.save(temp_filename)

                    # Compute filename
                    hash_txt = sha256sum(temp_filename)
                    dummy, suffix = os.path.splitext(file.filename)
                    hash_filename_basename = hash_txt + suffix
                    hash_filename = os.path.join(servicePoints.app.config["IMAGES_FOLDER"],
                        hash_filename_basename)

                    # Move temp file to permanent location
                    shutil.move(temp_filename, hash_filename)
                else:
                    msg = 'photo'

        if msg == '':
            cursor = servicePoints.model.get_db()
            username = flask.session["username"]
            studentOrgCur = cursor.execute('SELECT orgName FROM users WHERE '
                            'username =:who',
                            {"who": username})
            results = studentOrgCur.fetchone()
            orgName = results["orgName"]
            if orgName == "NONE":
                leader = "pending"
            else:
                studentOrgLeader = cursor.execute('SELECT username, pointReq FROM orgs WHERE '
                                'orgName =:who',
                                {"who": orgName})
                results = studentOrgLeader.fetchone()
                leader = results["username"]
                pointsS = results["pointReq"]

            cursor.execute('INSERT INTO requests(member, leader, service, description, filename) VALUES '
                '(:one,:two,:three,:four,:five)', {"one": username, "two": leader, "three": serviceType, "four": description, "five": hash_filename_basename})
            if leader != "pending" and pointsS:
                leaderEmailCur = cursor.execute('SELECT email FROM users WHERE '
                                'username =:who',
                                {"who": leader})
                results = leaderEmailCur.fetchone()
                leaderEmail = results["email"]                
                emsg = Message("New Service Points Request",
                    sender=("ServicePoints", "servicePnts@gmail.com"),
                    recipients=[leaderEmail])
                emsg.body = "Hi " + leader + "! " + username + " is requesting service points for " + serviceType + ": " + description
                mail.send(emsg)
            flash('service')
        else:
            flash(msg)

    return flask.redirect(flask.url_for('index'))

@servicePoints.app.route('/accounts/submitService/', methods=['GET', 'POST'])
def submitService():
    if flask.request.method == 'POST':
        serviceType = flask.request.form["service"]
        description = flask.request.form["description"]
        name = flask.request.form["name"] 
        link = flask.request.form["link"]
        username = flask.session["username"]

        data = (username, serviceType, name, description, link)

        cursor = servicePoints.model.get_db()
        cursor.execute("INSERT INTO posts(poster, service, name, description, link) VALUES (?, ?, ?, ?, ?)", data)
        flash('post')
    
    return flask.redirect(flask.url_for('index'))

@servicePoints.app.route('/accounts/deleteService/<string:id>', methods=['GET','POST'])
def deleteService(id):
    flash('delete')
    cursor = servicePoints.model.get_db()
    cursor.execute('DELETE FROM posts WHERE postid=?', id)

    return flask.redirect(flask.url_for('blood'))
    pass

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
    if orgName == "NONE":
        context = {"leader": "[when you join a student org, your request will be sent to the student org leader]"}
    else:
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

@servicePoints.app.route('/accounts/manageOrg/', methods=['GET', 'POST'])
def manageOrg():
    if 'username' in flask.session:
        username = flask.session["username"]
        if flask.request.method == 'POST':
            # Adds user to org
            if 'add' in flask.request.form:
                cursor = servicePoints.model.get_db()
                leaderCur = cursor.execute('SELECT orgName FROM orgs WHERE '
                    'username =:who',
                    {"who": username})
                results = leaderCur.fetchone()
                orgName = results["orgName"]                
                cursor.execute("DELETE from pendingOrgs WHERE username = ?", (flask.request.form["user"],))
                cursor.execute('UPDATE users SET orgName = ? WHERE username = ? ', (orgName, flask.request.form["user"],))
                cursor.execute("UPDATE requests SET leader = ? WHERE member = ?",
                                        (username, flask.request.form["user"],)) 
                memberEmailCur = cursor.execute('SELECT email FROM users WHERE '
                                'username =:who',
                                {"who": flask.request.form["user"]})
                results = memberEmailCur.fetchone()
                memberEmail = results["email"]                
                emsg = Message("Approved Org Request",
                    sender=("ServicePoints", "servicePnts@gmail.com"),
                    recipients=[memberEmail])
                emsg.body = "Hi " + flask.request.form["user"] + "! Your request to join " + orgName + " has been approved."
                mail.send(emsg)
            # Denies user from org
            if 'deny' in flask.request.form:
                cursor = servicePoints.model.get_db()
                leaderCur = cursor.execute('SELECT orgName FROM orgs WHERE '
                    'username =:who',
                    {"who": username})
                results = leaderCur.fetchone()
                orgName = results["orgName"] 
                cursor.execute("DELETE from pendingOrgs WHERE username = ?", (flask.request.form["user"],))
                memberEmailCur = cursor.execute('SELECT email, fullname FROM users WHERE '
                    'username =:who', {"who": flask.request.form["user"]})                
                results = memberEmailCur.fetchone()
                memberEmail = results["email"]
                memberName = results["fullname"]                
                emsg = Message("Denied Org Request",
                    sender=("ServicePoints", "servicePnts@gmail.com"),
                    recipients=[memberEmail])
                emsg.body = "Hi " + memberName + "! Your request to join " + orgName + " has been denied."
                mail.send(emsg)
            # Removes user from org
            if 'remove' in flask.request.form:
                cursor = servicePoints.model.get_db()
                cursor.execute("UPDATE users SET orgName = 'NONE' WHERE username = ? ", (flask.request.form["user"],))
                cursor.execute("UPDATE requests SET leader = 'pending' WHERE member = ?",
                                        (flask.request.form["user"],))
        cursor = servicePoints.model.get_db()
        leaderCur = cursor.execute('SELECT orgName FROM orgs WHERE '
                    'username =:who',
                    {"who": username})
        results = leaderCur.fetchone()
        orgName = results["orgName"]

        membersCur = cursor.execute('SELECT * FROM users WHERE orgname =:who', {"who": orgName})
        members = membersCur.fetchall()
        pendingCur = cursor.execute('SELECT username, fullname, email, hours FROM pendingOrgs WHERE '
                    'orgName =:who',
                    {"who": orgName})
        pending = pendingCur.fetchall()
        context = {'org': orgName, 'members': members, 'username': username, 'pending': pending, 'hours': flask.session["hours"]}
        return render_template('manageOrg.html', **context)
    return flask.redirect(flask.url_for('login'))


def sha256sum(filename):
    """Return sha256 hash of file content, similar to UNIX sha256sum."""
    content = open(filename, 'rb').read()
    sha256_obj = hashlib.sha256(content)
    return sha256_obj.hexdigest()

