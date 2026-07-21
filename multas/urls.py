from django.urls import path
from . import views

app_name = 'multas'
urlpatterns = [
    path('', views.lista, name='lista'),
    path('<int:id_multa>/anular/', views.anular, name='anular'),
]
