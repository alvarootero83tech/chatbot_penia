import requests
import re
import time

TELEGRAM_TOKEN = "TU_TOKEN_AQUI"
BACKEND_URL = "http://localhost:5000/api"

# Almacenamiento en memoria (en producción usar BD)
usuarios_telefono = {}

def enviar_mensaje(chat_id, texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': texto,
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

def validar_telefono(telefono):
    """Valida formato de teléfono internacional"""
    patron = r'^\+[0-9]{10,15}$'
    return re.match(patron, telefono) is not None

def procesar_mensaje(chat_id, texto_usuario):
    # Verificar si el usuario ya tiene teléfono registrado
    if chat_id not in usuarios_telefono:
        # Si el texto parece un número de teléfono válido, lo guardamos
        if validar_telefono(texto_usuario.strip()):
            telefono = texto_usuario.strip()
            usuarios_telefono[chat_id] = telefono
            enviar_mensaje(chat_id, f"✅ Teléfono {telefono} registrado correctamente.\n\nAhora puedes hacer reservas. Por ejemplo:\n'Reservo para el Real Madrid, voy yo y traigo 2 invitados'")
            
            # Opcional: verificar si el teléfono existe en la BD
            url = f"{BACKEND_URL}/mis_reservas"
            try:
                response = requests.post(url, json={'telefono': telefono}, timeout=5)
                data = response.json()
                if not data.get('success') and 'no registrado' in data.get('message', ''):
                    enviar_mensaje(chat_id, f"⚠️ Atención: El número {telefono} no está registrado en la base de datos de la peña. Contacta con un administrador para que te den de alta antes de hacer reservas.")
            except:
                pass
            return
        else:
            enviar_mensaje(chat_id, "📞 Por favor, envía tu número de teléfono en formato internacional.\n\nEjemplo: +34123456789\n\n(El teléfono debe estar registrado en la peña)")
            return
    
    # Si ya tiene teléfono, procesamos la reserva
    telefono = usuarios_telefono[chat_id]
    
    url = f"{BACKEND_URL}/reservar"
    payload = {
        'texto': texto_usuario,
        'telefono': telefono
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        mensaje = data.get('message', 'Respuesta sin mensaje')
        
        # Si el error es que el teléfono no está registrado, permitimos reintentar
        if 'no registrado' in mensaje.lower():
            # Limpiamos el teléfono guardado para que lo pida de nuevo
            del usuarios_telefono[chat_id]
            enviar_mensaje(chat_id, f"{mensaje}\n\nPor favor, vuelve a enviar tu número de teléfono para verificar.")
        else:
            enviar_mensaje(chat_id, mensaje)
    except Exception as e:
        enviar_mensaje(chat_id, f"⚠️ Error del servidor: {str(e)}")

def obtener_actualizaciones(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {'timeout': 30, 'offset': offset}
    try:
        response = requests.get(url, params=params, timeout=35)
        return response.json().get('result', [])
    except:
        return []

def main():
    print("🤖 Bot de Telegram iniciado...")
    print("📞 Identificación de socios por número de teléfono (obligatorio)")
    ultimo_id = 0
    
    while True:
        updates = obtener_actualizaciones(ultimo_id + 1 if ultimo_id else None)
        
        for update in updates:
            ultimo_id = update.get('update_id')
            
            message = update.get('message')
            if not message:
                continue
            
            chat_id = message['chat']['id']
            texto = message.get('text', '')
            
            if texto.lower() == '/start':
                enviar_mensaje(chat_id, "⚽ ¡Bienvenido al bot de reservas de la peña!\n\nPara empezar, envíame tu número de teléfono en formato internacional (el que tienes registrado en la peña).\n\nEjemplo: +34123456789")
                continue
            
            if texto.lower() == '/mis_reservas':
                if chat_id in usuarios_telefono:
                    url = f"{BACKEND_URL}/mis_reservas"
                    try:
                        response = requests.post(url, json={'telefono': usuarios_telefono[chat_id]})
                        data = response.json()
                        enviar_mensaje(chat_id, data.get('message', 'No se pudieron obtener tus reservas'))
                    except Exception as e:
                        enviar_mensaje(chat_id, f"Error: {str(e)}")
                else:
                    enviar_mensaje(chat_id, "Primero necesito tu número de teléfono. Envíamelo con el formato +34123456789")
                continue
            
            procesar_mensaje(chat_id, texto)
        
        time.sleep(1)

if __name__ == '__main__':
    main()