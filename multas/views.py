from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect

from prestamos.models import MBibliotecario, PMetodoPago, TMulta

from .servicios import anular_multa, calcular_saldo_pendiente, registrar_pago


def lista(request):
    if request.method == 'POST':
        multa_id = request.POST.get('multa')
        monto_pagado = request.POST.get('monto_pagado')
        metodo_pago_id = request.POST.get('metodo_pago')
        bibliotecario_id = request.POST.get('bibliotecario')

        try:
            _, saldo_restante = registrar_pago(multa_id, monto_pagado, metodo_pago_id, bibliotecario_id)
            if saldo_restante <= 0:
                messages.success(request, "Pago registrado. La multa quedó completamente pagada.")
            else:
                messages.success(request, f"Pago parcial registrado. Saldo pendiente: ${saldo_restante}.")
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))
        except Exception as e:
            messages.error(request, f"Error al registrar el pago: {e}")

        return redirect('multas:lista')

    bibliotecarios = MBibliotecario.objects.all().order_by('apellido', 'nombre')
    metodos_pago = PMetodoPago.objects.all().order_by('descripcion')

    multas_pendientes = TMulta.objects.filter(
        id_estado__codigo='pendiente'
    ).select_related(
        'id_estado',
        'id_tipo_multa',
        'id_devolucion',
        'id_devolucion__id_detalle',
        'id_devolucion__id_detalle__id_prestamo',
        'id_devolucion__id_detalle__id_prestamo__id_usuario',
    ).order_by('id_multa')

    for multa in multas_pendientes:
        multa.saldo_pendiente = calcular_saldo_pendiente(multa)

    return render(request, 'multas/lista.html', {
        'multas_pendientes': multas_pendientes,
        'bibliotecarios': bibliotecarios,
        'metodos_pago': metodos_pago,
    })


def anular(request, id_multa):
    if request.method == 'POST':
        try:
            anular_multa(id_multa)
            messages.success(request, "Multa anulada correctamente.")
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))
        except Exception as e:
            messages.error(request, f"Error al anular la multa: {e}")

    return redirect('multas:lista')
