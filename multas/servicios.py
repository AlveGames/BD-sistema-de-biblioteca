from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from prestamos.models import PEstado, TMulta, TPagoMulta

MONTO_POR_DIA_ATRASO = Decimal('0.50')

ESTADOS_MULTA_NO_PAGABLES = ('pagada', 'anulada')


def registrar_pago(multa_id, monto_pagado, metodo_pago_id, bibliotecario_id):
    """Registra un TPagoMulta y, si cubre el monto total, marca la multa como 'pagada'."""
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

        estado_pago_confirmado = PEstado.objects.get(entidad='PAGO_MULTA', codigo='confirmado')

        pago = TPagoMulta.objects.create(
            id_multa=multa,
            id_bibliotecario_id=bibliotecario_id,
            id_estado=estado_pago_confirmado,
            fecha_pago=timezone.now().date(),
            monto_pagado=monto_pagado,
            id_metodo_pago_id=metodo_pago_id,
        )

        # Compara lo pagado ACUMULADO (no solo este pago) contra el monto total,
        # ya que una multa puede saldarse en varios abonos.
        total_pagado = TPagoMulta.objects.filter(
            id_multa=multa, id_estado__codigo='confirmado'
        ).aggregate(total=Sum('monto_pagado'))['total'] or Decimal('0')

        if total_pagado >= multa.monto:
            estado_multa_pagada = PEstado.objects.get(entidad='MULTA', codigo='pagada')
            multa.id_estado = estado_multa_pagada
            multa.save(update_fields=['id_estado'])

        return pago
