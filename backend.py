from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
import re
import os

app = Flask(__name__)

# =============================================
# CONEXIÓN A LA BASE DE DATOS
# =============================================
import os
import mysql.connector
from mysql.connector import Error

# =============================================
# CONEXIÓN A LA BASE DE DATOS
# =============================================
def get_db_connection():
    try:
        # Leer las variables de entorno (los valores que configuraste en Render)
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '3306')
        db_name = os.environ.get('DB_NAME', 'mhdp')
        db_user = os.environ.get('DB_USER', 'root')
        db_password = os.environ.get('DB_PASSWORD', '')
        
        # Para depuración (después puedes borrar estos prints)
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
    query = "SELECT socioID, nombre, apellidos, bolsa FROM Socio WHERE tlf = %s"
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
        FROM Partido 
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
# FUNCIÓN: Insertar o actualizar reserva
# =============================================
def insertar_reserva(partidoID, socioID, plazaSocio, num_plazas_NO_socio, bonoUtilizado=False):
    connection = get_db_connection()
    if connection is None:
        return False, "Error de conexión a BD"
    
    cursor = connection.cursor()
    
    check_query = "SELECT * FROM ReservaPlazas WHERE partidoID = %s AND socioID = %s"
    cursor.execute(check_query, (partidoID, socioID))
    existe = cursor.fetchone()
    
    if existe:
        update_query = """
            UPDATE ReservaPlazas 
            SET plazaSocio = %s, num_plazas_NO_socio = %s, bonoUtilizado = %s
            WHERE partidoID = %s AND socioID = %s
        """
        cursor.execute(update_query, (plazaSocio, num_plazas_NO_socio, bonoUtilizado, partidoID, socioID))
        mensaje = "Reserva actualizada correctamente"
    else:
        insert_query = """
            INSERT INTO ReservaPlazas (partidoID, socioID, plazaSocio, num_plazas_NO_socio, bonoUtilizado)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (partidoID, socioID, plazaSocio, num_plazas_NO_socio, bonoUtilizado))
        mensaje = "Reserva creada correctamente"
    
    connection.commit()
    cursor.close()
    connection.close()
    
    return True, mensaje

# =============================================
# FUNCIÓN: Obtener precios actuales
# =============================================
def get_precios():
    connection = get_db_connection()
    if connection is None:
        return None, None
    
    cursor = connection.cursor()
    cursor.execute("SELECT precioSocio, precioNoSocio FROM Auxiliar WHERE id = 1")
    result = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    return (result[0], result[1]) if result else (None, None)


# ---------------------------------------------------- END POINTS DE APIs ------------------------------------------------------------------
# =============================================
# API ENDPOINT: Verificar socio por teléfono
# =============================================
@app.route('/api/verificar_socio', methods=['POST'])
def api_verificar_socio():
    data = request.get_json()
    telefono = data.get('telefono', '')
    
    if not telefono:
        return jsonify({'success': False, 'message': 'Teléfono requerido'}), 400
    
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
        return jsonify({'success': False, 'message': 'Número no registrado'}), 404

# =============================================
# API ENDPOINT: Obtener partidos disponibles
# =============================================
@app.route('/api/partidos_disponibles', methods=['GET'])
def api_partidos_disponibles():
    connection = get_db_connection()
    if connection is None:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT partidoID, nombreEquipoVisitante, fecha, hora, temporada, tipoPartido
        FROM Partido
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
        return jsonify({'success': False, 'existe': False, 'message': 'Faltan datos'}), 400
    
    connection = get_db_connection()
    if connection is None:
        return jsonify({'success': False, 'existe': False}), 500
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT plazaSocio, num_plazas_NO_socio, bonoUtilizado
        FROM ReservaPlazas
        WHERE socioID = %s AND partidoID = %s
    """, (socio_id, partido_id))
    reserva = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    if reserva:
        return jsonify({
            'success': True,
            'existe': True,
            'plaza_socio': reserva['plazaSocio'],
            'num_invitados': reserva['num_plazas_NO_socio'],
            'bono_utilizado': reserva['bonoUtilizado']
        })
    else:
        return jsonify({'success': True, 'existe': False})

# =============================================
# API ENDPOINT: Crear nueva reserva
# =============================================
@app.route('/api/crear_reserva', methods=['POST'])
def api_crear_reserva():
    data = request.get_json()
    socio_id = data.get('socio_id')
    partido_id = data.get('partido_id')
    plaza_socio = data.get('plaza_socio', False)
    num_plazas_NO_socio = data.get('num_plazas_NO_socio', 0)
    
    if not socio_id or not partido_id:
        return jsonify({'success': False, 'message': 'Faltan datos'}), 400
    
    exito, mensaje = insertar_reserva(partido_id, socio_id, plaza_socio, num_plazas_NO_socio, False)
    
    if exito:
        return jsonify({'success': True, 'message': f'✅ {mensaje}'})
    else:
        return jsonify({'success': False, 'message': mensaje}), 500

# =============================================
# API ENDPOINT: Modificar reserva existente
# =============================================
@app.route('/api/modificar_reserva', methods=['POST'])
def api_modificar_reserva():
    data = request.get_json()
    socio_id = data.get('socio_id')
    partido_id = data.get('partido_id')
    plaza_socio = data.get('plaza_socio', False)
    num_plazas_NO_socio = data.get('num_plazas_NO_socio', 0)
    
    if not socio_id or not partido_id:
        return jsonify({'success': False, 'message': 'Faltan datos'}), 400
    
    exito, mensaje = insertar_reserva(partido_id, socio_id, plaza_socio, num_plazas_NO_socio, False)
    
    if exito:
        return jsonify({'success': True, 'message': f'✅ {mensaje}'})
    else:
        return jsonify({'success': False, 'message': mensaje}), 500

# =============================================
# API ENDPOINT: Eliminar reserva
# =============================================
@app.route('/api/eliminar_reserva', methods=['POST'])
def api_eliminar_reserva():
    data = request.get_json()
    socio_id = data.get('socio_id')
    partido_id = data.get('partido_id')
    bono_utilizado = data.get('bono_utilizado', False)
    
    if not socio_id or not partido_id:
        return jsonify({'success': False, 'message': 'Faltan datos'}), 400
    
    connection = get_db_connection()
    if connection is None:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    cursor = connection.cursor()
    
    if bono_utilizado:
        cursor.execute("SELECT precioSocio FROM Auxiliar WHERE id = 1")
        result = cursor.fetchone()
        precio_socio = result[0] if result else 3
        
        cursor.execute("SELECT plazaSocio, num_plazas_NO_socio FROM ReservaPlazas WHERE socioID = %s AND partidoID = %s", 
                      (socio_id, partido_id))
        reserva = cursor.fetchone()
        
        if reserva:
            coste = 0
            if reserva[0]:
                coste += precio_socio
            coste += reserva[1] * 10
            
            cursor.execute("UPDATE Socio SET bolsa = bolsa - %s WHERE socioID = %s", (coste, socio_id))
    
    cursor.execute("DELETE FROM ReservaPlazas WHERE socioID = %s AND partidoID = %s", (socio_id, partido_id))
    connection.commit()
    
    cursor.close()
    connection.close()
    
    return jsonify({'success': True, 'message': '✅ Reserva cancelada correctamente'})

# =============================================
# API ENDPOINT: Obtener información de una reserva por socio y partido
# =============================================

@app.route('/api/reserva/<int:socio_id>/<int:partido_id>', methods=['GET'])
def api_obtener_reserva(socio_id, partido_id):
    connection = get_db_connection()
    if connection is None:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    cursor = connection.cursor(dictionary=True)
    
    # Consulta simplificada SIN fecha y SIN hora
    query = """
        SELECT 
            r.socioID,
            r.partidoID,
            r.plazaSocio,
            r.num_plazas_NO_socio,
            r.bonoUtilizado,
            p.nombreEquipoVisitante,
            p.temporada,
            p.tipoPartido,
            DATE_FORMAT(p.fecha, '%d-%m-%Y') as fecha,
            TIME_FORMAT(p.hora, '%H:%i') as hora,
            s.nombre,
            s.apellidos,
            s.tlf
        FROM ReservaPlazas r
        JOIN Partido p ON r.partidoID = p.partidoID
        JOIN Socio s ON r.socioID = s.socioID
        WHERE r.socioID = %s AND r.partidoID = %s
    """
    cursor.execute(query, (socio_id, partido_id))
    reserva = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    if not reserva:
        return jsonify({
            'success': False, 
            'message': f'No se encontró reserva para socio {socio_id} y partido {partido_id}'
        }), 404
    
    resultado = {
        'success': True,
        'reserva': {
            'partido': {
                'id': reserva['partidoID'],
                'equipo_visitante': reserva['nombreEquipoVisitante'],
                'temporada':reserva['temporada'],
                'tipo':reserva['tipoPartido'],
                'fecha':reserva['fecha'],
                'hora': reserva['hora']
            },
            'socio': {
                'id': reserva['socioID'],
                'nombre': reserva['nombre'],
                'apellidos': reserva['apellidos'],
                'telefono': reserva['tlf']
            },
            'plaza_socio': bool(reserva['plazaSocio']),
            'num_plazas_no_socio': reserva['num_plazas_NO_socio'],
            'bono_utilizado': bool(reserva['bonoUtilizado'])
        }
    }
    
    return jsonify(resultado), 200

# =============================================
# INICIAR SERVIDOR
# =============================================
if __name__ == '__main__':
    print("🚀 Backend de reservas iniciado en http://localhost:5000")
    print("📞 Identificación de socios por número de teléfono")
    app.run(debug=True, host='0.0.0.0', port=5000)