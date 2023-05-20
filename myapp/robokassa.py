import decimal
import hashlib
from urllib import parse


PASS1 = 'pDB2c8CHJ3HUV56nUmoX'
PASS2 = 'jg2Yx21tvP1tVDQ9shFk'


def calculate_signature(*args) -> str:
    """Create signature MD5.
    """
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


def check_signature_result(
    order_number: int,  # invoice number
    received_sum: decimal,  # cost of goods, RU
    received_signature: hex,  # SignatureValue
    password: str  # Merchant password
) -> bool:
    signature = calculate_signature('UMBRELLA_TRADING', received_sum, order_number, password)
    with open('logs', 'a') as f:
        f.write(received_signature + ' ' + signature)
    if signature.lower() == received_signature.lower():
        return True
    return False


# Формирование URL переадресации пользователя на оплату.

def generate_payment_link(
    cost: decimal,  # Сумма
    number: int,  # Номер заказа
    # description: str,  # Описание покупки
    is_test = 0,
    robokassa_payment_url = 'https://auth.robokassa.ru/Merchant/Index.aspx',
) -> str:
    """URL for redirection of the customer to the service.
    """
    signature = calculate_signature(
        'UMBRELLA_TRADING',
        cost,
        number,
        PASS1,
    )

    data = {
        'MerchantLogin': 'UMBRELLA_TRADING',
        'OutSum': cost,
        'InvoiceID': number,
        # 'Description': description,
        'SignatureValue': signature,
        'IsTest': is_test
    }
    return f'{robokassa_payment_url}?{parse.urlencode(data)}'


# Получение уведомления об исполнении операции (ResultURL).

def result_payment(request: dict) -> str:
    """Verification of notification (ResultURL).
    :param request: HTTP parameters.
    """
    # param_request = parse_response(request)
    param_request = request
    cost = param_request.get('OutSum', '')
    number = param_request.get('InvId', '')
    signature = param_request.get('SignatureValue', '')


    if check_signature_result(number, cost, signature, PASS2):
        return True, f'OK{param_request["InvId"]}'
    return False, "bad sign"
