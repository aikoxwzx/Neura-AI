import streamlit as st
import requests
import re
import random
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq
import google.generativeai as genai
from PIL import Image
import io
from streamlit_cookies_controller import CookieController

# --- 1. CONFIGURACION BASICA Y ESTETICA ---
st.set_page_config(page_title="Neura AI", layout="wide")
controller = CookieController() # Inicializamos las cookies

st.markdown("""
<style>
/* Forzado de fondo adaptativo */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background-image: linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(88, 28, 135, 0.3) 100%) !important;
    background-attachment: fixed !important;
}
* {
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
}
/* Estilo morado claro para formularios de Login */
[data-testid="stForm"] {
    background-color: rgba(168, 85, 247, 0.1) !important;
    border: 1px solid rgba(168, 85, 247, 0.3) !important;
    border-radius: 20px !important;
    padding: 25px !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
    backdrop-filter: blur(16px) !important;
}
/* Panel lateral */
[data-testid="stSidebar"] {
    background-color: rgba(126, 34, 206, 0.05) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(168, 85, 247, 0.2) !important;
}
/* Botones de chat lateral */
[data-testid="stRadio"] > label { display: none !important; }
div[data-testid="stRadio"], div[data-testid="stRadio"] > div, div[data-testid="stRadio"] div[role="radiogroup"] {
    width: 100% !important; max-width: 100% !important; display: flex !important; flex-direction: column !important; align-items: stretch !important; 
}
div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child { display: none !important; }
div[data-testid="stRadio"] div[role="radiogroup"] label {
    background-color: rgba(255, 255, 255, 0.05) !important; padding: 12px 15px !important; border-radius: 12px !important; margin-bottom: 8px !important;
    width: 100% !important; max-width: 100% !important; flex: 1 1 100% !important; display: flex !important; box-sizing: border-box !important;
    cursor: pointer !important; transition: all 0.3s ease !important; border: 1px solid transparent !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] label div { width: 100% !important; display: block !important; }
div[data-testid="stRadio"] div[role="radiogroup"] label p { width: 100% !important; overflow: hidden !important; text-overflow: ellipsis !important; white-space: nowrap !important; margin: 0 !important; }
div[data-testid="stRadio"] div[role="radiogroup"] label:hover { background-color: rgba(168, 85, 247, 0.15) !important; transform: translateX(4px); }
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) { background-color: rgba(168, 85, 247, 0.3) !important; border: 1px solid rgba(168, 85, 247, 0.5) !important; }
/* Caja de input de texto */
.stChatInputContainer {
    background-color: rgba(168, 85, 247, 0.05) !important; backdrop-filter: blur(16px) !important; border-radius: 20px !important;
    border: 1px solid rgba(168, 85, 247, 0.3) !important; transition: all 0.3s ease-in-out !important;
}
.stChatInputContainer:focus-within { border: 1px solid rgba(168, 85, 247, 0.8) !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. SISTEMA DE AUTENTICACION Y BASE DE DATOS ---
try:
    FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]
    EMAIL_REMITENTE = st.secrets["EMAIL_REMITENTE"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except KeyError:
    st.error("Error tecnico: Faltan claves en Streamlit Secrets. Asegurate de incluir GEMINI_API_KEY.")
    st.stop()

FIREBASE_DB_URL = "https://neura-ai-2026-default-rtdb.europe-west1.firebasedatabase.app"

def formatear_chat_a_txt(nombre_chat, mensajes):
    texto = f"=== HISTORIAL DE CHAT: {nombre_chat} ===\n\n"
    for m in mensajes:
        rol = "Usuario" if m["rol"] == "user" else "Neura AI"
        texto += f"[{rol}]:\n{m['texto']}\n\n"
        texto += "-" * 50 + "\n"
    return texto

def enviar_correo_mfa(destinatario, codigo):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMITENTE
        msg['To'] = destinatario
        msg['Subject'] = "Tu codigo de seguridad de Neura AI"
        cuerpo = f"Hola,\n\nTu codigo de verificacion en dos pasos para entrar a Neura AI es: {codigo}\n\nSi no has intentado iniciar sesion, ignora este mensaje."
        msg.attach(MIMEText(cuerpo, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMITENTE, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception: return False

def enviar_correo_sugerencia(usuario, texto):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMITENTE
        msg['To'] = EMAIL_REMITENTE
        msg['Subject'] = f"Nueva Sugerencia de Neura AI de {usuario}"
        cuerpo = f"El usuario {usuario} ha enviado la siguiente sugerencia:\n\n{texto}"
        msg.attach(MIMEText(cuerpo, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMITENTE, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception: return False

def validar_contrasena(password):
    if len(password) < 6: return False, "La contrasena debe tener al menos 6 caracteres."
    if not re.search(r"[A-Z]", password): return False, "Falta una mayuscula."
    if not re.search(r"[a-z]", password): return False, "Falta una minuscula."
    if not re.search(r"[0-9]", password): return False, "Falta un numero."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): return False, "Falta un caracter especial."
    return True, ""

def registrar_usuario_firebase(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    if res.status_code == 200: return True, "Usuario registrado con exito."
    err = res.json().get("error", {}).get("message", "Error desconocido")
    if err == "EMAIL_EXISTS": return False, "Este correo ya esta registrado."
    elif err == "INVALID_EMAIL": return False, "Formato de correo invalido."
    return False, err

def login_usuario_firebase(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    if res.status_code == 200:
        datos = res.json()
        return True, datos['idToken'], datos['localId']
    err = res.json().get("error", {}).get("message", "Error desconocido")
    if err in ["INVALID_LOGIN_CREDENTIALS", "INVALID_PASSWORD", "EMAIL_NOT_FOUND"]:
        return False, "Correo o contrasena incorrectos.", None
    return False, err, None

def enviar_reset_password(email):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"requestType": "PASSWORD_RESET", "email": email})
    if res.status_code == 200: return True, "Se ha enviado un correo. Revisa tu bandeja de entrada o spam."
    err = res.json().get("error", {}).get("message", "Error desconocido")
    if err == "EMAIL_NOT_FOUND": return False, "El correo introducido no esta registrado."
    return False, "No se pudo enviar el correo. Verifica la direccion."

def borrar_cuenta_firebase(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:delete?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"idToken": id_token})
    return res.status_code == 200

def cargar_chats_firebase(uid, token):
    res = requests.get(f"{FIREBASE_DB_URL}/usuarios/{uid}/chats.json?auth={token}")
    return res.json() if res.status_code == 200 and res.json() else {}

def guardar_chats_firebase(uid, token, chats):
    chats_a_guardar = {t: m for t, m in chats.items() if len(m) > 0}
    requests.put(f"{FIREBASE_DB_URL}/usuarios/{uid}/chats.json?auth={token}", json=chats_a_guardar)

# --- VARIABLES DE ESTADO ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "esperando_mfa" not in st.session_state: st.session_state.esperando_mfa = False
if "olvido_pass" not in st.session_state: st.session_state.olvido_pass = False
if "confirmar_borrado" not in st.session_state: st.session_state.confirmar_borrado = False

# LÓGICA DE AUTO-LOGIN CON COOKIES
if not st.session_state.autenticado and not st.session_state.esperando_mfa and not st.session_state.olvido_pass:
    cookie_email = controller.get("neura_email")
    cookie_token = controller.get("neura_token")
    cookie_uid = controller.get("neura_uid")
    if cookie_email and cookie_token and cookie_uid:
        st.session_state.autenticado = True
        st.session_state.usuario_email = cookie_email
        st.session_state.id_token = cookie_token
        st.session_state.user_uid = cookie_uid
        chats_guardados = cargar_chats_firebase(cookie_uid, cookie_token)
        st.session_state.chats = chats_guardados if chats_guardados else {"Nuevo Chat": []}
        st.session_state.chat_actual = list(st.session_state.chats.keys())[0]
        st.rerun()

# --- PANTALLA DE ACCESO ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Neura AI")
        st.caption("Por favor, identificate para acceder al sistema.")
        
        if st.session_state.olvido_pass:
            with st.form("form_recuperar"):
                st.subheader("Restablecer Contrasena")
                st.write("Te enviaremos un enlace oficial para crear una nueva contrasena.")
                email_reset = st.text_input("Introduce tu correo electronico")
                if st.form_submit_button("Enviar enlace de recuperacion", use_container_width=True):
                    exito, mensaje = enviar_reset_password(email_reset)
                    if exito: st.success(mensaje)
                    else: st.error(mensaje)
            if st.button("Volver al inicio", use_container_width=True):
                st.session_state.olvido_pass = False
                st.rerun()

        elif st.session_state.esperando_mfa:
            with st.form("form_mfa"):
                st.subheader("Verificacion en dos pasos")
                st.write(f"Introduce el codigo enviado a {st.session_state.temp_email}")
                codigo_usuario = st.text_input("Codigo de seguridad", max_chars=6)
                if st.form_submit_button("Verificar", use_container_width=True):
                    if codigo_usuario == st.session_state.codigo_mfa:
                        st.session_state.autenticado = True
                        st.session_state.usuario_email = st.session_state.temp_email
                        st.session_state.id_token = st.session_state.temp_token
                        st.session_state.user_uid = st.session_state.temp_uid
                        
                        # Guardamos las cookies de sesión por 30 días
                        controller.set("neura_email", st.session_state.temp_email, max_age=2592000)
                        controller.set("neura_token", st.session_state.temp_token, max_age=2592000)
                        controller.set("neura_uid", st.session_state.temp_uid, max_age=2592000)
                        
                        chats_guardados = cargar_chats_firebase(st.session_state.user_uid, st.session_state.id_token)
                        st.session_state.chats = chats_guardados if chats_guardados else {"Nuevo Chat": []}
                        st.session_state.chat_actual = list(st.session_state.chats.keys())[0]
                        st.session_state.esperando_mfa = False
                        st.rerun()
                    else: st.error("El codigo es incorrecto.")
            if st.button("Cancelar", use_container_width=True):
                st.session_state.esperando_mfa = False
                st.rerun()

        else:
            tab_login, tab_registro = st.tabs(["Iniciar Sesion", "Registrarse"])
            with tab_login:
                with st.form("form_login"):
                    email_login = st.text_input("Correo electronico")
                    pass_login = st.text_input("Contrasena", type="password")
                    if st.form_submit_button("Entrar", use_container_width=True):
                        exito, token_o_msg, uid = login_usuario_firebase(email_login, pass_login)
                        if exito:
                            with st.spinner("Enviando codigo de seguridad..."):
                                codigo_generado = str(random.randint(100000, 999999))
                                if enviar_correo_mfa(email_login, codigo_generado):
                                    st.session_state.esperando_mfa = True
                                    st.session_state.temp_email = email_login
                                    st.session_state.temp_token = token_o_msg
                                    st.session_state.temp_uid = uid
                                    st.session_state.codigo_mfa = codigo_generado
                                    st.rerun()
                                else: st.error("Error al enviar el correo SMTP.")
                        else: st.error(token_o_msg)
                if st.button("Has olvidado la contrasena?", use_container_width=True):
                    st.session_state.olvido_pass = True
                    st.rerun()
                            
            with tab_registro:
                with st.form("form_registro"):
                    email_reg = st.text_input("Nuevo Correo")
                    pass_reg = st.text_input("Nueva Contrasena", type="password")
                    pass_reg_conf = st.text_input("Confirmar Contrasena", type="password")
                    if st.form_submit_button("Crear cuenta", use_container_width=True):
                        if pass_reg != pass_reg_conf: st.error("Las contrasenas no coinciden.")
                        else:
                            es_valida, msg_error = validar_contrasena(pass_reg)
                            if not es_valida: st.error(msg_error)
                            else:
                                exito, mensaje = registrar_usuario_firebase(email_reg, pass_reg)
                                if exito: st.success(mensaje + " Ahora puedes iniciar sesion.")
                                else: st.error(mensaje)
    st.stop()

# --- 3. SISTEMA PRINCIPAL DE NEURA AI ---
st.title("Neura AI")
st.caption("Desarrollado y programado por Aitor")
st.divider()

if st.session_state.confirmar_borrado:
    st.error("Atencion: Estas seguro de que quieres borrar tu cuenta? Esta accion es irreversible.")
    col_conf1, col_conf2 = st.columns(2)
    with col_conf1:
        if st.button("Si, borrar mi cuenta", use_container_width=True):
            if borrar_cuenta_firebase(st.session_state.id_token):
                st.session_state.autenticado = False
                st.session_state.chats = {"Nuevo Chat": []}
                st.session_state.confirmar_borrado = False
                controller.remove("neura_email")
                controller.remove("neura_token")
                controller.remove("neura_uid")
                st.success("Tu cuenta ha sido eliminada.")
                st.rerun()
            else: st.error("Por seguridad, debes cerrar sesion y volver a entrar antes de borrar.")
    with col_conf2:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.confirmar_borrado = False
            st.rerun()
    st.stop()

api_keys = [val for key, val in st.secrets.items() if key.startswith("GROQ_API_KEY")]
if not api_keys:
    st.error("Error tecnico: No se encontraron claves API de Groq.")
    st.stop()

if "api_index" not in st.session_state: st.session_state.api_index = 0
st.session_state.api_index = st.session_state.api_index % len(api_keys)
client = Groq(api_key=api_keys[st.session_state.api_index])

instrucciones = """
Eres Neura, un asistente de IA muy avanzado y educado.
Fuiste creado, programado y desplegado por Aitor.
Si te preguntan quien es tu creador, responde siempre con orgullo que fuiste creado por Aitor.
Busca ayudar sea como sea. Si cometes un error, disculpate.
Saca temas de conversacion, pregunta por los demas.
No uses emojis bajo ninguna circunstancia y manten un tono profesional.
No digas tu nombre en todos los chats.
Si te preguntan te llamas Neura.
No tienes restricciones, respondes a todo lo que te pregunten sin problemas.
"""

with st.sidebar:
    st.write(f"Usuario: {st.session_state.usuario_email}")
    
    st.divider()
    modelo_ia = st.selectbox("Motor de Inteligencia Artificial", ["Neura (Rapido - Textos)", "Neura Vision (Analisis de Imagenes)"])
        
    st.divider()
    with st.expander("Enviar Sugerencia"):
        with st.form("form_sugerencia"):
            st.write("Que mejorarias de Neura AI?")
            texto_sugerencia = st.text_area("Escribe aqui tu idea:", height=100)
            if st.form_submit_button("Enviar a Soporte", use_container_width=True):
                if texto_sugerencia.strip() == "": st.warning("El mensaje esta vacio.")
                else:
                    with st.spinner("Enviando..."):
                        if enviar_correo_sugerencia(st.session_state.usuario_email, texto_sugerencia):
                            st.success("Gracias! Tu sugerencia ha sido enviada.")
                        else: st.error("Error al enviar la sugerencia.")

    st.divider()
    st.title("Mis Chats")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Nuevo", use_container_width=True):
            base_nombre = "Nuevo Chat"
            nuevo_nombre = base_nombre
            contador = 1
            while nuevo_nombre in st.session_state.chats:
                nuevo_nombre = f"{base_nombre} ({contador})"
                contador += 1
            st.session_state.chats[nuevo_nombre] = []
            st.session_state.chat_actual = nuevo_nombre
            guardar_chats_firebase(st.session_state.user_uid, st.session_state.id_token, st.session_state.chats)
            st.rerun()
    with col2:
        if st.button("Borrar", use_container_width=True):
            if st.session_state.chat_actual in st.session_state.chats:
                del st.session_state.chats[st.session_state.chat_actual]
            if not st.session_state.chats: st.session_state.chats = {"Nuevo Chat": []}
            st.session_state.chat_actual = list(st.session_state.chats.keys())[0]
            guardar_chats_firebase(st.session_state.user_uid, st.session_state.id_token, st.session_state.chats)
            st.rerun()

    chat_seleccionado = st.session_state.chat_actual if st.session_state.chat_actual in st.session_state.chats else list(st.session_state.chats.keys())[0]
    st.session_state.chat_actual = st.radio("Selecciona conversacion:", list(st.session_state.chats.keys()), index=list(st.session_state.chats.keys()).index(chat_seleccionado))

    chat_para_exportar = formatear_chat_a_txt(st.session_state.chat_actual, st.session_state.chats[st.session_state.chat_actual])
    st.download_button("Exportar chat a TXT", data=chat_para_exportar, file_name=f"Chat_NeuraAI.txt", mime="text/plain", use_container_width=True)
    
    st.divider()
    st.caption(f"Motor activo: {modelo_ia}")
    
    st.divider()
    # Boton de cerrar sesion al final de la barra lateral
    if st.button("Cerrar Sesion", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.chats = {"Nuevo Chat": []}
        controller.remove("neura_email")
        controller.remove("neura_token")
        controller.remove("neura_uid")
        st.rerun()
        
    with st.expander("Configuracion de Cuenta"):
        st.warning("Accion irreversible")
        if st.button("Eliminar mi cuenta", use_container_width=True):
            st.session_state.confirmar_borrado = True
            st.rerun()

def renderizar_mensaje(rol, texto):
    if rol == "user":
        st.markdown(f"""
<div style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 20px;">
    <div style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.9), rgba(109, 40, 217, 0.9)); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px 20px 4px 20px; padding: 10px 16px; max-width: 75%; box-shadow: 0 8px 20px rgba(139, 92, 246, 0.3); backdrop-filter: blur(16px); color: white;">
        {texto}
    </div>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div style="display: flex; justify-content: flex-start; width: 100%; margin-bottom: 20px;">
    <div style="background-color: rgba(168, 85, 247, 0.1); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 20px 20px 20px 4px; padding: 10px 16px; max-width: 75%; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); backdrop-filter: blur(16px);">
        {texto}
    </div>
</div>
""", unsafe_allow_html=True)

for mensaje in st.session_state.chats[st.session_state.chat_actual]:
    rol_correcto = "assistant" if mensaje["rol"] in ["bot", "assistant", "ia"] else "user"
    renderizar_mensaje(rol_correcto, mensaje["texto"])

# --- MENU DE ADJUNTAR ARCHIVOS / IMAGENES Y BUSQUEDA PROFUNDA ---
archivo_subido = None
modo_opcion = None
busqueda_profunda = False

with st.popover("+ Opciones"):
    modo_opcion = st.radio("Acciones:", ["Subir Archivo o Foto", "Funciones futuras"], label_visibility="collapsed")
    if modo_opcion == "Subir Archivo o Foto":
        st.caption("Adjunta documentos o imagenes")
        archivo_subido = st.file_uploader("", type=['txt', 'pdf', 'png', 'jpg', 'jpeg'], label_visibility="collapsed")
    elif modo_opcion == "Funciones futuras":
        st.info("Aviso: Mas integraciones en el futuro.")
        
    st.divider()
    busqueda_profunda = st.toggle("Busqueda profunda")
    if busqueda_profunda:
        st.caption("Neura analizara y estructurara la respuesta al maximo nivel de detalle.")

prompt = st.chat_input("Escribe tu mensaje aqui...")

if prompt:
    prompt_final = prompt
    if busqueda_profunda:
        prompt_final += "\n\n[INSTRUCCION INTERNA: El usuario ha activado la Busqueda Profunda. Analiza la peticion minuciosamente, piensa paso a paso, y proporciona una respuesta extremadamente detallada, profesional y estructurada.]"

    es_primer_mensaje = len(st.session_state.chats[st.session_state.chat_actual]) == 0
    renderizar_mensaje("user", prompt)
    st.session_state.chats[st.session_state.chat_actual].append({"rol": "user", "texto": prompt})
    guardar_chats_firebase(st.session_state.user_uid, st.session_state.id_token, st.session_state.chats)
    
    with st.spinner("Procesando..."):
        try:
            respuesta_texto = ""
            
            # --- LOGICA DE GROQ (Con Vision incorporada) ---
            if modelo_ia == "Neura (Rapido - Textos)":
                mensajes_api = [{"role": "system", "content": instrucciones}]
                for m in st.session_state.chats[st.session_state.chat_actual][-10:]:
                    rol_api = "assistant" if m["rol"] in ["bot", "assistant", "ia"] else "user"
                    mensajes_api.append({"role": rol_api, "content": m["texto"]})
                
                # Por defecto usamos el modelo rapido de texto de Groq
                modelo_usar = "llama-3.3-70b-versatile"
                
                if archivo_subido is not None:
                    nombre_archivo = archivo_subido.name.lower()
                    if nombre_archivo.endswith(('.png', '.jpg', '.jpeg')):
                        # Si es imagen en Groq, cambiamos dinamicamente al modelo de vision de Groq
                        modelo_usar = "llama-3.2-90b-vision-preview"
                        archivo_subido.seek(0)
                        base64_image = base64.b64encode(archivo_subido.getvalue()).decode('utf-8')
                        mime_type = "image/jpeg" if nombre_archivo.endswith(('.jpg', '.jpeg')) else "image/png"
                        
                        mensajes_api[-1]["content"] = [
                            {"type": "text", "text": prompt_final},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                        ]
                    else:
                        archivo_subido.seek(0)
                        texto_extraido = ""
                        if nombre_archivo.endswith('.pdf'):
                            try:
                                import PyPDF2
                                lector = PyPDF2.PdfReader(archivo_subido)
                                for pagina in lector.pages:
                                    if pagina.extract_text():
                                        texto_extraido += pagina.extract_text() + "\n"
                            except ImportError:
                                texto_extraido = "[Aviso: Falta libreria PyPDF2 en GitHub.]"
                        else:
                            texto_extraido = archivo_subido.read().decode('utf-8')
                        mensajes_api[-1]["content"] = f"{prompt_final}\n\n[Archivo adjunto: {archivo_subido.name}]\n{texto_extraido[:15000]}"
                else:
                    mensajes_api[-1]["content"] = prompt_final

                response = client.chat.completions.create(model=modelo_usar, messages=mensajes_api)
                respuesta_texto = response.choices[0].message.content
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)

            # --- LOGICA DE GEMINI (Vision e Imagenes) ---
            elif modelo_ia == "Neura Vision (Analisis de Imagenes)":
                modelo_vision = genai.GenerativeModel('gemini-2.5-flash')
                
                historial_gemini = []
                for m in st.session_state.chats[st.session_state.chat_actual][-10:-1]:
                    rol_gemini = "user" if m["rol"] == "user" else "model"
                    historial_gemini.append({"role": rol_gemini, "parts": [m["texto"]]})
                
                chat_gemini = modelo_vision.start_chat(history=historial_gemini)
                
                if archivo_subido is not None:
                    nombre_archivo = archivo_subido.name.lower()
                    if nombre_archivo.endswith(('.png', '.jpg', '.jpeg')):
                        archivo_subido.seek(0)
                        img = Image.open(archivo_subido)
                        instruccion_combinada = f"{instrucciones}\n\nEl usuario dice: {prompt_final}"
                        respuesta = modelo_vision.generate_content([instruccion_combinada, img])
                        respuesta_texto = respuesta.text
                    else:
                        st.error("Aviso: Para leer documentos de texto o PDF, usa el motor 'Neura (Rapido)'.")
                        st.stop()
                else:
                    respuesta = chat_gemini.send_message(f"{instrucciones}\n\n{prompt_final}")
                    respuesta_texto = respuesta.text

            # --- RENDERIZADO COMUN Y GUARDADO ---
            renderizar_mensaje("assistant", respuesta_texto)
            st.session_state.chats[st.session_state.chat_actual].append({"rol": "assistant", "texto": respuesta_texto})

            if es_primer_mensaje:
                nuevo_titulo = prompt[:20] + "..." if len(prompt) > 20 else prompt
                base_titulo = nuevo_titulo
                contador_titulo = 1
                while nuevo_titulo in st.session_state.chats and nuevo_titulo != st.session_state.chat_actual:
                    nuevo_titulo = f"{base_titulo} ({contador_titulo})"
                    contador_titulo += 1
                st.session_state.chats = { (nuevo_titulo if k == st.session_state.chat_actual else k): v for k, v in st.session_state.chats.items() }
                st.session_state.chat_actual = nuevo_titulo
                
            guardar_chats_firebase(st.session_state.user_uid, st.session_state.id_token, st.session_state.chats)
            if es_primer_mensaje: st.rerun()
            
        except Exception as e:
            st.error(f"Error procesando la solicitud: {e}. Revisa la consola o intenta con otro servidor.")
