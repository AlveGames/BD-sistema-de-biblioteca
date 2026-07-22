from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from prestamos.models import PEstado, TMulta, TPagoMulta

MONTO_POR_DIA_ATRASO = Decimal('0.50')

ESTADOS_MULTA_NO_PAGABLES = ('pagada', 'anulada')


def calcular_saldo_pendiente(multa):
    total_pagado = TPagoMulta.objects.filter(
        id_multa=multa, id_estado__codigo='confirmado'
    ).aggregate(total=Sum('monto_pagado'))['total'] or Decimal('0')
    return multa.monto - total_pagado


def registrar_pago(multa_id, monto_pagado, metodo_pago_id, bibliotecario_id):
    """Registra un TPagoMulta y, si cubre el saldo pendiente, marca la multa como 'pagada'.

    Devuelve (pago, saldo_pendiente_resultante) para que la vista arme el mensaje
    ("pagada" vs "pago parcial, saldo $X") sin volver a consultar.
    """
    try:
        monto_pagado = Decimal(str(monto_pagado))
    except (InvalidOperation, TypeError):
        raise ValidationError("El monto pagado no es un número válido.")

    if monto_pagado <= 0:
        raise ValidationError("El monto pagado debe ser mayor a cero.")

    with transaction.atomic():
        multa = TMulta.objects.select_related('id_estado').get(pk=multa_id)

        if multa.id_estado.codigo in ESTADOS_MULTA_NO_PAGABLES:
            raise ValidationError(
                f"La multa ya está en estado '{multa.id_estado.codigo}', no se puede registrar un pago."
            )

        # Una multa puede saldarse en varios abonos: se compara contra lo que
        # falta ACUMULADO, no contra el monto total original de la multa.
        saldo_pendiente = calcular_saldo_pendiente(multa)

        if monto_pagado > saldo_pendiente:
            raise ValidationError(
                f"El monto pagado (${monto_pagado}) supera el saldo pendiente de la multa "
                f"(${saldo_pendiente}). No se puede pagar de más."
            )

        estado_pago_confirmado = PEstado.objects.get(entidad='PAGO_MULTA', codigo='confirmado')

        pago = TPagoMulta.objects.create(
            id_multa=multa,
            id_bibliotecario_id=bibliotecario_id,
            id_estado=estado_pago_confirmado,
            fecha_pago=timezone.now().date(),
            monto_pagado=monto_pagado,
            id_metodo_pago_id=metodo_pago_id,
        )

        nuevo_saldo_pendiente = saldo_pendiente - monto_pagado

        if nuevo_saldo_pendiente <= 0:
            estado_multa_pagada = PEstado.objects.get(entidad='MULTA', codigo='pagada')
            multa.id_estado = estado_multa_pagada
            multa.save(update_fields=['id_estado'])

        return pago, nuevo_saldo_pendiente


def anular_multa(multa_id):
    """Marca una multa pendiente como anulada.

    Nota: TMulta no tiene ninguna columna para guardar un motivo de anulación
    (solo id_multa, id_devolucion, id_tipo_multa, monto, id_estado). No se agregó
    una columna nueva para esto -tocaría el esquema ya validado-, así que el motivo
    que capture la pantalla no se persiste en ningún lado todavía.
    """
    with transaction.atomic():
        try:
            multa = TMulta.objects.select_related('id_estado').get(pk=multa_id)
        except TMulta.DoesNotExist:
            raise ValidationError("La multa indicada no existe.")

        if multa.id_estado.codigo != 'pendiente':
            raise ValidationError(
                f"La multa ya está en estado '{multa.id_estado.codigo}', no se puede anular."
            )

        estado_anulada = PEstado.objects.get(entidad='MULTA', codigo='anulada')
        multa.id_estado = estado_anulada
        multa.save(update_fields=['id_estado'])
