from django import forms

from prestamos.models import MAutor, MBibliotecario, MEjemplar, MLibro, MUsuario, PEstado


class UsuarioForm(forms.ModelForm):
    class Meta:
        model = MUsuario
        fields = '__all__'
        widgets = {
            'password': forms.PasswordInput(render_value=True),
        }


class AutorForm(forms.ModelForm):
    class Meta:
        model = MAutor
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }


class BibliotecarioForm(forms.ModelForm):
    class Meta:
        model = MBibliotecario
        fields = '__all__'
        widgets = {
            'fecha_contratacion': forms.DateInput(attrs={'type': 'date'}),
        }


class LibroForm(forms.ModelForm):
    autores = forms.ModelMultipleChoiceField(
        queryset=MAutor.objects.all().order_by('nombre_autor'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = MLibro
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['autores'].initial = MAutor.objects.filter(
                rlibroautor__id_libro=self.instance
            )


class EjemplarForm(forms.ModelForm):
    class Meta:
        model = MEjemplar
        fields = '__all__'
        widgets = {
            'fecha_adquisicion': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El estado del ejemplar solo puede venir de los codigos de P_ESTADO
        # que pertenecen a la entidad EJEMPLAR (disponible/prestado/dañado/perdido).
        self.fields['id_estado'].queryset = PEstado.objects.filter(entidad='EJEMPLAR')
