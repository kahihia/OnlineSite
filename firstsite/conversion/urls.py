from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^conversion$', views.index, name='index'),
    url(r'^(?P<trans_id>[0-9]+)/$', views.detail, name='detail'),
]
