import datetime
import logging
import logging.config
import random
import serial
import signal
import glob
import time
import Queue

from datetime import timedelta
from PIL import Image
from apa102 import APA102
from utils.conf import settings
from utils.threading import run_background


from tornado.ioloop import IOLoop, PeriodicCallback

logger = logging.getLogger('enso')


class Particle():

    def __init__(self, leds, color, position, direction, speed):
        self.leds = leds
        self.color = color

        self.position = position
        self.direction = direction

        self.speed = speed
        self.frame = 0

    def update(self):
        try:
            self.leds.add_color(self.position, self.color)

            if self.frame >= self.speed:
                self.position += self.direction
                self.frame = 0
            else:
                self.frame += 1

            self.position %= self.leds.num_leds
        except:
            logger.exception('Particle update')


class Enso():

    def __init__(self):
        self.is_running = True
        self.is_exploding = False
        self.explosion = None
        self.explosion_name = ''
        self.explosion_frame = None
        self.explosion_position = None
        self.frame = 0

        self.reset_timeout = None

        self.game_sequence = None
        self.game_index = 0
        self.game_sequence_index = 0
        self.game_waiting = False

        self.mote = serial.Serial(settings.SERIAL_PORT, baudrate=settings.SERIAL_BAUD)
        self.mote.close()
        self.mote.open()

        self.particle_count = 0
        self.particles = [[], [], []]
        self.messaging = Queue.Queue()
        self.explosions = []
        self.controllers = [
            (False, None),
            (False, None),
            (False, None), ]

        logging.config.dictConfig(settings.LOGGING)
        signal.signal(signal.SIGTERM, self.sig_handler)
        signal.signal(signal.SIGINT, self.sig_handler)

        for name in glob.glob(settings.EXPLOSIONS_PATH):
            logger.info('Loading explosion {}...'.format(name))
            im = Image.open(name)
            self.explosions[name] = im.convert('RGB')

        self.leds = APA102(settings.LED_SPI_BUS, settings.LED_SPI_DEVICE, settings.LED_SPI_SPEED, settings.LED_COUNT)

    def mote_reader(self):
        read_buffer = []
        while self.is_running:
            try:
                datum = self.mote.read(1)

                if datum == '\n':
                    try:
                        particle_group = int(read_buffer[0]) - 2
                        command = read_buffer[1]
                        code = ord(read_buffer[2])

                    except:
                        read_buffer = []
                        continue

                    self.messaging.put((particle_group, command, code))

                    read_buffer = []

                else:
                    read_buffer.append(datum)
            except:
                logger.exception('Mote reader')

    def sig_handler(self, sig, frame):
        logger.warning('Caught signal: %s', sig)
        IOLoop.instance().add_callback(self.shutdown)

    def start(self):

        for i in range(3):
            self.mote.write(chr(2) + chr(0) + '\n')
            self.mote.write(chr(3) + chr(0) + '\n')
            self.mote.write(chr(4) + chr(0) + '\n')

        logger.info('Testing LEDs...')

        self.leds.show_color((255, 0, 0))
        self.leds.update()
        time.sleep(0.3)

        self.leds.show_color((255, 255, 0))
        self.leds.update()
        time.sleep(0.3)

        self.leds.show_color((0, 255, 0))
        self.leds.update()
        time.sleep(0.3)

        self.leds.show_color((0, 255, 255))
        self.leds.update()
        time.sleep(0.3)

        self.leds.show_color((0, 0, 255))
        self.leds.update()
        time.sleep(0.3)

        self.leds.show_color((255, 0, 255))
        self.leds.update()
        time.sleep(0.3)

        self.leds.show_color((255, 255, 255))
        self.leds.update()
        time.sleep(0.3)

        self.leds.show_color((0, 0, 0))
        self.leds.update()

        logger.info("Enable controllers...")
        self.set_controller_state(0, 1)

        time.sleep(0.2)
        self.set_controller_state(1, 1)

        time.sleep(0.2)
        self.set_controller_state(2, 1)

        logger.info("Starting Enso...")

        run_background(self.mote_reader)
        IOLoop.instance().add_callback(self.change_mode, self.standard_mode)

        IOLoop.instance().start()

    def start_explosion(self, position):
        self.is_exploding = True

        self.particles = [[], [], []]
        self.particle_count = 0
        self.leds.show_color((255, 255, 255))
        self.leds.update()

        self.is_exploding = True
        self.explosion_frame = 0
        self.frame = 0
        self.explosion_position = position

        # check for good images
        self.explosion = random.choice(self.explosions.values())

        self.set_all_controllers_state(0)

    def random_color(self, ranges):
        return (
            random.randint(ranges[0][0], ranges[0][1]),
            random.randint(ranges[1][0], ranges[1][1]),
            random.randint(ranges[2][0], ranges[2][1]),
        )

    def change_mode(self, next_mode):
        self.leds.show_color((255, 255, 255))
        self.leds.update()
        time.sleep(0.02)

        self.particle_count = 0
        self.particles = [[], [], []]

        for i in range(50):
            for x in range(9):
                self.leds.set_pixel(x*50 + i, (0, 0, 0))
            self.leds.update()
            time.sleep(0.02)

        # clear messages
        while not self.messaging.empty():
            self.messaging.get()
            self.messaging.task_done()

        self.set_all_controllers_state(1)

        self.update_loop = PeriodicCallback(next_mode, 1000/settings.FRAME_RATE)
        self.update_loop.start()

    def show_win(self):
        logger.info("WIN!")
        self.set_all_controllers_state(0)
        for i in range(settings.GAME_WIN_FRAMES):
            self.leds.show_color((0, 0, 0))
            for x in range(settings.GAME_WIN_SPARKLE):
                self.leds.set_pixel(random.randint(0, settings.LED_COUNT-1), (255, 255, 255))
            self.leds.update()

        self.set_all_controllers_state(1)
        IOLoop.instance().add_callback(self.change_mode, self.standard_mode)

    def game_mode(self):
        try:
            # first time through, make a sequence
            if self.game_sequence is None:
                self.game_sequence = []
                self.game_index = 0
                self.game_waiting = False
                for i in range(settings.GAME_SEQUENCE_SIZE):
                    self.game_sequence.append(random.randint(0, 2))

                self.set_all_controllers_state(1)
                time.sleep(0.5)

            # if we're not waiting, show the next sequence
            if not self.game_waiting:
                self.game_index += 1
                for i in range(self.game_index):
                    color = self.random_color(settings.PARTICLE_COLORS[self.game_sequence[i]])
                    self.leds.show_color(color)
                    self.leds.update()
                    time.sleep(settings.GAME_SHOW_TIME)

                    self.leds.show_color((0, 0, 0))
                    self.leds.update()
                    time.sleep(settings.GAME_BLANK_TIME)

                self.leds.show_color((0, 0, 0))
                self.leds.update()
                self.game_waiting = True
                self.game_time = datetime.datetime.now()
                self.game_sequence_index = 0

            # otherwise, listen for the sequence
            else:
                now = datetime.datetime.now()

                # timeout
                if (now - self.game_time).total_seconds() > settings.GAME_MOVE_TIME:
                    self.update_loop.stop()
                    self.game_sequence = None
                    self.update_loop.stop()
                    IOLoop.instance().add_callback(self.change_mode, self.standard_mode)

                while not self.messaging.empty():
                    item = self.messaging.get()

                    particle_group, command, code = item

                    if command == 'P':
                        if particle_group == self.game_sequence[self.game_sequence_index]:
                            self.game_sequence_index += 1

                            if self.game_sequence_index == self.game_index:

                                if self.game_index == len(self.game_sequence):
                                    self.messaging.task_done()
                                    self.update_loop.stop()
                                    self.show_win()
                                    return
                                else:
                                    self.game_waiting = False
                                    time.sleep(settings.GAME_NEXT_TIME)
                        else:
                            self.game_sequence = None
                            self.update_loop.stop()
                            IOLoop.instance().add_callback(self.change_mode, self.standard_mode)

                    self.messaging.task_done()

        except:
            logger.exception('Enso game mode')

    def standard_mode(self):
        try:
            while not self.messaging.empty():
                item = self.messaging.get()

                particle_group, command, code = item
                direction, speed = settings.PARTICLE_VECTOR[code]

                if self.reset_timeout is not None:
                    IOLoop.instance().remove_timeout(self.reset_timeout)

                self.reset_timeout = IOLoop.instance().add_timeout(timedelta(seconds=settings.RESET_TIMEOUT), self.change_mode, self.standard_mode)

                if command == 'S':
                    for particle in self.particles[particle_group]:
                        particle.speed = speed
                        particle.direction = direction

                elif command == 'P':
                    self.controllers[particle_group] = (True, datetime.datetime.now())

                    states, timestamps = zip(*self.controllers)
                    timestamps = list(timestamps)

                    # if all 3 buttons pressed at the same time, enter game mode
                    if all(states):
                        timestamps.sort()
                        if (timestamps[-1] - timestamps[0]).total_seconds() < 1.5:
                            self.update_loop.stop()
                            self.game_sequence = None
                            self.particles = [[], [], []]
                            self.particle_count = 0
                            IOLoop.instance().add_callback(self.change_mode, self.game_mode)

                            # no reset in game mode!
                            if self.reset_timeout is not None:
                                IOLoop.instance().remove_timeout(self.reset_timeout)
                            return

                elif command == 'R':

                    self.controllers[particle_group] = (False, None)

                    if not self.is_exploding and len(self.particles[particle_group]) < settings.PARTICLE_COLOR_MAX:
                        p = Particle(
                            self.leds,
                            self.random_color(settings.PARTICLE_COLORS[particle_group]),
                            settings.PARTICLE_POSITIONS[particle_group],
                            direction,
                            speed)

                        self.particles[particle_group].append(p)
                        self.particle_count += 1

                        self.set_controller_state(particle_group, 0)

                self.messaging.task_done()

            if not self.is_exploding:
                self.frame += 1

                if self.frame >= settings.FADE_STEP:
                    self.leds.darken()
                    self.frame = 0

                for particle_group in self.particles:
                    for particle in particle_group:
                        particle.update()

                run_background(self.leds.update)

                if self.particle_count == 3:
                    first = self.particles[0][0].position
                    checks = [self.particles[1][0].position, self.particles[2][0].position]

                    found = 0
                    for i in range(first - settings.EXPLOSION_RANGE, first + settings.EXPLOSION_RANGE):
                        c = i
                        if i < 0:
                            c = settings.LED_COUNT + i
                        elif i >= settings.LED_COUNT:
                            c -= settings.LED_COUNT
                        if c in checks:
                            found += 1

                    if found == 2:
                        self.start_explosion(first)

            else:
                self.frame += 1

                if self.frame >= settings.EXPLOSION_STEP:

                    self.frame = 0
                    self.leds.clear()

                    try:
                        width, height = self.explosion.size

                        for i in range(width):
                            self.leds.set_pixel((i - self.explosion_position) % width, self.explosion.getpixel((i, self.explosion_frame)))
                    except:
                        logger.exception('Problem with image "{}"'.format(self.explosion_name))
                        self.is_exploding = False
                        self.leds.show_color((0, 0, 0))

                    self.explosion_frame += 1
                    if self.explosion_frame >= (height - 1) or not self.is_exploding:
                        self.is_exploding = False
                        self.explosion_position = None
                        self.explosion_frame = None
                        self.explosion = None

                        self.set_all_controllers_state(1)

                        self.leds.show_color((0, 0, 0))

                    run_background(self.leds.update)

        except:
            logger.exception('Enso standard mode')

    def set_controller_state(self, controller, state):
        for i in range(settings.CONTROLLER_REPEAT):
            self.mote.write(chr(controller + 2) + chr(state) + '\n')
            time.sleep(settings.CONTROLLER_REPEAT_DELAY)

    def set_all_controllers_state(self, state):
        for i in range(settings.CONTROLLER_REPEAT):
            time.sleep(settings.CONTROLLER_REPEAT_DELAY)
            self.mote.write(chr(2) + chr(state) + '\n')
            time.sleep(settings.CONTROLLER_REPEAT_DELAY)
            self.mote.write(chr(3) + chr(state) + '\n')
            time.sleep(settings.CONTROLLER_REPEAT_DELAY)
            self.mote.write(chr(4) + chr(state) + '\n')

    def shutdown(self):
        logger.info('Stopping Enso...')

        self.set_all_controllers_state(0)

        self.leds.close()
        self.is_running = False

        try:
            pass

        except Exception as err:
            logger.error("could not close servers gracfully. {}".format(err))

        finally:
            IOLoop.instance().stop()
            logger.info('Shutdown')


if __name__ == "__main__":
    enso = Enso()
    enso.start()
