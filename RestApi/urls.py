from django.conf.urls import url, include
from django.contrib import admin
from RestApi import views

urlpatterns = [
    url(r'^users/', views.snippet_list),
    url(r'^get_token/', views.generate_token),
    url(r'^cash_out_order/', views.cash_out_order),
]
