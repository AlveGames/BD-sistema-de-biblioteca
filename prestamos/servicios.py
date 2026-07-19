from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Count, Sum
from django.utils import timezone

from .models import MEjemplar, PEstado, TDetallePrestamo, TMulta, TPrestamo, TReserva

MAX_EJEMPLARES_PRESTADOS = 3
DIAS_PLAZO_DEVOLUCION = 7


def validar_nuevo_prestamo(usuario_id, ejemplares_ids):
    """Lanza ValidationError si el usuario no puede recibir el nuevo préstamo."""
    if not ejemplares_ids:
        raise ValidationError("Debe seleccionar al menos un ejemplar.")

    estado_prestamo_activo = PEstado.objects.get(entidad='PRESTAMO', codigo='activo')
    estado_prestamo_vencido = PEstado.objects.get(entidad='PRESTAMO', codigo='vencido')

    prestamos_usuario = TPrestamo.objects.filter(id_usuario_id=usuario_id)

    if prestamos_usuario.filter(id_estado=estado_prestamo_vencido).exists():
        raise ValidationError("El usuario tiene préstamos vencidos, no puede pedir otro.")

    prestamos_activos = prestamos_usuario.filter(id_estado=estado_prestamo_activo)

    ejemplares_prestados_actualmente = TDetallePrestamo.objects.filter(
        id_prestamo__in=prestamos_activos
    ).count()

    if ejemplares_prestados_actualmente + len(ejemplares_ids) > MAX_EJEMPLARES_PRESTADOS:
        raise ValidationError(
            f"El usuario superaría el máximo de {MAX_EJEMPLARES_PRESTADOS} ejemplares prestados."
        )

    # Cadena real de FKs: TMulta.id_devolucion -> TDevolucion.id_detalle
    # -> TDetallePrestamo.id_prestamo -> TPrestamo.id_usuario
    tiene_multa_pendiente = TMulta.objects.filter(
        id_estado__entidad='MULTA',
        id_estado__codigo='pendiente',
        id_devolucion__id_detalle__id_prestamo__id_usuario_id=usuario_id,
    ).exists()

    if tiene_multa_pendiente:
        raise ValidationError("El usuario tiene una multa pendiente, no puede pedir un nuevo préstamo.")

    estado_ejemplar_disponible = PEstado.objects.get(entidad='EJEMPLAR', codigo='disponible')
    ejemplares_no_disponibles = MEjemplar.objects.filter(
        id_ejemplar__in=ejemplares_ids
    ).exclude(id_estado=estado_ejemplar_disponible).exists()

    if ejemplares_no_disponibles:
        raise ValidationError("Alguno de los ejemplares seleccionados ya no está disponible.")


def calcular_fecha_devolucion_esperada(fecha_prestamo):
    return fecha_prestamo + timedelta(days=DIAS_PLAZO_DEVOLUCION)


def contar_prestamos_activos():
    return TPrestamo.objects.filter(
        id_estado__entidad='PRESTAMO', id_estado__codigo='activo'
    ).count()


def contar_reservas_activas():
    # Reutiliza la misma lógica de 48h de reservas/servicios.py (PLAZO_HORAS_RESERVA):
    # no basta con id_estado='activa', porque ese campo puede quedar desactualizado.
    from reservas.servicios import PLAZO_HORAS_RESERVA

    limite_inferior = timezone.now() - timedelta(hours=PLAZO_HORAS_RESERVA)
    return TReserva.objects.filter(
        id_estado__entidad='RESERVA',
        id_estado__codigo='activa',
        fecha_reserva__gte=limite_inferior,
    ).count()


def contar_multas_pendientes():
    resultado = TMulta.objects.filter(
        id_estado__entidad='MULTA', id_estado__codigo='pendiente'
    ).aggregate(cantidad=Count('id_multa'), total=Sum('monto'))

    return {
        'cantidad': resultado['cantidad'] or 0,
        'total': resultado['total'] or Decimal('0'),
    }


def contar_ejemplares_disponibles():
    return MEjemplar.objects.filter(
        id_estado__entidad='EJEMPLAR', id_estado__codigo='disponible'
    ).count()
