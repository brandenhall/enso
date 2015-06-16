import time

from apa102 import APA102
from utils.conf import settings


leds = APA102(settings.LED_SPI_BUS, settings.LED_SPI_DEVICE, settings.LED_SPI_SPEED, settings.LED_COUNT)


leds.show_color((255, 0, 0))
leds.update()
time.sleep(1)

leds.show_color((0, 255, 0))
leds.update()
time.sleep(1)

leds.show_color((0, 0, 255))
leds.update()
time.sleep(1)

leds.show_color((0, 0, 0))
leds.update()
