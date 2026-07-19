from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek

from prestamos.models import MEjemplar, TDetallePrestamo, TMulta, TPrestamo

TRUNC_FUNCS_PERIODO = {
    'dia': TruncDate,
    'semana': TruncWeek,
    'mes': TruncMonth,
}


def prestamos_por_periodo(agrupacion='dia'):
    """Cantidad de préstamos agrupados por día, semana o mes (GROUP BY + COUNT)."""
    trunc_func = TRUNC_FUNCS_PERIODO.get(agrupacion, TruncDate)
    return (
        TPrestamo.objects
        .annotate(periodo=trunc_func('fecha_prestamo'))
        .values('periodo')
        .annotate(total_prestamos=Count('id_prestamo'))
        .order_by('periodo')
    )


def libros_mas_prestados():
    """Libros ordenados por cantidad de veces prestados (Count sobre TDetallePrestamo)."""
    return (
        TDetallePrestamo.objects
        .values('id_ejemplar__id_libro__id_libro', 'id_ejemplar__id_libro__titulo_libro')
        .annotate(veces_prestado=Count('id_detalle'))
        .order_by('-veces_prestado')
    )


def usuarios_con_multas_pendientes():
    """Usuarios con multas pendientes: cantidad y monto total adeudado.

    Cadena real de FKs: TMulta.id_devolucion -> TDevolucion.id_detalle
    -> TDetallePrestamo.id_prestamo -> TPrestamo.id_usuario
    """
    return (
        TMulta.objects
        .filter(id_estado__entidad='MULTA', id_estado__codigo='pendiente')
        .values(
            'id_devolucion__id_detalle__id_prestamo__id_usuario__id_usuario',
            'id_devolucion__id_detalle__id_prestamo__id_usuario__nombres',
            'id_devolucion__id_detalle__id_prestamo__id_usuario__apellidos',
        )
        .annotate(
            cantidad_multas=Count('id_multa'),
            monto_total=Sum('monto'),
        )
        .order_by('-monto_total')
    )


def ejemplares_disponibles_por_categoria():
    """Cantidad de ejemplares disponibles agrupados por categoría del libro."""
    return (
        MEjemplar.objects
        .filter(id_estado__entidad='EJEMPLAR', id_estado__codigo='disponible')
        .values('id_libro__id_categoria__id_categoria', 'id_libro__id_categoria__nombre')
        .annotate(total_disponibles=Count('id_ejemplar'))
        .order_by('-total_disponibles')
    )
