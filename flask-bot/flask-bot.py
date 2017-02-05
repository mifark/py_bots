# -*- coding: utf-8 -*-

# This is a simple echo bot using decorators and webhook with flask
# It echoes any incoming text messages and does not use the polling method.

import flask
import telebot
import logging
import os
from Queue import Queue
from threading import Thread
import checktemp
import config
from threading import Timer

dirpath = os.path.dirname(__file__)
# Path to the ssl certificate
WEBHOOK_SSL_CERT = os.path.join(dirpath, 'webhook_cert.pem')
# Path to the ssl private key
WEBHOOK_SSL_PRIV = os.path.join(dirpath, 'webhook_pkey.pem')

# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

WEBHOOK_URL_BASE = "https://%s:%s" % (config.WEBHOOK_HOST, config.WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (config.bot_token)

logger = telebot.logger
logger.setLevel(logging.INFO)

bot = telebot.TeleBot(config.bot_token)
app = flask.Flask(__name__)

global_q = Queue()
basedata = {}


# global_q.put(basedata)

# Empty webserver index, return nothing, just http 200


@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''


# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message,
                 ("Hi there, I am EchoBot.\n"
                  "I am here to echo your kind words back to you."))


# Handle all other messages
@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    basedata[message.chat.username] = message.chat.id
    global_q.put(basedata)
    bot.reply_to(message, message.text)


def printchatid(in_q):
    while True:
        print global_q.get()


def process_with_timer(in_q):
    print "checked"
    if in_q.not_empty:
        data = in_q.get()
        if data.has_key(config.user):
            bot.send_message(basedata[config.user], checktemp.check_sensors())
        in_q.put(data)
    Timer(config.time, process_with_timer, (global_q,)).start()


Timer(config.time, process_with_timer, (global_q,)).start()

# t1 = Thread(target=printchatid, args=(global_q,))
# t1.start()

# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()
# Set webhook
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))
# Start flask server
app.run(host=config.WEBHOOK_LISTEN,
        port=config.WEBHOOK_PORT,
        ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV),
        debug=True)
