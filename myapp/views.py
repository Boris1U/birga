from django.contrib.auth import (authenticate, decorators, forms, login,
                                 logout, update_session_auth_hash)
from django.http import request, response, FileResponse, HttpResponse
from django.shortcuts import redirect, render
from django.db.models import Sum, Count
from django.views.decorators.csrf import csrf_exempt

from django.db.models.functions import TruncMonth

import requests, bs4

import pandas as pd
import openpyxl

from . import robokassa


from binance.spot import Spot

from .models import News, History, PayHistory, Profile, Type
from .forms import ProfileCreationForm
from .utils import garantex_get_token, garantex_get_history, binance_get_account, binance_get_history

from datetime import datetime as dt
from datetime import timedelta

from django.core.mail import send_mail
from django.conf import settings


def login_view(request: request.HttpRequest):
    form = forms.AuthenticationForm()
    if request.method != 'POST':
        return render(
                request=request,
                template_name='auth/login.html',
                context={
                    'form': form,
                }
            )

    user = authenticate(
        username=request.POST['username'],
        password=request.POST['password']
    )
    if not user:
        return render(
            request=request,
            template_name='auth/login.html',
            context={
                'login_error': 'НЕВЕРНЫЙ ЛОГИН ИЛИ ПАРОЛЬ',
                'form': form,
            }
        )
    if user.is_active:
        login(request, user)
        return redirect(to='home_page')

    return response.HttpResponse({'error': 'Аккаунт заблокирован'})


def registration_view(request):
    if request.method != 'POST':
        return render(
            request=request,
            template_name='auth/registration.html',
            context={
                'form': ProfileCreationForm(),
            }
        )
    
    form = ProfileCreationForm(request.POST)
    if form.is_valid():
        form.save()
        new_user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1'],
        )
        login(request, new_user)
        return redirect(to='home_page')
    return render(request, 'auth/registration.html', {'form': form})
    

@decorators.login_required
def home_page_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    
    history = garantex_get_history(request.user.garantex_jwt)
    history += binance_get_history(request.user.binance_api, request.user.binance_secret_key)

    if request.method == 'GET':
        return render(request, 'main/home.html', {'history': history})


    if request.POST.get('action') == 'reset':
        return render(request, 'main/home.html', {'history': history})

    filtered_history = []

    filter_date = '1900-01-01T00:01'

    if request.POST.get('date'):
        filter_date = request.POST.get('date')

    filter_date = dt.strptime(filter_date, '%Y-%m-%dT%H:%M')


    if request.POST.get('birja') == 'БИРЖА':
        for item in history:
            if item.get('created_at') >= filter_date:
                filtered_history.append(item)
    else:
        for item in history:
            if request.POST.get('birja') == item['birja'] and item.get('created_at') >= filter_date:
                filtered_history.append(item)

    
    # if request.POST.get('action') == 'export':
        # print(filtered_history)
        # df = pd.DataFrame(
        #     [
        #         ['Время', 'Тип валюты', 'Цена', 'Кол-во', 'Сумма ордера', 'Тип ордера'],
        #         [[item['created_at'], item['birja']] for item in filtered_history],
        #     ],
        #     # index=False,
        #     columns=[request.user.username]
        # )
        # df.to_excel('otchet.xlsx', sheet_name='Лист1')
        # return FileResponse(open('otchet.xlsx', 'rb'))


    return render(request, 'main/home.html', {
        'history': filtered_history, 
        'filter_user': request.POST.get('user'), 
        'filter_birja': request.POST.get('birja'), 
        'filter_date': request.POST.get('date')
        }
    )


@decorators.login_required
def calculator_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    client = Spot()
    prices = client.ticker_price(symbols=['BTCRUB', 'USDTRUB', 'ETHRUB', 'BNBRUB'])
    for price in prices:
        price['price'] = "{:.2f}".format(float(price['price']))
    return render(request, 'main/calculator.html', {'prices': prices})


@decorators.login_required
def news_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    data = []
    try:
        page = requests.get('https://www.rbc.ru/crypto/tags/?tag=Криптовалюта')
        soup = bs4.BeautifulSoup(page.text, 'html.parser')
        News.objects.all().delete()
        for item in soup.findAll('div', class_='item js-rm-central-column-item item_image-mob js-tag-item'):
            curr_item = item.find_all('img')[0]
            data.append(News(
                site='RBC',
                image_link=curr_item.get('src'),
                text=curr_item.get('alt'),
                link=item.find_all('a')[1].get('href'),
            ))

        News.objects.bulk_create(data)
    except Exception:
        pass

    
    if 'reset' in request.POST:
        return render(request, 'main/news.html', {'data': data})
    
    if not data:
        data = News.objects.all()
    
    filters = request.POST.get('news_words')
    if not filters:
        return render(request, 'main/news.html', {'data': data})
    
    filtered_news = []
    for item in data:
        for fil in filters.split(', '):
            if fil in item.text:
                filtered_news.append(item)
    
    return render(request, 'main/news.html', {'data': filtered_news, 'filters': filters})

@decorators.login_required
def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        if request.FILES.get('image'):
            request.user.image = request.FILES.get('image')
            request.user.save()
            return render(request, 'main/profile.html')

        if request.POST.get('birja') == 'binance':
            if request.POST.get('action') == 'delete':
                request.user.binance_secret_key = None
                request.user.binance_api = None
                request.user.save()
                return render(request, 'main/profile.html')

            try:
                binance_get_account(
                    api_key=request.POST.get('binance-api-key'),
                    api_secret=request.POST.get('binance-api-secret')
                )
            except Exception:
                return render(request, 'main/profile.html')

            request.user.binance_secret_key = request.POST['binance-api-secret']
            request.user.binance_api = request.POST['binance-api-key']
            request.user.save()
            return render(request, 'main/profile.html')
        
        if request.POST.get('birja') == 'garantex':
            if request.POST.get('action') == 'delete':
                request.user.garantex_secret_key = None
                request.user.garantex_uid = None
                request.user.garantex_jwt = None
                request.user.save()
                return render(request, 'main/profile.html')

            token = garantex_get_token(
                request.POST['garantex-secret-key'],
                request.POST['garantex-uid'],
            )

            if not token:
                return render(request, 'main/profile.html')

            request.user.garantex_secret_key = request.POST['garantex-secret-key']
            request.user.garantex_uid = request.POST['garantex-uid']
            request.user.garantex_jwt = token
            request.user.save()
            return render(request, 'main/profile.html')
    return render(request, 'main/profile.html', {'garantex_token': request.user.garantex_jwt != None})

def refresh_history(user):
    try:
        history = garantex_get_history(user.garantex_jwt)
        history += binance_get_history(user.binance_api, user.binance_secret_key)
        History.objects.filter(account=user).delete()
        data = []
        for item in history:
            del item['price']
            data.append(History(account=user, **item))
        History.objects.bulk_create(data)
    except Exception as e:
        print(e)


@decorators.login_required
def statistic_view(request):
    # send_mail(
    #     '123',
    #     'test',
    #     settings.EMAIL_HOST_USER,
    #     ['zhulkin01@gmail.com',]
    # )


    account = request.user

    refresh_history(account)

    now = dt.now()

    filters = {}

    filter_hour = request.POST.get('filter_hour')
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')



    if filter_hour and filter_hour != 'ПЕРИОД':
        now -=  timedelta(hours=int(filter_hour))
        filters['created_at__gte'] = now

    if from_date:
        filter_hour = ''
        filters['created_at__gte'] = dt.strptime(from_date, '%Y-%m-%dT%H:%M')

    if to_date:
        filter_hour = ''
        filters['created_at__lte'] = dt.strptime(to_date, '%Y-%m-%dT%H:%M')

    if request.POST.get('action') == 'reset':
        filters = {}
        filter_hour = None
        from_date = None
        to_date = None

    all_buys = History.objects.filter(account=account, side='buy', **filters).aggregate(Sum('total_price'))['total_price__sum'] or 0
    all_sells = History.objects.filter(account=account, side='sell', **filters).aggregate(Sum('total_price'))['total_price__sum'] or 0

    all_count = History.objects.filter(account=account, **filters).count()
    all_profit = all_sells-all_buys
    if all_buys == 0 :
        all_spred = 0
    else:
        all_spred = (all_sells/all_buys) * 100 - 100

    days_buys = History.objects.filter(account=account, side='buy').values('created_at__date').annotate(buys=Sum('total_price'))
    days_sells = History.objects.filter(account=account, side='sell').values('created_at__date').annotate(sells=Sum('total_price'))

    MIN_VALUE = -1351513311
    best_day = {'date': '', 'profit':MIN_VALUE, 'spred': 0}

    for item in days_buys:
        for item2 in days_sells:
            if item['created_at__date'] == item2['created_at__date']:
                if item['buys'] - item2['sells'] > best_day['profit']:
                    best_day['profit'] = item['buys'] - item2['sells']
                    best_day['spred'] = (best_day['profit'] / item['buys']) * 100
                    best_day['date'] = item['created_at__date']

    if best_day['profit'] == MIN_VALUE:
        best_day['profit'] = 0

    best_day['profit'] = "{:.2f}".format(best_day['profit'])
    best_day['spred'] = "{:.2f}".format(best_day['spred'])


    months_buys = History.objects.filter(account=account, side='buy').annotate(month=TruncMonth('created_at')).values('month').annotate(total=Sum('total_price'), count=Count('total_price'))
    months_sells = History.objects.filter(account=account, side='sell').annotate(month=TruncMonth('created_at')).values('month').annotate(total=Sum('total_price'), count=Count('total_price'))


    best_month = {'date': '', 'profit': MIN_VALUE, 'amount': 0}

    for item in months_buys:
        for item2 in months_sells:
            if item['month'] == item2['month']:
                if item['total'] - item2['total'] > best_month['profit']:
                    best_month['profit'] = item['total'] - item2['total']
                    best_month['amount'] = item['count'] + item2['count']
                    best_month['date'] = item['month'].strftime('%b %Y')

    if best_month['profit'] == MIN_VALUE:
        best_month['profit'] = 0

    best_month['profit'] = "{:.2f}".format(best_month['profit'])


    return render(request, 'main/statistic.html', context={
        'all_buys': "{:.2f}".format(all_buys), 
        'all_sells': "{:.2f}".format(all_sells),
        'all_profit': "{:.2f}".format(all_profit),
        'all_spred': "{:.2f}".format(all_spred),
        'all_count': all_count,
        'best_day': best_day,
        'best_month': best_month,
        'from_date': from_date,
        'to_date': to_date,
        'filter_hour': filter_hour,
    })

@decorators.login_required
def subscription_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'main/subscription.html')

@decorators.login_required
def logout_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    logout(request)
    return redirect('login')

@decorators.login_required
def change_password(request: request.HttpRequest):
    if request.method != 'POST':
        form = forms.PasswordChangeForm(request.user)
        return render(request, 'auth/password-change.html', {'form': form})

    form = forms.PasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return redirect('profile_page')

    return render(request, 'auth/password-change.html', {'form': form})


def password_reset(request):
    return render(request, 'auth/password-reset.html')

def password_reset_sended(request):
    return render(request, 'auth/password-reset-send.html')

def password_reset_form(request):
    return render(request, 'auth/password-reset-form.html')

def password_reset_complete(request):
    return render(request, 'auth/password-reset-complete.html')


@decorators.login_required
def create_payment(request):
    if request.method != 'POST':
        return redirect('profile_page')
    
    cost = 0
    try:
        cost = int(request.POST.get('cost'))
    except:
        return redirect('profile_page')

    item = PayHistory.objects.create(account=request.user, status='В процессе')
    item.save()
    return redirect(robokassa.generate_payment_link(cost, item.number, 1))
    


SUMM = {
    '1500': 30,
    '7000': 180,
    '12000': 360,

    '5000': 30,
    '25000': 180,
    '50000': 360,
}

# ROBOKASSA
@csrf_exempt
def result(request):
    if request.method != 'POST':
        return HttpResponse('only POST method')

    import json
    with open('logs', 'w') as f:
        f.write(json.dumps(request.POST.dict()))

    good, text = robokassa.result_payment(request.POST)
    # if not good:
    #     return HttpResponse(text)
    
    item = PayHistory.objects.get(number=request.POST.get('InvId'))
    item.status = 'Оплачено'
    item.save()

    profile = Profile.objects.get(id=item.account.id)

    if not profile.subscription_active:
        profile.subscription_expiration_date = dt.now()

    profile.subscription_expiration_date += timedelta(days=SUMM[request.POST.get('OutSum')])
    profile.type = Type.PERSONAL if request.POST.get('OutSum') in ['1500', '7000', '12000'] else Type.BUSINESS
    profile.subscription_active = True

    profile.save()
    return HttpResponse(text)

@csrf_exempt
def success(request):
    return redirect('profile_page')
    # return render(request, 'robokassa/success.html')

@csrf_exempt
def fail(request):
    return redirect('profile_page')
    # return render(request, 'robokassa/fail.html')
