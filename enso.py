import glob
import logging
import logging.config
import os
import random
import serial
import signal
import sys
import time
import Queue

import Adafruit_BBIO.UART as UART

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
        self.explosion_timeout = None
        self.explosion = None
        self.explosion_frame = None
        self.explosion_position = None
        self.frame = 0

        self.mote = serial.Serial(settings.SERIAL_PORT, baudrate=settings.SERIAL_BAUD)
        self.mote.close()
        self.mote.open()

        self.mote.write(chr(2) + chr(1) + '\n')
        self.mote.write(chr(3) + chr(1) + '\n')
        self.mote.write(chr(4) + chr(1) + '\n')

        self.particles = [[], [], []]
        self.messaging = Queue.Queue()

        logging.config.dictConfig(settings.LOGGING)
        signal.signal(signal.SIGTERM, self.sig_handler)
        signal.signal(signal.SIGINT, self.sig_handler)

        if not os.path.exists(settings.PATTERNS_PATH):
            logger.error('PATTERNS_PATH does not exist!')
            sys.exit(0)

        self.explosion_animations = []

        for explosion_path in glob.glob(os.path.join(settings.PATTERNS_PATH, '*.png')):
            logger.info('Loading "{}"...'.format(os.path.basename(explosion_path)))
            im = Image.open(explosion_path)
            self.explosion_animations.append(im.convert('RGB'))

        self.leds = APA102(settings.LED_SPI_BUS, settings.LED_SPI_DEVICE, settings.LED_COUNT)

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

        logger.info("Starting Enso...")

        self.draw_loop = PeriodicCallback(self.update, 1000/settings.FRAMERATE_STANDARD)
        self.draw_loop.start()

        run_background(self.mote_reader)

        IOLoop.instance().start()

    def start_explosion(self):
        self.is_exploding = True

        self.particles = [[], [], []]
        self.leds.show_color((255, 255, 255))

        self.is_exploding = True
        self.explosion_timeout = None
        self.explosion_frame = 0
        self.explosion_position = int(settings.LED_COUNT / 2)

        width = None
        height = None

        self.draw_loop.callback_time = 1000/settings.FRAMERATE_EXPLOSION

        # check for good images
        while width is None:
            self.explosion = random.choice(self.explosion_animations)
            width, height = self.explosion.size

        self.explosion_frame = 0
        try:
            self.mote.write(chr(2) + chr(0) + '\n')
            self.mote.write(chr(3) + chr(0) + '\n')
            self.mote.write(chr(4) + chr(0) + '\n')
        except:
            logger.exception("Can't write to mote!")

    def random_color(self, ranges):
        return (
            random.randint(ranges[0][0], ranges[0][1]),
            random.randint(ranges[1][0], ranges[1][1]),
            random.randint(ranges[2][0], ranges[2][1]),
        )

    def update(self):
        try:
            if not self.messaging.empty():
                item = self.messaging.get()

                particle_group, command, code = item
                direction, speed = settings.PARTICLE_VECTOR[code]

                if command == 'S':
                    for particle in self.particles[particle_group]:
                        particle.speed = speed
                        particle.direction = direction

                elif command == 'F':

                    if self.explosion_timeout is not None:
                        IOLoop.instance().remove_timeout(self.explosion_timeout)

                    self.explosion_timeout = IOLoop.instance().add_timeout(timedelta(seconds=settings.EXPLOSION_DELAY), self.start_explosion)

                    if not self.is_exploding and len(self.particles[particle_group]) < settings.PARTICLE_COLOR_MAX:
                        p = Particle(
                            self.leds,
                            self.random_color(settings.PARTICLE_COLORS[particle_group]),
                            0,
                            direction,
                            speed)

                        self.particles[particle_group].append(p)

                        if len(self.particles[particle_group]) == settings.PARTICLE_COLOR_MAX:
                            self.mote.write(chr(particle_group + 2) + chr(0) + '\n')

                self.messaging.task_done()

            if not self.is_exploding:
                self.frame += 1

                if self.frame % settings.FADE_STEP == 0:
                    self.leds.darken()
                    self.frame = 0

                for particle_group in self.particles:
                    for particle in particle_group:
                        particle.update()

            else:
                self.leds.clear()

                try:
                    width, height = self.explosion.size
                    offset = width / 2 - self.explosion_position

                    for i in range(width):
                        self.leds[(i - offset) % width] = self.explosion.getpixel((i, self.explosion_frame))
                except:
                    logger.exception("Problem with image")
                    self.is_exploding = False

                self.explosion_frame += 1
                if self.explosion_frame == height or not self.is_exploding:
                    self.is_exploding = False
                    self.explosion_position = None
                    self.explosion_frame = None
                    self.explosion = None

                    self.mote.write(chr(2) + chr(1) + '\n')
                    self.mote.write(chr(3) + chr(1) + '\n')
                    self.mote.write(chr(4) + chr(1) + '\n')

                    self.draw_loop.callback_time = 1000/settings.FRAMERATE_STANDARD

            self.leds.update()
        except:
            logger.exception('Enso update')

    def shutdown(self):
        logger.info('Stopping Enso...')

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
    try:
        UART.setup("UART1")
    except:
        logging.info("Could not setup UART1!")
    enso = Enso()
    enso.start()
