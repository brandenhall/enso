import math
import spidev


class APA102():

    def __init__(self, bus, device, speed, num_leds):
        self.bus = bus
        self.device = device
        self.speed = speed

        self.spi = spidev.SpiDev()
        self.spi.open(self.bus, self.device)
        self.spi.max_speed_hz = self.speed

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
            self.data[index + 1] >>= 1
            self.data[index + 2] >>= 1
            self.data[index + 3] >>= 1

    def close(self):
        self.clear()
        self.update()
        self.spi.close()

    def show_color(self, color):
        self.data = self.header + [255, color[2], color[1], color[0]] * self.num_leds + self.footer

    def add_color(self, key, value):
        index = 4 * (key + 1)
        self.data[index + 1] += min(255, value[2])
        self.data[index + 2] += min(255, value[1])
        self.data[index + 3] += min(255, value[0])

    def get_pixel(self, index):
        if index > -1 and index < self.num_leds:
            index = 4 * (index + 1)
            return (self.data[index + 3], self.data[index + 2], self.data[index + 1])
        else:
            return None

    def set_pixel(self, index, color):
        if index > -1 and index < self.num_leds:
            index = 4 * (index + 1)
            self.data[index + 1] = color[2]
            self.data[index + 2] = color[1]
            self.data[index + 3] = color[0]

    def update(self):
        try:
            self.spi.writebytes(self.data)
        except:
            self.spi.close()
            self.spi = spidev.SpiDev()
            self.spi.open(self.bus, self.device)
            self.spi.max_speed_hz = self.speed
