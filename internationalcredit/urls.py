from django.conf.urls import include, url
from internationalcredit import views

urlpatterns = [
    url(r'^$', views.home),
    url(r'callback/', views.callback)
]
