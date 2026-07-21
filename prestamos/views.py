from datetime import date

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render, redirect

from .models import MBibliotecario, MEjemplar, MUsuario, PEstado, TDetallePrestamo, TDevolucion, TPrestamo
from .servicios import (
    calcular_fecha_devolucion_esperada,
    contar_ejemplares_disponibles,
    contar_multas_pendientes,
    contar_prestamos_activos,
    contar_reservas_activas,
    procesar_devolucion,
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
    estado_prestamo_vencido = PEstado.objects.get(entidad='PRESTAMO', codigo='vencido')

    usuarios = MUsuario.objects.all().order_by('apellidos', 'nombres')
    bibliotecarios = MBibliotecario.objects.all().order_by('apellido', 'nombre')
    ejemplares_disponibles = MEjemplar.objects.filter(
        id_estado=estado_ejemplar_disponible
    ).select_related('id_libro').order_by('id_libro__titulo_libro')

    # Por detalle/ejemplar (no por préstamo): un préstamo con varios ejemplares
    # puede tener algunos ya devueltos y otros pendientes.
    detalles_pendientes = TDetallePrestamo.objects.filter(
        id_prestamo__id_estado__in=[estado_prestamo_activo, estado_prestamo_vencido]
    ).exclude(
        id_detalle__in=TDevolucion.objects.values_list('id_detalle', flat=True)
    ).select_related(
        'id_prestamo__id_usuario', 'id_prestamo__id_estado', 'id_ejemplar__id_libro'
    ).order_by('-id_prestamo__fecha_prestamo')

    condiciones_ejemplar = PEstado.objects.filter(entidad='CONDICION_EJEMPLAR').order_by('id_estado')

    return render(request, 'prestamos/lista.html', {
        'usuarios': usuarios,
        'bibliotecarios': bibliotecarios,
        'ejemplares_disponibles': ejemplares_disponibles,
        'detalles_pendientes': detalles_pendientes,
        'condiciones_ejemplar': condiciones_ejemplar,
    })


def registrar_devolucion(request, id_detalle):
    if request.method == 'POST':
        condicion_id = request.POST.get('condicion')
        try:
            procesar_devolucion(id_detalle, condicion_id)
            messages.success(request, "Devolución registrada correctamente.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect('prestamos:lista')
