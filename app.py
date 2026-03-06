import streamlit as st
import requests
import re
import random
from groq import Groq

# --- 1. CONFIGURACIÓN BÁSICA Y ESTÉTICA ---
st.set_page_config(page_title="Neura AI", layout="wide")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"], .stApp {
    background-image: linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(88, 28, 135, 0.3) 100%) !important;
    background-attachment: fixed !important;
    background-color: #0e1117 !important; 
}
[data-testid="stSidebar"] {
    background-color: rgba(126, 34, 206, 0.05) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(168, 85, 247, 0.2) !important;
}
/* Botones de Chat */
[data-testid="stRadio"] > label { display: none !important; }
div[data-testid="stRadio"] div[role="radiogroup"] label {
    background-color: rgba(255, 255, 255, 0.05) !important;
    padding: 12px 15px !important;
    border-radius: 12px !important;
    margin-bottom: 8px !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    border: 1px solid transparent !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
    background-color: rgba(168, 85, 247, 0.15) !important;
    transform: translateX(4px);
}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
    background-color: rgba(168, 85, 247, 0.3) !important;
    border: 1px solid rgba(168, 85, 247, 0.5) !important;
}
</style>
""", unsafe_allow_html=True)

# --- 2. SISTEMA DE AUTENTICACIÓN Y BASE DE DATOS ---
try:
    FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]
except KeyError:
    st.error("Error técnico: Falta FIREBASE_API_KEY en los secretos.")
    st.stop()

FIREBASE_DB_URL = "https://neura-ai-2026-default-rtdb.europe-west1.firebasedatabase.app"

def validar_contrasena(password):
    if len(password) < 6: return False, "La contraseña debe tener al menos 6 caracteres."
    if not re.search(r"[A-Z]", password): return False, "Debe contener al menos una mayúscula."
    if not re.search(r"[a-z]", password): return False, "Debe contener al menos una minúscula."
    if not re.search(r"[0-9]", password): return False, "Debe contener al menos un número."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): return False, "Debe contener al menos un carácter especial."
    return True, ""

def registrar_usuario_firebase(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    respuesta = requests.post(url, json=payload)
    return respuesta.status_code == 200

def login_usuario_firebase(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    respuesta = requests.post(url, json=payload)
    if respuesta.status_code == 200:
        datos = respuesta.json()
        return True, datos['idToken'], datos['localId']
    return False, "Correo o contraseña incorrectos.", None

def cargar_chats_firebase(uid, token):
    url = f"{FIREBASE_DB_URL}/usuarios/{uid}/chats.json?auth={token}"
    respuesta = requests.get(url)
    return respuesta.json() if respuesta.status_code == 200 and respuesta.json() else {}

def guardar_chats_firebase(uid, token, chats):
    chats_a_guardar = {titulo: mensajes for titulo, mensajes in chats.items() if len(mensajes) > 0}
    url = f"{FIREBASE_DB_URL}/usuarios/{uid}/chats.json?auth={token}"
    requests.put(url, json=chats_a_guardar)

# --- 3. LÓGICA DE MFA Y SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "esperando_mfa" not in st.session_state:
    st.session_state.esperando_mfa = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Neura AI")
        
        if not st.session_state.esperando_mfa:
            tab_login, tab_registro = st.tabs(["Iniciar Sesión", "Registrarse"])
            
            with tab_login:
                with st.form("form_login"):
                    email_login = st.text_input("Correo electrónico")
                    pass_login = st.text_input("Contraseña", type="password")
                    if st.form_submit_button("Entrar", use_container_width=True):
                        exito, token, uid = login_usuario_firebase(email_login, pass_login)
                        if exito:
                            # Aquí activaríamos el envío del código MFA al correo
                            st.session_state.esperando_mfa = True
                            st.session_state.temp_token = token
                            st.session_state.temp_uid = uid
                            st.session_state.temp_email = email_login
                            st.session_state.codigo_mfa = str(random.randint(100000, 999999))
                            
                            # NOTA: Aquí iría la función para enviar el correo con el código
                            st.info(f"DEBUG: Tu código MFA es {st.session_state.codigo_mfa}") 
                            st.rerun()
                        else: st.error(token)
            
            with tab_registro:
                with st.form("form_registro"):
                    email_reg = st.text_input("Nuevo Correo")
                    pass_reg = st.text_input("Nueva Contraseña", type="password")
                    if st.form_submit_button("Crear cuenta", use_container_width=True):
                        valido, msg = validar_contrasena(pass_reg)
                        if valido:
                            if registrar_usuario_firebase(email_reg, pass_reg): st.success("Cuenta creada.")
                            else: st.error("Error al registrar.")
                        else: st.error(msg)
        else:
            # Pantalla de verificación de código MFA
            st.subheader("Verificación de Seguridad")
            st.write(f"Introduce el código enviado a {st.session_state.temp_email}")
            codigo_usuario = st.text_input("Código de 6 dígitos", maxLength=6)
            
            if st.button("Verificar", use_container_width=True):
                if codigo_usuario == st.session_state.codigo_mfa:
                    st.session_state.autenticado = True
                    st.session_state.usuario_email = st.session_state.temp_email
                    st.session_state.id_token = st.session_state.temp_token
                    st.session_state.user_uid = st.session_state.temp_uid
                    
                    chats = cargar_chats_firebase(st.session_state.user_uid, st.session_state.id_token)
                    st.session_state.chats = chats if chats else {"Nuevo Chat": []}
                    st.session_state.chat_actual = list(st.session_state.chats.keys())[0]
                    st.session_state.esperando_mfa = False
                    st.rerun()
                else: st.error("Código incorrecto.")
            
            if st.button("Volver"):
                st.session_state.esperando_mfa = False
                st.rerun()
    st.stop()

# --- 4. MOTOR DE CHAT PRINCIPAL ---
st.title("Neura AI")
# ... (Aquí continúa el código de Groq y visuales que ya tenías)
