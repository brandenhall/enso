import math
from Adafruit_BBIO.SPI import SPI


class APA102():

    def __init__(self, bus, device, num_leds):
        self.bus = bus
        self.device = device
        self.spi = SPI(self.bus, self.device)
        self.num_leds = num_leds
        self.header = [0, 0, 0, 0]
        self.footer = [0, ] * int(math.ceil(self.num_leds / 16.0))
        self.clear_state = self.header + [255, 0, 0, 0] * self.num_leds + self.footer
        self.clear()

    def clear(self):
        self.data = self.clear_state[:]

    def darken(self):
        for i in range(self.num_leds):
            index = 4 * (i + 1)
            self.data[index + 3] = self.data[index + 3] >> 1
            self.data[index + 1] = self.data[index + 1] >> 1
            self.data[index + 2] = self.data[index + 2] >> 1

    def close(self):
        self.clear()
        self.update()
        self.spi.close()

    def show_color(self, color):
        self.data = self.header + [255, color[1], color[2], color[0]] * self.num_leds + self.footer

    def add_color(self, key, value):
        index = 4 * (key + 1)
        self.data[index + 3] += value[0]
        self.data[index + 1] += value[1]
        self.data[index + 2] += value[2]

    def __getitem__(self, key):
        if key > -1 and key < self.num_leds:
            index = 4 * (key + 1)
            return (self.data[index + 3], self.data[index + 1], self.data[index + 2])
        else:
            return None

    def __setitem__(self, key, value):
        if key > -1 and key < self.num_leds:
            index = 4 * (key + 1)
            self.data[index + 3] = value[0]
            self.data[index + 1] = value[1]
            self.data[index + 2] = value[2]

    def update(self):
        try:
            self.spi.writebytes(self.data)
        except:
            self.spi.close()
            self.spi = SPI(self.bus, self.device)

