from flask import Flask, render_template_string, request, jsonify
import requests
import re

app = Flask(__name__)

# Almacenamiento temporal de sesiones (en producción usar BD o Redis)
sesiones = {}

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
    
    function generarSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    function deshabilitarBoton(btn) {
        if (btn) {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
        }
    }
    
    function habilitarBotonEnviar(habilitado) {
        const btn = document.getElementById('btnEnviar');
        if (btn) {
            btn.disabled = !habilitado;
        }
    }
    
    function eliminarFormularioAnterior() {
        const formularioExistente = document.getElementById('formulario_reserva');
        if (formularioExistente) {
            formularioExistente.remove();
        }
        const formularioModificacion = document.getElementById('formulario_modificacion');
        if (formularioModificacion) {
            formularioModificacion.remove();
        }
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
                mensaje.querySelector('.options-container') ||
                mensaje.querySelector('.formulario-reserva')) {
                mensaje.remove();
            }
        });
    }
    
    function eliminarOpcionesPartidos() {
        const opcionesDiv = document.getElementById('opciones_partidos');
        if (opcionesDiv) {
            opcionesDiv.remove();
        }
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
        
        // Deshabilitar botón mientras se procesa
        habilitarBotonEnviar(false);
        
        if (!sessionId) {
            sessionId = generarSessionId();
        }
        
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
            body: JSON.stringify({
                texto: texto,
                session_id: sessionId
            })
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
                        deshabilitarBoton(btn);
                        seleccionarPartido(btn.dataset.partidoId, btn.dataset.partidoNombre);
                    };
                    optionsDiv.appendChild(btn);
                });

                // Línea separadora
                    const hr = document.createElement('hr');
                    hr.style.margin = '15px 0';
                    hr.style.border = 'none';
                    hr.style.borderTop = '1px solid #e8e4d8';
                    optionsDiv.appendChild(hr);
                    
                    // Botón para consultar bono
                    const btnBono = document.createElement('button');
                    btnBono.textContent = '💰 ¿Quieres consultar si tienes bono?';
                    btnBono.className = 'option-button';
                    btnBono.style.backgroundColor = '#27ae60';
                    btnBono.onclick = (e) => {
                        deshabilitarBoton(btnBono);
                        consultarBono();
                    };
                optionsDiv.appendChild(btnBono);

                botMsg.appendChild(optionsDiv);
                chatMessages.appendChild(botMsg);
                habilitarBotonEnviar(false);
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
                        deshabilitarBoton(btn);
                        const asiste = document.getElementById('asisteCheckbox').checked;
                        const invitados = obtenerInvitados('invitadosInput');
                        enviarReserva(data.partido_id, asiste, invitados);
                    };
                }
                habilitarBotonEnviar(false);
            }
            else {
                botMsg.innerHTML = data.mensaje;
                chatMessages.appendChild(botMsg);
                if (data.mensaje && (data.mensaje.includes('Número no registrado') || data.mensaje.includes('intenta con otro número'))) {
                    habilitarBotonEnviar(true);
                } else {
                    habilitarBotonEnviar(false);
                }
            }
            
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(error => {
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            botMsg.innerHTML = '⚠️ Error de conexión con el servidor';
            document.getElementById('chatMessages').appendChild(botMsg);
            habilitarBotonEnviar(true);
        });
    }
    
    function mostrarFormularioModificacion(partidoId, asisteActual, invitadosActual) {
        limpiarMensajesYFormularios();
        
        if (invitadosActual === null || invitadosActual === undefined) {
            invitadosActual = 0;
        }
        
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
                deshabilitarBoton(btn);
                const asiste = document.getElementById('asisteCheckboxMod').checked;
                const invitados = obtenerInvitados('invitadosInputMod');
                enviarModificacion(partidoId, asiste, invitados);
            };
        }
        habilitarBotonEnviar(false);
    }
    
    function seleccionarPartido(partidoId, partidoNombre) {
        if (partidoSeleccionado === partidoId) {
            return;
        }
        partidoSeleccionado = partidoId;
        
        const opcionesDiv = document.getElementById('opciones_partidos');
        if (opcionesDiv) {
            const botones = opcionesDiv.querySelectorAll('.option-button');
            botones.forEach(btn => {
                deshabilitarBoton(btn);
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
                        deshabilitarBoton(btn);
                        if (op.valor === 'cancelar') {
                            enviarConfirmacionEliminar(data.partido_id, data.bono_utilizado);
                        } else if (op.valor === 'modificar') {
                            mostrarFormularioModificacion(data.partido_id, data.asiste_actual, data.invitados_actual);
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
                mostrarFormularioModificacion(data.partido_id, data.asiste, data.invitados);
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
                        deshabilitarBoton(btn);
                        const asiste = document.getElementById('asisteCheckbox').checked;
                        const invitados = obtenerInvitados('invitadosInput');
                        enviarReserva(data.partido_id, asiste, invitados);
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
        body: JSON.stringify({
            opcion: valor,
            session_id: sessionId
        })
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
            
            // Botones de partidos
            data.opciones.forEach(op => {
                const btn = document.createElement('button');
                btn.textContent = op.texto;
                btn.className = 'option-button';
                btn.dataset.partidoId = op.partido_id;
                btn.onclick = (e) => {
                    deshabilitarBoton(btn);
                    seleccionarPartido(op.partido_id, op.texto);
                };
                optionsDiv.appendChild(btn);
            });
            
            // Línea separadora
            const hr = document.createElement('hr');
            hr.style.margin = '15px 0';
            hr.style.border = 'none';
            hr.style.borderTop = '1px solid #e8e4d8';
            optionsDiv.appendChild(hr);
            
            // Botón para consultar bono
            const btnBono = document.createElement('button');
            btnBono.textContent = '💰 ¿Quieres consultar si tienes bono?';
            btnBono.className = 'option-button';
            btnBono.style.backgroundColor = '#27ae60';
            btnBono.onclick = (e) => {
                deshabilitarBoton(btnBono);
                consultarBono();
            };
            optionsDiv.appendChild(btnBono);
            
            botMsg.appendChild(optionsDiv);
            chatMessages.appendChild(botMsg);
            partidoSeleccionado = null;
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
    
    function enviarReserva(partidoId, asiste, invitados) {
        const chatMessages = document.getElementById('chatMessages');
        const loadingMsg = document.createElement('div');
        loadingMsg.className = 'message bot-message';
        loadingMsg.innerHTML = '⏳ Procesando tu reserva...';
        loadingMsg.id = 'loading_msg';
        chatMessages.appendChild(loadingMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        fetch('/api/confirmar_reserva', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                partido_id: partidoId,
                asiste: asiste,
                invitados: invitados,
                session_id: sessionId
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
                if (msg.innerHTML.includes('Reserva para:') || 
                    msg.innerHTML.includes('Indica los detalles')) {
                    msg.remove();
                }
            });
            
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            botMsg.innerHTML = data.mensaje;
            chatMessages.appendChild(botMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            partidoSeleccionado = null;
            
            if (data.mensaje && data.mensaje.includes('Puedes hacer una nueva reserva')) {
                habilitarBotonEnviar(true);
            } else {
                habilitarBotonEnviar(false);
            }
        })
        .catch(error => {
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
    
    function enviarModificacion(partidoId, asiste, invitados) {
        const chatMessages = document.getElementById('chatMessages');
        const loadingMsg = document.createElement('div');
        loadingMsg.className = 'message bot-message';
        loadingMsg.innerHTML = '⏳ Procesando tu modificación...';
        loadingMsg.id = 'loading_msg';
        chatMessages.appendChild(loadingMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        fetch('/api/modificar_reserva', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                partido_id: partidoId,
                asiste: asiste,
                invitados: invitados,
                session_id: sessionId
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
                if (msg.innerHTML.includes('Modifica los detalles') || 
                    msg.innerHTML.includes('✏️ Modifica los detalles')) {
                    msg.remove();
                }
            });
            
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-message';
            botMsg.innerHTML = data.mensaje;
            chatMessages.appendChild(botMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            partidoSeleccionado = null;
            
            if (data.mensaje && data.mensaje.includes('Puedes hacer una nueva reserva')) {
                habilitarBotonEnviar(true);
            } else {
                habilitarBotonEnviar(false);
            }
        })
        .catch(error => {
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
    
    fetch('/api/consultar_bono', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: sessionId
        })
    })
    .then(response => response.json())
    .then(data => {
        const loading = document.getElementById('loading_msg');
        if (loading) loading.remove();
        
        limpiarMensajesYFormularios();
        
        const botMsg = document.createElement('div');
        botMsg.className = 'message bot-message';
        
        if (data.success) {
            botMsg.innerHTML = data.message;
            chatMessages.appendChild(botMsg);
            
            // Después de mostrar la información, reiniciar la sesión
            setTimeout(() => {
                const reinicioMsg = document.createElement('div');
                reinicioMsg.className = 'message bot-message';
                reinicioMsg.innerHTML = '🔄 Puedes hacer una nueva reserva. Por favor, ingresa tu número de teléfono:';
                chatMessages.appendChild(reinicioMsg);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                
                // Reiniciar variables de sesión
                sessionId = null;
                partidoSeleccionado = null;
                habilitarBotonEnviar(true);
            }, 2000);
        } else {
            botMsg.innerHTML = '❌ ' + data.message;
            chatMessages.appendChild(botMsg);
            habilitarBotonEnviar(true);
        }
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
    })
    .catch(error => {
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
    const chatMessages = document.getElementById('chatMessages');
    
    // Limpiar mensajes y formularios anteriores
    limpiarMensajesYFormularios();
    
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'message bot-message';
    loadingMsg.innerHTML = '⏳ Procesando cancelación...';
    loadingMsg.id = 'loading_msg';
    chatMessages.appendChild(loadingMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    fetch('/api/eliminar_reserva', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            partido_id: partidoId,
            bono_utilizado: bonoUtilizado,
            session_id: sessionId
        })
    })
    .then(response => response.json())
    .then(data => {
        const loading = document.getElementById('loading_msg');
        if (loading) loading.remove();
        
        // Volver a limpiar después de la respuesta (por si acaso)
        limpiarMensajesYFormularios();
        
        const botMsg = document.createElement('div');
        botMsg.className = 'message bot-message';
        botMsg.innerHTML = data.mensaje;
        chatMessages.appendChild(botMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        partidoSeleccionado = null;
        
        if (data.mensaje && data.mensaje.includes('Puedes hacer una nueva reserva')) {
            habilitarBotonEnviar(true);
        } else {
            habilitarBotonEnviar(false);
        }
    })
    .catch(error => {
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
        
        // Habilitar botón al inicio porque el bot ya pide el teléfono
        habilitarBotonEnviar(true);
        
        if (input) {
            input.addEventListener('keypress', function(event) {
                if (event.keyCode === 13 || event.key === 'Enter') {
                    event.preventDefault();
                    if (!boton.disabled) {
                        enviarMensaje();
                    }
                }
            });
        }
        
        if (boton) {
            boton.addEventListener('click', function() {
                if (!boton.disabled) {
                    enviarMensaje();
                }
            });
        }
    });
</script>
</body>
</html>
'''

# =============================================
# FUNCIONES DEL BACKEND DEL CHATBOT
# =============================================

BACKEND_URL = "https://chatbot-penia.onrender.com/api"

def verificar_telefono(telefono):
    try:
        url = f"{BACKEND_URL}/verificar_socio"
        print(f"🔍 Llamando a: {url}")
        response = requests.post(url, json={'telefono': telefono}, timeout=5)
        print(f"🔍 Status code: {response.status_code}")
        print(f"🔍 Respuesta: {response.text}")
        return response.json()
    except Exception as e:
        print(f"❌ Error en verificar_telefono: {e}")
        return {'success': False, 'message': 'Error de conexión'}

def obtener_partidos_disponibles():
    try:
        response = requests.get(f"{BACKEND_URL}/partidos_disponibles", timeout=5)
        return response.json()
    except:
        return {'success': False, 'partidos': []}

def obtener_reserva_existente(socio_id, partido_id):
    try:
        response = requests.post(f"{BACKEND_URL}/reserva_existente", json={'socio_id': socio_id, 'partido_id': partido_id}, timeout=5)
        return response.json()
    except:
        return {'success': False, 'existe': False}

def obtener_detalles_reserva_api(socio_id, partido_id):
    """Obtiene los detalles de una reserva desde el endpoint del backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/reserva/{socio_id}/{partido_id}", timeout=5)
        return response.json()
    except:
        return {'success': False, 'message': 'Error de conexión'}

def crear_reserva(socio_id, partido_id, asiste, invitados):
    try:
        # Primero crear/modificar la reserva
        response = requests.post(f"{BACKEND_URL}/crear_reserva", json={'socio_id': socio_id, 'partido_id': partido_id, 'plaza_socio': asiste, 'num_plazas_NO_socio': invitados}, timeout=5)
        resultado = response.json()
        
        if resultado.get('success'):
            # Luego obtener los detalles de la reserva recién creada
            detalles = obtener_detalles_reserva_api(socio_id, partido_id)
            
            if detalles.get('success'):
                reserva = detalles.get('reserva', {})
                partido = reserva.get('partido', {})
                socio = reserva.get('socio', {})
                
                asiste_texto = "✅ Sí" if reserva.get('plaza_socio') else "❌ No"
                
                mensaje_detallado = f"""
✅ Reserva creada correctamente

📋 DETALLES DE LA RESERVA:
━━━━━━━━━
⚽ Partido: {partido.get('equipo_visitante', 'No disponible')}
📅 Fecha: {partido.get('fecha', 'No disponible')}
🕐 Hora: {partido.get('hora', 'No disponible')}
🏷️ Temporada: {partido.get('temporada', 'No disponible')}
📌 Tipo: {partido.get('tipo', 'No disponible')}

👤 Socio: {socio.get('nombre', '')} {socio.get('apellidos', '')}
📞 Teléfono: {socio.get('telefono', 'No disponible')}
🎫 Asistes como socio al partido: {asiste_texto}
👥 Número de NO socios: {reserva.get('num_plazas_no_socio', 0)}
💰 Bono utilizado: {"✅ Sí" if reserva.get('bono_utilizado') else "❌ No"}
━━━━━━━━━

"""
                return {'success': True, 'message': mensaje_detallado}
        else:
            return {'success': False, 'message': resultado.get('message', 'Error al crear la reserva')}
    except:
        return {'success': False, 'message': 'Error de conexión'}

def modificar_reserva(socio_id, partido_id, asiste, invitados):
    try:
        # Primero modificar la reserva
        response = requests.post(f"{BACKEND_URL}/modificar_reserva", json={'socio_id': socio_id, 'partido_id': partido_id, 'plaza_socio': asiste, 'num_plazas_NO_socio': invitados}, timeout=5)
        resultado = response.json()
        
        if resultado.get('success'):
            # Luego obtener los detalles de la reserva modificada
            detalles = obtener_detalles_reserva_api(socio_id, partido_id)
            
            if detalles.get('success'):
                reserva = detalles.get('reserva', {})
                partido = reserva.get('partido', {})
                socio = reserva.get('socio', {})
                
                asiste_texto = "✅ Sí" if reserva.get('plaza_socio') else "❌ No"
                
                mensaje_detallado = f"""
✅ Reserva modificada correctamente

📋 DETALLES DE LA RESERVA:
━━━━━━━━━
⚽ Partido: {partido.get('equipo_visitante', 'No disponible')}
📅 Fecha: {partido.get('fecha', 'No disponible')}
🕐 Hora: {partido.get('hora', 'No disponible')}
🏷️ Temporada: {partido.get('temporada', 'No disponible')}
📌 Tipo: {partido.get('tipo', 'No disponible')}

👤 Socio: {socio.get('nombre', '')} {socio.get('apellidos', '')}
📞 Teléfono: {socio.get('telefono', 'No disponible')}
🎫 Asistes como socio al partido: {asiste_texto}
👥 Número de NO socios: {reserva.get('num_plazas_no_socio', 0)}
💰 Bono utilizado: {"✅ Sí" if reserva.get('bono_utilizado') else "❌ No"}
━━━━━━━━━

"""
                return {'success': True, 'message': mensaje_detallado}
            
        else:
            return {'success': False, 'message': resultado.get('message', 'Error al modificar la reserva')}
    except:
        return {'success': False, 'message': 'Error de conexión'}

def eliminar_reserva(socio_id, partido_id, bono_utilizado):
    try:
        response = requests.post(f"{BACKEND_URL}/eliminar_reserva", json={'socio_id': socio_id, 'partido_id': partido_id, 'bono_utilizado': bono_utilizado}, timeout=5)
        return response.json()
    except:
        return {'success': False, 'message': 'Error de conexión'}


def consultar_bono(telefono):
    """Consulta los datos del socio (incluyendo bolsa) por teléfono"""
    try:
        response = requests.post(f"{BACKEND_URL}/verificar_socio", json={'telefono': telefono}, timeout=5)
        return response.json()
    except:
        return {'success': False, 'message': 'Error de conexión'}
    


# =============================================
# RUTAS DE FLASK
# =============================================

@app.route('/')
def index():
    return render_template_string(HTML)

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
            resultado = verificar_telefono(telefono)
            
            if resultado.get('success'):
                sesion['paso'] = 'telefono_validado'
                sesion['socio_id'] = resultado['socio_id']
                sesion['socio_nombre'] = resultado['nombre']
                sesion['telefono'] = telefono
                
                partidos = obtener_partidos_disponibles()
                
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
                        'opciones': opciones
                    })
                else:
                    return jsonify({
                        'tipo': 'mensaje',
                        'mensaje': '⚠️ No hay partidos disponibles para reservar en este momento.'
                    })
            else:
                return jsonify({
                    'tipo': 'mensaje',
                    'mensaje': f'❌ {resultado.get("message", "Número no registrado")}\n\nPor favor, intenta con otro número o contacta al administrador.'
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
    
    if opcion.startswith('partido_'):
        partido_id = int(opcion.split('_')[1])
        sesion['partido_seleccionado'] = partido_id
        
        reserva = obtener_reserva_existente(sesion['socio_id'], partido_id)
        
        if reserva.get('existe'):
            sesion['paso'] = 'reserva_existente'
            sesion['reserva_actual'] = reserva
            sesion['partido_seleccionado'] = partido_id
            
            return jsonify({
                'tipo': 'opciones_reserva_existente',
                'mensaje': f"⚠️ Ya tienes una reserva para este partido.\n\n📋 Reserva actual:\n• Asistes: {'✅ Sí' if reserva.get('plaza_socio') else '❌ No'}\n• Invitados: {reserva.get('num_invitados', 0)}\n• Bono utilizado: {'✅ Sí' if reserva.get('bono_utilizado') else '❌ No'}\n\n¿Qué deseas hacer?",
                'partido_id': partido_id,
                'bono_utilizado': reserva.get('bono_utilizado', False),
                'asiste_actual': reserva.get('plaza_socio', False),
                'invitados_actual': reserva.get('num_invitados', 0),
                'opciones': [
                    {'texto': '❌ Cancelar reserva', 'valor': 'cancelar'},
                    {'texto': '✏️ Modificar reserva', 'valor': 'modificar'},
                    {'texto': '🔙 Salir (volver al menú)', 'valor': 'salir'}
                ]
            })
        else:
            sesion['paso'] = 'hacer_reserva'
            partidos = obtener_partidos_disponibles()
            partido_nombre = "este partido"
            for p in partidos.get('partidos', []):
                if p['partidoID'] == partido_id:
                    partido_nombre = p['nombreEquipoVisitante']
                    break
            
            return jsonify({
                'tipo': 'formulario_reserva',
                'mensaje': f"⚽ Reserva para: {partido_nombre}\n\nIndica los detalles de tu reserva:",
                'partido_id': partido_id
            })
    
    elif opcion == 'menu_principal':
        partidos = obtener_partidos_disponibles()
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

@app.route('/api/confirmar_reserva', methods=['POST'])
def confirmar_reserva():
    data = request.get_json()
    session_id = data.get('session_id', '')
    partido_id = data.get('partido_id')
    asiste = data.get('asiste', False)
    invitados = data.get('invitados', 0)
    
    try:
        invitados = max(0, min(int(invitados), 999))
    except:
        invitados = 0
    
    if session_id not in sesiones:
        return jsonify({'mensaje': 'Sesión no válida'})
    
    sesion = sesiones[session_id]
    
    resultado = crear_reserva(sesion['socio_id'], partido_id, asiste, invitados)
    
    if resultado.get('success'):
        sesiones[session_id] = {'paso': 'esperando_telefono'}
        return jsonify({'mensaje': resultado.get('message', '✅ Reserva creada correctamente') + '\n\n🔄 Puedes hacer una nueva reserva. Por favor, ingresa tu número de teléfono:'})
    else:
        return jsonify({'mensaje': f'❌ Error: {resultado.get("message", "No se pudo crear la reserva")}'})

@app.route('/api/modificar_reserva', methods=['POST'])
def modificar_reserva_route():
    data = request.get_json()
    session_id = data.get('session_id', '')
    partido_id = data.get('partido_id')
    asiste = data.get('asiste', False)
    invitados = data.get('invitados', 0)
    
    try:
        invitados = max(0, min(int(invitados), 999))
    except:
        invitados = 0
    
    if session_id not in sesiones:
        return jsonify({'mensaje': 'Sesión no válida'})
    
    sesion = sesiones[session_id]
    
    resultado = modificar_reserva(sesion['socio_id'], partido_id, asiste, invitados)
    
    if resultado.get('success'):
        sesiones[session_id] = {'paso': 'esperando_telefono'}
        return jsonify({'mensaje': resultado.get('message', '✅ Reserva modificada correctamente') + '\n\n🔄 Puedes hacer una nueva reserva. Por favor, ingresa tu número de teléfono:'})
    else:
        return jsonify({'mensaje': f'❌ Error: {resultado.get("message", "No se pudo modificar la reserva")}'})

@app.route('/api/eliminar_reserva', methods=['POST'])
def eliminar_reserva_route():
    data = request.get_json()
    session_id = data.get('session_id', '')
    partido_id = data.get('partido_id')
    bono_utilizado = data.get('bono_utilizado', False)
    
    if session_id not in sesiones:
        return jsonify({'mensaje': 'Sesión no válida'})
    
    sesion = sesiones[session_id]
    
    resultado = eliminar_reserva(sesion['socio_id'], partido_id, bono_utilizado)
    
    if resultado.get('success'):
        sesiones[session_id] = {'paso': 'esperando_telefono'}
        return jsonify({'mensaje': resultado.get('message', '✅ Reserva cancelada correctamente') + '\n\n🔄 Puedes hacer una nueva reserva. Por favor, ingresa tu número de teléfono:'})
    else:
        return jsonify({'mensaje': f'❌ Error: {resultado.get("message", "No se pudo cancelar la reserva")}'})


@app.route('/api/consultar_bono', methods=['POST'])
def api_consultar_bono():
    data = request.get_json()
    session_id = data.get('session_id', '')
    
    if session_id not in sesiones:
        return jsonify({'success': False, 'message': 'Sesión no válida. Por favor, reinicia el chat.'})
    
    sesion = sesiones[session_id]
    telefono = sesion.get('telefono')
    
    if not telefono:
        return jsonify({'success': False, 'message': 'No hay teléfono registrado. Por favor, ingresa tu número de teléfono primero.'})
    
    resultado = consultar_bono(telefono)
    
    if resultado.get('success'):
        mensaje = f"""
📋 INFORMACIÓN DE TU BONO:
━━━━━━━━━
👤 Socio: {resultado.get('nombre')} {resultado.get('apellidos')}
📞 Teléfono: {telefono}
💰 Saldo actual (bolsa): {resultado.get('bolsa', 0)}€
━━━━━━━━━
ℹ️ Si quieres consultar algún dato sobre tu bono, ampliarlo o cambiar el teléfono, avisa a tu administrador.
"""
        return jsonify({'success': True, 'message': mensaje})
    else:
        return jsonify({'success': False, 'message': resultado.get('message', 'Error al consultar el bono')})


if __name__ == '__main__':
    app.run(debug=True, port=5001)