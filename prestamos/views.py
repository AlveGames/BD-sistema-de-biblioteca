from datetime import date

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render, redirect

from .models import MBibliotecario, MEjemplar, MUsuario, PEstado, TDetallePrestamo, TPrestamo
from .servicios import (
    calcular_fecha_devolucion_esperada,
    contar_ejemplares_disponibles,
    contar_multas_pendientes,
    contar_prestamos_activos,
    contar_reservas_activas,
    validar_nuevo_prestamo,
)


def inicio(request):
    contexto = {
        'prestamos_activos': contar_prestamos_activos(),
        'reservas_activas': contar_reservas_activas(),
        'multas_pendientes': contar_multas_pendientes(),
        'ejemplares_disponibles': contar_ejemplares_disponibles(),
    }
    return render(request, 'prestamos/inicio.html', contexto)


def lista(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario')
        bibliotecario_id = request.POST.get('bibliotecario')
        ejemplares_ids = request.POST.getlist('ejemplares')

        try:
            with transaction.atomic():
                validar_nuevo_prestamo(usuario_id, ejemplares_ids)

                estado_prestamo_activo = PEstado.objects.get(entidad='PRESTAMO', codigo='activo')
                estado_ejemplar_prestado = PEstado.objects.get(entidad='EJEMPLAR', codigo='prestado')

                fecha_prestamo = date.today()
                prestamo = TPrestamo.objects.create(
                    id_usuario_id=usuario_id,
                    id_bibliotecario_id=bibliotecario_id,
                    fecha_prestamo=fecha_prestamo,
                    fecha_devolucion_esperada=calcular_fecha_devolucion_esperada(fecha_prestamo),
                    id_estado=estado_prestamo_activo,
                )

                for ejemplar_id in ejemplares_ids:
                    TDetallePrestamo.objects.create(
                        id_prestamo=prestamo,
                        id_ejemplar_id=ejemplar_id,
                    )

                MEjemplar.objects.filter(id_ejemplar__in=ejemplares_ids).update(
                    id_estado=estado_ejemplar_prestado
                )

            messages.success(request, "Préstamo registrado correctamente.")
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))
        except Exception as e:
            messages.error(request, f"Error al registrar el préstamo: {e}")

        return redirect('prestamos:lista')

    estado_ejemplar_disponible = PEstado.objects.get(entidad='EJEMPLAR', codigo='disponible')
    estado_prestamo_activo = PEstado.objects.get(entidad='PRESTAMO', codigo='activo')

    usuarios = MUsuario.objects.all().order_by('apellidos', 'nombres')
    bibliotecarios = MBibliotecario.objects.all().order_by('apellido', 'nombre')
    ejemplares_disponibles = MEjemplar.objects.filter(
        id_estado=estado_ejemplar_disponible
    ).select_related('id_libro').order_by('id_libro__titulo_libro')
    prestamos_activos = TPrestamo.objects.filter(
        id_estado=estado_prestamo_activo
    ).select_related('id_usuario', 'id_bibliotecario', 'id_estado').order_by('-fecha_prestamo')

    return render(request, 'prestamos/lista.html', {
        'usuarios': usuarios,
        'bibliotecarios': bibliotecarios,
        'ejemplares_disponibles': ejemplares_disponibles,
        'prestamos_activos': prestamos_activos,
    })
