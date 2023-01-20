from dataclasses import dataclass
import sqlite3


@dataclass
class Card:
    bank: str
    card_number: str
    expr_date: str
    cvv: str
    payment_system: str
    address: str
    city: str
    state: str
    postal_code: str
    country: str

    def __repr__(self):
        card_number = self.card_number[:12] + '*' * 4
        return f"Карта {self.payment_system} {card_number}"


@dataclass
class Order:
    telegram_id: str
    amount: str
    payment_id: str
    date: str

    def __repr__(self):
        return f"Заказ на ${self.amount} от {self.telegram_id} ({self.date})"


def create_connection(db_file):
    return sqlite3.connect(db_file, check_same_thread=False)


def new_card(conn: sqlite3.Connection, *args):
    sql = '''INSERT INTO cards(telegram_id, bank, card_number, expr_date, cvv, payment_system, address, city, state, postal_code, country) VALUES(?,?,?,?,?,?,?,?,?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, args)
    conn.commit()
    return cur.lastrowid


def get_cards(conn: sqlite3.Connection, telegram_id: str):
    sql = '''SELECT * FROM cards WHERE telegram_id = ?'''
    cur = conn.cursor()
    cur.execute(sql, (telegram_id,))
    cards = [Card(*row[2:]) for row in cur.fetchall()]
    return cards


def delete_card(conn: sqlite3.Connection, telegram_id: str, card: Card):
    sql = '''DELETE FROM cards WHERE telegram_id = ? AND card_number = ?'''
    cur = conn.cursor()
    cur.execute(sql, (telegram_id, card.card_number))
    conn.commit()
    return cur.lastrowid


def new_order(conn: sqlite3.Connection, *args):
    sql = '''INSERT INTO orders(telegram_id, amount, payment_id, date) VALUES(?,?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, args)
    conn.commit()
    return cur.lastrowid


def get_orders(conn: sqlite3.Connection):
    sql = '''SELECT * FROM orders'''
    cur = conn.cursor()
    cur.execute(sql)
    orders = [Order(*row[1:]) for row in cur.fetchall()]
    return orders


def delete_order(conn: sqlite3.Connection, order: Order):
    sql = '''DELETE FROM orders WHERE telegram_id = ? AND payment_id = ?'''
    cur = conn.cursor()
    cur.execute(sql, (order.telegram_id, order.payment_id))
    conn.commit()
    return cur.lastrowid
