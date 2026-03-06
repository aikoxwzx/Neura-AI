import streamlit as st
from groq import Groq

# --- 1. CONFIGURACIÓN BÁSICA Y ESTÉTICA (Glassmorphism Avanzado) ---
st.set_page_config(page_title="Neura AI", page_icon="🌌", layout="centered")

css = """
<style>
/* Fondo general de la página */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%);
    color: white;
}

/* Ocultar iconos de perfil por completo */
[data-testid="stChatMessageAvatar"] {
    display: none !important;
}

/* Reducir el hueco que dejan los avatares invisibles */
.stChatMessage {
    gap: 0.5rem !important;
    width: 100% !important;
}

/* --- ESTILO CRISTAL (Glassmorphism Base) --- */
[data-testid="stChatMessageContent"] {
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    padding: 12px 18px !important;
    color: #e2e8f0 !important;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
    display: inline-block !important;
}

/* --- USUARIO: A la DERECHA y Azul Cristal --- */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
    display: flex !important;
    flex-direction: row-reverse !important;
}

div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
    background: rgba(56, 189, 248, 0.15) !important; 
    border: 1px solid rgba(56, 189, 248, 0.3) !important;
    border-radius: 20px 20px 0px 20px !important; 
    margin-left: auto !important; /* Empuja la burbuja a la derecha */
    max-width: 75% !important;
    text-align: left !important;
}

/* --- IA (Neura): A la IZQUIERDA y Gris Cristal --- */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
    display: flex !important;
    flex-direction: row !important;
}

div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
    background: rgba(255, 255, 255, 0.05) !important; 
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 20px 20px 20px 0px !important; 
    margin-right: auto !important; /* Empuja la burbuja a la izquierda */
    max-width: 75% !important;
}

/* Textos adaptados al modo oscuro */
h1, h2, h3, p, span { color: #f8fafc !important; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

st.title("🌌 Neura AI (Powered by Groq ⚡)")
st.caption("Desarrollado y programado por Aitor")
st.divider()

# --- 2. SISTEMA DE ROTACIÓN DE API KEYS (Load Balancing) ---
try:
    api_keys = [st.secrets["GROQ_API_KEY_1"], st.secrets["GROQ_API_KEY_2"]]
except KeyError:
    st.error("⚠️ Error técnico: Faltan GROQ_API_KEY_1 o GROQ_API_KEY_2 en los secretos de Streamlit.")
    st.stop()

if "api_index" not in st.session_state:
    st.session_state.api_index = 0

clave_actual = api_keys[st.session_state.api_index]
client = Groq(api_key=clave_actual)

instrucciones = """
Eres Neura, un asistente de IA muy avanzado y educado.
Fuiste creado, programado y desplegado por Aitor.
Si te preguntan quién es tu creador, responde siempre con orgullo que fuiste creado por Aitor.
Busca ayudar sea como sea. Si cometes un error, discúlpate.
Saca temas de conversación, pregunta por los demás.
No uses emojis y mantén un tono profesional.
No digas tu nombre en todos los chats.
"""

# --- 3. BARRA LATERAL ---
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
    archivo_subido = st.file_uploader("Sube texto", type=["txt"])
    
    st.divider()
    st.caption(f"🔧 API en uso: Servidor {st.session_state.api_index + 1}")
    st.caption("Aitor | Ciberseguridad")

# --- 4. HISTORIAL DE CHAT ---
for mensaje in st.session_state.chats[st.session_state.chat_actual]:
    with st.chat_message(mensaje["rol"]):
        st.write(mensaje["texto"])

# --- 5. LÓGICA DE ENVÍO Y ROTACIÓN ---
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    # Guardamos mensaje del usuario
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.chats[st.session_state.chat_actual].append({"rol": "user", "texto": prompt})
    
    # Preparamos el historial para Groq
    mensajes_api = [{"role": "system", "content": instrucciones}]
    for m in st.session_state.chats[st.session_state.chat_actual][-5:]:
        mensajes_api.append({"role": "assistant" if m["rol"] == "bot" else "user", "content": m["texto"]})
    
    if archivo_subido is not None:
        texto_archivo = archivo_subido.read().decode('utf-8')
        mensajes_api[-1]["content"] = f"{prompt}\n\n[Archivo adjunto:]\n{texto_archivo}"

    # Respuesta de IA y manejo de errores
    with st.chat_message("assistant"):
        with st.spinner("Procesando a velocidad extrema..."):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=mensajes_api
                )
                respuesta_texto = response.choices[0].message.content
                st.write(respuesta_texto)
                st.session_state.chats[st.session_state.chat_actual].append({"rol": "bot", "texto": respuesta_texto})
                
                # Si todo va bien, rotamos la clave para el próximo uso
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
                
            except Exception as e:
                # Si falla, rotamos y avisamos
                st.error("⚠️ Fallo en la conexión o cuota agotada. Cambiando de servidor... Por favor, vuelve a enviar tu mensaje.")
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
