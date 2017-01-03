"""firstsite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from interpay import views
from django.conf.urls.i18n import i18n_patterns
from django.views.generic.base import TemplateView
admin.autodiscover()
urlpatterns = [
    url('^admin/', admin.site.urls),
    url(r'^conversion/', include('conversion.urls')),
    url(r'^currencies/', include('currencies.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'session_security/', include('session_security.urls')),

    # url(r'^$', TemplateView.as_view(template_name="main_page.html")),
    # url(r'^home/', TemplateView.as_view(template_name="home.html")),
    # url(r'^wallets/', TemplateView.as_view(template_name="wallets.html")),
    # url(r'^trans-history/', TemplateView.as_view(template_name="trans_history.html")),
    # url(r'^reports/', TemplateView.as_view(template_name="reports.html"), name='reports'),
    # url(r'^general/', TemplateView.as_view(template_name="home.html"), name='general'),
    # url(r'^register/$', views.register, name='register'),
    # url(r'^login/$', views.user_login, name='login'),
    # url(r'^logout/$', views.user_logout, name='logout'),

    url(r'^$', views.main_page),
    url(r'^home/', views.home),
    url(r'^wallets/$', views.wallets),
    url(r'^wallets/convert_currency/$', views.convert_currency),
    url(r'^wallets/(?P<wallet_id>\d+)/$', views.wallet),
    url(r'^wallets/actual_convert/$', views.actual_convert),
    # url(r'^wallets/rials/$', views.convert_rial),
    # url(r'^wallets/euros/$', views.convert_euro),
    # url(r'^wallets/pounds/$', views.convert_pound),
    # url(r'^trans-history/', views.trans_history),
    url(r'^reports/', views.reports, name='reports'),
    url(r'^general/', views.general, name='general'),
    url(r'^register/$', views.register, name='register'),
    url(r'^login/$', views.user_login, name='login'),
    url(r'^logout/$', views.user_logout, name='logout'),

    url(r'^verif/$', views.verify_user, name='verif'),
    url(r'^sms/$', views.send_sms, name='sms'),
    url(r'^retrieve_pass/$', views.retrieve_pass, name='retrieve_pass'),
    url(r'^top-up/', views.recharge_account, name='recharge_account'),
    url(r'^bank-accounts/', views.bank_accounts, name='bank_accounts'),

]

urlpatterns += i18n_patterns(
    # url(r'^accounts/', include('registration.backends.hmac.urls')),

    # url(r'^admin/', admin.site.urls),
    # url(r'^$', TemplateView.as_view(template_name="main_page.html")),
    # url(r'^home/', TemplateView.as_view(template_name="home.html")),
    # url(r'^wallets/', TemplateView.as_view(template_name="wallets.html")),
    # url(r'^trans-history/', TemplateView.as_view(template_name="trans_history.html")),
    # url(r'^reports/', TemplateView.as_view(template_name="reports.html"), name='reports'),
    # url(r'^general/', TemplateView.as_view(template_name="home.html"), name='general'),
    # url(r'^register/$', views.register, name='register'),
    # url(r'^login/$', views.user_login, name='login'),
    # url(r'^logout/$', views.user_logout, name='logout'),
    # url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^admin/', admin.site.urls),
    url(r'session_security/', include('session_security.urls')),


    url(r'^home/', views.home),
    # url(r'^wallets/dollars/$', views.convert_dollar),
    # url(r'^wallets/rials/$', views.convert_rial),
    # url(r'^wallets/euros/$', views.convert_euro),
    # url(r'^wallets/pounds/$', views.convert_pound),
    url(r'^wallets$', views.wallets),
    url(r'^trans-history/', views.trans_history),
    url(r'^reports/', views.reports, name='reports'),
    url(r'^general/', views.general, name='general'),
    url(r'^register/$', views.register, name='register'),
    url(r'^login/$', views.user_login, name='login'),
    url(r'^logout/$', views.user_logout, name='logout'),
    url(r'^verif/$', views.verify_user, name='verif'),
    url(r'^sms/$', views.send_sms, name='sms'),
    url(r'^retrieve_pass/$', views.retrieve_pass, name='retrieve_pass'),
    url(r'^top-up/', views.recharge_account, name='recharge_account'),
    url(r'^bank-accounts/', views.bank_accounts, name='bank_accounts'),
    url(r'^$', views.main_page),
)

