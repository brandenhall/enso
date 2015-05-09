from apa102 import APA102
from utils.conf import settings


leds = APA102(settings.LED_SPI_BUS, settings.LED_SPI_DEVICE, settings.LED_COUNT)


for i in range(settings.LED_COUNT / 3):
    leds[i * 3] = (255, 0, 0)
    leds[i * 3 + 1] = (0, 255, 0)
    leds[i * 3 + 2] = (0, 0, 255)

leds.update()
