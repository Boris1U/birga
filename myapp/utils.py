import requests
from binance.spot import Spot

from datetime import datetime, timedelta


def binance_get_account(api_key, api_secret):
    client = Spot(api_key=api_key, api_secret=api_secret)
    client.account()


def binance_get_history(api_key, api_secret):
    clean_data = []
    now = datetime.now()
    try:
        client = Spot(api_key=api_key, api_secret=api_secret)
        history = []
        history += client.c2c_trade_history('buy').get('data')
        history += client.c2c_trade_history('sell').get('data')

    except Exception:
        return clean_data


    for item in history:
        clean_data.append({
            'currency': item.get('asset').lower(),
            'birja': 'Binance',
            'created_at': datetime.fromtimestamp(item.get('createTime') / 1000.0),
            'side': item.get('tradeType').lower(),
            'price': item.get('unitPrice'),
            'volume': item.get('amount'),
            'total_price': item.get('totalPrice'),
        })
    clean_data = sorted(clean_data, key=lambda x: x['created_at'], reverse=True)
    return clean_data



def garantex_get_token(private_key, uid):
    resp = requests.post('https://garantex.io/api_test', data={'secret_key': private_key, 'uid': uid})
    if resp.status_code == '200':
        resp.json()['data']['token']
    else:
        return None


def garantex_get_history(token):
    history = []

    if not token:
        return history
    try:
        history += requests.get('https://garantex.io/api/v2/otc/deals', headers={'Authorization': 'Bearer {}'.format(token)}).json()
        clean_data = []
        for item in history:
            clean_data.append({
                'currency': item.get('currency'),
                'birja': 'Garantex',
                'created_at': datetime.strptime(item["created_at"], '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None),
                'side': item.get('direction'),
                'price': item.get('price'),
                'volume': item.get('amount'),
                'total_price': item.get('volume'),
            })
    except Exception:
        return history
        
    return history
    