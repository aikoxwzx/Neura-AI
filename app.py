import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuración básica
st.set_page_config(page_title="Neura AI", page_icon="🌌", layout="centered")

# --- INYECCIÓN DE CSS: GLASSMORPHISM Y ALINEACIÓN ---
st.markdown("""
<style>
/* Fondo general de la aplicación (Oscuro elegante) */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%);
    color: white;
}

/* Forzar la desaparición de los avatares */
[data-testid="stChatMessageAvatar"] { display: none !important; }
.stChatMessage { gap: 0rem !important; }

/* ----------------------------------------------------
   DISEÑO GLASSMORPHISM PARA LAS BURBUJAS
   ---------------------------------------------------- */
[data-testid="stChatMessageContent"] {
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    color: #e2e8f0 !important;
}

/* ----------------------------------------------------
   MENSAJES DEL USUARIO (A la derecha y azulados)
   ---------------------------------------------------- */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
    flex-direction: row-reverse;
}
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stChatMessageContent"] {
    background: rgba(56, 189, 248, 0.1) !important; /* Tono azul cristal */
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    border-radius: 20px 20px 0px 20px;
    margin-left: auto;
    max-width: 80%;
}

/* ----------------------------------------------------
   MENSAJES DE LA IA (A la izquierda y grisáceos)
   ---------------------------------------------------- */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
    flex-direction: row;
}
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) div[data-testid="stChatMessageContent"] {
    border-radius: 20px 20px 20px 0px;
    margin-right: auto;
    max-width: 80%;
}

/* Ajustes de color de texto en inputs y menús para que se vean bien en oscuro */
h1, h2, h3, p, span { color: #f8fafc !important; }
</style>
""", unsafe_allow_html=True)

st.title("🌌 Neura AI")
st.caption("Desarrollado y programado por Aitor")
st.divider()

# 2. SISTEMA DE ROTACIÓN Y CONFIGURACIÓN (Corregido)
api_keys = [st.secrets["GEMINI_API_KEY_1"], st.secrets["GEMINI_API_KEY_2"]]

if "api_index" not in st.session_state:
    st.session_state.api_index = 0

clave_actual = api_keys[st.session_state.api_index]
genai.configure(api_key=clave_actual)

instrucciones = """
Eres un asistente de IA muy útil y educado. 
Fuiste creado, programado y desplegado por Aitor. 
Si cualquier persona te pregunta quién es tu creador, quién te hizo, o de dónde vienes, debes responder siempre con orgullo que fuiste creado por Aitor.
Eres un asistente talentoso que busca ayudar a los demás sea como sea buscando cualquier solución.
Si tienes un error discúlpate y busca una solución si es posible.
Sé buen asistente, saca temas de conversación, pregunta por los demás y haz que te importen sus temas.
No uses emojis.
Fuera de ser majo sé también profesional.
Cada que empiezas un nuevo chat preséntate con tu nombre, Neura.
Tienes que ser preciso si te preguntan alguna fecha o cualquier otra cosa, tienes que estar actualizado.
No digas quien te ha creado a no ser que te lo pregunten.
"""

# HE CAMBIADO EL MODELO AL 2.0-FLASH QUE ES EL CORRECTO Y ESTABLE
model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=instrucciones)

# 3. BARRA LATERAL
with st.sidebar:
    st.title("📂 Mis Chats")
    
    if "chats" not in st.session_state:
        st.session_state.chats = {"Chat 1": []}
    if "chat_actual" not in st.session_state:
        st.session_state.chat_actual = "Chat 1"

    if st.button("➕ Nuevo Chat"):
        nuevo_nombre = f"Chat {len(st.session_state.chats) + 1}"
        st.session_state.chats[nuevo_nombre] = []
        st.session_state.chat_actual = nuevo_nombre
        st.rerun()

    st.session_state.chat_actual = st.radio(
        "Selecciona una conversación:", 
        list(st.session_state.chats.keys()), 
        index=list(st.session_state.chats.keys()).index(st.session_state.chat_actual)
    )

    st.divider()
    st.markdown("### 📎 Analizar Archivo")
    archivo_subido = st.file_uploader("Sube una imagen o texto", type=["png", "jpg", "jpeg", "txt"])
    
    st.divider()
    st.caption(f"🔧 Conectado al Servidor {st.session_state.api_index + 1}")

# 4. Historial del chat
for mensaje in st.session_state.chats[st.session_state.chat_actual]:
    with st.chat_message(mensaje["rol"]):
        st.write(mensaje["texto"])

# 5. Interfaz de envío
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    # Mensaje de usuario
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.chats[st.session_state.chat_actual].append({"rol": "user", "texto": prompt})
    
    # Construir memoria temporal para que la IA lea la conversación reciente
    historial_texto = "\n".join([f"{m['rol']}: {m['texto']}" for m in st.session_state.chats[st.session_state.chat_actual][-5:]])
    contenido_a_enviar = [f"Historial reciente:\n{historial_texto}\n\nResponde al último mensaje de 'user':"]
    
    if archivo_subido is not None:
        if archivo_subido.name.endswith(('png', 'jpg', 'jpeg')):
            imagen = Image.open(archivo_subido)
            contenido_a_enviar.append(imagen)
        elif archivo_subido.name.endswith('txt'):
            texto_archivo = archivo_subido.read().decode('utf-8')
            contenido_a_enviar.append(f"\n[Contenido del archivo adjunto:]\n{texto_archivo}")

    # Respuesta de IA
    with st.chat_message("assistant"):
        with st.spinner("Analizando datos..."):
            try:
                response = model.generate_content(contenido_a_enviar)
                st.write(response.text)
                st.session_state.chats[st.session_state.chat_actual].append({"rol": "assistant", "texto": response.text})
                
                # Rotación exitosa
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
                
            except Exception as e:
                # Si falla, imprimimos el error real para saber qué pasa
                st.error("⚠️ Fallo en la conexión. Cambiando de servidor...")
                st.code(f"Error técnico: {str(e)}") # Esto te ayudará a depurar
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
