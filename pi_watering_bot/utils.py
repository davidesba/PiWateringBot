from functools import wraps

import attr

import ADS1115
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
class Sensor:
    name = attr.ib(type=str)
    pin = attr.ib(type=int)

    @property
    def value(self) -> float:
        return 0.0

    @property
    def wet(self) -> bool:
        return False


@attr.s
class AdcSensor(Sensor):
    threshold = attr.ib(type=float)

    @property
    def value(self) -> float:
        return ads.readADCSingleEnded(self.pin)

    @property
    def wet(self) -> bool:
        return self.value < self.threshold


@attr.s
class PinSensor(Sensor):
    def __attrs_post_init__(self):
        gpio.setup(self.pin, gpio.IN)

    @property
    def value(self) -> float:
        if gpio.input(self.pin) == gpio.HIGH:
            return 3.3
        return 0.0

    @property
    def wet(self) -> bool:
        return gpio.input(self.pin) == gpio.HIGH


@attr.s
class WateringMng:
    pump = attr.ib(type=int)

    def __attrs_post_init__(self):
        gpio.setwarnings(False)
        gpio.setup(self.pump, gpio.OUT, initial=gpio.LOW)

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
        return any(
            sensor.wet
            for sensor in sensors
        )


config = confight.load_app('pi-watering-bot')
sensors = list()
gpio.setmode(gpio.BCM)
ads = ADS1115.ADS1115()
for name, sensor in config['hardware']['sensors'].items():
    sensors.append(
        AdcSensor(name, sensor['pin'], sensor['threshold'])
        if sensor['type'] == 'adc'
        else PinSensor(name, sensor['pin'])
    )
