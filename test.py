
from db import create_connection, get_cards, get_orders, new_card, new_order

conn = create_connection("easypay.db")


conn.execute("DROP TABLE IF EXISTS cards")
conn.execute("DROP TABLE IF EXISTS orders")

sqlite_create_table_cards = '''CREATE TABLE IF NOT EXISTS cards (
                                id INTEGER PRIMARY KEY,
                                telegram_id TEXT NOT NULL,
                                bank TEXT NOT NULL,
                                card_number TEXT NOT NULL,
                                expr_date TEXT NOT NULL,
                                cvv TEXT NOT NULL,
                                payment_system TEXT NOT NULL,
                                address TEXT NOT NULL,
                                city TEXT NOT NULL,
                                state TEXT,
                                postal_code TEXT NOT NULL,
                                country TEXT NOT NULL
                            );'''

sqlite_create_table_orders = '''CREATE TABLE IF NOT EXISTS orders (
                                id INTEGER PRIMARY KEY,
                                telegram_id TEXT NOT NULL,
                                amount TEXT NOT NULL,
                                payment_id TEXT NOT NULL,
                                date TEXT NOT NULL
                                );'''


cursor = conn.cursor()

cursor.execute(sqlite_create_table_cards)
cursor.execute(sqlite_create_table_orders)

new_card(conn, "854079788", "Bank of America", "123456789", "12/2021", "123",
         "Visa", "123 Main St", "New York", "NY", "12345", "USA")
new_card(conn, "854079788", "Chase", "987654321", "12/2021", "123",
         "Mastercard", "456 Main St", "New York", "NY", "12345", "USA")
print(get_cards(conn, "854079788"))
new_order(conn, "854079788", "100", "123456789", "12/12/2020")
print(get_orders(conn))

cursor.close()
# save (commit) the changes
