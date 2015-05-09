FRAMERATE_STANDARD = 180
FRAMERATE_EXPLOSION = 60
TRAIL_SIZE = 12

SERIAL_PORT = '/dev/ttyO1'
SERIAL_BAUD = 9600

FADE_STEP = 8

EXPLOSION_DELAY = 30

PARTICLE_LIFE_MIN = 8
PARTICLE_LIFE_MAX = 32
PARTICLE_COLOR_MAX = 3
PARTICLE_COLORS = [
    ((255, 255), (0, 0), (0, 0)),
    ((0, 0), (255, 255), (0, 0)),
    ((0, 0), (0, 0), (255, 255)),
]
PARTICLE_VECTOR = [
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8),
    (-1, 8), (-1, 7), (-1, 6), (-1, 5), (-1, 4), (-1, 3), (-1, 2), (-1, 1),
]


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "%(asctime)s.%(msecs).03d %(levelname)s [%(module)s:%(lineno)s] %(message)s",
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
    },
    'handlers': {
        'logfile': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "/var/log/enso/enso.log",
            'maxBytes': 1000000,
            'backupCount': 4,
            'formatter': 'standard',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'root': {
        'handlers': ['logfile', 'console', ],
        'propagate': True,
        'level': 'WARNING',
    },
    'loggers': {
        'enso': {
            'handlers': ['logfile', 'console', ],
            'propagate': False,
            'level': 'INFO',
        },
    },
}
