import streamlit as st
from groq import Groq

# --- 1. CONFIGURACIÓN BÁSICA Y ESTÉTICA (Glassmorphism Definitivo) ---
st.set_page_config(page_title="Neura AI", page_icon="🌌", layout="centered")

css = """
<style>
/* 1. Fondo general oscuro estilo terminal/cyber */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%);
    color: white;
}

/* 2. OCULTAR AVATARES (Forzado máximo) */
.stAvatar, [data-testid="stChatMessageAvatar"] {
    display: none !important;
}

/* 3. Limpiar el contenedor base del chat */
.stChatMessage {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    width: 100% !important; /* Vital para que puedan ir a los extremos */
}

/* 4. Estilo de la Burbuja de Cristal (Efecto Glassmorphism) */
[data-testid="stChatMessageContent"] {
    padding: 12px 18px !important;
    border-radius: 20px !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    color: #e2e8f0 !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    max-width: 80% !important;
    width: fit-content !important;
    flex-grow: 0 !important; /* Evita que la burbuja se estire ocupando todo el ancho */
}

/* 5. TÚ (USUARIO) -> A la Derecha (Azulado) */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    flex-direction: row-reverse !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
    background-color: rgba(56, 189, 248, 0.15) !important; 
    border: 1px solid rgba(56, 189, 248, 0.3) !important;
    border-bottom-right-radius: 4px !important; /* Pico de chat a la derecha */
    margin-left: auto !important; /* Empuja el globo a la derecha */
}

/* 6. NEURA (IA) -> A la Izquierda (Gris) */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    flex-direction: row !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
    background-color: rgba(255, 255, 255, 0.05) !important; 
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-bottom-left-radius: 4px !important; /* Pico de chat a la izquierda */
    margin-right: auto !important; /* Empuja el globo a la izquierda */
}

/* Textos adaptados al modo oscuro */
h1, h2, h3, p, span, label { color: #f8fafc !important; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

st.title("🌌 Neura AI (Powered by Groq ⚡)")
st.caption("Desarrollado y programado por Aitor")
st.divider()

# --- 2. SISTEMA DE ROTACIÓN DE API KEYS ---
try:
    api_keys = [st.secrets["GROQ_API_KEY_1"], st.secrets["GROQ_API_KEY_2"]]
except KeyError:
    st.error("⚠️ Error técnico: Faltan GROQ_API_KEY_1 o GROQ_API_KEY_2 en Streamlit Secrets.")
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
    st.caption(f"🔧 Servidor en uso: {st.session_state.api_index + 1}")
    st.caption("Aitor | Ciberseguridad")

# --- 4. HISTORIAL DE CHAT (Con auto-corrección) ---
for mensaje in st.session_state.chats[st.session_state.chat_actual]:
    # El parche: Si el mensaje antiguo dice "bot", lo leemos como "assistant" para no romper el CSS
    rol_correcto = "assistant" if mensaje["rol"] in ["bot", "assistant"] else "user"
    with st.chat_message(rol_correcto):
        st.write(mensaje["texto"])

# --- 5. LÓGICA DE ENVÍO Y ROTACIÓN ---
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    # Mostramos mensaje del usuario
    with st.chat_message("user"):
        st.write(prompt)
    # A partir de ahora, guardamos a la IA SIEMPRE como "assistant"
    st.session_state.chats[st.session_state.chat_actual].append({"rol": "user", "texto": prompt})
    
    # Preparamos el historial para Groq
    mensajes_api = [{"role": "system", "content": instrucciones}]
    for m in st.session_state.chats[st.session_state.chat_actual][-5:]:
        rol_api = "assistant" if m["rol"] in ["bot", "assistant"] else "user"
        mensajes_api.append({"role": rol_api, "content": m["texto"]})
    
    if archivo_subido is not None:
        texto_archivo = archivo_subido.read().decode('utf-8')
        mensajes_api[-1]["content"] = f"{prompt}\n\n[Archivo adjunto:]\n{texto_archivo}"

    # Respuesta de IA y manejo de errores
    with st.chat_message("assistant"):
        with st.spinner("Procesando..."):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=mensajes_api
                )
                respuesta_texto = response.choices[0].message.content
                st.write(respuesta_texto)
                st.session_state.chats[st.session_state.chat_actual].append({"rol": "assistant", "texto": respuesta_texto})
                
                # Rotamos la clave para el próximo uso
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
                
            except Exception as e:
                st.error("⚠️ Fallo en la conexión o cuota agotada. Cambiando de servidor... Por favor, vuelve a enviar tu mensaje.")
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
