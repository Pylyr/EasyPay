import logging
from tg import updater

DEBUG = True

logging.basicConfig(
    format='%(asctime)s - %(filename)s - %(funcName)s (%(lineno)d) - %(levelname)s - %(message)s', level=logging.INFO,
)

if DEBUG:

    updater.start_polling()
else:
    pass
    # port = int(os.getenv('PORT', 4200))  # Heroku port

    # updater.start_webhook(listen="0.0.0.0",
    #                       port=port,
    #                       url_path=API_TOKEN,
    #                       webhook_url=f'https://fundstrat-subscription-bot.herokuapp.com/{API_TOKEN}')

    # updater.idle()
