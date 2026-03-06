import streamlit as st
from groq import Groq

# --- 1. CONFIGURACIÓN BÁSICA Y ESTÉTICA (Glassmorphism y Cleanup) ---
st.set_page_config(page_title="Neura AI", page_icon="🌌", layout="centered")

css = """
<style>
/* 1. Fondo Degradado Oscuro Elegante */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%);
    color: white;
}

/* 2. Quitar iconos y avatares */
[data-testid="stChatMessageAvatar"] {
    display: none !important;
}
.stChatMessage {
    gap: 0.5rem !important;
}

/* 3. Estilo Base para Burbujas de Chat (Efecto Cristal translucido) */
[data-testid="stChatMessageContent"] {
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
    color: #e2e8f0;
}

/* 4. Mensajes del USUARIO -> A LA DERECHA y Azul Cristal */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
    flex-direction: row-reverse !important;
}
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
    background-color: rgba(56, 189, 248, 0.1) !important; 
    border-color: rgba(56, 189, 248, 0.2);
    border-bottom-right-radius: 2px; 
    text-align: right;
    margin-left: auto;
    max-width: 80%;
}

/* 5. Mensajes de la IA -> A LA IZQUIERDA y Gris Cristal */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
    flex-direction: row !important;
}
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
    background-color: rgba(255, 255, 255, 0.05) !important; 
    border-bottom-left-radius: 2px; 
    margin-right: auto;
    max-width: 80%;
}

/* Ajustar colores para que se vea bien en fondo oscuro */
h1, h2, h3, p, span { color: #f8fafc !important; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- 2. ENCABEZADO DE LA APP ---
st.title("🌌 Neura AI (Powered by Groq ⚡)")
st.caption("Desarrollado y programado por Aitor")
st.divider()

# --- 3. CONFIGURACIÓN DE GROQ ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("⚠️ Error: No se ha encontrado la clave GROQ_API_KEY en los secretos de Streamlit.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

instrucciones = """
Eres Neura, un asistente de IA educado y directo.
Fuiste programado por Aitor.
Sé buen asistente, saca temas de conversación.
No uses emojis.
"""

# --- 4. BARRA LATERAL ---
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
    st.caption("Aitor | Ciberseguridad")

# --- 5. IMPRIMIR HISTORIAL ---
for mensaje in st.session_state.chats[st.session_state.chat_actual]:
    with st.chat_message(mensaje["rol"]):
        st.write(mensaje["texto"])

# --- 6. INTERFAZ DE ENVÍO ---
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.chats[st.session_state.chat_actual].append({"rol": "user", "texto": prompt})
    
    mensajes_api = [{"role": "system", "content": instrucciones}]
    for m in st.session_state.chats[st.session_state.chat_actual][-5:]:
        mensajes_api.append({"role": "assistant" if m["rol"] == "bot" else "user", "content": m["texto"]})
    
    if archivo_subido is not None:
        texto_archivo = archivo_subido.read().decode('utf-8')
        mensajes_api[-1]["content"] = f"{prompt}\n\n[Archivo adjunto:]\n{texto_archivo}"

    with st.chat_message("assistant"):
        with st.spinner("Procesando..."):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=mensajes_api
                )
                respuesta_texto = response.choices[0].message.content
                st.write(respuesta_texto)
                st.session_state.chats[st.session_state.chat_actual].append({"rol": "bot", "texto": respuesta_texto})
                
            except Exception as e:
                st.error("⚠️ Fallo en la conexión. Reintenta enviar tu mensaje.")
