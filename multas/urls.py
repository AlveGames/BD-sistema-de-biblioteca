from django.urls import path
from . import views

app_name = 'multas'
urlpatterns = [
    path('', views.lista, name='lista'),
]
