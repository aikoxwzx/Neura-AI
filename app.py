import streamlit as st
from groq import Groq

# --- 1. CONFIGURACIÓN BÁSICA Y ESTÉTICA (Glassmorphism) ---
st.set_page_config(page_title="Neura AI", page_icon="🌌", layout="centered")

css = """
<style>
/* Fondo general */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%);
    color: white;
}

/* Ocultar iconos de perfil */
[data-testid="stChatMessageAvatar"] {
    display: none !important;
}
.stChatMessage {
    gap: 0.5rem !important;
}

/* Estilo Cristal para los mensajes */
[data-testid="stChatMessageContent"] {
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
    color: #e2e8f0;
}

/* USUARIO: A la derecha y azul */
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

/* =========================================
       1. TÚ (USUARIO) -> A LA DERECHA
       ========================================= */
    [data-testid="stChatMessage"]:has(.mensaje-usuario) {{
        flex-direction: row-reverse !important; /* Mueve el avatar y el inicio a la Derecha */
    }}
    
    [data-testid="stChatMessage"]:has(.mensaje-usuario) [data-testid="stChatMessageContent"] {{
        max-width: 65% !important; 
        
        /* Efecto Liquid Glass 3D VERDE */
        background: linear-gradient(135deg, rgba(220, 248, 198, 0.85) 0%, rgba(180, 230, 150, 0.4) 100%) !important;
        backdrop-filter: blur(16px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(180%) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.9) !important;
        border-left: 1px solid rgba(255, 255, 255, 0.9) !important;
        border-right: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-radius: 20px 4px 20px 20px !important; /* Punta de chat a la DERECHA */
        padding: 12px 18px !important;
        /* Sombra hiperrealista: exterior oscura + luz interior + sombra interior */
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15), inset 0 2px 6px rgba(255, 255, 255, 0.8), inset 0 -2px 6px rgba(0, 0, 0, 0.05) !important;
        color: #111b21 !important;
        animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
    }}

    /* =========================================
       2. LA IA -> A LA IZQUIERDA
       ========================================= */
    [data-testid="stChatMessage"]:has(.mensaje-ia) {{
        flex-direction: row !important; /* Mantiene el avatar y el inicio a la Izquierda */
    }}
    
    [data-testid="stChatMessage"]:has(.mensaje-ia) [data-testid="stChatMessageContent"] {{
        max-width: 65% !important;

}
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
    background-color: rgba(255, 255, 255, 0.05) !important; 
    border-bottom-left-radius: 2px; 
    margin-right: auto;
    max-width: 80%;
}

h1, h2, h3, p, span { color: #f8fafc !important; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

st.title("🌌 Neura AI")
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
    st.caption("Aitor)

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
                # st.code(f"Error técnico: {e}") # Descomenta esto si quieres ver el error exacto en pantalla
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
