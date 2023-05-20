from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login', views.login_view, name='login'),
    path('registration', views.registration_view, name='registration'),
    path('logout', views.logout_view, name='logout'),
    path('change-password', views.change_password, name='password-change'),
    # path('password-reset', views.password_reset, name='password-reset'),
    path('', views.home_page_view, name='home_page'),
    path('calculator', views.calculator_view, name='calculator_page'),
    path('news', views.news_view, name='news_page'),
    path('profile', views.profile_view, name='profile_page'),
    path('stats', views.statistic_view, name='statistics_page'),
    path('subscription', views.subscription_view, name='subscription_page'),
    path('create-payment', views.create_payment, name='create-payment'),

    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    #robokassa
    path('result', views.result),
    path('success', views.success),
    path('fail', views.fail),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)