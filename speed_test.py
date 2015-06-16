import time
import datetime

from apa102 import APA102
from utils.conf import settings


leds = APA102(settings.LED_SPI_BUS, settings.LED_SPI_DEVICE, settings.LED_SPI_SPEED, settings.LED_COUNT)


leds.show_color((0, 0, 0))
leds.update()
time.sleep(2)

a = datetime.datetime.now()

red = (255, 0, 0)
for i in range(450):
    leds.set_pixel(i, red)
    leds.update()

print(datetime.datetime.now() - a)
