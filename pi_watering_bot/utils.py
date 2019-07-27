from functools import wraps

import attr
import confight
import RPi.GPIO as gpio


def authenticate(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if args[0].message.from_user.id not in config[
            'allowed-user-ids'
        ].values():
            args[1].bot.send_message(
                chat_id=args[0].message.chat_id,
                text='User not allowed for this bot'
            )
            return
        return f(*args, **kwargs)
    return wrapped


@attr.s
class WateringMng:
    pump = attr.ib(type=int)
    sensor = attr.ib(type=int)

    def __attrs_post_init__(self):
        gpio.setwarnings(False)
        gpio.setmode(gpio.BOARD)
        gpio.setup(self.pump, gpio.OUT, initial=gpio.LOW)
        gpio.setup(self.sensor, gpio.IN)

    def water_on(self):
        if not self.pump_on and not self.sensor_on:
            gpio.output(self.pump, gpio.HIGH)

    def water_off(self):
        if self.pump_on:
            gpio.output(self.pump, gpio.LOW)

    @property
    def pump_on(self) -> bool:
        return gpio.input(self.pump) == gpio.HIGH

    @property
    def sensor_on(self) -> bool:
        return gpio.input(self.sensor) == gpio.HIGH


config = confight.load_app('pi-watering-bot')
