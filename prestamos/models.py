# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class MAutor(models.Model):
    id_autor = models.AutoField(primary_key=True)
    nombre_autor = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS')
    fecha_nacimiento = models.DateField(blank=True, null=True)
    bibliografia = models.CharField(max_length=500, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    id_nacionalidad = models.ForeignKey('PNacionalidad', models.DO_NOTHING, db_column='id_nacionalidad')

    class Meta:
        managed = False
        db_table = 'M_AUTOR'


class MBibliotecario(models.Model):
    id_bibliotecario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80, db_collation='Modern_Spanish_CI_AS')
    correo = models.CharField(unique=True, max_length=80, db_collation='Modern_Spanish_CI_AS')
    apellido = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS')
    telefono = models.CharField(max_length=15, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    fecha_contratacion = models.DateField()
    estado = models.CharField(max_length=20, db_collation='Modern_Spanish_CI_AS')

    class Meta:
        managed = False
        db_table = 'M_BIBLIOTECARIO'


class MEjemplar(models.Model):
    id_ejemplar = models.AutoField(primary_key=True)
    id_libro = models.ForeignKey('MLibro', models.DO_NOTHING, db_column='id_libro')
    id_estado = models.ForeignKey('PEstado', models.DO_NOTHING, db_column='id_estado')
    fecha_adquisicion = models.DateField()
    numero_serie = models.CharField(unique=True, max_length=30, db_collation='Modern_Spanish_CI_AS')

    class Meta:
        managed = False
        db_table = 'M_EJEMPLAR'


class MLibro(models.Model):
    id_libro = models.AutoField(primary_key=True)
    titulo_libro = models.CharField(max_length=150, db_collation='Modern_Spanish_CI_AS')
    isbn = models.CharField(unique=True, max_length=20, db_collation='Modern_Spanish_CI_AS')
    anio_publicacion = models.IntegerField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    id_categoria = models.ForeignKey('PCategoria', models.DO_NOTHING, db_column='id_categoria')

    class Meta:
        managed = False
        db_table = 'M_LIBRO'


class MUsuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=80, db_collation='Modern_Spanish_CI_AS')
    apellidos = models.CharField(max_length=80, db_collation='Modern_Spanish_CI_AS')
    password = models.CharField(max_length=250, db_collation='Modern_Spanish_CI_AS')
    edad = models.IntegerField(blank=True, null=True)
    id_nacionalidad = models.ForeignKey('PNacionalidad', models.DO_NOTHING, db_column='id_nacionalidad')
    email = models.CharField(unique=True, max_length=100, db_collation='Modern_Spanish_CI_AS')
    telefono = models.CharField(max_length=15, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    dni = models.CharField(db_column='DNI', unique=True, max_length=15, db_collation='Modern_Spanish_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'M_USUARIO'


class PCategoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, db_collation='Modern_Spanish_CI_AS')
    descripcion = models.CharField(max_length=200, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'P_CATEGORIA'


class PEstado(models.Model):
    id_estado = models.AutoField(primary_key=True)
    entidad = models.CharField(max_length=30, db_collation='Modern_Spanish_CI_AS')
    codigo = models.CharField(max_length=40, db_collation='Modern_Spanish_CI_AS')
    descripcion = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'P_ESTADO'


class PMetodoPago(models.Model):
    id_metodo_pago = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS')

    class Meta:
        managed = False
        db_table = 'P_METODO_PAGO'


class PNacionalidad(models.Model):
    id_nacionalidad = models.AutoField(primary_key=True)
    nombre_nacionalidad = models.CharField(max_length=50, db_collation='Modern_Spanish_CI_AS')

    class Meta:
        managed = False
        db_table = 'P_NACIONALIDAD'


class PTipoMulta(models.Model):
    id_tipo_multa = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS')

    class Meta:
        managed = False
        db_table = 'P_TIPO_MULTA'


class RLibroAutor(models.Model):
    pk = models.CompositePrimaryKey('id_libro', 'id_autor')
    id_libro = models.ForeignKey(MLibro, models.DO_NOTHING, db_column='id_libro')
    id_autor = models.ForeignKey(MAutor, models.DO_NOTHING, db_column='id_autor')
    rol = models.CharField(max_length=40, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'R_LIBRO_AUTOR'


class TDetallePrestamo(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_prestamo = models.ForeignKey('TPrestamo', models.DO_NOTHING, db_column='id_prestamo')
    id_ejemplar = models.ForeignKey(MEjemplar, models.DO_NOTHING, db_column='id_ejemplar')

    class Meta:
        managed = False
        db_table = 'T_DETALLE_PRESTAMO'


class TDevolucion(models.Model):
    id_devolucion = models.AutoField(primary_key=True)
    id_detalle = models.ForeignKey(TDetallePrestamo, models.DO_NOTHING, db_column='id_detalle')
    fecha_devolucion_real = models.DateField()
    id_estado = models.ForeignKey(PEstado, models.DO_NOTHING, db_column='id_estado')
    dias_atraso = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'T_DEVOLUCION'


class TMulta(models.Model):
    id_multa = models.AutoField(primary_key=True)
    id_devolucion = models.ForeignKey(TDevolucion, models.DO_NOTHING, db_column='id_devolucion')
    id_tipo_multa = models.ForeignKey(PTipoMulta, models.DO_NOTHING, db_column='id_tipo_multa')
    monto = models.DecimalField(max_digits=8, decimal_places=2)
    id_estado = models.ForeignKey(PEstado, models.DO_NOTHING, db_column='id_estado')

    class Meta:
        managed = False
        db_table = 'T_MULTA'


class TPagoMulta(models.Model):
    id_pago = models.AutoField(primary_key=True)
    id_multa = models.ForeignKey(TMulta, models.DO_NOTHING, db_column='id_multa')
    id_bibliotecario = models.ForeignKey(MBibliotecario, models.DO_NOTHING, db_column='id_bibliotecario')
    id_estado = models.ForeignKey(PEstado, models.DO_NOTHING, db_column='id_estado')
    fecha_pago = models.DateField()
    monto_pagado = models.DecimalField(max_digits=8, decimal_places=2)
    id_metodo_pago = models.ForeignKey(PMetodoPago, models.DO_NOTHING, db_column='id_metodo_pago')

    class Meta:
        managed = False
        db_table = 'T_PAGO_MULTA'


class TPrestamo(models.Model):
    id_prestamo = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(MUsuario, models.DO_NOTHING, db_column='id_usuario')
    id_bibliotecario = models.ForeignKey(MBibliotecario, models.DO_NOTHING, db_column='id_bibliotecario')
    id_reserva = models.ForeignKey('TReserva', models.DO_NOTHING, db_column='id_reserva', blank=True, null=True)
    fecha_prestamo = models.DateField()
    id_estado = models.ForeignKey(PEstado, models.DO_NOTHING, db_column='id_estado')
    fecha_devolucion_esperada = models.DateField()

    class Meta:
        managed = False
        db_table = 'T_PRESTAMO'


class TReserva(models.Model):
    id_reserva = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(MUsuario, models.DO_NOTHING, db_column='id_usuario')
    id_libro = models.ForeignKey(MLibro, models.DO_NOTHING, db_column='id_libro')
    fecha_reserva = models.DateTimeField()
    fecha_vencimiento = models.DateField()
    id_estado = models.ForeignKey(PEstado, models.DO_NOTHING, db_column='id_estado')

    class Meta:
        managed = False
        db_table = 'T_RESERVA'


