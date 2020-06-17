import os

APPLICATION_ROOT = '/'

SECRET_KEY = b'''\xf4\xb2\x9f\x80\xb1\xef\x01\xc6\x10
\xca\xdd\x84\xd4\xf3\x0c\x95\xad\xa6\xdc\xaf\xd3\xbeI\xf7'''
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

