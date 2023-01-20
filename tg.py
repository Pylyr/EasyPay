from typing import Any, Dict, cast
from global_init import API_TOKEN
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext import Updater, CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from db import *
from payment import get_payment_link, get_payment_status

START, ORDER_MENU, ORDER_SELECTION, ORDER_PAYMENT, CARDS_MENU, CARD, FAQ_MENU, FAQ_ANSWER, CONTACT_MENU, ADMIN_MENU, ADMIN_ADD_CARD, ADMIN_ORDERS, ORDER = range(
    13)

# START
ORDER_PAGE, MY_CARDS_PAGE, FAQ_PAGE, CONTACT_PAGE, ADMIN_PAGE = range(5)

# ORDER_MENU
ORDER10_70, ORDER75_145, ORDER150_250, ORDER_MENU_BACK = range(4)

# ORDER_SELECTION
ORDER_SELECTION_BACK = 0

# ORDER_PAYMENT
ORDER_CONFIRM, ORDER_DONE, ORDER_PAYMENT_BACK = range(3)

# CARDS_MENU
CARD_FULL, CARDS_MENU_BACK = range(2)

# CARD
CARD_DELETE_CONFIRM, CARD_DELETE_DONE, CARD_BACK = range(3)

# FAQ_MENU
USAGE, SERVICES, WORK, WHERE, REPLENISH, CVV, BILLING, EXPIRATION, WHAT_NOT, FAQ_MENU_BACK = range(10)

# FAQ_ANSWER
FAQ_ANSWER_BACK = 0

# CONTACT_MENU
CONTACT_MENU_BACK = 0

# ADMIN_MENU
ADMIN_MENU_BACK = 0

# ADMIN_ORDERS
ADMIN_ORDERS_BACK = 0

# ORDER
ORDER_COMPLETED, ORDER_BACK = range(2)

# ADMIN_ADD_CARD
ADMIN_ADD_CARD_BACK = 0

ORDER_DIV = {10: 5, 75: 10, 150: 25}
ORDER_COMISSION = {10: 2.95, 75: 3.95, 150: 4.95}


conn = create_connection("easypay.db")
ADMINS = [854079788, 891312329]


def fallback(update: Update, context: CallbackContext):
    del context.user_data['message_id']
    return start(update, context)


def start(update: Update, context: CallbackContext):
    keyboard = ([[
        InlineKeyboardButton(
            'Купить карту', callback_data=ORDER_PAGE)],
        [
        InlineKeyboardButton(
            'Мои Карты', callback_data=MY_CARDS_PAGE)],
        [
        InlineKeyboardButton(
            'FAQ', callback_data=FAQ_PAGE)],
        [
        InlineKeyboardButton(
            'Обратная связь', callback_data=CONTACT_PAGE)]])

    if update.effective_chat.id in ADMINS:
        keyboard.append([InlineKeyboardButton('Админка', callback_data=ADMIN_PAGE)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if "message_id" not in cast(Dict[str, Any], context.user_data):
        context.user_data["message_id"] = update.message.message_id + 1
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=start_message(),
                                 reply_markup=reply_markup)
    else:
        context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                      message_id=context.user_data["message_id"],
                                      text=start_message(),
                                      reply_markup=reply_markup)

    return START


def order_card_page(update: Update, context: CallbackContext):
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('От $10 до $70 (Комиссия $2.95)', callback_data=ORDER10_70)],
        [InlineKeyboardButton('От $75 до $145 (Комиссия $3.95)', callback_data=ORDER75_145)],
        [InlineKeyboardButton('От $150 до $250 (Комиссия $4.95)', callback_data=ORDER150_250)],
        [InlineKeyboardButton('Назад', callback_data=ORDER_MENU_BACK)]
    ])
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=order_card_message(),
                                  reply_markup=reply_markup)

    return ORDER_MENU


def order_card_generic(min: int, max: int, update: Update, context: CallbackContext):
    context.user_data['price_interval'] = (min, max)
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('Назад', callback_data=ORDER_SELECTION_BACK)]
    ])
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=input_order_amount_message(min, max),
                                  reply_markup=reply_markup)

    return ORDER_SELECTION


def order10_70(update: Update, context: CallbackContext):
    return order_card_generic(10, 70, update, context)


def order75_145(update: Update, context: CallbackContext):
    return order_card_generic(75, 145, update, context)


def order150_250(update: Update, context: CallbackContext):
    return order_card_generic(150, 250, update, context)


def order_card_input(update: Update, context: CallbackContext):
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('Назад', callback_data=ORDER_SELECTION_BACK)]
    ])
    amount = update.message.text
    if amount.isdigit():
        amount = int(amount)
        mini, maxi = context.user_data['price_interval']
        if mini <= amount <= maxi and amount % ORDER_DIV[mini] != 0:
            try:
                context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                              message_id=context.user_data["message_id"],
                                              text=not_divisible_by_message(ORDER_DIV[mini]),
                                              reply_markup=reply_markup)
            except:
                pass

            return ORDER_SELECTION

        elif mini <= amount <= maxi:
            context.user_data['amount'] = amount
            return order_card_payment(update, context)

    try:
        context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                      message_id=context.user_data["message_id"],
                                      text=invalid_amount_message(),
                                      reply_markup=reply_markup)
    except:
        pass

    return ORDER_SELECTION


def order_card_payment(update: Update, context: CallbackContext):
    payment_link, payment_id = get_payment_link(100 * context.user_data['amount'])
    context.user_data['payment_id'] = payment_id

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('Оплатить', url=payment_link)],
        [InlineKeyboardButton('Подтвердить платёж', callback_data=ORDER_CONFIRM)],
        [InlineKeyboardButton('Назад', callback_data=ORDER_PAYMENT_BACK)]
    ])
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=order_card_payment_message(context.user_data['amount']),
                                  reply_markup=reply_markup)
    return ORDER_PAYMENT


def notify_admins(context: CallbackContext, telegram_id: int, amount: int, payment_id: str):
    for admin in ADMINS:
        try:
            context.bot.send_message(chat_id=admin,
                                     text=order_card_admin_message(telegram_id, amount, payment_id))
        except:
            pass


def order_confirm(update: Update, context: CallbackContext):
    payment_id = context.user_data['payment_id']

    # if get_payment_status(payment_id) == "CONFIRMED":
    if True:
        notify_admins(context, update.effective_chat.id, context.user_data['amount'], payment_id)
        context.user_data['payment_id'] = None
        context.user_data['amount'] = None
        context.user_data['price_interval'] = None

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('В главное меню', callback_data=ORDER_DONE)]
        ])
        context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                      message_id=context.user_data["message_id"],
                                      text=order_successful_message(),
                                      reply_markup=reply_markup)
        return ORDER_PAYMENT
    else:
        try:
            context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                          message_id=context.user_data["message_id"],
                                          text=order_fail_message(),
                                          reply_markup=update.callback_query.message.reply_markup)
        except:
            pass
        return ORDER_PAYMENT


def my_cards_page(update: Update, context: CallbackContext):
    context.user_data["cards"] = get_cards(conn, update.effective_chat.id)
    keyboard = [[InlineKeyboardButton(f"{card}", callback_data=f"card{i}")]
                for i, card in enumerate(context.user_data["cards"])]
    keyboard.append([InlineKeyboardButton('Назад', callback_data=CARDS_MENU_BACK)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=my_cards_message(),
                                  reply_markup=reply_markup)

    return CARDS_MENU


def card_page(update: Update, context: CallbackContext):
    context.user_data["last_card"] = context.user_data["cards"][int(update.callback_query.data[4:])]
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('Удалить карту', callback_data=CARD_DELETE_CONFIRM)],
        [InlineKeyboardButton('Назад', callback_data=CARD_BACK)],
    ])
    card = context.user_data["cards"][int(update.callback_query.data[4:])]
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=card_message(card),
                                  reply_markup=reply_markup)

    return CARD


def card_delete_warning(update: Update, context: CallbackContext):
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Да', callback_data=CARD_DELETE_DONE)], [InlineKeyboardButton(
        'Нет', callback_data=f"card{context.user_data['cards'].index(context.user_data['last_card'])}")], ])
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=card_delete_warning_message(),
                                  reply_markup=reply_markup)

    return CARD


def card_delete_confirm(update: Update, context: CallbackContext):
    delete_card(conn, update.effective_chat.id, context.user_data["last_card"])
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('В главное меню', callback_data=CARD_BACK)],
    ])
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=card_deleted_message(),
                                  reply_markup=reply_markup)

    return CARD


def faq_page(update: Update, context: CallbackContext):
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('Как пользоваться виртуальной картой?',
                              callback_data=USAGE)],
        [InlineKeyboardButton('Какие сервисы можно оплатить с помощью виртуальной карты?',
                              callback_data=SERVICES)],
        [InlineKeyboardButton('Как работает вирутальная карта?',
                              callback_data=WORK)],
        [InlineKeyboardButton('Где я могу совершать покупки?',
                              callback_data=WHERE)],
        [InlineKeyboardButton('Можно ли пополнить баланс виртуальной карты?',
                              callback_data=REPLENISH)],
        [InlineKeyboardButton('Как узнать номер/срок действия/CVV виртуальной карты?',
                              callback_data=CVV)],
        [InlineKeyboardButton('Как узнать биллинг адрес виртуальной карты?',
                              callback_data=BILLING)],
        [InlineKeyboardButton('Какой срок действия виртуальной карты?',
                              callback_data=EXPIRATION)],
        [InlineKeyboardButton('Что нельзя делать?',
                              callback_data=WHAT_NOT)],
        [InlineKeyboardButton('Назад',
                              callback_data=FAQ_MENU_BACK)],
    ])
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=faq_message(),
                                  reply_markup=reply_markup)

    return FAQ_MENU


def faq_generic(faq_answer: str, update: Update, context: CallbackContext):

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('Назад',
                              callback_data=FAQ_ANSWER_BACK)],
    ])
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=faq_answer,
                                  reply_markup=reply_markup)

    return FAQ_ANSWER


def faq_usage(update: Update, context: CallbackContext):
    return faq_generic(faq_usage_answer(), update, context)


def faq_services(update: Update, context: CallbackContext):
    return faq_generic(faq_services_answer(), update, context)


def faq_work(update: Update, context: CallbackContext):
    return faq_generic(faq_work_answer(), update, context)


def faq_where(update: Update, context: CallbackContext):
    return faq_generic(faq_where_answer(), update, context)


def faq_replenish(update: Update, context: CallbackContext):
    return faq_generic(faq_replenish_answer(), update, context)


def faq_cvv(update: Update, context: CallbackContext):
    return faq_generic(faq_cvv_answer(), update, context)


def faq_billing(update: Update, context: CallbackContext):
    return faq_generic(faq_billing_answer(), update, context)


def faq_expiration(update: Update, context: CallbackContext):
    return faq_generic(faq_expiration_answer(), update, context)


def faq_what_not(update: Update, context: CallbackContext):
    return faq_generic(faq_what_not_answer(), update, context)


def contact_page(update: Update, context: CallbackContext):

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('Назад',
                              callback_data=CONTACT_MENU_BACK)],
    ])
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=contact_message(),
                                  reply_markup=reply_markup)
    return CONTACT_MENU


def admin_page(update: Update, context: CallbackContext):
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('Заказы', callback_data=ADMIN_ORDERS)],
        [InlineKeyboardButton('Добавить карту', callback_data=ADMIN_ADD_CARD)],
        [InlineKeyboardButton('Назад',
                              callback_data=ADMIN_MENU_BACK)],
    ])
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=admin_menu_message(),
                                  reply_markup=reply_markup)
    return ADMIN_MENU


def admin_orders(update: Update, context: CallbackContext):
    context.user_data["orders"] = get_orders(conn)
    keyboard = [[InlineKeyboardButton(f"{order}", callback_data=f"order{i}")]
                for i, order in enumerate(context.user_data["orders"])]

    keyboard.append([InlineKeyboardButton('Назад',
                                          callback_data=ADMIN_ORDERS_BACK)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=admin_orders_message(),
                                  reply_markup=reply_markup)
    return ADMIN_ORDERS


def close_order(update: Update, context: CallbackContext):
    delete_order(conn, context.user_data["last_order"])
    return admin_orders(update, context)


def order_page(update: Update, context: CallbackContext):
    order_id = int(update.callback_query.data[5:])
    order = context.user_data["orders"][order_id]
    context.user_data["last_order"] = order
    keyboard = [
        [InlineKeyboardButton('Закрыть заказ',
                              callback_data=ORDER_COMPLETED)],
        [InlineKeyboardButton('Назад',
                              callback_data=ORDER_BACK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=order_message(order),
                                  reply_markup=reply_markup)
    return ORDER


def admin_add_card(update: Update, context: CallbackContext):
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('Назад',
                              callback_data=ADMIN_MENU_BACK)],
    ])
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=admin_add_card_message(),
                                  reply_markup=reply_markup)
    return ADMIN_ADD_CARD


def notify_user(context: CallbackContext, telegram_id: str):
    context.bot.send_message(chat_id=telegram_id, text=f'Ваш заказ готов!')


def admin_add_card_input(update: Update, context: CallbackContext):
    entry_input = update.message.text.split(";")
    if len(entry_input) != 11:
        try:
            context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                          message_id=context.user_data["message_id"],
                                          text=falty_card_input_message(),
                                          reply_markup=update.callback_query.message.reply_markup)
        except:
            pass
        return ADMIN_ADD_CARD

    new_card(conn, *entry_input)
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('Назад',
                              callback_data=ADMIN_ADD_CARD_BACK)],
    ])
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=context.user_data["message_id"],
                                  text=admin_add_card_success_message(),
                                  reply_markup=reply_markup)
    notify_user(context, entry_input[0])
    return ADMIN_ADD_CARD


########## Texts ##########


def start_message():
    return f'Привет! Я бот EasyPay Bot. У меня ты можешь купить карту Visa/Mastercard для оплаты зарубежных подписок.'


def order_card_message():
    return f'Купить карту'


def input_order_amount_message(min: int, max: int):
    if min == 10:
        div = 5
    elif min == 75:
        div = 10
    else:
        div = 25
    return f'Введите сумму покупки в долларах (от {min} до {max}).\n' + \
        f'Внимание: сумма должна быть кратна {div}!'


def not_divisible_by_message(div: int):
    return f'Сумма должна быть кратна {div}. Попробуйте еще раз.'


def invalid_amount_message():
    return f'Неправильная сумма. Попробуйте еще раз.'


def order_card_payment_message(amount: int):
    return f'Оплатить ${amount}.'


def order_card_admin_message(telegram_id: int, amount: int, payment_id):
    return f'Пользователь {telegram_id} заказал карту на сумму ${amount}.\n' + \
        f'Платежный ID: {payment_id}'


def order_successful_message():
    return f'Заказ успешно оформлен!'


def order_fail_message():
    return f'Заказ не оформлен. Попробуйте еще раз.'


def my_cards_message():
    return f'Мои карты'


def card_message(card: Card):
    return f'Банк эмитент: {card.bank}\n' + \
        f'Номер карты: {card.card_number}\n' + \
        f'Срок действия: {card.expr_date}\n' + \
        f'CVV: {card.cvv}\n' + \
        f'Платежная система: {card.payment_system}\n' + \
        f'Адрес: {card.address}\n' + \
        f'Город: {card.city}\n' + \
        f'Штат: {card.state}\n' + \
        f'Почтовый индекс: {card.postal_code}\n' + \
        f'Страна: {card.country}\n' + \
        """* Перед использованием настоятельно рекомендуем
ознакомиться с разделом FAQ. Использовать только с
помощью VPN сервиса с местоположением США."""


def card_delete_warning_message():
    return f'Вы уверены, что хотите удалить карту? Это действие необратимо.'


def card_deleted_message():
    return f'Карта успешно удалена.'


def faq_message():
    return f'FAQ'


def faq_usage_answer():
    return """1) Оплата виртуальной картой должна
обязательно осуществляться с помощью VPN
сервиса (строго регион США)
2) Оплата только в долларах США.
3) При оплате могут запросить биллинг адрес.
В таком случае, используйте тот адрес,
который Вам был предоставлен при покупке
карты. Если Вы потеряли или забыли свой
биллинг адрес, воспользуйтесь разделом
"Моя карта".
4) Из-за того, что большинство инстранных
сервисов и подписок прекратили работу с
клиентами из России, использовать старый
аккаунт, зарегестрированный в России не
получится. Для успешной оплаты сервиса или
подписки необходимо в настройках аккаунта
сменить регион на США."""


def faq_services_answer():
    return """Какие сервисы можно
оплатить с помощью
виртуальной карты
Оплатить виртуальной картой можно
практически любой сервис и подписку,
которая принимает оплату с помощью Visa.
Мы регулярно проводим тестовые оплаты
различных сервисов (первостепенно - самые
популярные, такие как YouTube, Apple, Adobe
и тд). Для Вашего удобства, ниже можете
увидеть список* сервисов, которые успешно
прошли тестовую оплату с помощью
виртуальной карты:
1) YouTube
2) Steam
3) Adobe
4) Netflix
5) Canva
6) Spotify
7) Zoom
8) PlayStation
9) Google
10) Dropbox
* Список постоянно обновляется. Если
нужного Вам сервиса нет в списке и данный
сервис не принял у Вас оплату виртуальной
картой, обратитесь к нам в поддержку."""


def faq_work_answer():
    return """Принцип работы виртуальной карты ничем не отличается от
обычной пластиковой карты. Вам необходимо ввести номер
виртуальной карты, код и даты для того, чтобы совершить
оплату."""


def faq_where_answer():
    return """Выпуск виртуальной карты, которую мы предлогаем
осуществляется Американским банком. Использование
данной виртуальной карты предусматривается строго в
США. Исходя из этого, для успешной оплаты данной картой
какого либо сервиса, необходимо использовать VPN с
местоположением США, а так же в настройках аккаунта
сервиса изменить местоположение на США."""


def faq_replenish_answer():
    return """К сожалению, баланс виртуальной карты пополнить нельзя."""


def faq_cvv_answer():
    return """Перейдите в раздел "Мои Карты"""


def faq_billing_answer():
    return """Перейдите в раздел "Мои Карты"""


def faq_expiration_answer():
    return """Срок действия виртуальной карты 7 лет."""


def faq_what_not_answer():
    return """1) Оплачивать без использования VPN сервисов с
местоположением США
2) Пополнять баланс карты
3) Выбирать любые регионы подписок, кроме США
4) Переводить деньги с виртуальной карты на любую
другую банковскую карту
5) Оплачивать в любой валюте, кроме долларов США"""


def contact_message():
    return f'Если у тебя есть вопросы, то пиши в тех. поддержку: @easy_pay_bot_support'


def admin_menu_message():
    return f'Административное меню'


def admin_orders_message():
    return f'Заказы'


def order_message(order: Order):
    return f'ID пользователя: {order.telegram_id}\n' \
           f'Сумма: ${order.amount}\n' \
           f'PaymentId: {order.payment_id}\n' \
           f'Дата: {order.date}\n'


def admin_add_card_message():
    return f'Введите данные карты в данном формате:\n' + \
        f'Номер карты;Срок действия;CVV;Платежная система;Банк эмитент;' + \
        f'Телеграм пользователя;Адрес;Город;Штат;Почтовый индекс;Страна\n' + \
        f'Пример: 854079788;1234567890123456;01/21;123;Visa;Chase;12 Main;NYC;NY;123456;USA'


def falty_card_input_message():
    return f'Неправильный ввод. Попробуйте еще раз.'


def admin_add_card_success_message():
    return f'Карта успешно добавлена.'


updater = Updater(API_TOKEN, use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        START: [
            CallbackQueryHandler(faq_page, pattern=str(FAQ_PAGE)),
            CallbackQueryHandler(order_card_page, pattern=str(ORDER_PAGE)),
            CallbackQueryHandler(my_cards_page, pattern=str(MY_CARDS_PAGE)),
            CallbackQueryHandler(contact_page, pattern=str(CONTACT_PAGE)),
            CallbackQueryHandler(admin_page, pattern=str(ADMIN_PAGE)),
        ],
        ORDER_MENU: [
            CallbackQueryHandler(order10_70, pattern=str(ORDER10_70)),
            CallbackQueryHandler(order75_145, pattern=str(ORDER75_145)),
            CallbackQueryHandler(order150_250, pattern=str(ORDER150_250)),
            CallbackQueryHandler(start, pattern=str(ORDER_MENU_BACK)),
        ],
        ORDER_SELECTION: [
            CallbackQueryHandler(order_card_page, pattern=str(ORDER_SELECTION_BACK)),
            MessageHandler(Filters.text, order_card_input),
        ],
        ORDER_PAYMENT: [
            CallbackQueryHandler(order_confirm, pattern=str(ORDER_CONFIRM)),
            CallbackQueryHandler(order_card_page, pattern=str(ORDER_PAYMENT_BACK)),
            CallbackQueryHandler(start, pattern=str(ORDER_DONE)),
        ],
        CARDS_MENU: [
            CallbackQueryHandler(card_page, pattern=r'^card\d+$'),
            CallbackQueryHandler(start, pattern=str(CARDS_MENU_BACK)),
        ],
        CARD: [
            CallbackQueryHandler(card_delete_warning, pattern=str(CARD_DELETE_CONFIRM)),
            CallbackQueryHandler(card_page, pattern=r'^card\d+$'),
            CallbackQueryHandler(card_delete_confirm, pattern=str(CARD_DELETE_DONE)),
            CallbackQueryHandler(my_cards_page, pattern=str(CARD_BACK))
        ],
        FAQ_MENU: [
            CallbackQueryHandler(faq_usage, pattern=str(USAGE)),
            CallbackQueryHandler(faq_services, pattern=str(SERVICES)),
            CallbackQueryHandler(faq_work, pattern=str(WORK)),
            CallbackQueryHandler(faq_where, pattern=str(WHERE)),
            CallbackQueryHandler(faq_replenish, pattern=str(REPLENISH)),
            CallbackQueryHandler(faq_cvv, pattern=str(CVV)),
            CallbackQueryHandler(faq_billing, pattern=str(BILLING)),
            CallbackQueryHandler(faq_expiration, pattern=str(EXPIRATION)),
            CallbackQueryHandler(faq_what_not, pattern=str(WHAT_NOT)),
            CallbackQueryHandler(start, pattern=str(FAQ_MENU_BACK)),
        ],
        FAQ_ANSWER: [
            CallbackQueryHandler(faq_page, pattern=str(FAQ_ANSWER_BACK)),
        ],
        CONTACT_MENU: [
            CallbackQueryHandler(start, pattern=str(CONTACT_MENU_BACK)),
        ],
        ADMIN_MENU: [
            CallbackQueryHandler(admin_orders, pattern=str(ADMIN_ORDERS)),
            CallbackQueryHandler(admin_add_card, pattern=str(ADMIN_ADD_CARD)),
            CallbackQueryHandler(start, pattern=str(ADMIN_MENU_BACK)),
        ],
        ADMIN_ORDERS: [
            CallbackQueryHandler(order_page, pattern=r'^order\d+$'),
            CallbackQueryHandler(admin_page, pattern=str(ADMIN_ORDERS_BACK)),
        ],
        ORDER: [
            CallbackQueryHandler(close_order, pattern=str(ORDER_COMPLETED)),
            CallbackQueryHandler(admin_orders, pattern=str(ORDER_BACK)),
        ],
        ADMIN_ADD_CARD: [
            CallbackQueryHandler(admin_page, pattern=str(ADMIN_ADD_CARD_BACK)),
            MessageHandler(Filters.text, admin_add_card_input),
        ]

    },
    fallbacks=[CommandHandler('start', fallback)],

))
