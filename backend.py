from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
import re
import os

from flask_cors import CORS
app = Flask(__name__)
CORS(app)


# =============================================
# CONEXIÓN A LA BASE DE DATOS
# =============================================
def get_db_connection():
    try:
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '3306')
        db_name = os.environ.get('DB_NAME', 'defaultdb')
        db_user = os.environ.get('DB_USER', 'root')
        db_password = os.environ.get('DB_PASSWORD', '')
        
        print(f"Conectando a BD: host={db_host}, port={db_port}, db={db_name}, user={db_user}")
        
        connection = mysql.connector.connect(
            host=db_host,
            port=int(db_port),
            database=db_name,
            user=db_user,
            password=db_password
        )
        print("✅ Conexión exitosa a la base de datos")
        return connection
    except Error as e:
        print(f"Error de conexión: {e}")
        return None


# =============================================
# FUNCIÓN: Obtener socio por teléfono
# =============================================
def get_socio_by_tlf(telefono):
    if not telefono:
        return None
    
    connection = get_db_connection()
    if connection is None:
        return None
    
    cursor = connection.cursor(dictionary=True)
    query = "SELECT socioID, nombre, apellidos, bolsa FROM socio WHERE tlf = %s"
    cursor.execute(query, (telefono,))
    socio = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    return socio


# =============================================
# FUNCIÓN: Obtener partidoID por nombre de equipo (solo disponibles)
# =============================================
def get_partido_id(nombre_equipo):
    connection = get_db_connection()
    if connection is None:
        return None
    
    cursor = connection.cursor()
    query = """
        SELECT partidoID 
        FROM partido 
        WHERE nombreEquipoVisitante LIKE %s 
          AND disponible = TRUE
        ORDER BY fecha DESC 
        LIMIT 1
    """
    cursor.execute(query, (f"%{nombre_equipo}%",))
    result = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    return result[0] if result else None


# =============================================
# FUNCIÓN: Obtener precios actuales
# =============================================
def get_precios():
    connection = get_db_connection()
    if connection is None:
        return None, None
    
    cursor = connection.cursor()
    cursor.execute("SELECT precioSocio, precioNoSocio FROM auxiliar WHERE id = 1")
    result = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    return (result[0], result[1]) if result else (None, None)


# =============================================
# FUNCIÓN: Calcular coste total de una reserva
# =============================================
def calcular_coste_total(plaza_socio, num_plazas_NO_socio):
    precios = get_precios()
    if precios is None:
        return 0
    precio_socio, precio_no_socio = precios
    coste = (precio_socio if plaza_socio else 0) + (num_plazas_NO_socio * precio_no_socio)
    return coste


# =============================================
# FUNCIÓN: Insertar o actualizar reserva (crea o modifica según exista)
# =============================================
def insertar_reserva(partidoID, socioID, plazaSocio, num_plazas_NO_socio, usar_bolsa=False):
    connection = get_db_connection()
    if connection is None:
        return False, "Error de conexión a BD", 0
    
    cursor = connection.cursor()
    
    # Calcular coste total siempre
    coste_total = calcular_coste_total(plazaSocio, num_plazas_NO_socio)
    
    # precioApagar siempre guarda el coste total
    precio_apagar = coste_total
    
    # bonoUtilizado se pone según si marcó "usar bolsa" o no
    bono_utilizado = usar_bolsa
    
    check_query = "SELECT * FROM reservaplazas WHERE partidoID = %s AND socioID = %s"
    cursor.execute(check_query, (partidoID, socioID))
    existe = cursor.fetchone()
    
    if existe:
        update_query = """
            UPDATE reservaplazas 
            SET plazaSocio = %s, num_plazas_NO_socio = %s, bonoUtilizado = %s, precioApagar = %s
            WHERE partidoID = %s AND socioID = %s
        """
        cursor.execute(update_query, (plazaSocio, num_plazas_NO_socio, bono_utilizado, precio_apagar, partidoID, socioID))
        mensaje = "Reserva actualizada correctamente"
    else:
        insert_query = """
            INSERT INTO reservaplazas (partidoID, socioID, plazaSocio, num_plazas_NO_socio, bonoUtilizado, precioApagar)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (partidoID, socioID, plazaSocio, num_plazas_NO_socio, bono_utilizado, precio_apagar))
        mensaje = "Reserva creada correctamente"
    
    connection.commit()
    cursor.close()
    connection.close()
    
    return True, mensaje, coste_total, bono_utilizado

# =============================================
# FUNCIÓN INTERNA: Obtener detalles de una reserva (reutilizable)
# =============================================
def _obtener_detalles_reserva(socio_id, partido_id):
    connection = get_db_connection()
    if connection is None:
        return None
    
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT 
            r.socioID,
            r.partidoID,
            r.plazaSocio,
            r.num_plazas_NO_socio,
            r.bonoUtilizado,
            r.precioApagar,
            p.nombreEquipoVisitante,
            p.temporada,
            p.tipoPartido,
            DATE_FORMAT(p.fecha, '%d-%m-%Y') as fecha,
            TIME_FORMAT(p.hora, '%H:%i') as hora,
            s.nombre,
            s.apellidos,
            s.tlf,
            s.bolsa
        FROM reservaplazas r
        JOIN partido p ON r.partidoID = p.partidoID
        JOIN socio s ON r.socioID = s.socioID
        WHERE r.socioID = %s AND r.partidoID = %s
    """
    cursor.execute(query, (socio_id, partido_id))
    reserva = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    return reserva



# ---------------------------------------------------- ENDPOINTS --------------------------------------------------

# =============================================
# API ENDPOINT: Verificar socio por teléfono
# =============================================
@app.route('/api/verificar_socio', methods=['POST'])
def api_verificar_socio():
    data = request.get_json()
    telefono = data.get('telefono', '')
    
    if not telefono:
        return jsonify({'success': False, 'mensaje': 'Teléfono requerido'}), 400
    
    socio = get_socio_by_tlf(telefono)
    if socio:
        return jsonify({
            'success': True, 
            'socio_id': socio['socioID'],
            'nombre': socio['nombre'],
            'apellidos': socio['apellidos'],
            'bolsa': socio['bolsa']
        })
    else:
        return jsonify({'success': False, 'mensaje': 'Número no registrado'}), 404


# =============================================
# API ENDPOINT: Obtener partidos disponibles
# =============================================
@app.route('/api/partidos_disponibles', methods=['GET'])
def api_partidos_disponibles():
    connection = get_db_connection()
    if connection is None:
        return jsonify({'success': False, 'mensaje': 'Error de conexión'}), 500
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT partidoID, nombreEquipoVisitante, fecha, hora, temporada, tipoPartido
        FROM partido
        WHERE disponible = TRUE
        ORDER BY fecha
    """)
    partidos = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    for partido in partidos:
        if partido['fecha']:
            if hasattr(partido['fecha'], 'strftime'):
                partido['fecha'] = partido['fecha'].strftime('%Y-%m-%d')
            else:
                partido['fecha'] = str(partido['fecha'])
        if partido['hora']:
            if hasattr(partido['hora'], 'strftime'):
                partido['hora'] = partido['hora'].strftime('%H:%M:%S')
            else:
                partido['hora'] = str(partido['hora'])
    
    return jsonify({'success': True, 'partidos': partidos})


# =============================================
# API ENDPOINT: Verificar si existe reserva
# =============================================
@app.route('/api/reserva_existente', methods=['POST'])
def api_reserva_existente():
    data = request.get_json()
    socio_id = data.get('socio_id')
    partido_id = data.get('partido_id')
    
    if not socio_id or not partido_id:
        return jsonify({'success': False, 'existe': False, 'mensaje': 'Faltan datos'}), 400
    
    connection = get_db_connection()
    if connection is None:
        return jsonify({'success': False, 'existe': False, 'mensaje': 'Error de conexión'}), 500
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT plazaSocio, num_plazas_NO_socio, bonoUtilizado, precioApagar
        FROM reservaplazas
        WHERE socioID = %s AND partidoID = %s
    """, (socio_id, partido_id))
    reserva = cursor.fetchone()
    
    cursor2 = connection.cursor(dictionary=True)
    cursor2.execute("SELECT bolsa FROM socio WHERE socioID = %s", (socio_id,))
    saldo = cursor2.fetchone()
    bolsa_actual = saldo['bolsa'] if saldo else 0
    cursor2.close()
    
    cursor.close()
    connection.close()
    
    if reserva:
        return jsonify({
            'success': True,
            'existe': True,
            'plaza_socio': reserva['plazaSocio'],
            'num_invitados': reserva['num_plazas_NO_socio'],
            'bono_utilizado': reserva['bonoUtilizado'],
            'precio_apagar': reserva['precioApagar'] if reserva['precioApagar'] is not None else 0.00,
            'bolsa_actual': bolsa_actual
        })
    else:
        return jsonify({
            'success': True,
            'existe': False,
            'bolsa_actual': bolsa_actual
        })


# =============================================
# API ENDPOINT: Crear o modificar reserva (único endpoint)
# =============================================
@app.route('/api/crear_reserva', methods=['POST'])
def api_crear_reserva():
    data = request.get_json()
    telefono = data.get('telefono')
    partido_id = data.get('partido_id')
    plaza_socio = data.get('plaza_socio', False)
    num_plazas_NO_socio = data.get('num_plazas_NO_socio', 0)
    usar_bolsa = data.get('usar_bolsa', False)
    
    if not telefono or not partido_id:
        return jsonify({'success': False, 'mensaje': 'Faltan datos (teléfono o partido)'}), 400
    
    socio = get_socio_by_tlf(telefono)
    if not socio:
        return jsonify({'success': False, 'mensaje': 'Número no registrado'}), 404
    
    socio_id = socio['socioID']
    exito, mensaje, coste, bono_utilizado = insertar_reserva(partido_id, socio_id, plaza_socio, num_plazas_NO_socio, usar_bolsa)
    
    if not exito:
        return jsonify({'success': False, 'mensaje': mensaje}), 500
    
    # Obtener los detalles completos usando la función interna
    detalles = _obtener_detalles_reserva(socio_id, partido_id)
    
    if not detalles:
        return jsonify({'success': True, 'mensaje': f'✅ {mensaje}'})
    
    # Construir mensaje detallado
    asiste_texto = "✅ Sí" if detalles['plazaSocio'] else "❌ No"
    bono_texto = "✅ Sí" if detalles['bonoUtilizado'] else "❌ No"
    
    mensaje_detallado = f"""
✅ {mensaje}

📋 DETALLES DE LA RESERVA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚽ Partido: {detalles['nombreEquipoVisitante']}
📅 Fecha: {detalles['fecha']}
🕐 Hora: {detalles['hora']}
🏷️ Temporada: {detalles['temporada']}
📌 Tipo: {detalles['tipoPartido']}

👤 Socio: {detalles['nombre']} {detalles['apellidos']}
📞 Teléfono: {detalles['tlf']}
🎫 Asiste al partido: {asiste_texto}
👥 Número de no socios: {detalles['num_plazas_NO_socio']}
💰 Bono utilizado: {bono_texto}
💶 Precio a pagar (informativo): {detalles['precioApagar']}€
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    return jsonify({'success': True, 'mensaje': mensaje_detallado})


# =============================================
# API ENDPOINT: Eliminar reserva
# =============================================
@app.route('/api/eliminar_reserva', methods=['POST'])
def api_eliminar_reserva():
    data = request.get_json()
    socio_id = data.get('socio_id')
    partido_id = data.get('partido_id')
    
    if not socio_id or not partido_id:
        return jsonify({'success': False, 'mensaje': 'Faltan datos'}), 400
    
    connection = get_db_connection()
    if connection is None:
        return jsonify({'success': False, 'mensaje': 'Error de conexión'}), 500
    
    cursor = connection.cursor()
    
    cursor.execute("DELETE FROM reservaplazas WHERE socioID = %s AND partidoID = %s", (socio_id, partido_id))
    connection.commit()
    
    cursor.close()
    connection.close()
    
    return jsonify({'success': True, 'mensaje': '✅ Reserva cancelada correctamente'})


# =============================================
# API ENDPOINT: Obtener información de una reserva por socio y partido
# =============================================
@app.route('/api/reserva/<int:socio_id>/<int:partido_id>', methods=['GET'])
def api_obtener_reserva(socio_id, partido_id):
    detalles = _obtener_detalles_reserva(socio_id, partido_id)
    
    if not detalles:
        return jsonify({
            'success': False, 
            'mensaje': f'No se encontró reserva para socio {socio_id} y partido {partido_id}'
        }), 404
    
    resultado = {
        'success': True,
        'reserva': {
            'partido': {
                'id': detalles['partidoID'],
                'equipo_visitante': detalles['nombreEquipoVisitante'],
                'temporada': detalles['temporada'],
                'tipo': detalles['tipoPartido'],
                'fecha': detalles['fecha'],
                'hora': detalles['hora']
            },
            'socio': {
                'id': detalles['socioID'],
                'nombre': detalles['nombre'],
                'apellidos': detalles['apellidos'],
                'telefono': detalles['tlf'],
                'bolsa': detalles['bolsa']
            },
            'plaza_socio': bool(detalles['plazaSocio']),
            'num_plazas_no_socio': detalles['num_plazas_NO_socio'],
            'bono_utilizado': bool(detalles['bonoUtilizado']),
            'precio_apagar': float(detalles['precioApagar']) if detalles['precioApagar'] is not None else 0.00
        }
    }
    
    return jsonify(resultado), 200


# =============================================
# INICIAR SERVIDOR
# =============================================
if __name__ == '__main__':
    print("🚀 Backend de reservas iniciado en http://localhost:5000")
    print("📞 Identificación de socios por número de teléfono")
    print("💰 La bolsa es meramente informativa: no se descuenta ni se actualiza")
    app.run(debug=True, host='0.0.0.0', port=5000)