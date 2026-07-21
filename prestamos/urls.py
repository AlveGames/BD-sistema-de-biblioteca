from django.urls import path
from . import views

app_name = 'prestamos'
urlpatterns = [
    path('', views.lista, name='lista'),
    path('devolucion/<int:id_detalle>/', views.registrar_devolucion, name='registrar_devolucion'),
]
