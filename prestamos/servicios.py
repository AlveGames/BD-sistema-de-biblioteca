from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from .models import (
    MEjemplar,
    PEstado,
    PTipoMulta,
    TDetallePrestamo,
    TDevolucion,
    TMulta,
    TPrestamo,
    TReserva,
)

MAX_EJEMPLARES_PRESTADOS = 3
DIAS_PLAZO_DEVOLUCION = 7
MONTO_MULTA_POR_DIA = Decimal('0.50')

CONDICION_A_ESTADO_EJEMPLAR = {
    'bueno': 'disponible',
    'regular': 'disponible',
    'dañado': 'dañado',
    'perdido': 'perdido',
}


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


def procesar_devolucion(id_detalle, condicion_id):
    """Registra la devolución de un ejemplar (por id_detalle) dentro de una transacción.

    Nota: se lanza `Exception` (no `ValidationError`) a propósito, porque la vista
    que consume esta función atrapa `except Exception as e: ... str(e)` y espera
    el texto plano del mensaje, no la representación en lista de ValidationError.
    """
    with transaction.atomic():
        if TDevolucion.objects.filter(id_detalle_id=id_detalle).exists():
            raise Exception("Esta devolución ya fue registrada.")

        try:
            detalle = TDetallePrestamo.objects.select_related('id_prestamo').get(pk=id_detalle)
        except TDetallePrestamo.DoesNotExist:
            raise Exception("El detalle de préstamo indicado no existe.")

        try:
            estado_condicion = PEstado.objects.get(entidad='CONDICION_EJEMPLAR', pk=int(condicion_id))
        except (PEstado.DoesNotExist, TypeError, ValueError):
            raise Exception("Debe seleccionar una condición de ejemplar válida.")

        codigo_estado_ejemplar = CONDICION_A_ESTADO_EJEMPLAR.get(estado_condicion.codigo)
        if codigo_estado_ejemplar is None:
            raise Exception("Condición de ejemplar no reconocida.")

        prestamo = detalle.id_prestamo
        dias_atraso = max(0, (date.today() - prestamo.fecha_devolucion_esperada).days)

        devolucion = TDevolucion.objects.create(
            id_detalle=detalle,
            fecha_devolucion_real=date.today(),
            id_estado=estado_condicion,
            dias_atraso=dias_atraso,
        )

        # La condición reportada determina el estado del ejemplar: NO todos vuelven
        # a "disponible" (dañado -> EJEMPLAR/dañado, perdido -> EJEMPLAR/perdido).
        estado_ejemplar = PEstado.objects.get(entidad='EJEMPLAR', codigo=codigo_estado_ejemplar)
        MEjemplar.objects.filter(pk=detalle.id_ejemplar_id).update(id_estado=estado_ejemplar)

        if dias_atraso > 0:
            tipo_multa_atraso = PTipoMulta.objects.get(descripcion='Atraso en devolución')
            estado_multa_pendiente = PEstado.objects.get(entidad='MULTA', codigo='pendiente')
            TMulta.objects.create(
                id_devolucion=devolucion,
                id_tipo_multa=tipo_multa_atraso,
                monto=Decimal(dias_atraso) * MONTO_MULTA_POR_DIA,
                id_estado=estado_multa_pendiente,
            )

        quedan_detalles_sin_devolucion = TDetallePrestamo.objects.filter(
            id_prestamo=prestamo
        ).exclude(
            id_detalle__in=TDevolucion.objects.values_list('id_detalle', flat=True)
        ).exists()

        if not quedan_detalles_sin_devolucion:
            estado_prestamo_devuelto = PEstado.objects.get(entidad='PRESTAMO', codigo='devuelto')
            TPrestamo.objects.filter(pk=prestamo.pk).update(id_estado=estado_prestamo_devuelto)
