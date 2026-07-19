from django.urls import path

from . import views

app_name = 'mantenimiento'
urlpatterns = [
    path('', views.index, name='index'),

    path('usuarios/', views.UsuarioListView.as_view(), name='usuario_lista'),
    path('usuarios/nuevo/', views.UsuarioCreateView.as_view(), name='usuario_crear'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_editar'),
    path('usuarios/<int:pk>/eliminar/', views.UsuarioDeleteView.as_view(), name='usuario_eliminar'),

    path('bibliotecarios/', views.BibliotecarioListView.as_view(), name='bibliotecario_lista'),
    path('bibliotecarios/nuevo/', views.BibliotecarioCreateView.as_view(), name='bibliotecario_crear'),
    path('bibliotecarios/<int:pk>/editar/', views.BibliotecarioUpdateView.as_view(), name='bibliotecario_editar'),
    path('bibliotecarios/<int:pk>/eliminar/', views.BibliotecarioDeleteView.as_view(), name='bibliotecario_eliminar'),

    path('autores/', views.AutorListView.as_view(), name='autor_lista'),
    path('autores/nuevo/', views.AutorCreateView.as_view(), name='autor_crear'),
    path('autores/<int:pk>/editar/', views.AutorUpdateView.as_view(), name='autor_editar'),
    path('autores/<int:pk>/eliminar/', views.AutorDeleteView.as_view(), name='autor_eliminar'),

    path('libros/', views.LibroListView.as_view(), name='libro_lista'),
    path('libros/nuevo/', views.LibroCreateView.as_view(), name='libro_crear'),
    path('libros/<int:pk>/editar/', views.LibroUpdateView.as_view(), name='libro_editar'),
    path('libros/<int:pk>/eliminar/', views.LibroDeleteView.as_view(), name='libro_eliminar'),

    path('ejemplares/', views.EjemplarListView.as_view(), name='ejemplar_lista'),
    path('ejemplares/nuevo/', views.EjemplarCreateView.as_view(), name='ejemplar_crear'),
    path('ejemplares/<int:pk>/editar/', views.EjemplarUpdateView.as_view(), name='ejemplar_editar'),
    path('ejemplares/<int:pk>/eliminar/', views.EjemplarDeleteView.as_view(), name='ejemplar_eliminar'),
]
