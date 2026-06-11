@app.route('/api/crear_reserva', methods=['POST'])
def api_crear_reserva():
    data = request.get_json()
    telefono = data.get('telefono')
    partido_id = data.get('partido_id')
    plaza_socio = data.get('plaza_socio', False)
    num_plazas_NO_socio = data.get('num_plazas_NO_socio', 0)
    usar_bolsa = data.get('usar_bolsa', False)
    socio_id = data.get('socio_id')  # Nuevo: para modificaciones del admin

    if not partido_id:
        return jsonify({'success': False, 'mensaje': 'Faltan datos (partido)'}), 400

    # Si viene socio_id, lo usamos directamente (modo admin)
    if socio_id:
        exito, mensaje, coste, bono_utilizado = insertar_reserva(partido_id, socio_id, plaza_socio, num_plazas_NO_socio, usar_bolsa)
        if not exito:
            return jsonify({'success': False, 'mensaje': mensaje}), 500
        return jsonify({'success': True, 'mensaje': '✅ Reserva modificada correctamente'})

    # Si no, usamos el teléfono (modo normal)
    if not telefono:
        return jsonify({'success': False, 'mensaje': 'Faltan datos (teléfono)'}), 400

    socio = get_socio_by_tlf(telefono)
    if not socio:
        return jsonify({'success': False, 'mensaje': 'Número no registrado'}), 404

    socio_id = socio['socioID']
    exito, mensaje, coste, bono_utilizado = insertar_reserva(partido_id, socio_id, plaza_socio, num_plazas_NO_socio, usar_bolsa)

    if not exito:
        return jsonify({'success': False, 'mensaje': mensaje}), 500

    detalles = _obtener_detalles_reserva(socio_id, partido_id)

    if not detalles:
        return jsonify({'success': True, 'mensaje': f'✅ {mensaje}\n\n🔄 Puedes hacer una nueva reserva. Por favor, ingresa tu número de teléfono:'})

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
💶 Precio a pagar (Se descontará del bono, si procede): {detalles['precioApagar']}€
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 Puedes hacer una nueva reserva. Por favor, ingresa tu número de teléfono:
"""

    return jsonify({'success': True, 'mensaje': mensaje_detallado})