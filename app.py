from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy.sql import func
import os
from db import db
from models import Usuario, Cliente, Servicio, Plan, Cotizacion, Venta, Carpeta, Archivo, HostingFacturacion, HostingRenovacion
from datetime import datetime
import base64
import pytz
from flask import send_file
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from models import Cotizacion, Cliente, Servicio  # asegúrate de importar tus modelos
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bpstudio:bUqf0JXdcVNIHLcd3D6aguP93veUOAnI@dpg-d1vgur2dbo4c73fggvlg-a.oregon-postgres.render.com/gestion_client'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/')
def home():
    return 'API gestion_client funcionando ✅'

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = Usuario.query.filter_by(username=data.get('username')).first()
    if user and user.password == data.get('password'):
        return jsonify({
            'status': 'success',
            'message': 'Login exitoso',
            'user': {'username': user.username, 'name': user.name}
        })
    return jsonify({'status': 'error', 'message': 'Credenciales inválidas'}), 401

@app.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    total_clientes = Cliente.query.count()
    total_servicios = Servicio.query.count()
    total_ventas = Venta.query.count()
    total_ganancias = db.session.query(func.sum(Venta.monto_total)).scalar() or 0.0
    return jsonify({
        'clientes': total_clientes,
        'servicios': total_servicios,
        'ventas': total_ventas,
        'ganancias': float(total_ganancias)
    })

@app.route('/archivo/<int:id>/contenido', methods=['GET'])
def obtener_contenido_archivo(id):
    archivo = Archivo.query.get(id)
    if archivo and archivo.contenido:
        contenido_base64 = base64.b64encode(archivo.contenido).decode('utf-8')
        return jsonify({'contenido': contenido_base64})
    return jsonify({'error': 'Archivo no encontrado'}), 404

def generate_crud_routes(model, route_name):
    list_endpoint = f'get_all_{route_name}'
    get_endpoint = f'get_one_{route_name}'
    create_endpoint = f'create_{route_name}'
    update_endpoint = f'update_{route_name}'
    delete_endpoint = f'delete_{route_name}'

    @app.route(f'/{route_name}', methods=['GET'], endpoint=list_endpoint)
    def get_all():
        items = model.query.all()
        result = []
        for item in items:
            data = item.__dict__.copy()
            data.pop('_sa_instance_state', None)
            if isinstance(item, Archivo):
                data.pop('contenido', None)
            result.append(data)
        return jsonify(result)

    @app.route(f'/{route_name}/<int:item_id>', methods=['GET'], endpoint=get_endpoint)
    def get_one(item_id):
        item = model.query.get(item_id)
        if item:
            result = item.__dict__.copy()
            result.pop('_sa_instance_state', None)
            if isinstance(item, Archivo):
                result.pop('contenido', None)
            return jsonify(result)
        return jsonify({'error': 'No encontrado'}), 404

    if model == Archivo:
        @app.route(f'/{route_name}', methods=['POST'], endpoint=create_endpoint)
        def create_file():
            archivo = request.files.get('archivo')
            if not archivo:
                return jsonify({'error': 'Archivo no proporcionado'}), 400

            contenido = archivo.read()

            nuevo_archivo = Archivo(
                nombre_archivo=request.form.get('nombre_archivo'),
                tipo_documento=request.form.get('tipo_documento'),
                mes=request.form.get('mes'),
                anio=int(request.form.get('anio')),
                carpeta_id=int(request.form.get('carpeta_id')),
                fecha_subida=datetime.utcnow(),
                contenido=contenido
            )

            db.session.add(nuevo_archivo)
            db.session.commit()

            return jsonify({'message': 'Archivo subido correctamente'})
    else:
        @app.route(f'/{route_name}', methods=['POST'], endpoint=create_endpoint)
        def create_item():
            data = request.json
            item = model(**data)
            db.session.add(item)
            db.session.commit()
            return jsonify({'message': f'{route_name[:-1].capitalize()} creado exitosamente'})

    @app.route(f'/{route_name}/<int:item_id>', methods=['PUT'], endpoint=update_endpoint)
    def update_item(item_id):
        item = model.query.get(item_id)
        if not item:
            return jsonify({'error': 'No encontrado'}), 404
        data = request.form if model == Archivo else request.json
        for key, value in data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        if model == Archivo and 'archivo' in request.files:
            item.contenido = request.files['archivo'].read()
        db.session.commit()
        return jsonify({'message': f'{route_name[:-1].capitalize()} actualizado exitosamente'})

    @app.route(f'/{route_name}/<int:item_id>', methods=['DELETE'], endpoint=delete_endpoint)
    def delete_item(item_id):
        item = model.query.get(item_id)
        if not item:
            return jsonify({'error': 'No encontrado'}), 404
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': f'{route_name[:-1].capitalize()} eliminado exitosamente'})

with app.app_context():
    db.create_all()
@app.route('/ventas', methods=['GET'])
def obtener_ventas():
    resultados = db.session.query(
        Venta.id,
        Venta.cliente_id,
        Cliente.nombre.label('nombre'),
        Cliente.apellido.label('apellido'),
        Cliente.telefono,
        Cliente.correo,
        Cliente.ruc,
        Cliente.dni,
        Venta.servicio_id,
        Servicio.nombre_servicio.label('nombre_servicio'),
        Venta.fecha_servicio,
        Venta.fecha_inicio,
        Venta.fecha_fin,
        Venta.monto_total,
        Venta.fecha_registro,
        Venta.notas,
        Venta.tipo_documento
    ).join(Cliente, Cliente.id == Venta.cliente_id)\
     .join(Servicio, Servicio.id == Venta.servicio_id)\
     .all()

    ventas = []
    for v in resultados:
        ventas.append({
            'id': v.id,
            'cliente_id': v.cliente_id,
            'nombre': v.nombre,
            'apellido': v.apellido,
            'telefono': v.telefono,
            'correo': v.correo,
            'ruc': v.ruc,
            'dni': v.dni,
            'servicio_id': v.servicio_id,
            'nombre_servicio': v.nombre_servicio,
            'fecha_servicio': v.fecha_servicio.isoformat(),
            'fecha_inicio': v.fecha_inicio.isoformat() if v.fecha_inicio else None,
            'fecha_fin': v.fecha_fin.isoformat() if v.fecha_fin else None,
            'monto_total': float(v.monto_total),
            'fecha_registro': v.fecha_registro.isoformat() if v.fecha_registro else None,
            'notas': v.notas,
            'tipo_documento': v.tipo_documento,
        })
    return jsonify(ventas)

from datetime import datetime

@app.route('/cotizaciones', methods=['POST'])
def crear_cotizacion():
    data = request.json
    lima_tz = pytz.timezone('America/Lima')
    ahora_lima = datetime.now(lima_tz)

    nueva = Cotizacion(
        cliente_id=data.get('cliente_id'),
        servicio_id=data.get('servicio_id'),
        plan_id=data.get('plan_id'),
        precio_sin_igv=data.get('precio_sin_igv'),
        precio_con_igv=data.get('precio_con_igv'),
        detalles=data.get('detalles'),
        fecha_creacion=ahora_lima  # 👈 con hora exacta de Lima
    )
    db.session.add(nueva)
    db.session.commit()
    return jsonify({'message': 'Cotización creada'})

@app.route('/cotizaciones-filtradas', methods=['GET'])
def cotizaciones_filtradas():
    anio = request.args.get('anio', type=int)
    mes = request.args.get('mes', type=int)
    cliente_id = request.args.get('cliente_id', type=int)
    servicio_id = request.args.get('servicio_id', type=int)

    query = Cotizacion.query

    if anio:
        query = query.filter(func.extract('year', Cotizacion.fecha_creacion) == anio)
    if mes:
        query = query.filter(func.extract('month', Cotizacion.fecha_creacion) == mes)
    if cliente_id:
        query = query.filter(Cotizacion.cliente_id == cliente_id)
    if servicio_id:
        query = query.filter(Cotizacion.servicio_id == servicio_id)

    cotizaciones = query.all()

    resultado = []
    for c in cotizaciones:
        resultado.append({
            'id': c.id,
            'cliente_id': c.cliente_id,
            'servicio_id': c.servicio_id,
            'plan_id': c.plan_id,
            'precio_sin_igv': float(c.precio_sin_igv),
            'precio_con_igv': float(c.precio_con_igv),
            'detalles': c.detalles,
            'fecha_creacion': c.fecha_creacion.isoformat() if c.fecha_creacion else None,
            'fecha_registro': c.fecha_registro.isoformat() if c.fecha_registro else None,
        })

    return jsonify(resultado)

@app.route('/cotizacion/<int:id>/pdf')
def generar_pdf_cotizacion(id):
    cotizacion = Cotizacion.query.get_or_404(id)
    cliente = Cliente.query.get(cotizacion.cliente_id)
    servicio = Servicio.query.get(cotizacion.servicio_id)
    plan = Plan.query.get(cotizacion.plan_id)  # 👈 aquí traes el plan

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, 750, "Cotización")

    p.setFont("Helvetica", 14)
    p.drawString(50, 720, f"Cliente: {cliente.nombre} {cliente.apellido}")
    p.drawString(50, 700, f"Servicio: {servicio.nombre_servicio}")
    p.drawString(50, 680, f"Plan: {plan.nombre_plan if plan else 'Ninguno'}")  # 👈 corregido
    p.drawString(50, 660, f"Precio sin IGV: S/ {cotizacion.precio_sin_igv:.2f}")
    p.drawString(50, 640, f"Precio con IGV: S/ {cotizacion.precio_con_igv:.2f}")
    p.drawString(50, 620, f"Detalles: {cotizacion.detalles}")
    p.drawString(50, 600, f"Fecha creación: {cotizacion.fecha_creacion.strftime('%d/%m/%Y')}")

    p.showPage()
    p.save()

    buffer.seek(0)
    return send_file(
        buffer,
        download_name=f'cotizacion_{id}.pdf',
        mimetype='application/pdf'
    )
# ---------- RUTAS SERVICIOS ----------
@app.route('/servicios', methods=['GET'])
def get_servicios():
    servicios = Servicio.query.all()
    return jsonify([{'id': s.id, 'nombre_servicio': s.nombre_servicio} for s in servicios])

@app.route('/servicios', methods=['POST'])
def crear_servicio():
    data = request.json
    nuevo = Servicio(nombre_servicio=data['nombre_servicio'])
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({'message': 'Servicio creado'})

@app.route('/servicios/<int:id>', methods=['PUT'])
def actualizar_servicio(id):
    data = request.json
    servicio = Servicio.query.get_or_404(id)
    servicio.nombre_servicio = data['nombre_servicio']
    db.session.commit()
    return jsonify({'message': 'Servicio actualizado'})

@app.route('/servicios/<int:id>', methods=['DELETE'])
def eliminar_servicio(id):
    servicio = Servicio.query.get_or_404(id)
    db.session.delete(servicio)
    db.session.commit()
    return jsonify({'message': 'Servicio eliminado'})

# ---------- RUTAS PLANES ----------
@app.route('/planes', methods=['GET'])
def get_planes():
    planes = Plan.query.all()
    return jsonify([
        {
            'id': p.id,
            'nombre_plan': p.nombre_plan,
            'descripcion': p.descripcion,
            'duracion': p.duracion,
            'servicio_id': p.servicio_id,
            'precio': float(p.precio),
            'caracteristicas': p.caracteristicas
        } for p in planes
    ])

@app.route('/planes', methods=['POST'])
def crear_plan():
    data = request.json
    nuevo = Plan(
        nombre_plan=data['nombre_plan'],
        descripcion=data.get('descripcion', ''),
        duracion=data.get('duracion', 30),
        servicio_id=data['servicio_id'],
        precio=data.get('precio', 0.00),
        caracteristicas=data.get('caracteristicas', '')
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({'message': 'Plan creado'})

@app.route('/planes/<int:id>', methods=['PUT'])
def actualizar_plan(id):
    data = request.json
    plan = Plan.query.get_or_404(id)
    plan.nombre_plan = data['nombre_plan']
    plan.descripcion = data.get('descripcion', '')
    plan.duracion = data.get('duracion', 30)
    plan.servicio_id = data['servicio_id']
    plan.precio = data.get('precio', 0.00)
    plan.caracteristicas = data.get('caracteristicas', '')
    db.session.commit()
    return jsonify({'message': 'Plan actualizado'})

@app.route('/planes/<int:id>', methods=['DELETE'])
def eliminar_plan(id):
    plan = Plan.query.get_or_404(id)
    db.session.delete(plan)
    db.session.commit()
    return jsonify({'message': 'Plan eliminado'})

# ---------- RUTAS USUARIOS ----------
@app.route('/usuarios', methods=['GET'])
def get_usuarios():
    usuarios = Usuario.query.all()
    return jsonify([
        {
            'id': u.id,
            'username': u.username,
            'name': u.name,
            'created_at': u.created_at.strftime('%d/%m/%Y %H:%M')
        } for u in usuarios
    ])

@app.route('/usuarios', methods=['POST'])
def crear_usuario():
    data = request.json
    nuevo = Usuario(
        username=data['username'],
        password=data['password'],
        name=data['name']
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({'message': 'Usuario creado'})

@app.route('/usuarios/<int:id>', methods=['PUT'])
def actualizar_usuario(id):
    data = request.json
    usuario = Usuario.query.get_or_404(id)
    usuario.username = data['username']
    usuario.password = data['password']
    usuario.name = data['name']
    db.session.commit()
    return jsonify({'message': 'Usuario actualizado'})

@app.route('/usuarios/<int:id>', methods=['DELETE'])
def eliminar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    return jsonify({'message': 'Usuario eliminado'})

# ENDPOINTS HOSTING

@app.route("/hostings", methods=["GET"])
def listar_hostings():
    hostings = HostingFacturacion.query.all()
    return jsonify([{
        "id": h.id,
        "cliente": h.cliente,
        "proveedor": h.proveedor,
        "plan": h.plan,
        "fecha_inicio": h.fecha_inicio.isoformat(),
        "fecha_renovacion": h.fecha_renovacion.isoformat(),
        "monto": float(h.monto),
        "periodo": h.periodo,
        "estado": h.estado,
        "notificacion_enviada": h.notificacion_enviada,
        "notas": h.notas
    } for h in hostings])

@app.route("/hostings", methods=["POST"])
def crear_hosting():
    data = request.json
    nuevo = HostingFacturacion(
        cliente=data["cliente"],
        proveedor=data["proveedor"],
        plan=data["plan"],
        fecha_inicio=datetime.strptime(data["fecha_inicio"], "%Y-%m-%d"),
        fecha_renovacion=datetime.strptime(data["fecha_renovacion"], "%Y-%m-%d"),
        monto=data["monto"],
        periodo=data["periodo"],
        estado=data.get("estado", "activo"),
        notificacion_enviada=data.get("notificacion_enviada", False),
        notas=data.get("notas", "")
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"mensaje": "Hosting creado exitosamente"})

@app.route("/hostings/<int:id>", methods=["PUT"])
def actualizar_hosting(id):
    h = HostingFacturacion.query.get_or_404(id)
    data = request.json
    h.cliente = data["cliente"]
    h.proveedor = data["proveedor"]
    h.plan = data["plan"]
    h.fecha_inicio = datetime.strptime(data["fecha_inicio"], "%Y-%m-%d")
    h.fecha_renovacion = datetime.strptime(data["fecha_renovacion"], "%Y-%m-%d")
    h.monto = data["monto"]
    h.periodo = data["periodo"]
    h.estado = data["estado"]
    h.notificacion_enviada = data.get("notificacion_enviada", False)
    h.notas = data.get("notas", "")
    db.session.commit()
    return jsonify({"mensaje": "Hosting actualizado correctamente"})

@app.route("/hostings/<int:id>", methods=["DELETE"])
def eliminar_hosting(id):
    h = HostingFacturacion.query.get_or_404(id)
    db.session.delete(h)
    db.session.commit()
    return jsonify({"mensaje": "Hosting eliminado correctamente"})

# ENDPOINTS RENOVACIONES

@app.route("/renovaciones/<int:hosting_id>", methods=["GET"])
def listar_renovaciones(hosting_id):
    renovaciones = HostingRenovacion.query.filter_by(hosting_id=hosting_id).all()
    return jsonify([{
        "id": r.id,
        "hosting_id": r.hosting_id,
        "fecha_anterior": r.fecha_anterior.isoformat(),
        "fecha_nueva": r.fecha_nueva.isoformat(),
        "monto": float(r.monto),
        "fecha_renovacion": r.fecha_renovacion.isoformat()
    } for r in renovaciones])

@app.route("/renovaciones", methods=["POST"])
def crear_renovacion():
    data = request.json
    renovacion = HostingRenovacion(
        hosting_id=data["hosting_id"],
        fecha_anterior=datetime.strptime(data["fecha_anterior"], "%Y-%m-%d"),
        fecha_nueva=datetime.strptime(data["fecha_nueva"], "%Y-%m-%d"),
        monto=data["monto"],
        fecha_renovacion=datetime.strptime(data["fecha_renovacion"], "%Y-%m-%d")
    )
    db.session.add(renovacion)
    db.session.commit()
    return jsonify({"mensaje": "Renovación registrada correctamente"})


generate_crud_routes(Cliente, 'clientes')
generate_crud_routes(Servicio, 'servicios')
generate_crud_routes(Plan, 'planes')
generate_crud_routes(Cotizacion, 'cotizaciones')
generate_crud_routes(Venta, 'ventas')
generate_crud_routes(Carpeta, 'carpetas')
generate_crud_routes(Archivo, 'archivos')
generate_crud_routes(HostingFacturacion, 'hosting_facturacion')
generate_crud_routes(HostingRenovacion, 'hosting_renovaciones')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
