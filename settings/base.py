FRAME_RATE = 300
EXPLOSION_STEP = 10
TRAIL_SIZE = 18

CONTROLLER_REPEAT = 3
CONTROLLER_REPEAT_DELAY = 0.05

GAME_SHOW_TIME = 0.4
GAME_BLANK_TIME = 0.1
GAME_MOVE_TIME = 4
GAME_NEXT_TIME = 0.5
GAME_SEQUENCE_SIZE = 9
GAME_WIN_FRAMES = 3000
GAME_WIN_SPARKLE = 10

RESET_TIMEOUT = 60

SERIAL_PORT = '/dev/ttyAMA0'
SERIAL_BAUD = 9600

FADE_STEP = 20

EXPLOSION_RANGE = 10

PARTICLE_COLOR_MAX = 1
PARTICLE_COLORS = [
    ((255, 255), (0, 2), (0, 2)),
    ((0, 2), (255, 255), (0, 2)),
    ((0, 2), (0, 2), (255, 255)),
]
PARTICLE_POSITIONS = [0, 150, 300]
PARTICLE_VECTOR = [
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8),
    (-1, 8), (-1, 7), (-1, 6), (-1, 5), (-1, 4), (-1, 3), (-1, 2), (-1, 1),
]

EXPLOSIONS_PATH = 'patterns/lhc/*.png'

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
