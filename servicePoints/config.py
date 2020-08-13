import os
from servicePoints.utils import key

APPLICATION_ROOT = '/'

SECRET_KEY = key()
SESSION_COOKIE_NAME = 'login'

IMAGES_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    'var', 'images'
)
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

DATABASE_FILENAME = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    'var', 'servicePoints.sqlite3'
)

