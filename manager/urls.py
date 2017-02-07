from django.conf.urls import include, url
from manager import views

urlpatterns = [
    url(r'^withdrawal_requests/', views.withdrawal_requests),
    url(r'^$', views.home),
]
