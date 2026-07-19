from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone

from prestamos.models import MLibro, MUsuario, PEstado, TReserva

from .servicios import calcular_estado_real, calcular_fecha_vencimiento, validar_nueva_reserva


def lista(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario')
        libro_id = request.POST.get('libro')

        try:
            with transaction.atomic():
                validar_nueva_reserva(usuario_id, libro_id)

                estado_reserva_activa = PEstado.objects.get(entidad='RESERVA', codigo='activa')

                fecha_reserva = timezone.now()
                fecha_vencimiento = calcular_fecha_vencimiento(fecha_reserva)

                TReserva.objects.create(
                    id_usuario_id=usuario_id,
                    id_libro_id=libro_id,
                    fecha_reserva=fecha_reserva,
                    fecha_vencimiento=fecha_vencimiento.date(),
                    id_estado=estado_reserva_activa,
                )

            messages.success(request, "Reserva registrada correctamente.")
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))
        except Exception as e:
            messages.error(request, f"Error al registrar la reserva: {e}")

        return redirect('reservas:lista')

    usuarios = MUsuario.objects.all().order_by('apellidos', 'nombres')
    libros = MLibro.objects.all().order_by('titulo_libro')

    reservas_activas = TReserva.objects.filter(
        id_estado__codigo='activa'
    ).select_related('id_usuario', 'id_libro', 'id_estado').order_by('-fecha_reserva')

    for reserva in reservas_activas:
        reserva.estado_calculado = calcular_estado_real(reserva)

    return render(request, 'reservas/lista.html', {
        'usuarios': usuarios,
        'libros': libros,
        'reservas_activas': reservas_activas,
    })
