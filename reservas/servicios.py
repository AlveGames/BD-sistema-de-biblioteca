from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from prestamos.models import TDetallePrestamo, TMulta, TReserva

MAX_RESERVAS_ACTIVAS = 2
PLAZO_HORAS_RESERVA = 48


def calcular_fecha_vencimiento(fecha_reserva):
    return fecha_reserva + timedelta(hours=PLAZO_HORAS_RESERVA)


def calcular_estado_real(reserva):
    """Estado real de la reserva: fecha_vencimiento (DATE) no es confiable,
    así que la vigencia se recalcula con fecha_reserva (DATETIME) + 48h."""
    codigo = reserva.id_estado.codigo
    if codigo in ('convertida', 'cancelada'):
        return codigo

    limite = calcular_fecha_vencimiento(reserva.fecha_reserva)
    if timezone.now() >= limite:
        return 'vencida'
    return 'activa'


def validar_nueva_reserva(usuario_id, libro_id):
    if not libro_id:
        raise ValidationError("Debe seleccionar un libro.")

    # Cadena real de FKs: TMulta.id_devolucion -> TDevolucion.id_detalle
    # -> TDetallePrestamo.id_prestamo -> TPrestamo.id_usuario
    tiene_multa_pendiente = TMulta.objects.filter(
        id_estado__entidad='MULTA',
        id_estado__codigo='pendiente',
        id_devolucion__id_detalle__id_prestamo__id_usuario_id=usuario_id,
    ).exists()

    if tiene_multa_pendiente:
        raise ValidationError("El usuario tiene una multa pendiente, no puede hacer una nueva reserva.")

    limite_inferior = timezone.now() - timedelta(hours=PLAZO_HORAS_RESERVA)

    reservas_activas_usuario = TReserva.objects.filter(
        id_usuario_id=usuario_id,
        id_estado__codigo='activa',
        fecha_reserva__gte=limite_inferior,
    )

    if reservas_activas_usuario.filter(id_libro_id=libro_id).exists():
        raise ValidationError("El usuario ya tiene ese libro reservado activamente.")

    if reservas_activas_usuario.count() >= MAX_RESERVAS_ACTIVAS:
        raise ValidationError(
            f"El usuario superaría el máximo de {MAX_RESERVAS_ACTIVAS} reservas activas."
        )

    # Cadena real de FKs: TDetallePrestamo.id_ejemplar (MEjemplar) -> id_libro
    # TDetallePrestamo.id_prestamo -> TPrestamo.id_usuario / id_estado
    tiene_prestamo_activo_mismo_libro = TDetallePrestamo.objects.filter(
        id_ejemplar__id_libro_id=libro_id,
        id_prestamo__id_usuario_id=usuario_id,
        id_prestamo__id_estado__codigo='activo',
    ).exists()

    if tiene_prestamo_activo_mismo_libro:
        raise ValidationError("El usuario ya tiene un ejemplar de este libro prestado actualmente.")
