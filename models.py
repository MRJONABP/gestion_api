from datetime import datetime
from sqlalchemy.sql import func
from db import db  # Importa la instancia de SQLAlchemy

# --------------------- MODELOS ---------------------

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    telefono = db.Column(db.String(15))
    correo = db.Column(db.String(100))
    ruc = db.Column(db.String(20))
    dni = db.Column(db.String(15))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

class Servicio(db.Model):
    __tablename__ = 'servicios'
    id = db.Column(db.Integer, primary_key=True)
    nombre_servicio = db.Column(db.String(255), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    precio = db.Column(db.Float, default=0.0)

class Plan(db.Model):
    __tablename__ = 'planes'
    id = db.Column(db.Integer, primary_key=True)
    nombre_plan = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text)
    duracion = db.Column(db.Integer, default=30)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=False)
    precio = db.Column(db.Numeric(10, 2), default=0.00)
    caracteristicas = db.Column(db.Text)

class Cotizacion(db.Model):
    __tablename__ = 'cotizaciones'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=False)
    plan = db.Column(db.String(50))
    precio_sin_igv = db.Column(db.Numeric(10, 2), nullable=False)
    precio_con_igv = db.Column(db.Numeric(10, 2), nullable=False)
    detalles = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime(timezone=True), default=func.now())
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    plan_id = db.Column(db.Integer, db.ForeignKey('planes.id'))

class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    telefono = db.Column(db.String(15))
    correo = db.Column(db.String(100))
    ruc = db.Column(db.String(20))
    dni = db.Column(db.String(15))
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=False)
    fecha_servicio = db.Column(db.Date, nullable=False)
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    monto_total = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    notas = db.Column(db.Text)
    tipo_documento = db.Column(db.String(10), default='boleta')

class Carpeta(db.Model):
    __tablename__ = 'carpetas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

class Archivo(db.Model):
    __tablename__ = 'archivos'
    id = db.Column(db.Integer, primary_key=True)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    carpeta_id = db.Column(db.Integer, db.ForeignKey('carpetas.id'))
    mes = db.Column(db.String(15), nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    tipo_documento = db.Column(db.String(50), nullable=False)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    contenido = db.Column(db.LargeBinary, nullable=False)  # ✅ Debes incluir esto si trabajas con archivos binarios


class HostingFacturacion(db.Model):
    __tablename__ = 'hosting_facturacion'
    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(100), default='', nullable=False)
    proveedor = db.Column(db.String(100), nullable=False)
    plan = db.Column(db.String(100), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_renovacion = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    periodo = db.Column(db.String(15), nullable=False)
    estado = db.Column(db.String(15), default='activo')
    notificacion_enviada = db.Column(db.Boolean, default=False)
    notas = db.Column(db.Text)

class HostingRenovacion(db.Model):
    __tablename__ = 'hosting_renovaciones'
    id = db.Column(db.Integer, primary_key=True)
    hosting_id = db.Column(db.Integer, db.ForeignKey('hosting_facturacion.id'), nullable=False)
    fecha_anterior = db.Column(db.Date, nullable=False)
    fecha_nueva = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_renovacion = db.Column(db.Date, nullable=False)
