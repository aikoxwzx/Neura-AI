import streamlit as st
import requests
import re
import urllib.parse
from groq import Groq

# --- 1. CONFIGURACIÓN BÁSICA Y ESTÉTICA (Liquid Glass Morado Adaptativo) ---
st.set_page_config(page_title="Neura AI", layout="wide")

st.markdown("""
<style>
/* Forzado de fondo anti-parpadeo */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background-image: linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(88, 28, 135, 0.3) 100%) !important;
    background-attachment: fixed !important;
    background-color: #0e1117 !important; 
}

* {
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
}

/* Panel Lateral */
[data-testid="stSidebar"] {
    background-color: rgba(126, 34, 206, 0.05) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(168, 85, 247, 0.2) !important;
}

/* Botones de Chat y Radio Buttons */
[data-testid="stRadio"] > label { display: none !important; }

div[data-testid="stRadio"], div[data-testid="stRadio"] > div, div[data-testid="stRadio"] div[role="radiogroup"] {
    width: 100% !important; max-width: 100% !important; display: flex !important; flex-direction: column !important; align-items: stretch !important; 
}

div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child { display: none !important; }

div[data-testid="stRadio"] div[role="radiogroup"] label {
    background-color: rgba(255, 255, 255, 0.05) !important; padding: 12px 15px !important; border-radius: 12px !important; margin-bottom: 8px !important;
    width: 100% !important; max-width: 100% !important; flex: 1 1 100% !important; display: flex !important; box-sizing: border-box !important;
    cursor: pointer !important; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important; border: 1px solid transparent !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] label div { width: 100% !important; display: block !important; }
div[data-testid="stRadio"] div[role="radiogroup"] label p { width: 100% !important; overflow: hidden !important; text-overflow: ellipsis !important; white-space: nowrap !important; margin: 0 !important; }
div[data-testid="stRadio"] div[role="radiogroup"] label:hover { background-color: rgba(168, 85, 247, 0.15) !important; transform: translateX(4px); }
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) { background-color: rgba(168, 85, 247, 0.3) !important; border: 1px solid rgba(168, 85, 247, 0.5) !important; box-shadow: 0 2px 10px rgba(168, 85, 247, 0.1) !important; }

/* Caja de input */
.stChatInputContainer {
    background-color: rgba(168, 85, 247, 0.05) !important; backdrop-filter: blur(16px) !important; border-radius: 20px !important;
    border: 1px solid rgba(168, 85, 247, 0.3) !important; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important; transition: all 0.3s ease-in-out !important;
}
.stChatInputContainer:focus-within { border: 1px solid rgba(168, 85, 247, 0.8) !important; box-shadow: 0 4px 20px rgba(168, 85, 247, 0.2) !important; }

/* Botón Google Auth */
.btn-google {
    display: block; width: 100%; padding: 10px; margin-top: 15px; border-radius: 8px; text-align: center; font-weight: bold;
    background-color: white; color: #1e1e2f; text-decoration: none; border: 1px solid #ddd; transition: all 0.3s;
}
.btn-google:hover { background-color: #f1f5f9; transform: translateY(-2px); }
</style>
""", unsafe_allow_html=True)

# --- 2. CREDENCIALES Y VARIABLES DE ENTORNO ---
try:
    FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]
    GOOGLE_CLIENT_ID = st.secrets.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET", "")
    REDIRECT_URI = st.secrets.get("REDIRECT_URI", "http://localhost:8501")
except KeyError:
    st.error("Faltan variables de entorno en Streamlit Secrets.")
    st.stop()

FIREBASE_DB_URL = "https://neura-ai-2026-default-rtdb.europe-west1.firebasedatabase.app"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# --- 3. FUNCIONES DE BASE DE DATOS Y RED DE FIREBASE ---
def validar_contrasena(password):
    if len(password) < 6: return False, "Mínimo 6 caracteres."
    if not re.search(r"[A-Z]", password): return False, "Falta una mayúscula."
    if not re.search(r"[a-z]", password): return False, "Falta una minúscula."
    if not re.search(r"[0-9]", password): return False, "Falta un número."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): return False, "Falta un carácter especial."
    return True, ""

def registrar_usuario_firebase(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    if res.status_code == 200: return True, "Registrado."
    err = res.json().get("error", {}).get("message", "Error")
    return False, "Correo ya registrado" if err == "EMAIL_EXISTS" else err

def login_usuario_firebase(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    if res.status_code == 200:
        d = res.json()
        return True, d['idToken'], d['localId']
    return False, "Credenciales incorrectas.", None

def cargar_chats_firebase(uid, token):
    res = requests.get(f"{FIREBASE_DB_URL}/usuarios/{uid}/chats.json?auth={token}")
    if res.status_code == 200 and res.json() is not None: return res.json()
    return {}

def guardar_chats_firebase(uid, token, chats):
    chats_a_guardar = {t: m for t, m in chats.items() if len(m) > 0}
    requests.put(f"{FIREBASE_DB_URL}/usuarios/{uid}/chats.json?auth={token}", json=chats_a_guardar)

# --- 4. MOTOR OAUTH 2.0 (GOOGLE) ---
def generar_url_google():
    params = {
        "client_id": GOOGLE_CLIENT_ID, "redirect_uri": REDIRECT_URI, "response_type": "code",
        "scope": "openid email profile", "prompt": "select_account"
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

def intercambiar_codigo_google(codigo):
    data = { "client_id": GOOGLE_CLIENT_ID, "client_secret": GOOGLE_CLIENT_SECRET, "code": codigo, "grant_type": "authorization_code", "redirect_uri": REDIRECT_URI }
    res = requests.post("https://oauth2.googleapis.com/token", data=data)
    if res.status_code == 200: return res.json().get("id_token")
    return None

def login_firebase_con_google(google_id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={FIREBASE_API_KEY}"
    payload = { "postBody": f"id_token={google_id_token}&providerId=google.com", "requestUri": REDIRECT_URI, "returnIdpCredential": True, "returnSecureToken": True }
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        d = res.json()
        return True, d['idToken'], d['localId'], d.get('email', 'Usuario Google')
    return False, None, None, None

# INTERCEPTOR DE RED: Revisa si venimos de regreso desde la página de login de Google
if "code" in st.query_params and not st.session_state.autenticado:
    codigo_autorizacion = st.query_params["code"]
    st.query_params.clear() # Limpia la URL rápidamente por seguridad
    
    with st.spinner("Validando identidad con Google..."):
        token_google = intercambiar_codigo_google(codigo_autorizacion)
        if token_google:
            exito, fb_token, uid, email = login_firebase_con_google(token_google)
            if exito:
                st.session_state.autenticado = True
                st.session_state.usuario_email = email
                st.session_state.id_token = fb_token
                st.session_state.user_uid = uid
                
                chats_guardados = cargar_chats_firebase(uid, fb_token)
                if not chats_guardados: chats_guardados = {"Nuevo Chat": []}
                st.session_state.chats = chats_guardados
                st.session_state.chat_actual = list(chats_guardados.keys())[0]
                st.rerun()
            else:
                st.error("Error al vincular tu cuenta de Google con la base de datos.")
        else:
            st.error("El código de autorización de Google ha caducado o es inválido.")

# --- 5. PANTALLA DE LOGIN / REGISTRO ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Neura AI")
        st.caption("Por favor, identifícate para acceder al sistema.")
        
        tab_login, tab_registro = st.tabs(["Iniciar Sesión", "Registrarse"])
        
        with tab_login:
            with st.form("form_login"):
                email_login = st.text_input("Correo electrónico")
                pass_login = st.text_input("Contraseña", type="password")
                submit_login = st.form_submit_button("Entrar", use_container_width=True)
                
                if submit_login:
                    exito, token_o_msg, uid = login_usuario_firebase(email_login, pass_login)
                    if exito:
                        st.session_state.autenticado = True
                        st.session_state.usuario_email = email_login
                        st.session_state.id_token = token_o_msg
                        st.session_state.user_uid = uid
                        
                        chats_guardados = cargar_chats_firebase(uid, token_o_msg)
                        if not chats_guardados: chats_guardados = {"Nuevo Chat": []}
                        
                        base_nombre = "Nuevo Chat"
                        nuevo_nombre = base_nombre
                        contador = 1
                        while nuevo_nombre in chats_guardados:
                            nuevo_nombre = f"{base_nombre} ({contador})"
                            contador += 1
                        chats_guardados[nuevo_nombre] = []
                        st.session_state.chats = chats_guardados
                        st.session_state.chat_actual = nuevo_nombre
                        st.rerun()
                    else:
                        st.error(token_o_msg)
            
            # Botón de Login con Google
            st.markdown(f'<a href="{generar_url_google()}" target="_self" class="btn-google">Continuar con Google</a>', unsafe_allow_html=True)
                        
        with tab_registro:
            with st.form("form_registro"):
                email_reg = st.text_input("Nuevo Correo")
                pass_reg = st.text_input("Nueva Contraseña", type="password")
                pass_reg_conf = st.text_input("Confirmar Contraseña", type="password")
                submit_reg = st.form_submit_button("Crear cuenta", use_container_width=True)
                
                if submit_reg:
                    if pass_reg != pass_reg_conf:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        es_valida, msg_error = validar_contrasena(pass_reg)
                        if not es_valida:
                            st.error(msg_error)
                        else:
                            exito, mensaje = registrar_usuario_firebase(email_reg, pass_reg)
                            if exito: st.success(mensaje + " Ahora puedes iniciar sesión.")
                            else: st.error(mensaje)
    st.stop()

# --- 6. SISTEMA PRINCIPAL DE NEURA AI ---
st.title("Neura AI")
st.caption("Desarrollado y programado por Aitor")
st.divider()

api_keys = [val for key, val in st.secrets.items() if key.startswith("GROQ_API_KEY")]

if not api_keys:
    st.error("Faltan claves API de Groq en los secretos de Streamlit.")
    st.stop()

if "api_index" not in st.session_state: st.session_state.api_index = 0
st.session_state.api_index = st.session_state.api_index % len(api_keys)
client = Groq(api_key=api_keys[st.session_state.api_index])

instrucciones = """
Eres Neura, un asistente de IA muy avanzado y educado.
Fuiste creado, programado y desplegado por Aitor.
Si te preguntan quién es tu creador, responde siempre con orgullo que fuiste creado por Aitor.
Busca ayudar sea como sea. Si cometes un error, discúlpate.
Saca temas de conversación, pregunta por los demás.
No uses emojis y mantén un tono profesional.
No digas tu nombre en todos los chats.
Si te preguntan te llamas Neura.
"""

with st.sidebar:
    st.write(f"Usuario: {st.session_state.usuario_email}")
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.chats = {"Nuevo Chat": []}
        st.rerun()
        
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
            if not st.session_state.chats:
                st.session_state.chats = {"Nuevo Chat": []}
            st.session_state.chat_actual = list(st.session_state.chats.keys())[0]
            guardar_chats_firebase(st.session_state.user_uid, st.session_state.id_token, st.session_state.chats)
            st.rerun()

    chat_seleccionado = st.session_state.chat_actual if st.session_state.chat_actual in st.session_state.chats else list(st.session_state.chats.keys())[0]
    st.session_state.chat_actual = st.radio("Selecciona una conversación:", list(st.session_state.chats.keys()), index=list(st.session_state.chats.keys()).index(chat_seleccionado))

    st.divider()
    st.markdown("### Analizar Archivo")
    archivo_subido = st.file_uploader("Sube texto", type=["txt"])
    st.divider()
    st.caption(f"Servidor en uso: {st.session_state.api_index + 1} de {len(api_keys)}")
    st.caption("NeuraAI")

def renderizar_mensaje(rol, texto):
    if rol == "user":
        st.markdown(f"""
<div style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 20px;">
    <div style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.9), rgba(109, 40, 217, 0.9)); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px 20px 4px 20px; padding: 10px 16px; max-width: 75%; box-shadow: 0 8px 20px rgba(139, 92, 246, 0.3); backdrop-filter: blur(16px); font-weight: 400;">
        <span style="color: white !important;">{texto}</span>
    </div>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div style="display: flex; justify-content: flex-start; width: 100%; margin-bottom: 20px;">
    <div style="background-color: rgba(168, 85, 247, 0.1); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 20px 20px 20px 4px; padding: 10px 16px; max-width: 75%; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); backdrop-filter: blur(16px); font-weight: 400;">
        <span>{texto}</span>
    </div>
</div>
""", unsafe_allow_html=True)

for mensaje in st.session_state.chats[st.session_state.chat_actual]:
    rol_correcto = "assistant" if mensaje["rol"] in ["bot", "assistant", "ia"] else "user"
    renderizar_mensaje(rol_correcto, mensaje["texto"])

prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    es_primer_mensaje = len(st.session_state.chats[st.session_state.chat_actual]) == 0
    renderizar_mensaje("user", prompt)
    st.session_state.chats[st.session_state.chat_actual].append({"rol": "user", "texto": prompt})
    guardar_chats_firebase(st.session_state.user_uid, st.session_state.id_token, st.session_state.chats)
    
    mensajes_api = [{"role": "system", "content": instrucciones}]
    for m in st.session_state.chats[st.session_state.chat_actual][-10:]:
        rol_api = "assistant" if m["rol"] in ["bot", "assistant", "ia"] else "user"
        mensajes_api.append({"role": rol_api, "content": m["texto"]})
    
    if archivo_subido is not None:
        archivo_subido.seek(0)
        texto_archivo = archivo_subido.read().decode('utf-8')
        mensajes_api[-1]["content"] = f"{prompt}\n\n[Archivo adjunto:]\n{texto_archivo}"

    with st.spinner("Procesando..."):
        try:
            response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=mensajes_api)
            respuesta_texto = response.choices[0].message.content
            
            renderizar_mensaje("assistant", respuesta_texto)
            st.session_state.chats[st.session_state.chat_actual].append({"rol": "assistant", "texto": respuesta_texto})
            st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)

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
            st.error(f"Error de red. Cambiando de servidor... Intenta de nuevo.")
            st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
