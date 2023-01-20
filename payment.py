from typing import Tuple
import requests
import hashlib
import time


from global_init import TERMINAL, TERM_PASS


def sign_request(js: dict):

    js["Password"] = TERM_PASS
    jsl = sorted(js.items())
    jss = "".join([x[1] for x in jsl])
    j_hash = hashlib.sha256(jss.encode('utf-8'))
    js["Token"] = j_hash.hexdigest()
    del js["Password"]
    return js


def get_payment_link(price: int) -> Tuple[str, str]:

    headers = {'Content-type': 'application/json'}
    parms = {"TerminalKey": TERMINAL,
             "OrderId": f"{int(time.time())}",
             "Amount": f"{price}",
             "Receipt": {
                 "Email": "fundstrat@yandex.ru",
                 "Taxation": "usn_income_outcome",
                 "Items":
                 [
                     {
                         "Name": "Подписка Fundstrat GA Россия - 1 месяц",
                         "Price": f"{price}",
                         "Amount": f"{price}",
                         "Quantity": "1",
                         "Tax": "none"
                     }
                 ]
             }}
    r = requests.post('https://securepay.tinkoff.ru/v2/Init/',
                      json=parms,
                      headers=headers)
    return r.json()["PaymentURL"], r.json()["PaymentId"]


def get_payment_status(paymentId: str) -> str:
    ''' Retrieves the status of the payment '''

    headers = {'Content-type': 'application/json'}
    parms = {"TerminalKey": TERMINAL,
             "PaymentId": paymentId}

    r = requests.post('https://securepay.tinkoff.ru/v2/GetState',
                      json=sign_request(parms),
                      headers=headers)

    return r.json()["Status"]
