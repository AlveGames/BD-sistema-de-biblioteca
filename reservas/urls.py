from django.urls import path
from . import views

app_name = 'reservas'
urlpatterns = [
    path('', views.lista, name='lista'),
    path('<int:id_reserva>/convertir/', views.convertir_reserva, name='convertir_reserva'),
    path('<int:id_reserva>/cancelar/', views.cancelar, name='cancelar'),
]
