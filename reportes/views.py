from django.shortcuts import render

from .servicios import (
    ejemplares_disponibles_por_categoria,
    libros_mas_prestados,
    prestamos_por_periodo,
    usuarios_con_multas_pendientes,
)

TABS_VALIDAS = ('prestamos', 'libros', 'multas', 'categorias')
AGRUPACIONES_VALIDAS = ('dia', 'semana', 'mes')


def index(request):
    tab = request.GET.get('tab', 'prestamos')
    if tab not in TABS_VALIDAS:
        tab = 'prestamos'

    agrupacion = request.GET.get('agrupacion', 'dia')
    if agrupacion not in AGRUPACIONES_VALIDAS:
        agrupacion = 'dia'

    context = {
        'tab': tab,
        'agrupacion': agrupacion,
    }

    if tab == 'prestamos':
        context['prestamos_periodo'] = prestamos_por_periodo(agrupacion)
    elif tab == 'libros':
        context['libros_mas_prestados'] = libros_mas_prestados()
    elif tab == 'multas':
        context['usuarios_multas'] = usuarios_con_multas_pendientes()
    elif tab == 'categorias':
        context['ejemplares_categoria'] = ejemplares_disponibles_por_categoria()

    return render(request, 'reportes/index.html', context)
