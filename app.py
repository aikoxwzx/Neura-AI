import streamlit as st
from groq import Groq

# --- 1. CONFIGURACIÓN BÁSICA Y ESTÉTICA (Liquid Glass iOS Style) ---
st.set_page_config(page_title="Neura AI", page_icon="✨", layout="centered")

# Forzamos el fondo claro azulito (estilo Apple) y textos oscuros
st.markdown("""
<style>
/* Fondo general degradado azul muy suave */
.stApp {
    background: #f0f9ff !important;
    background-image: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%) !important;
    color: #1e293b !important;
}

/* Forzar que todos los textos nativos sean oscuros para que se lean bien */
h1, h2, h3, p, span, label, div { color: #1e293b !important; }

/* Darle un toque de cristal esmerilado también al panel lateral */
[data-testid="stSidebar"] {
    background-color: rgba(255, 255, 255, 0.4) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.3) !important;
}

/* Estilizar el campo de texto de entrada */
.stChatInputContainer {
    background-color: rgba(255, 255, 255, 0.6) !important;
    backdrop-filter: blur(16px) !important;
    border-radius: 20px !important;
    border: 1px solid rgba(255, 255, 255, 0.8) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
}
</style>
""", unsafe_allow_html=True)

st.title("✨ Neura AI (Powered by Groq ⚡)")
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

# --- 3. BARRA LATERAL (Con nuevo botón de borrado) ---
with st.sidebar:
    st.title("📂 Mis Chats")
    
    if "chats" not in st.session_state:
        st.session_state.chats = {"Chat 1": []}
    if "chat_actual" not in st.session_state:
        st.session_state.chat_actual = "Chat 1"

    if st.button("➕ Nuevo Chat", use_container_width=True):
        nuevo_nombre = f"Chat {len(st.session_state.chats) + 1}"
        st.session_state.chats[nuevo_nombre] = []
        st.session_state.chat_actual = nuevo_nombre
        st.rerun()

    st.session_state.chat_actual = st.radio(
        "Selecciona una conversación:", 
        list(st.session_state.chats.keys()), 
        index=list(st.session_state.chats.keys()).index(st.session_state.chat_actual)
    )

    # NUEVO: Botón para vaciar el chat actual
    if st.button("🗑️ Vaciar Chat Actual", type="primary", use_container_width=True):
        st.session_state.chats[st.session_state.chat_actual] = []
        st.rerun()

    st.divider()
    st.markdown("### 📎 Analizar Archivo")
    archivo_subido = st.file_uploader("Sube texto", type=["txt"])
    
    st.divider()
    st.caption(f"🔧 Servidor en uso: {st.session_state.api_index + 1}")
    st.caption("Aitor | Ciberseguridad")

# --- 4. MOTOR GRÁFICO PERSONALIZADO (Liquid Glass iOS) ---
def renderizar_mensaje(rol, texto):
    if rol == "user":
        # Burbuja del usuario: Estilo iMessage (Azul vibrante translúcido)
        st.markdown(f"""
<div style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 20px;">
    <div style="background-color: rgba(10, 132, 255, 0.85); color: white; border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 20px 20px 4px 20px; padding: 10px 16px; max-width: 75%; box-shadow: 0 8px 20px rgba(10, 132, 255, 0.2); backdrop-filter: blur(16px) saturate(180%); -webkit-backdrop-filter: blur(16px) saturate(180%); font-weight: 400;">
        <span style="color: white !important;">{texto}</span>
    </div>
</div>
""", unsafe_allow_html=True)
    else:
        # Burbuja de Neura: Estilo iOS claro (Blanco esmerilado)
        st.markdown(f"""
<div style="display: flex; justify-content: flex-start; width: 100%; margin-bottom: 20px;">
    <div style="background-color: rgba(255, 255, 255, 0.7); color: #1d1d1f; border: 1px solid rgba(255, 255, 255, 0.8); border-radius: 20px 20px 20px 4px; padding: 10px 16px; max-width: 75%; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); backdrop-filter: blur(16px) saturate(180%); -webkit-backdrop-filter: blur(16px) saturate(180%); font-weight: 400;">
        <span style="color: #1d1d1f !important;">{texto}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Imprimir el historial de la conversación
for mensaje in st.session_state.chats[st.session_state.chat_actual]:
    rol_correcto = "assistant" if mensaje["rol"] in ["bot", "assistant", "ia"] else "user"
    renderizar_mensaje(rol_correcto, mensaje["texto"])

# --- 5. LÓGICA DE ENVÍO ---
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    # Mostramos mensaje nuevo del usuario al instante
    renderizar_mensaje("user", prompt)
    st.session_state.chats[st.session_state.chat_actual].append({"rol": "user", "texto": prompt})
    
    # Preparamos el historial para Groq
    mensajes_api = [{"role": "system", "content": instrucciones}]
    for m in st.session_state.chats[st.session_state.chat_actual][-5:]:
        rol_api = "assistant" if m["rol"] in ["bot", "assistant", "ia"] else "user"
        mensajes_api.append({"role": rol_api, "content": m["texto"]})
    
    if archivo_subido is not None:
        texto_archivo = archivo_subido.read().decode('utf-8')
        mensajes_api[-1]["content"] = f"{prompt}\n\n[Archivo adjunto:]\n{texto_archivo}"

    # IA procesando
    with st.spinner("Procesando..."):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=mensajes_api
            )
            respuesta_texto = response.choices[0].message.content
            
            # Mostrar respuesta de Neura
            renderizar_mensaje("assistant", respuesta_texto)
            st.session_state.chats[st.session_state.chat_actual].append({"rol": "assistant", "texto": respuesta_texto})
            
            # Rotamos la clave
            st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
            
        except Exception as e:
            st.error("⚠️ Fallo en la conexión o cuota agotada. Cambiando de servidor... Por favor, vuelve a enviar tu mensaje.")
            st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
