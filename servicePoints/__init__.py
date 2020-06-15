import flask
app = flask.Flask(__name__)
app.config.from_object('servicePoints.config')
app.config.from_envvar('SERVICEPOINTS_SETTINGS', silent=True)
import servicePoints.views
import servicePoints.model
