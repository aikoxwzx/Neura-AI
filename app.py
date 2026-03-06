import streamlit as st
from groq import Groq

# --- 1. CONFIGURACIÓN BÁSICA Y ESTÉTICA (Liquid Glass Morado Adaptativo) ---
st.set_page_config(page_title="Neura AI", layout="wide")

# CSS para el cristal líquido morado y botones de la barra lateral estirados
st.markdown("""
<style>
/* Capa morada semitransparente que se mezcla con el fondo nativo de Streamlit */
.stApp {
    background-image: linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(88, 28, 135, 0.3) 100%) !important;
}

/* Panel lateral de cristal esmerilado con toque morado */
[data-testid="stSidebar"] {
    background-color: rgba(126, 34, 206, 0.05) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(168, 85, 247, 0.2) !important;
/* ESTAS SON LAS LÍNEAS NUEVAS PARA ENSANCHARLO */
    min-width: 380px !important;
    max-width: 380px !important;
}

/* ------------------------------------------------------------------
   Transformar selectores de chat en bloques largos (Ancho 100%)
   ------------------------------------------------------------------ */
/* Ocultar el título "Selecciona una conversación:" */
[data-testid="stRadio"] > label {
    display: none !important;
}

/* Contenedor del grupo de botones */
[data-testid="stRadio"] div[role="radiogroup"] {
    width: 100% !important;
}

/* Ocultar el círculo nativo (el punto rojo/blanco) */
[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {
    display: none !important; 
}

/* Estilo de la caja base del chat (No seleccionado) - ANCHO TOTAL */
[data-testid="stRadio"] div[role="radiogroup"] label {
    background-color: rgba(255, 255, 255, 0.05) !important;
    padding: 12px 15px !important;
    border-radius: 12px !important;
    margin-bottom: 8px !important;
    width: 100% !important; /* Estira la caja hasta el borde del panel */
    display: flex !important;
    box-sizing: border-box !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    border: 1px solid transparent !important;
}

/* Forzar que el texto interno también ocupe todo el ancho sin romperse */
[data-testid="stRadio"] div[role="radiogroup"] label div {
    width: 100% !important;
}
[data-testid="stRadio"] div[role="radiogroup"] label p {
    width: 100% !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
    margin: 0 !important;
}

/* Efecto al pasar el ratón por encima */
[data-testid="stRadio"] div[role="radiogroup"] label:hover {
    background-color: rgba(168, 85, 247, 0.15) !important;
}

/* Estilo para el chat SELECCIONADO (Activo) */
[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
    background-color: rgba(168, 85, 247, 0.3) !important;
    border: 1px solid rgba(168, 85, 247, 0.5) !important;
    box-shadow: 0 2px 10px rgba(168, 85, 247, 0.1) !important;
}
/* ------------------------------------------------------------------ */

/* Caja de entrada de texto flotante */
.stChatInputContainer {
    background-color: rgba(168, 85, 247, 0.05) !important;
    backdrop-filter: blur(16px) !important;
    border-radius: 20px !important;
    border: 1px solid rgba(168, 85, 247, 0.3) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
}
</style>
""", unsafe_allow_html=True)

st.title("Neura AI")
st.caption("Desarrollado y programado por Aitor")
st.divider()

# --- 2. SISTEMA DE ROTACIÓN DE API KEYS ---
try:
    api_keys = [st.secrets["GROQ_API_KEY_1"], st.secrets["GROQ_API_KEY_2"]]
except KeyError:
    st.error("Error técnico: Faltan GROQ_API_KEY_1 o GROQ_API_KEY_2 en Streamlit Secrets.")
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

# --- 3. BARRA LATERAL (Gestión total de salas de chat) ---
with st.sidebar:
    st.title("Mis Chats")
    
    if "chats" not in st.session_state:
        st.session_state.chats = {"Nuevo Chat": []}
    if "chat_actual" not in st.session_state:
        st.session_state.chat_actual = "Nuevo Chat"

    # Botones en columnas para crear y DESTRUIR chats
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Nuevo", use_container_width=True):
            # Asegurar que el nombre base sea único si se pulsa varias veces seguidas
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
            # Elimina el chat completo del diccionario
            del st.session_state.chats[st.session_state.chat_actual]
            
            # Si se borran todos los chats, crea uno de emergencia
            if len(st.session_state.chats) == 0:
                st.session_state.chats = {"Nuevo Chat": []}
                
            # Salta automáticamente al primer chat disponible
            st.session_state.chat_actual = list(st.session_state.chats.keys())[0]
            st.rerun()

    st.session_state.chat_actual = st.radio(
        "Selecciona una conversación:", 
        list(st.session_state.chats.keys()), 
        index=list(st.session_state.chats.keys()).index(st.session_state.chat_actual)
    )

    st.divider()
    st.markdown("### Analizar Archivo")
    archivo_subido = st.file_uploader("Sube texto", type=["txt"])
    
    st.divider()
    st.caption(f"Servidor en uso: {st.session_state.api_index + 1}")
    st.caption("NeuraAI")

# --- 4. MOTOR GRÁFICO PERSONALIZADO (Burbujas Moradas) ---
def renderizar_mensaje(rol, texto):
    if rol == "user":
        # Burbuja del usuario: Morado vibrante degradado (Estilo iMessage premium)
        st.markdown(f"""
<div style="display: flex; justify-content: flex-end; width: 100%; margin-bottom: 20px;">
    <div style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.9), rgba(109, 40, 217, 0.9)); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px 20px 4px 20px; padding: 10px 16px; max-width: 75%; box-shadow: 0 8px 20px rgba(139, 92, 246, 0.3); backdrop-filter: blur(16px); font-weight: 400;">
        <span style="color: white !important;">{texto}</span>
    </div>
</div>
""", unsafe_allow_html=True)
    else:
        # Burbuja de Neura: Cristal lila transparente (Se adapta al modo claro/oscuro)
        st.markdown(f"""
<div style="display: flex; justify-content: flex-start; width: 100%; margin-bottom: 20px;">
    <div style="background-color: rgba(168, 85, 247, 0.1); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 20px 20px 20px 4px; padding: 10px 16px; max-width: 75%; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); backdrop-filter: blur(16px); font-weight: 400;">
        <span>{texto}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Imprimir el historial de la conversación
for mensaje in st.session_state.chats[st.session_state.chat_actual]:
    rol_correcto = "assistant" if mensaje["rol"] in ["bot", "assistant", "ia"] else "user"
    renderizar_mensaje(rol_correcto, mensaje["texto"])

# --- 5. LÓGICA DE ENVÍO Y AUTO-RENOMBRAMIENTO ---
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    # Verificamos si es el primer mensaje de este chat para renombrarlo luego
    es_primer_mensaje = len(st.session_state.chats[st.session_state.chat_actual]) == 0

    # Mostramos mensaje nuevo del usuario
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

            # Si era el primer mensaje, renombramos el chat actual
            if es_primer_mensaje:
                # Cogemos los primeros 20 caracteres del prompt
                nuevo_titulo = prompt[:20] + "..." if len(prompt) > 20 else prompt
                
                # Evitar nombres duplicados
                base_titulo = nuevo_titulo
                contador_titulo = 1
                while nuevo_titulo in st.session_state.chats and nuevo_titulo != st.session_state.chat_actual:
                    nuevo_titulo = f"{base_titulo} ({contador_titulo})"
                    contador_titulo += 1
                
                # Reconstruimos el diccionario de chats para mantener el orden visual
                nuevos_chats = {}
                for clave, valor in st.session_state.chats.items():
                    if clave == st.session_state.chat_actual:
                        nuevos_chats[nuevo_titulo] = valor
                    else:
                        nuevos_chats[clave] = valor
                
                st.session_state.chats = nuevos_chats
                st.session_state.chat_actual = nuevo_titulo
                
                # Recargamos la interfaz para que aparezca el nuevo nombre en la barra lateral
                st.rerun()
            
        except Exception as e:
            st.error("Fallo en la conexión. Cambiando de servidor... Por favor, vuelve a enviar tu mensaje.")
            st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
