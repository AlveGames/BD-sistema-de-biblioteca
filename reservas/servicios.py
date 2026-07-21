from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from prestamos.models import MEjemplar, PEstado, TDetallePrestamo, TMulta, TPrestamo, TReserva
from prestamos.servicios import calcular_fecha_devolucion_esperada, validar_nuevo_prestamo

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


def convertir_a_prestamo(reserva_id, ejemplar_id, bibliotecario_id):
    """Convierte una reserva vigente en un préstamo. Reutiliza validar_nuevo_prestamo
    (prestamos/servicios.py) para no duplicar las reglas de máximo de ejemplares,
    préstamos vencidos y multas pendientes."""
    with transaction.atomic():
        try:
            reserva = TReserva.objects.select_related('id_usuario', 'id_libro', 'id_estado').get(pk=reserva_id)
        except TReserva.DoesNotExist:
            raise ValidationError("La reserva indicada no existe.")

        if calcular_estado_real(reserva) != 'activa':
            raise ValidationError("Esta reserva ya no está activa, no se puede convertir a préstamo.")

        if not ejemplar_id:
            raise ValidationError("Debe seleccionar un ejemplar disponible del libro reservado.")

        if not bibliotecario_id:
            raise ValidationError("Debe seleccionar un bibliotecario.")

        estado_ejemplar_disponible = PEstado.objects.get(entidad='EJEMPLAR', codigo='disponible')
        try:
            ejemplar = MEjemplar.objects.get(
                pk=ejemplar_id, id_libro_id=reserva.id_libro_id, id_estado=estado_ejemplar_disponible
            )
        except MEjemplar.DoesNotExist:
            raise ValidationError(
                "El ejemplar seleccionado no corresponde al libro reservado o ya no está disponible."
            )

        validar_nuevo_prestamo(reserva.id_usuario_id, [ejemplar_id])

        estado_prestamo_activo = PEstado.objects.get(entidad='PRESTAMO', codigo='activo')
        estado_ejemplar_prestado = PEstado.objects.get(entidad='EJEMPLAR', codigo='prestado')
        estado_reserva_convertida = PEstado.objects.get(entidad='RESERVA', codigo='convertida')

        fecha_prestamo = timezone.now().date()
        prestamo = TPrestamo.objects.create(
            id_usuario=reserva.id_usuario,
            id_bibliotecario_id=bibliotecario_id,
            id_reserva=reserva,
            fecha_prestamo=fecha_prestamo,
            fecha_devolucion_esperada=calcular_fecha_devolucion_esperada(fecha_prestamo),
            id_estado=estado_prestamo_activo,
        )
        TDetallePrestamo.objects.create(id_prestamo=prestamo, id_ejemplar=ejemplar)
        MEjemplar.objects.filter(pk=ejemplar.pk).update(id_estado=estado_ejemplar_prestado)
        TReserva.objects.filter(pk=reserva.pk).update(id_estado=estado_reserva_convertida)

        return prestamo


def cancelar_reserva(reserva_id):
    """Cancela una reserva vigente. Acción directa, sin validaciones adicionales."""
    try:
        reserva = TReserva.objects.select_related('id_estado').get(pk=reserva_id)
    except TReserva.DoesNotExist:
        raise ValidationError("La reserva indicada no existe.")

    if calcular_estado_real(reserva) != 'activa':
        raise ValidationError("Solo se pueden cancelar reservas activas.")

    estado_cancelada = PEstado.objects.get(entidad='RESERVA', codigo='cancelada')
    TReserva.objects.filter(pk=reserva.pk).update(id_estado=estado_cancelada)
