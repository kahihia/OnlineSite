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
    url(r'^$', views.main_page),
    url(r'^home/', views.home),
    url(r'^wallets/', views.wallets),
    url(r'^trans-history/', views.trans_history),
    url(r'^reports/', views.reports, name='reports'),
    url(r'^general/', views.general, name='general'),
    url(r'^register/$', views.register, name='register'),
    url(r'^login/$', views.user_login, name='login'),
    url(r'^logout/$', views.user_logout, name='logout'),

]

urlpatterns += i18n_patterns(
    url('r^admin/', admin.site.urls),
    url(r'^$', views.main_page),
    url(r'^home/', views.home),
    url(r'^wallets/', views.wallets),
    url(r'^trans-history/', views.trans_history),
    url(r'^reports/', views.reports, name='reports'),
    url(r'^general/', views.general, name='general'),
    url(r'^register/$', views.register, name='register'),
    url(r'^login/$', views.user_login, name='login'),
    url(r'^logout/$', views.user_logout, name='logout'),
)

