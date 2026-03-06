import streamlit as st
from groq import Groq

# --- 1. CONFIGURACIÓN BÁSICA Y ESTÉTICA (Liquid Glass Morado Adaptativo) ---
st.set_page_config(page_title="Neura AI", layout="wide")

st.markdown("""
<style>
/* Capa morada semitransparente que se mezcla con el fondo nativo de Streamlit */
.stApp {
    background-image: linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(88, 28, 135, 0.3) 100%) !important;
}

/* --- PANEL LATERAL (Responsive + Animaciones) --- */
[data-testid="stSidebar"] {
    background-color: rgba(126, 34, 206, 0.05) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(168, 85, 247, 0.2) !important;
    /* Animación fluida al abrir/cerrar el panel */
    transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), width 0.4s ease-in-out, min-width 0.4s ease-in-out !important;
}

/* Resoluciones de ordenador (Desktop): Auto-ajustable con "clamp" */
@media (min-width: 768px) {
    [data-testid="stSidebar"] {
        /* Se adapta dinámicamente: mínimo 280px, ideal 25% de la pantalla, máximo 380px */
        width: clamp(280px, 25vw, 380px) !important;
        min-width: clamp(280px, 25vw, 380px) !important;
    }
}

/* --- BOTONES DE CHAT (Estirados y con animación hover) --- */
[data-testid="stRadio"] > label {
    display: none !important;
}

div[data-testid="stRadio"],
div[data-testid="stRadio"] > div,
div[data-testid="stRadio"] div[role="radiogroup"] {
    width: 100% !important;
    max-width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important; 
}

div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {
    display: none !important; 
}

div[data-testid="stRadio"] div[role="radiogroup"] label {
    background-color: rgba(255, 255, 255, 0.05) !important;
    padding: 12px 15px !important;
    border-radius: 12px !important;
    margin-bottom: 8px !important;
    width: 100% !important; 
    max-width: 100% !important;
    flex: 1 1 100% !important; 
    display: flex !important;
    box-sizing: border-box !important;
    cursor: pointer !important;
    /* Animación suave para los colores y el movimiento */
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    border: 1px solid transparent !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] label div {
    width: 100% !important;
    display: block !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] label p {
    width: 100% !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
    margin: 0 !important;
}

/* Efecto al pasar el ratón: se ilumina y se desliza ligeramente a la derecha */
div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
    background-color: rgba(168, 85, 247, 0.15) !important;
    transform: translateX(4px); 
}

/* Chat seleccionado */
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
    background-color: rgba(168, 85, 247, 0.3) !important;
    border: 1px solid rgba(168, 85, 247, 0.5) !important;
    box-shadow: 0 2px 10px rgba(168, 85, 247, 0.1) !important;
}

/* --- CAJA DE INPUT DE TEXTO (Con animación al escribir) --- */
.stChatInputContainer {
    background-color: rgba(168, 85, 247, 0.05) !important;
    backdrop-filter: blur(16px) !important;
    border-radius: 20px !important;
    border: 1px solid rgba(168, 85, 247, 0.3) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
    transition: all 0.3s ease-in-out !important;
}

/* Se ilumina cuando haces clic para escribir */
.stChatInputContainer:focus-within {
    border: 1px solid rgba(168, 85, 247, 0.8) !important;
    box-shadow: 0 4px 20px rgba(168, 85, 247, 0.2) !important;
}
</style>
""", unsafe_allow_html=True)

st.title("Neura AI")
st.caption("Desarrollado y programado por Aitor")
st.divider()

# --- 2. SISTEMA DE ROTACIÓN DE API KEYS DINÁMICO ---
# Captura automáticamente cualquier clave que empiece por "GROQ_API_KEY"
api_keys = [val for key, val in st.secrets.items() if key.startswith("GROQ_API_KEY")]

if not api_keys:
    st.error("⚠️ Error técnico: No se encontraron claves API de Groq en los secretos de Streamlit.")
    st.stop()

if "api_index" not in st.session_state:
    st.session_state.api_index = 0

# Asegurarse de que el índice no se salga de rango si se cambian las claves
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
"""

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.title("Mis Chats")
    
    if "chats" not in st.session_state:
        st.session_state.chats = {"Nuevo Chat": []}
    if "chat_actual" not in st.session_state:
        st.session_state.chat_actual = "Nuevo Chat"

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
            st.rerun()
            
    with col2:
        if st.button("Borrar", use_container_width=True):
            if st.session_state.chat_actual in st.session_state.chats:
                del st.session_state.chats[st.session_state.chat_actual]
            
            if not st.session_state.chats:
                st.session_state.chats = {"Nuevo Chat": []}
                
            st.session_state.chat_actual = list(st.session_state.chats.keys())[0]
            st.rerun()

    # Manejo seguro del radio button por si el chat actual fue borrado externamente
    chat_seleccionado = st.session_state.chat_actual if st.session_state.chat_actual in st.session_state.chats else list(st.session_state.chats.keys())[0]
    
    st.session_state.chat_actual = st.radio(
        "Selecciona una conversación:", 
        list(st.session_state.chats.keys()), 
        index=list(st.session_state.chats.keys()).index(chat_seleccionado)
    )

    st.divider()
    st.markdown("### Analizar Archivo")
    archivo_subido = st.file_uploader("Sube texto", type=["txt"])
    
    st.divider()
    st.caption(f"Servidor en uso: {st.session_state.api_index + 1} de {len(api_keys)}")
    st.caption("NeuraAI")

# --- 4. MOTOR GRÁFICO PERSONALIZADO ---
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

# Imprimir el historial de la conversación actual
for mensaje in st.session_state.chats[st.session_state.chat_actual]:
    rol_correcto = "assistant" if mensaje["rol"] in ["bot", "assistant", "ia"] else "user"
    renderizar_mensaje(rol_correcto, mensaje["texto"])

# --- 5. LÓGICA DE ENVÍO Y AUTO-RENOMBRAMIENTO ---
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    es_primer_mensaje = len(st.session_state.chats[st.session_state.chat_actual]) == 0

    renderizar_mensaje("user", prompt)
    st.session_state.chats[st.session_state.chat_actual].append({"rol": "user", "texto": prompt})
    
    mensajes_api = [{"role": "system", "content": instrucciones}]
    # Ampliado a 10 para que Neura tenga mejor memoria a corto plazo
    for m in st.session_state.chats[st.session_state.chat_actual][-10:]:
        rol_api = "assistant" if m["rol"] in ["bot", "assistant", "ia"] else "user"
        mensajes_api.append({"role": rol_api, "content": m["texto"]})
    
    # Solución al bug del puntero de lectura de archivos
    if archivo_subido is not None:
        archivo_subido.seek(0) # Reinicia la lectura para no enviar textos vacíos en el segundo prompt
        texto_archivo = archivo_subido.read().decode('utf-8')
        mensajes_api[-1]["content"] = f"{prompt}\n\n[Archivo adjunto:]\n{texto_archivo}"

    with st.spinner("Procesando..."):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=mensajes_api
            )
            respuesta_texto = response.choices[0].message.content
            
            renderizar_mensaje("assistant", respuesta_texto)
            st.session_state.chats[st.session_state.chat_actual].append({"rol": "assistant", "texto": respuesta_texto})
            
            st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)

            # Lógica de renombramiento automático
            if es_primer_mensaje:
                nuevo_titulo = prompt[:20] + "..." if len(prompt) > 20 else prompt
                base_titulo = nuevo_titulo
                contador_titulo = 1
                
                # Evitar colisiones de nombres
                while nuevo_titulo in st.session_state.chats and nuevo_titulo != st.session_state.chat_actual:
                    nuevo_titulo = f"{base_titulo} ({contador_titulo})"
                    contador_titulo += 1
                
                # Reconstruir el diccionario manteniendo el orden
                st.session_state.chats = {
                    (nuevo_titulo if k == st.session_state.chat_actual else k): v 
                    for k, v in st.session_state.chats.items()
                }
                st.session_state.chat_actual = nuevo_titulo
                st.rerun()
            
        except Exception as e:
            st.error(f"⚠️ Error: {e}. Cambiando de servidor...")
            st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
