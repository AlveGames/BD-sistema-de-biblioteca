from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from prestamos.models import MAutor, MBibliotecario, MEjemplar, MLibro, MUsuario, RLibroAutor

from .forms import AutorForm, BibliotecarioForm, EjemplarForm, LibroForm, UsuarioForm


def index(request):
    return render(request, 'mantenimiento/index.html')


class ProtegerEliminacionMixin:
    """Evita el error 500 cuando la fila tiene registros relacionados (FK con ON DELETE NO ACTION en SQL Server)."""

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except IntegrityError:
            messages.error(
                self.request,
                "No se puede eliminar: tiene registros relacionados (préstamos, reservas, "
                "multas, etc.). Elimina o reasigna esos registros primero.",
            )
            return HttpResponseRedirect(self.get_success_url())


# ---------- Usuario ----------

class UsuarioListView(ListView):
    model = MUsuario
    template_name = 'mantenimiento/usuario_lista.html'
    extra_context = {'titulo': 'Usuarios'}


class UsuarioCreateView(CreateView):
    model = MUsuario
    form_class = UsuarioForm
    template_name = 'mantenimiento/form_generico.html'
    success_url = reverse_lazy('mantenimiento:usuario_lista')
    extra_context = {'titulo': 'Nuevo usuario', 'url_cancelar': 'mantenimiento:usuario_lista'}


class UsuarioUpdateView(UpdateView):
    model = MUsuario
    form_class = UsuarioForm
    template_name = 'mantenimiento/form_generico.html'
    success_url = reverse_lazy('mantenimiento:usuario_lista')
    extra_context = {'titulo': 'Editar usuario', 'url_cancelar': 'mantenimiento:usuario_lista'}


class UsuarioDeleteView(ProtegerEliminacionMixin, DeleteView):
    model = MUsuario
    template_name = 'mantenimiento/confirm_delete_generico.html'
    success_url = reverse_lazy('mantenimiento:usuario_lista')
    extra_context = {'titulo': 'Eliminar usuario', 'url_cancelar': 'mantenimiento:usuario_lista'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['descripcion'] = f"{self.object.nombres} {self.object.apellidos}"
        return context


# ---------- Autor ----------

class AutorListView(ListView):
    model = MAutor
    template_name = 'mantenimiento/autor_lista.html'
    extra_context = {'titulo': 'Autores'}


class AutorCreateView(CreateView):
    model = MAutor
    form_class = AutorForm
    template_name = 'mantenimiento/form_generico.html'
    success_url = reverse_lazy('mantenimiento:autor_lista')
    extra_context = {'titulo': 'Nuevo autor', 'url_cancelar': 'mantenimiento:autor_lista'}


class AutorUpdateView(UpdateView):
    model = MAutor
    form_class = AutorForm
    template_name = 'mantenimiento/form_generico.html'
    success_url = reverse_lazy('mantenimiento:autor_lista')
    extra_context = {'titulo': 'Editar autor', 'url_cancelar': 'mantenimiento:autor_lista'}


class AutorDeleteView(ProtegerEliminacionMixin, DeleteView):
    model = MAutor
    template_name = 'mantenimiento/confirm_delete_generico.html'
    success_url = reverse_lazy('mantenimiento:autor_lista')
    extra_context = {'titulo': 'Eliminar autor', 'url_cancelar': 'mantenimiento:autor_lista'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['descripcion'] = self.object.nombre_autor
        return context


# ---------- Bibliotecario ----------

class BibliotecarioListView(ListView):
    model = MBibliotecario
    template_name = 'mantenimiento/bibliotecario_lista.html'
    extra_context = {'titulo': 'Bibliotecarios'}


class BibliotecarioCreateView(CreateView):
    model = MBibliotecario
    form_class = BibliotecarioForm
    template_name = 'mantenimiento/form_generico.html'
    success_url = reverse_lazy('mantenimiento:bibliotecario_lista')
    extra_context = {'titulo': 'Nuevo bibliotecario', 'url_cancelar': 'mantenimiento:bibliotecario_lista'}


class BibliotecarioUpdateView(UpdateView):
    model = MBibliotecario
    form_class = BibliotecarioForm
    template_name = 'mantenimiento/form_generico.html'
    success_url = reverse_lazy('mantenimiento:bibliotecario_lista')
    extra_context = {'titulo': 'Editar bibliotecario', 'url_cancelar': 'mantenimiento:bibliotecario_lista'}


class BibliotecarioDeleteView(ProtegerEliminacionMixin, DeleteView):
    model = MBibliotecario
    template_name = 'mantenimiento/confirm_delete_generico.html'
    success_url = reverse_lazy('mantenimiento:bibliotecario_lista')
    extra_context = {'titulo': 'Eliminar bibliotecario', 'url_cancelar': 'mantenimiento:bibliotecario_lista'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['descripcion'] = f"{self.object.nombre} {self.object.apellido}"
        return context


# ---------- Libro (con autores vía R_LIBRO_AUTOR) ----------

class LibroAutoresMixin:
    def form_valid(self, form):
        response = super().form_valid(form)
        autores_seleccionados = list(form.cleaned_data.get('autores', []))
        RLibroAutor.objects.filter(id_libro=self.object).exclude(
            id_autor__in=autores_seleccionados
        ).delete()
        for autor in autores_seleccionados:
            RLibroAutor.objects.get_or_create(id_libro=self.object, id_autor=autor)
        return response


class LibroListView(ListView):
    model = MLibro
    template_name = 'mantenimiento/libro_lista.html'
    extra_context = {'titulo': 'Libros'}


class LibroCreateView(LibroAutoresMixin, CreateView):
    model = MLibro
    form_class = LibroForm
    template_name = 'mantenimiento/form_generico.html'
    success_url = reverse_lazy('mantenimiento:libro_lista')
    extra_context = {'titulo': 'Nuevo libro', 'url_cancelar': 'mantenimiento:libro_lista'}


class LibroUpdateView(LibroAutoresMixin, UpdateView):
    model = MLibro
    form_class = LibroForm
    template_name = 'mantenimiento/form_generico.html'
    success_url = reverse_lazy('mantenimiento:libro_lista')
    extra_context = {'titulo': 'Editar libro', 'url_cancelar': 'mantenimiento:libro_lista'}


class LibroDeleteView(ProtegerEliminacionMixin, DeleteView):
    model = MLibro
    template_name = 'mantenimiento/confirm_delete_generico.html'
    success_url = reverse_lazy('mantenimiento:libro_lista')
    extra_context = {'titulo': 'Eliminar libro', 'url_cancelar': 'mantenimiento:libro_lista'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['descripcion'] = self.object.titulo_libro
        return context


# ---------- Ejemplar ----------

class EjemplarListView(ListView):
    model = MEjemplar
    template_name = 'mantenimiento/ejemplar_lista.html'
    extra_context = {'titulo': 'Ejemplares'}

    def get_queryset(self):
        return super().get_queryset().select_related('id_libro', 'id_estado')


class EjemplarCreateView(CreateView):
    model = MEjemplar
    form_class = EjemplarForm
    template_name = 'mantenimiento/form_generico.html'
    success_url = reverse_lazy('mantenimiento:ejemplar_lista')
    extra_context = {'titulo': 'Nuevo ejemplar', 'url_cancelar': 'mantenimiento:ejemplar_lista'}


class EjemplarUpdateView(UpdateView):
    model = MEjemplar
    form_class = EjemplarForm
    template_name = 'mantenimiento/form_generico.html'
    success_url = reverse_lazy('mantenimiento:ejemplar_lista')
    extra_context = {'titulo': 'Editar ejemplar', 'url_cancelar': 'mantenimiento:ejemplar_lista'}


class EjemplarDeleteView(ProtegerEliminacionMixin, DeleteView):
    model = MEjemplar
    template_name = 'mantenimiento/confirm_delete_generico.html'
    success_url = reverse_lazy('mantenimiento:ejemplar_lista')
    extra_context = {'titulo': 'Eliminar ejemplar', 'url_cancelar': 'mantenimiento:ejemplar_lista'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['descripcion'] = f"{self.object.id_libro.titulo_libro} (serie {self.object.numero_serie})"
        return context
