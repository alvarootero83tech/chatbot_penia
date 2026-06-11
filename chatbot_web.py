from flask import Flask, render_template_string, request, jsonify
import requests
import re
import os

app = Flask(__name__)

sesiones = {}

BACKEND_URL = os.environ.get('BACKEND_URL', "https://chatbot-penia.onrender.com/api")

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Chatbot de Reservas - Peña</title>
    <meta charset="UTF-8">
    <style>
        .formulario-reserva {
            margin-top: 15px;
            padding: 15px;
            background-color: #fffef9;
            border: 1px solid #e8e4d8;
            border-radius: 12px;
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }
        .checkbox-group label {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            font-size: 14px;
        }
        .checkbox-group input[type="checkbox"] {
            width: 18px;
            height: 18px;
            margin: 0;
            cursor: pointer;
        }
        .input-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 15px;
        }
        .input-group label {
            font-size: 13px;
            color: #444;
            margin-bottom: 5px;
        }
        .input-group input {
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            width: 120px;
        }
        .input-group input[type="number"] {
            width: 100px;
        }
        .input-group button {
            padding: 10px 20px;
            background-color: #4a9fd4;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            width: auto;
            align-self: flex-start;
        }
        .input-group button:hover {
            background-color: #2a7db5;
        }
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .chat-container {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .chat-messages {
            height: 600px;
            overflow-y: auto;
            padding: 20px;
            background-color: #fdfbf3;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 18px;
            max-width: 70%;
            word-wrap: break-word;
        }
        .user-message {
            background-color: #4a9fd4;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        .bot-message {
            background-color: #e8e4d8;
            color: #333;
            margin-right: auto;
            white-space: pre-line;
        }
        .option-button {
            background-color: #4a9fd4;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 5px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
        }
        .option-button:hover {
            background-color: #2a7db5;
        }
        .option-button-admin {
            background-color: #e67e22;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 5px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
        }
        .option-button-admin:hover {
            background-color: #d35400;
        }
        .options-container {
            display: flex;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        .chat-input {
            display: flex;
            padding: 15px;
            background-color: white;
            border-top: 1px solid #e8e4d8;
        }
        .chat-input input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 20px;
            font-size: 14px;
        }
        .chat-input button {
            margin-left: 10px;
            padding: 10px 20px;
            background-color: #4a9fd4;
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .chat-input button:hover:not(:disabled) {
            background-color: #2a7db5;
        }
        .chat-input button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        h1 {
            text-align: center;
            color: #333;
        }
    </style>
</head>
<body>
    <h1>🤖 Chatbot de Reservas</h1>
    <iframe src="https://chatbot-penia.onrender.com" width="0" height="0" style="border:0; display:none;"></iframe>
    <div class="chat-container">
        <div class="chat-messages" id="chatMessages">
            <div class="message bot-message">
                ¡Bienvenido al sistema de reservas de la peña! ⚽<br><br>
                Para empezar, por favor ingresa tu número de teléfono registrado:<br>
                Ejemplo: +34123456789
            </div>
        </div>
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Escribe tu mensaje aquí...">
            <button id="btnEnviar" disabled>Enviar</button>
        </div>
    </div>

  <script>
    let sessionId = null;
    let partidoSeleccionado = null;
    let telefonoGlobal = sessionStorage.getItem('telefonoGlobal') || null;
    const BACKEND_URL = "{{ backend_url }}";
    
    function generarSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    function habilitarBotonEnviar(habilitado) {
        const btn = document.getElementById('btnEnviar');
        if (btn) {
            btn.disabled = !habilitado;
        }
    }
    
    function eliminarFormularioAnterior() {
        const formularioExistente = document.getElementById('formulario_reserva');
        if (formularioExistente) formularioExistente.remove();
        const formularioModificacion = document.getElementById('formulario_modificacion');
        if (formularioModificacion) formularioModificacion.remove();
    }
    
    function eliminarMensajesBotAnteriores() {
        const chatMessages = document.getElementById('chatMessages');
        const mensajes = chatMessages.querySelectorAll('.bot-message');
        mensajes.forEach(mensaje => {
            if (mensaje.innerHTML.includes('Selecciona el partido') ||
                mensaje.innerHTML.includes('Reserva para:') ||
                mensaje.innerHTML.includes('Modifica los detalles') ||
                mensaje.innerHTML.includes('¿Qué deseas hacer?') ||
                mensaje.innerHTML.includes('Ya tienes una reserva') ||
                mensaje.innerHTML.includes('Bienvenido Administrador') ||
                mensaje.querySelector('.options-container') ||
                mensaje.querySelector('.formulario-reserva')) {
                mensaje.remove();
            }
        });
    }
    
    function eliminarOpcionesPartidos() {
        const opcionesDiv = document.getElementById('opciones_partidos');
        if (opcionesDiv) opcionesDiv.remove();
        const opcionesAdmin = document.getElementById('opciones_admin');
        if (opcionesAdmin) opcionesAdmin.remove();
    }
    
    function limpiarMensajesYFormularios() {
        eliminarMensajesBotAnteriores();
        eliminarFormularioAnterior();
        eliminarOpcionesPartidos();
    }
    
    function obtenerInvitados(idInput) {
        let valor = parseInt(document.getElementById(idInput).value);
        if (isNaN(valor) || valor < 0) {
            valor = 0;
            document.getElementById(idInput).value = 0;
        }
        return valor;
    }
    
    function enviarMensaje() {
        const input = document.getElementById('messageInput');
        const texto = input.value.trim();
        if (!texto) return;
        
        habilitarBotonEnviar(false);
        if (!sessionId) sessionId = generarSessionId();
        
        const chatMessages = document.getElementById('chatMessages');
        const userMsg = document.createElement('div');
        userMsg.className = 'message user-message';
        userMsg.innerHTML = texto;
        chatMessages.appendChild(userMsg);
        input.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ texto: texto, session_id: sessionId })
        })
        .then(response => response.json())
        .then(data => {
            limpiarMensajesYFormularios();
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            
            if (data.tipo === 'opciones') {
                botMsg.innerHTML = data.mensaje;
                const optionsDiv = document.createElement('div');
                optionsDiv.className = 'options-container';
                optionsDiv.id = 'opciones_partidos';
                data.opciones.forEach(op => {
                    const btn = document.createElement('button');
                    btn.textContent = op.texto;
                    btn.className = 'option-button';
                    btn.dataset.partidoId = op.partido_id;
                    btn.dataset.partidoNombre = op.texto;
                    btn.onclick = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        btn.disabled = true;
                        btn.style.opacity = '0.5';
                        btn.style.cursor = 'not-allowed';
                        seleccionarPartido(btn.dataset.partidoId, btn.dataset.partidoNombre);
                    };
                    optionsDiv.appendChild(btn);
                });
                const hr = document.createElement('hr');
                hr.style.margin = '15px 0';
                hr.style.border = 'none';
                hr.style.borderTop = '1px solid #e8e4d8';
                optionsDiv.appendChild(hr);
                const btnBono = document.createElement('button');
                btnBono.textContent = '💰 ¿Quieres consultar si tienes bono?';
                btnBono.className = 'option-button';
                btnBono.style.backgroundColor = '#27ae60';
                btnBono.onclick = (e) => {
                    btnBono.disabled = true;
                    btnBono.style.opacity = '0.5';
                    btnBono.style.cursor = 'not-allowed';
                    consultarBono();
                };
                optionsDiv.appendChild(btnBono);
                botMsg.appendChild(optionsDiv);
                chatMessages.appendChild(botMsg);
                habilitarBotonEnviar(false);
                
                if (data.telefono) {
                    telefonoGlobal = data.telefono;
                    sessionStorage.setItem('telefonoGlobal', data.telefono);
                }
            }
            else if (data.tipo === 'opciones_admin') {
                botMsg.innerHTML = data.mensaje;
                const optionsDiv = document.createElement('div');
                optionsDiv.className = 'options-container';
                optionsDiv.id = 'opciones_admin';
                data.opciones.forEach(op => {
                    const btn = document.createElement('button');
                    btn.textContent = op.texto;
                    btn.className = 'option-button-admin';
                    btn.onclick = (e) => {
                        btn.disabled = true;
                        btn.style.opacity = '0.5';
                        btn.style.cursor = 'not-allowed';
                        enviarRespuestaOpcion(op.valor);
                    };
                    optionsDiv.appendChild(btn);
                });
                botMsg.appendChild(optionsDiv);
                chatMessages.appendChild(botMsg);
                habilitarBotonEnviar(false);
                
                if (data.telefono) {
                    telefonoGlobal = data.telefono;
                    sessionStorage.setItem('telefonoGlobal', data.telefono);
                }
            }
            else if (data.tipo === 'formulario_reserva') {
                botMsg.innerHTML = data.mensaje;
                const formDiv = document.createElement('div');
                formDiv.className = 'formulario-reserva';
                formDiv.id = 'formulario_reserva';
                
                const checkboxDiv = document.createElement('div');
                checkboxDiv.className = 'checkbox-group';
                checkboxDiv.innerHTML = `
                    <label>
                        <input type="checkbox" id="asisteCheckbox">
                        <span>✅ Asisto al partido</span>
                    </label>
                `;
                formDiv.appendChild(checkboxDiv);
                
                if (data.bolsa_actual > 0) {
                    const bolsaDiv = document.createElement('div');
                    bolsaDiv.className = 'checkbox-group';
                    bolsaDiv.innerHTML = `
                        <label>
                            <input type="checkbox" id="usarBolsaCheckbox">
                            <span>💰 Usar saldo de la bolsa (${data.bolsa_actual}€ disponible)</span>
                        </label>
                    `;
                    formDiv.appendChild(bolsaDiv);
                }
                
                const inputDiv = document.createElement('div');
                inputDiv.className = 'input-group';
                inputDiv.innerHTML = `
                    <label>👥 ¿Cuántos no socios asistirán al partido de tu parte?</label>
                    <input type="number" id="invitadosInput" placeholder="Número de invitados" value="0" min="0" step="1">
                    <button id="btnConfirmarReserva">✅ Confirmar reserva</button>
                `;
                formDiv.appendChild(inputDiv);
                botMsg.appendChild(formDiv);
                chatMessages.appendChild(botMsg);
                
                const btn = document.getElementById('btnConfirmarReserva');
                if (btn) {
                    btn.onclick = () => {
                        btn.disabled = true;
                        btn.style.opacity = '0.5';
                        btn.style.cursor = 'not-allowed';
                        const asiste = document.getElementById('asisteCheckbox').checked;
                        const invitados = obtenerInvitados('invitadosInput');
                        const usarBolsa = document.getElementById('usarBolsaCheckbox') ? document.getElementById('usarBolsaCheckbox').checked : false;
                        enviarReserva(data.partido_id, asiste, invitados, usarBolsa);
                    };
                }
                habilitarBotonEnviar(false);
            }
            else {
                botMsg.innerHTML = data.mensaje;
                chatMessages.appendChild(botMsg);
                habilitarBotonEnviar(true);
            }
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(error => {
            console.error(error);
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            botMsg.innerHTML = '⚠️ Error de conexión con el servidor';
            document.getElementById('chatMessages').appendChild(botMsg);
            habilitarBotonEnviar(true);
        });
    }
    
    function mostrarFormularioModificacion(partidoId, asisteActual, invitadosActual, bolsaActual) {
        limpiarMensajesYFormularios();
        if (invitadosActual === null || invitadosActual === undefined) invitadosActual = 0;
        
        const chatMessages = document.getElementById('chatMessages');
        const botMsg = document.createElement('div');
        botMsg.className = 'message bot-message';
        botMsg.innerHTML = "✏️ Modifica los detalles de tu reserva:";
        
        const formDiv = document.createElement('div');
        formDiv.className = 'formulario-reserva';
        formDiv.id = 'formulario_modificacion';
        
        const checkboxDiv = document.createElement('div');
        checkboxDiv.className = 'checkbox-group';
        checkboxDiv.innerHTML = `
            <label>
                <input type="checkbox" id="asisteCheckboxMod" ${asisteActual ? 'checked' : ''}>
                <span>✅ Asisto al partido</span>
            </label>
        `;
        formDiv.appendChild(checkboxDiv);
        
        if (bolsaActual > 0) {
            const bolsaDiv = document.createElement('div');
            bolsaDiv.className = 'checkbox-group';
            bolsaDiv.innerHTML = `
                <label>
                    <input type="checkbox" id="usarBolsaCheckboxMod">
                    <span>💰 Usar saldo de la bolsa (${bolsaActual}€ disponible)</span>
                </label>
            `;
            formDiv.appendChild(bolsaDiv);
        }
        
        const inputDiv = document.createElement('div');
        inputDiv.className = 'input-group';
        inputDiv.innerHTML = `
            <label>👥 ¿Cuántos no socios asistirán al partido de tu parte?</label>
            <input type="number" id="invitadosInputMod" placeholder="Número de invitados" value="${invitadosActual}" min="0" step="1">
            <button id="btnConfirmarModificacion">✏️ Confirmar modificación</button>
        `;
        formDiv.appendChild(inputDiv);
        botMsg.appendChild(formDiv);
        chatMessages.appendChild(botMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        const btn = document.getElementById('btnConfirmarModificacion');
        if (btn) {
            btn.onclick = () => {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
                const asiste = document.getElementById('asisteCheckboxMod').checked;
                const invitados = obtenerInvitados('invitadosInputMod');
                const usarBolsa = document.getElementById('usarBolsaCheckboxMod') ? document.getElementById('usarBolsaCheckboxMod').checked : false;
                enviarModificacion(partidoId, asiste, invitados, usarBolsa);
            };
        }
        habilitarBotonEnviar(false);
    }
    
    function seleccionarPartido(partidoId, partidoNombre) {
        if (partidoSeleccionado === partidoId) return;
        partidoSeleccionado = partidoId;
        
        const opcionesDiv = document.getElementById('opciones_partidos');
        if (opcionesDiv) {
            const botones = opcionesDiv.querySelectorAll('.option-button');
            botones.forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
            });
        }
        
        fetch('/api/opcion', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                opcion: `partido_${partidoId}`,
                session_id: sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            limpiarMensajesYFormularios();
            const chatMessages = document.getElementById('chatMessages');
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            
            if (data.tipo === 'opciones_reserva_existente') {
                botMsg.innerHTML = data.mensaje;
                const optionsDiv = document.createElement('div');
                optionsDiv.className = 'options-container';
                data.opciones.forEach(op => {
                    const btn = document.createElement('button');
                    btn.textContent = op.texto;
                    btn.className = 'option-button';
                    btn.onclick = () => {
                        btn.disabled = true;
                        btn.style.opacity = '0.5';
                        btn.style.cursor = 'not-allowed';
                        if (op.valor === 'cancelar') {
                            enviarConfirmacionEliminar(data.partido_id, data.bono_utilizado);
                        } else if (op.valor === 'modificar') {
                            mostrarFormularioModificacion(data.partido_id, data.asiste_actual, data.invitados_actual, data.bolsa_actual);
                        } else if (op.valor === 'salir') {
                            enviarRespuestaOpcion('menu_principal');
                        }
                    };
                    optionsDiv.appendChild(btn);
                });
                botMsg.appendChild(optionsDiv);
                chatMessages.appendChild(botMsg);
                habilitarBotonEnviar(false);
            }
            else if (data.tipo === 'formulario_modificar') {
                mostrarFormularioModificacion(data.partido_id, data.asiste, data.invitados, data.bolsa_actual);
                return;
            }
            else if (data.tipo === 'formulario_reserva') {
                botMsg.innerHTML = data.mensaje;
                const formDiv = document.createElement('div');
                formDiv.className = 'formulario-reserva';
                formDiv.id = 'formulario_reserva';
                const checkboxDiv = document.createElement('div');
                checkboxDiv.className = 'checkbox-group';
                checkboxDiv.innerHTML = `
                    <label>
                        <input type="checkbox" id="asisteCheckbox">
                        <span>✅ Asisto al partido</span>
                    </label>
                `;
                formDiv.appendChild(checkboxDiv);
                if (data.bolsa_actual > 0) {
                    const bolsaDiv = document.createElement('div');
                    bolsaDiv.className = 'checkbox-group';
                    bolsaDiv.innerHTML = `
                        <label>
                            <input type="checkbox" id="usarBolsaCheckbox">
                            <span>💰 Usar saldo de la bolsa (${data.bolsa_actual}€ disponible)</span>
                        </label>
                    `;
                    formDiv.appendChild(bolsaDiv);
                }
                const inputDiv = document.createElement('div');
                inputDiv.className = 'input-group';
                inputDiv.innerHTML = `
                    <label>👥 ¿Cuántos no socios asistirán al partido de tu parte?</label>
                    <input type="number" id="invitadosInput" placeholder="Número de invitados" value="0" min="0" step="1">
                    <button id="btnConfirmarReserva">✅ Confirmar reserva</button>
                `;
                formDiv.appendChild(inputDiv);
                botMsg.appendChild(formDiv);
                chatMessages.appendChild(botMsg);
                const btn = document.getElementById('btnConfirmarReserva');
                if (btn) {
                    btn.onclick = () => {
                        btn.disabled = true;
                        btn.style.opacity = '0.5';
                        btn.style.cursor = 'not-allowed';
                        const asiste = document.getElementById('asisteCheckbox').checked;
                        const invitados = obtenerInvitados('invitadosInput');
                        const usarBolsa = document.getElementById('usarBolsaCheckbox') ? document.getElementById('usarBolsaCheckbox').checked : false;
                        enviarReserva(data.partido_id, asiste, invitados, usarBolsa);
                    };
                }
                habilitarBotonEnviar(false);
            }
            else {
                botMsg.innerHTML = data.mensaje;
                chatMessages.appendChild(botMsg);
                habilitarBotonEnviar(false);
            }
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });
    }
    
    function enviarRespuestaOpcion(valor) {
        fetch('/api/opcion', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ opcion: valor, session_id: sessionId })
        })
        .then(response => response.json())
        .then(data => {
            limpiarMensajesYFormularios();
            const chatMessages = document.getElementById('chatMessages');
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            if (data.tipo === 'opciones') {
                botMsg.innerHTML = data.mensaje;
                const optionsDiv = document.createElement('div');
                optionsDiv.className = 'options-container';
                optionsDiv.id = 'opciones_partidos';
                data.opciones.forEach(op => {
                    const btn = document.createElement('button');
                    btn.textContent = op.texto;
                    btn.className = 'option-button';
                    btn.dataset.partidoId = op.partido_id;
                    btn.onclick = (e) => {
                        btn.disabled = true;
                        btn.style.opacity = '0.5';
                        btn.style.cursor = 'not-allowed';
                        seleccionarPartido(op.partido_id, op.texto);
                    };
                    optionsDiv.appendChild(btn);
                });
                const hr = document.createElement('hr');
                hr.style.margin = '15px 0';
                hr.style.border = 'none';
                hr.style.borderTop = '1px solid #e8e4d8';
                optionsDiv.appendChild(hr);
                const btnBono = document.createElement('button');
                btnBono.textContent = '💰 ¿Quieres consultar si tienes bono?';
                btnBono.className = 'option-button';
                btnBono.style.backgroundColor = '#27ae60';
                btnBono.onclick = (e) => {
                    btnBono.disabled = true;
                    btnBono.style.opacity = '0.5';
                    btnBono.style.cursor = 'not-allowed';
                    consultarBono();
                };
                optionsDiv.appendChild(btnBono);
                botMsg.appendChild(optionsDiv);
                chatMessages.appendChild(botMsg);
                partidoSeleccionado = null;
                habilitarBotonEnviar(false);
            } else if (data.tipo === 'opciones_admin') {
                botMsg.innerHTML = data.mensaje;
                const optionsDiv = document.createElement('div');
                optionsDiv.className = 'options-container';
                optionsDiv.id = 'opciones_admin';
                data.opciones.forEach(op => {
                    const btn = document.createElement('button');
                    btn.textContent = op.texto;
                    btn.className = 'option-button-admin';
                    btn.onclick = (e) => {
                        btn.disabled = true;
                        btn.style.opacity = '0.5';
                        btn.style.cursor = 'not-allowed';
                        enviarRespuestaOpcion(op.valor);
                    };
                    optionsDiv.appendChild(btn);
                });
                botMsg.appendChild(optionsDiv);
                chatMessages.appendChild(botMsg);
                habilitarBotonEnviar(false);
            } else {
                botMsg.innerHTML = data.mensaje;
                chatMessages.appendChild(botMsg);
                habilitarBotonEnviar(false);
            }
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });
    }
    
    function enviarReserva(partidoId, asiste, invitados, usarBolsa) {
        if (!telefonoGlobal) {
            alert('No hay teléfono registrado. Reinicia el chat.');
            return;
        }
        const chatMessages = document.getElementById('chatMessages');
        const loadingMsg = document.createElement('div');
        loadingMsg.className = 'message bot-message';
        loadingMsg.innerHTML = '⏳ Procesando tu reserva...';
        loadingMsg.id = 'loading_msg';
        chatMessages.appendChild(loadingMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        fetch(`${BACKEND_URL}/crear_reserva`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                telefono: telefonoGlobal,
                partido_id: partidoId,
                plaza_socio: asiste,
                num_plazas_NO_socio: invitados,
                usar_bolsa: usarBolsa
            })
        })
        .then(response => response.json())
        .then(data => {
            const loading = document.getElementById('loading_msg');
            if (loading) loading.remove();
            const formulario = document.getElementById('formulario_reserva');
            if (formulario) formulario.remove();
            const todosMensajes = document.querySelectorAll('.bot-message');
            todosMensajes.forEach(msg => {
                if (msg.innerHTML.includes('Reserva para:') || msg.innerHTML.includes('Indica los detalles')) {
                    msg.remove();
                }
            });
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            botMsg.innerHTML = data.mensaje;
            chatMessages.appendChild(botMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            partidoSeleccionado = null;
            telefonoGlobal = null;
            sessionStorage.removeItem('telefonoGlobal');
            sessionId = null;
            habilitarBotonEnviar(true);
        })
        .catch(error => {
            console.error(error);
            const loading = document.getElementById('loading_msg');
            if (loading) loading.remove();
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            botMsg.innerHTML = '⚠️ Error de conexión con el servidor';
            chatMessages.appendChild(botMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            habilitarBotonEnviar(true);
        });
    }
    
    function enviarModificacion(partidoId, asiste, invitados, usarBolsa) {
        if (!telefonoGlobal) {
            alert('No hay teléfono registrado. Reinicia el chat.');
            return;
        }
        const chatMessages = document.getElementById('chatMessages');
        const loadingMsg = document.createElement('div');
        loadingMsg.className = 'message bot-message';
        loadingMsg.innerHTML = '⏳ Procesando tu modificación...';
        loadingMsg.id = 'loading_msg';
        chatMessages.appendChild(loadingMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        fetch(`${BACKEND_URL}/crear_reserva`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                telefono: telefonoGlobal,
                partido_id: partidoId,
                plaza_socio: asiste,
                num_plazas_NO_socio: invitados,
                usar_bolsa: usarBolsa
            })
        })
        .then(response => response.json())
        .then(data => {
            const loading = document.getElementById('loading_msg');
            if (loading) loading.remove();
            const formulario = document.getElementById('formulario_modificacion');
            if (formulario) formulario.remove();
            const formularioReserva = document.getElementById('formulario_reserva');
            if (formularioReserva) formularioReserva.remove();
            const todosMensajes = document.querySelectorAll('.bot-message');
            todosMensajes.forEach(msg => {
                if (msg.innerHTML.includes('Modifica los detalles') || msg.innerHTML.includes('✏️ Modifica los detalles')) {
                    msg.remove();
                }
            });
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            botMsg.innerHTML = data.mensaje;
            chatMessages.appendChild(botMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            partidoSeleccionado = null;
            telefonoGlobal = null;
            sessionStorage.removeItem('telefonoGlobal');
            sessionId = null;
            habilitarBotonEnviar(true);
        })
        .catch(error => {
            console.error(error);
            const loading = document.getElementById('loading_msg');
            if (loading) loading.remove();
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            botMsg.innerHTML = '⚠️ Error de conexión con el servidor';
            chatMessages.appendChild(botMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            habilitarBotonEnviar(true);
        });
    }
    
    function consultarBono() {
        const chatMessages = document.getElementById('chatMessages');
        const loadingMsg = document.createElement('div');
        loadingMsg.className = 'message bot-message';
        loadingMsg.innerHTML = '⏳ Consultando tu bono...';
        loadingMsg.id = 'loading_msg';
        chatMessages.appendChild(loadingMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        fetch(`${BACKEND_URL}/verificar_socio`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ telefono: telefonoGlobal })
        })
        .then(response => response.json())
        .then(data => {
            const loading = document.getElementById('loading_msg');
            if (loading) loading.remove();
            limpiarMensajesYFormularios();
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            if (data.success) {
                botMsg.innerHTML = `
📋 INFORMACIÓN DE TU BONO:
━━━━━━━━━
👤 Socio: ${data.nombre} ${data.apellidos}
📞 Teléfono: ${telefonoGlobal}
💰 Saldo actual (bolsa): ${data.bolsa}€
━━━━━━━━━
ℹ️ Si quieres consultar algún dato sobre tu bono, ampliarlo o cambiar el teléfono, avisa a tu administrador.
`;
                chatMessages.appendChild(botMsg);
               setTimeout(() => {
                    partidoSeleccionado = null;
                    enviarRespuestaOpcion('menu_principal');
                }, 2000);
            } else {
                botMsg.innerHTML = '❌ ' + data.mensaje;
                chatMessages.appendChild(botMsg);
                habilitarBotonEnviar(true);
            }
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(error => {
            console.error(error);
            const loading = document.getElementById('loading_msg');
            if (loading) loading.remove();
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            botMsg.innerHTML = '⚠️ Error de conexión con el servidor';
            chatMessages.appendChild(botMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            habilitarBotonEnviar(true);
        });
    }
    
    function enviarConfirmacionEliminar(partidoId, bonoUtilizado) {
        if (!telefonoGlobal) {
            alert('No hay teléfono registrado. Reinicia el chat.');
            return;
        }
        const chatMessages = document.getElementById('chatMessages');
        limpiarMensajesYFormularios();
        const loadingMsg = document.createElement('div');
        loadingMsg.className = 'message bot-message';
        loadingMsg.innerHTML = '⏳ Procesando cancelación...';
        loadingMsg.id = 'loading_msg';
        chatMessages.appendChild(loadingMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        fetch(`${BACKEND_URL}/eliminar_reserva`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                telefono: telefonoGlobal,
                partido_id: partidoId,
                bono_utilizado: bonoUtilizado
            })
        })
        .then(response => response.json())
        .then(data => {
            const loading = document.getElementById('loading_msg');
            if (loading) loading.remove();
            
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            
            if (data.mensaje) {
                botMsg.innerHTML = data.mensaje + ' 🔄 Puedes hacer una nueva reserva. Por favor, ingresa tu número de teléfono:';
            } else {
                botMsg.innerHTML = '✅ Reserva cancelada correctamente. 🔄 Puedes hacer una nueva reserva. Por favor, ingresa tu número de teléfono:';
            }
            
            chatMessages.appendChild(botMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            partidoSeleccionado = null;
            telefonoGlobal = null;
            sessionStorage.removeItem('telefonoGlobal');
            sessionId = null;
            habilitarBotonEnviar(true);
        })
        .catch(error => {
            console.error(error);
            const loading = document.getElementById('loading_msg');
            if (loading) loading.remove();
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            botMsg.innerHTML = '⚠️ Error de conexión con el servidor';
            chatMessages.appendChild(botMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            habilitarBotonEnviar(true);
        });
    }
    
    document.addEventListener('DOMContentLoaded', function() {
        const input = document.getElementById('messageInput');
        const boton = document.getElementById('btnEnviar');
        habilitarBotonEnviar(true);
        if (input) {
            input.addEventListener('keypress', function(event) {
                if (event.keyCode === 13 || event.key === 'Enter') {
                    event.preventDefault();
                    if (!boton.disabled) enviarMensaje();
                }
            });
        }
        if (boton) {
            boton.addEventListener('click', function() {
                if (!boton.disabled) enviarMensaje();
            });
        }
    });
</script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML, backend_url=BACKEND_URL)


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    texto = data.get('texto', '')
    session_id = data.get('session_id', '')

    if session_id not in sesiones:
        sesiones[session_id] = {'paso': 'esperando_telefono'}

    sesion = sesiones[session_id]

    if sesion['paso'] == 'esperando_telefono':
        if re.match(r'^\+?[0-9]{9,15}$', texto.strip()):
            telefono = texto.strip()
            resultado = requests.post(
                f"{BACKEND_URL}/verificar_socio",
                json={'telefono': telefono},
                timeout=180
            ).json()

            if resultado.get('success'):
                sesion['socio_id'] = resultado['socio_id']
                sesion['socio_nombre'] = resultado['nombre']
                sesion['telefono'] = telefono

                # Verificar si es administrador
                if resultado.get('administrador', False):
                    sesion['paso'] = 'menu_admin'
                    sesion['es_admin'] = True
                    return jsonify({
                        'tipo': 'opciones_admin',
                        'mensaje': f"✅ ¡Bienvenido Administrador {resultado['nombre']}! 🔧\n\nSelecciona una opción:",
                        'telefono': telefono,
                        'opciones': [
                            {'texto': '📋 Gestión de partidos', 'valor': 'admin_partidos'},
                            {'texto': '🎫 Gestión de reservas', 'valor': 'admin_reservas'},
                            {'texto': '👥 Gestión de socios', 'valor': 'admin_socios'},
                            {'texto': '🔙 Salir (modo socio)', 'valor': 'admin_salir'}
                        ]
                    })

                sesion['paso'] = 'telefono_validado'
                sesion['es_admin'] = False

                partidos = requests.get(
                    f"{BACKEND_URL}/partidos_disponibles",
                    timeout=180
                ).json()

                if partidos.get('success') and partidos.get('partidos'):
                    opciones = []
                    for p in partidos['partidos']:
                        opciones.append({
                            'texto': f"⚽ {p['nombreEquipoVisitante']} - {p['fecha']}",
                            'valor': f"partido_{p['partidoID']}",
                            'partido_id': p['partidoID']
                        })
                    return jsonify({
                        'tipo': 'opciones',
                        'mensaje': f"✅ Teléfono validado. ¡Bienvenido {resultado['nombre']}! 📞\n\nSelecciona el partido para el que quieres reservar:",
                        'opciones': opciones,
                        'telefono': telefono
                    })
                else:
                    return jsonify({
                        'tipo': 'mensaje',
                        'mensaje': '⚠️ No hay partidos disponibles para reservar en este momento.'
                    })
            else:
                return jsonify({
                    'tipo': 'mensaje',
                    'mensaje': f'❌ {resultado.get("mensaje", "Número no registrado")}\n\nPor favor, intenta con otro número o contacta al administrador.'
                })
        else:
            return jsonify({
                'tipo': 'mensaje',
                'mensaje': '📞 Por favor, ingresa un número de teléfono válido con formato internacional.\nEjemplo: +34123456789'
            })

    return jsonify({'tipo': 'mensaje', 'mensaje': 'Comando no reconocido.'})


@app.route('/api/opcion', methods=['POST'])
def opcion():
    data = request.get_json()
    opcion = data.get('opcion', '')
    session_id = data.get('session_id', '')

    if session_id not in sesiones:
        return jsonify({'tipo': 'mensaje', 'mensaje': 'Sesión no válida. Por favor reinicia el chat.'})

    sesion = sesiones[session_id]

    # --- OPCIONES DE ADMINISTRADOR ---
    if opcion.startswith('admin_'):
        if sesion.get('es_admin') != True:
            return jsonify({'tipo': 'mensaje', 'mensaje': 'No tienes permisos de administrador.'})

        if opcion == 'admin_partidos':
            sesion['paso'] = 'admin_partidos'
            return jsonify({
                'tipo': 'opciones_admin',
                'mensaje': '📋 GESTIÓN DE PARTIDOS\n\nSelecciona una opción:',
                'opciones': [
                    {'texto': '📋 Ver últimos 4 partidos', 'valor': 'admin_ver_partidos'},
                    {'texto': '➕ Crear partido', 'valor': 'admin_crear_partido'},
                    {'texto': '✏️ Editar partido', 'valor': 'admin_editar_partido'},
                    {'texto': '🔙 Volver al menú', 'valor': 'admin_menu'}
                ]
            })

        if opcion == 'admin_partidos':
            sesion['paso'] = 'admin_partidos'
            return jsonify({
                'tipo': 'opciones_admin',
                'mensaje': '📋 GESTIÓN DE PARTIDOS\n\nSelecciona una opción:',
                'opciones': [
                    {'texto': '📋 Ver últimos 4 partidos', 'valor': 'admin_ver_partidos'},
                    {'texto': '➕ Crear partido', 'valor': 'admin_crear_partido'},
                    {'texto': '✏️ Editar partido', 'valor': 'admin_editar_partido'},
                    {'texto': '🔙 Volver al menú', 'valor': 'admin_menu'}
                ]
            })

        elif opcion == 'admin_menu':
            sesion['paso'] = 'menu_admin'
            return jsonify({
                'tipo': 'opciones_admin',
                'mensaje': '✅ Menú de Administrador\n\nSelecciona una opción:',
                'opciones': [
                    {'texto': '📋 Gestión de partidos', 'valor': 'admin_partidos'},
                    {'texto': '🎫 Gestión de reservas', 'valor': 'admin_reservas'},
                    {'texto': '👥 Gestión de socios', 'valor': 'admin_socios'},
                    {'texto': '🔙 Salir (modo socio)', 'valor': 'admin_salir'}
                ]
            })

        elif opcion == 'admin_reservas':
            sesion['paso'] = 'admin_reservas'
            return jsonify({
                'tipo': 'mensaje',
                'mensaje': '🎫 GESTIÓN DE RESERVAS\n\nPróximamente podrás ver y gestionar todas las reservas.\n\nEscribe *MENU* para volver al menú de administrador.'
            })

        elif opcion == 'admin_socios':
            sesion['paso'] = 'admin_socios'
            return jsonify({
                'tipo': 'mensaje',
                'mensaje': '👥 GESTIÓN DE SOCIOS\n\nPróximamente podrás añadir, editar y eliminar socios.\n\nEscribe *MENU* para volver al menú de administrador.'
            })

        elif opcion == 'admin_salir':
            sesion['paso'] = 'telefono_validado'
            sesion['es_admin'] = False
            partidos = requests.get(
                f"{BACKEND_URL}/partidos_disponibles",
                timeout=180
            ).json()
            if partidos.get('success') and partidos.get('partidos'):
                opciones = []
                for p in partidos['partidos']:
                    opciones.append({
                        'texto': f"⚽ {p['nombreEquipoVisitante']} - {p['fecha']}",
                        'valor': f"partido_{p['partidoID']}",
                        'partido_id': p['partidoID']
                    })
                return jsonify({
                    'tipo': 'opciones',
                    'mensaje': 'Selecciona el partido para el que quieres reservar:',
                    'opciones': opciones
                })
            else:
                return jsonify({
                    'tipo': 'mensaje',
                    'mensaje': '⚠️ No hay partidos disponibles para reservar en este momento.'
                })

    if opcion.startswith('partido_'):
        partido_id = int(opcion.split('_')[1])
        sesion['partido_seleccionado'] = partido_id

        reserva = requests.post(
            f"{BACKEND_URL}/reserva_existente",
            json={'socio_id': sesion['socio_id'], 'partido_id': partido_id},
            timeout=180
        ).json()

        socio_data = requests.post(
            f"{BACKEND_URL}/verificar_socio",
            json={'telefono': sesion['telefono']},
            timeout=180
        ).json()
        bolsa_actual = socio_data.get('bolsa', 0) if socio_data.get('success') else 0

        if reserva.get('existe'):
            sesion['paso'] = 'reserva_existente'
            sesion['reserva_actual'] = reserva
            return jsonify({
                'tipo': 'opciones_reserva_existente',
                'mensaje': f"⚠️ Ya tienes una reserva para este partido.\n\n📋 Reserva actual:\n• Asistes: {'✅ Sí' if reserva.get('plaza_socio') else '❌ No'}\n• Invitados: {reserva.get('num_invitados', 0)}\n• Bono utilizado: {'✅ Sí' if reserva.get('bono_utilizado') else '❌ No'}\n\n¿Qué deseas hacer?",
                'partido_id': partido_id,
                'bono_utilizado': reserva.get('bono_utilizado', False),
                'asiste_actual': reserva.get('plaza_socio', False),
                'invitados_actual': reserva.get('num_invitados', 0),
                'bolsa_actual': bolsa_actual,
                'opciones': [
                    {'texto': '❌ Cancelar reserva', 'valor': 'cancelar'},
                    {'texto': '✏️ Modificar reserva', 'valor': 'modificar'},
                    {'texto': '🔙 Salir (volver al menú)', 'valor': 'salir'}
                ]
            })
        else:
            sesion['paso'] = 'hacer_reserva'
            partidos = requests.get(
                f"{BACKEND_URL}/partidos_disponibles",
                timeout=180
            ).json()
            partido_nombre = "este partido"
            for p in partidos.get('partidos', []):
                if p['partidoID'] == partido_id:
                    partido_nombre = p['nombreEquipoVisitante']
                    break
            return jsonify({
                'tipo': 'formulario_reserva',
                'mensaje': f"⚽ Reserva para: {partido_nombre}\n\nIndica los detalles de tu reserva:",
                'partido_id': partido_id,
                'bolsa_actual': bolsa_actual
            })

    elif opcion == 'menu_principal':
        partidos = requests.get(
            f"{BACKEND_URL}/partidos_disponibles",
            timeout=180
        ).json()
        if partidos.get('success') and partidos.get('partidos'):
            opciones = []
            for p in partidos['partidos']:
                opciones.append({
                    'texto': f"⚽ {p['nombreEquipoVisitante']} - {p['fecha']}",
                    'valor': f"partido_{p['partidoID']}",
                    'partido_id': p['partidoID']
                })
            return jsonify({
                'tipo': 'opciones',
                'mensaje': "Selecciona el partido para el que quieres reservar:",
                'opciones': opciones
            })

    return jsonify({'tipo': 'mensaje', 'mensaje': 'Opción no válida.'})


if __name__ == '__main__':
    app.run(debug=True, port=5001)