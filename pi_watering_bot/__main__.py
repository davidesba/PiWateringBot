from datetime import datetime, timedelta

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from pi_watering_bot.utils import WateringMng, authenticate, config
from telegram import Bot
from telegram.ext import CommandHandler, Updater


def program_off():
    mng.water_off()
    bot = Bot(config['bot']['bot-key'])
    for chat in config['allowed-user-ids'].values():
        bot.send_message(
            chat_id=chat,
            text='Water OFF'
        )


@authenticate
def start(update, context):
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text='Welcome to pi-watering-bot. Please issue a command.'
    )


@authenticate
def water_on(update, context):
    if context.args and not mng.pump_on:
        scheduler.add_job(
            program_off, 'date',
            run_date=datetime.now() + timedelta(seconds=int(context.args[0]))
        )
    mng.water_on()
    status(update, context)


@authenticate
def water_off(update, context):
    mng.water_off()
    status(update, context)


@authenticate
def status(update, context):
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text='Water %s\nSensor %s' % (
            'ON' if mng.pump_on else 'OFF',
            'ON' if mng.sensor_on else 'OFF'
        )
    )


mng = WateringMng(
    config['hardware']['pump-pin'],
    config['hardware']['sensor-pin']
)
scheduler = BackgroundScheduler(
    executors={
        'default': ThreadPoolExecutor(1)
    },
    jobstores={
        'default': SQLAlchemyJobStore(
            url='sqlite:////var/lib/pi-watering-bot/schedule.sqlite'
        )
    }
)
scheduler.start()
updater = Updater(config['bot']['bot-key'], use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('water_on', water_on))
dispatcher.add_handler(CommandHandler('water_off', water_off))
dispatcher.add_handler(CommandHandler('status', status))

updater.start_polling()
updater.idle()
