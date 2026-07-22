from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone

from prestamos.models import MBibliotecario, MEjemplar, MLibro, MUsuario, PEstado, TReserva

from .servicios import (
    calcular_fecha_vencimiento,
    cancelar_reserva,
    convertir_a_prestamo,
    sincronizar_reservas_vencidas,
    validar_nueva_reserva,
)


def lista(request):
    sincronizar_reservas_vencidas()

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
    bibliotecarios = MBibliotecario.objects.all().order_by('apellido', 'nombre')

    # sincronizar_reservas_vencidas() ya corrió arriba, así que este filtro por el
    # campo guardado es confiable: toda reserva realmente vencida ya fue corregida
    # a id_estado='vencida' antes de llegar aquí (no hace falta recalcular por fila).
    reservas_activas = TReserva.objects.filter(
        id_estado__codigo='activa'
    ).select_related('id_usuario', 'id_libro', 'id_estado').order_by('-fecha_reserva')

    estado_ejemplar_disponible = PEstado.objects.get(entidad='EJEMPLAR', codigo='disponible')

    for reserva in reservas_activas:
        reserva.ejemplares_disponibles = MEjemplar.objects.filter(
            id_libro_id=reserva.id_libro_id, id_estado=estado_ejemplar_disponible
        )

    return render(request, 'reservas/lista.html', {
        'usuarios': usuarios,
        'libros': libros,
        'bibliotecarios': bibliotecarios,
        'reservas_activas': reservas_activas,
    })


def convertir_reserva(request, id_reserva):
    if request.method == 'POST':
        ejemplar_id = request.POST.get('ejemplar')
        bibliotecario_id = request.POST.get('bibliotecario')
        try:
            convertir_a_prestamo(id_reserva, ejemplar_id, bibliotecario_id)
            messages.success(request, "Reserva convertida a préstamo correctamente.")
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))
        except Exception as e:
            messages.error(request, f"Error al convertir la reserva: {e}")

    return redirect('reservas:lista')


def cancelar(request, id_reserva):
    if request.method == 'POST':
        try:
            cancelar_reserva(id_reserva)
            messages.success(request, "Reserva cancelada correctamente.")
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))
        except Exception as e:
            messages.error(request, f"Error al cancelar la reserva: {e}")

    return redirect('reservas:lista')
