import streamlit as st
from groq import Groq

# --- 1. CONFIGURACIÓN BÁSICA Y ESTÉTICA (Glassmorphism Definitivo) ---
st.set_page_config(page_title="Neura AI", page_icon="🌌", layout="centered")

css = """
<style>
/* Fondo general oscuro */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%);
    color: white;
}

/* 1. Ocultar iconos de perfil para dejarlo limpio */
[data-testid="stChatMessageAvatar"] {
    display: none !important;
}

/* 2. Forzar que el contenedor principal ocupe todo el ancho */
[data-testid="stChatMessage"] {
    width: 100% !important;
    background-color: transparent !important;
}

/* 3. Estructura base de TODAS las burbujas (Efecto Cristal) */
[data-testid="stChatMessageContent"] {
    padding: 12px 18px !important;
    border-radius: 15px !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    color: #e2e8f0 !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    flex-grow: 0 !important; /* Vital para que la burbuja no se estire de lado a lado */
}

/* =========================================
   4. TÚ (USUARIO) -> A LA DERECHA
   ========================================= */
/* Usamos el truco del 'has' buscando nuestra marca HTML invisible */
[data-testid="stChatMessage"]:has(.marca-usuario) {
    flex-direction: row-reverse !important;
}

[data-testid="stChatMessage"]:has(.marca-usuario) [data-testid="stChatMessageContent"] {
    background-color: rgba(56, 189, 248, 0.15) !important; 
    border: 1px solid rgba(56, 189, 248, 0.3) !important;
    border-bottom-right-radius: 2px !important; 
    margin-left: auto !important; /* Esto es lo que lo empuja a la derecha */
    max-width: 75% !important;
}

/* =========================================
   5. LA IA (NEURA) -> A LA IZQUIERDA
   ========================================= */
[data-testid="stChatMessage"]:has(.marca-ia) {
    flex-direction: row !important;
}

[data-testid="stChatMessage"]:has(.marca-ia) [data-testid="stChatMessageContent"] {
    background-color: rgba(255, 255, 255, 0.05) !important; 
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-bottom-left-radius: 2px !important; 
    margin-right: auto !important; /* Esto es lo que lo empuja a la izquierda */
    max-width: 75% !important;
}

/* Ajustes de color de texto */
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

# --- 4. HISTORIAL DE CHAT (Inyectando marcas invisibles) ---
for mensaje in st.session_state.chats[st.session_state.chat_actual]:
    with st.chat_message(mensaje["rol"]):
        if mensaje["rol"] == "user":
            # Imprime el texto junto a una etiqueta HTML invisible para engañar al CSS
            st.markdown(f"<span class='marca-usuario'></span>{mensaje['texto']}", unsafe_allow_html=True)
        else:
            st.markdown(f"<span class='marca-ia'></span>{mensaje['texto']}", unsafe_allow_html=True)

# --- 5. LÓGICA DE ENVÍO Y ROTACIÓN ---
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    # 1. Guardamos e imprimimos el mensaje del usuario con su marca
    with st.chat_message("user"):
        st.markdown(f"<span class='marca-usuario'></span>{prompt}", unsafe_allow_html=True)
    st.session_state.chats[st.session_state.chat_actual].append({"rol": "user", "texto": prompt})
    
    # 2. Preparamos el historial para Groq
    mensajes_api = [{"role": "system", "content": instrucciones}]
    for m in st.session_state.chats[st.session_state.chat_actual][-5:]:
        # Adaptamos "bot" o "assistant" al formato que entiende Groq
        rol_api = "assistant" if m["rol"] in ["bot", "assistant"] else "user"
        mensajes_api.append({"role": rol_api, "content": m["texto"]})
    
    # Si hay un archivo subido, lo unimos al mensaje
    if archivo_subido is not None:
        texto_archivo = archivo_subido.read().decode('utf-8')
        mensajes_api[-1]["content"] = f"{prompt}\n\n[Archivo adjunto:]\n{texto_archivo}"

    # 3. Respuesta de IA y manejo de errores
    with st.chat_message("assistant"):
        with st.spinner("Procesando a velocidad extrema..."):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=mensajes_api
                )
                respuesta_texto = response.choices[0].message.content
                
                # Imprimimos la respuesta de Neura con la marca de IA invisible
                st.markdown(f"<span class='marca-ia'></span>{respuesta_texto}", unsafe_allow_html=True)
                st.session_state.chats[st.session_state.chat_actual].append({"rol": "assistant", "texto": respuesta_texto})
                
                # Si todo va bien, rotamos la clave para el próximo uso
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
                
            except Exception as e:
                # Si falla, rotamos y avisamos
                st.error("⚠️ Fallo en la conexión o cuota agotada. Cambiando de servidor... Por favor, vuelve a enviar tu mensaje.")
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
