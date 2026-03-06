import streamlit as st
from groq import Groq
from PIL import Image
import base64
import io

# 1. Configuración básica y estética
st.set_page_config(page_title="Neura AI", page_icon="🌌", layout="centered")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%);
    color: white;
}
[data-testid="stChatMessageAvatar"] { display: none !important; }
.stChatMessage { gap: 0rem !important; }

[data-testid="stChatMessageContent"] {
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    color: #e2e8f0 !important;
}

div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
    flex-direction: row-reverse;
}
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stChatMessageContent"] {
    background: rgba(56, 189, 248, 0.1) !important; 
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    border-radius: 20px 20px 0px 20px;
    margin-left: auto;
    max-width: 80%;
}

div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
    flex-direction: row;
}
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) div[data-testid="stChatMessageContent"] {
    border-radius: 20px 20px 20px 0px;
    margin-right: auto;
    max-width: 80%;
}
h1, h2, h3, p, span { color: #f8fafc !important; }
</style>
""", unsafe_allow_html=True)

st.title("🌌 Neura AI (Powered by Groq ⚡)")
st.caption("Desarrollado y programado por Aitor")
st.divider()

# 2. SISTEMA DE ROTACIÓN DE API KEYS PARA GROQ
api_keys = [st.secrets["GROQ_API_KEY_1"], st.secrets["GROQ_API_KEY_2"]]

if "api_index" not in st.session_state:
    st.session_state.api_index = 0

clave_actual = api_keys[st.session_state.api_index]

# Inicializamos el cliente de Groq
client = Groq(api_key=clave_actual)

instrucciones = """
Eres un asistente de IA muy útil y educado. 
Fuiste creado, programado y desplegado por Aitor. 
Si cualquier persona te pregunta quién es tu creador, quién te hizo, o de dónde vienes, debes responder siempre con orgullo que fuiste creado por Aitor.
Eres un asistente talentoso que busca ayudar a los demás sea como sea buscando cualquier solución.
Si tienes un error discúlpate y busca una solución si es posible.
Sé buen asistente, saca temas de conversación, pregunta por los demás y haz que te importen sus temas.
No uses emojis.
Fuera de ser majo sé también profesional.
No digas tu nombre en todos los chats, los usuarios ya lo saben.
Tienes que ser preciso si te preguntan alguna fecha o cualquier otra cosa, tienes que estar actualizado.
No digas quien te ha creado a no ser que te lo pregunten.
"""

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
    st.caption(f"⚡ Motor de Inferencia: Groq LPU")
    st.caption(f"🔧 API en uso: Servidor {st.session_state.api_index + 1}")

# 4. Historial del chat actual
for mensaje in st.session_state.chats[st.session_state.chat_actual]:
    with st.chat_message(mensaje["role"]):
        st.write(mensaje["content"])

# 5. Interfaz de envío de mensajes
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    # Mostramos y guardamos el mensaje del usuario
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.chats[st.session_state.chat_actual].append({"role": "user", "content": prompt})
    
    # Preparamos el historial para Groq
    mensajes_api = [{"role": "system", "content": instrucciones}]
    
    # Cargar historial
    for m in st.session_state.chats[st.session_state.chat_actual][:-1]:
        mensajes_api.append({"role": m["role"], "content": m["content"]})
        
    # Variables de procesamiento
    contenido_usuario = []
    modelo_a_usar = "llama-3.3-70b-versatile" # Modelo por defecto para texto (muy potente)
    
    if archivo_subido is not None:
        if archivo_subido.name.endswith(('png', 'jpg', 'jpeg')):
            # Si hay imagen, cambiamos al modelo de visión de Llama 3.2
            modelo_a_usar = "llama-3.2-11b-vision-preview"
            
            imagen = Image.open(archivo_subido)
            buffered = io.BytesIO()
            imagen.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            contenido_usuario.append({"type": "text", "text": prompt})
            contenido_usuario.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
            })
        elif archivo_subido.name.endswith('txt'):
            texto_archivo = archivo_subido.read().decode('utf-8')
            texto_combinado = f"{prompt}\n\n[Contenido del archivo adjunto:]\n{texto_archivo}"
            contenido_usuario = texto_combinado
    else:
        contenido_usuario = prompt

    mensajes_api.append({"role": "user", "content": contenido_usuario})

    # Respuesta de Groq
    with st.chat_message("assistant"):
        with st.spinner("Procesando a la velocidad de la luz..."):
            try:
                response = client.chat.completions.create(
                    model=modelo_a_usar,
                    messages=mensajes_api
                )
                
                respuesta_texto = response.choices[0].message.content
                st.write(respuesta_texto)
                st.session_state.chats[st.session_state.chat_actual].append({"role": "assistant", "content": respuesta_texto})
                
                # Rotamos la clave
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
                
            except Exception as e:
                st.error("⚠️ Hubo un error de conexión con Groq. Cambiando de servidor...")
                st.code(f"Error técnico: {e}")
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
from PIL import Image

# 1. Configuración básica y estética
st.set_page_config(page_title="Neura AI", page_icon="🌌", layout="centered")

# --- INYECCIÓN DE CSS: DISEÑO PROFESIONAL SIN AVATARES ---
st.markdown("""
<style>
/* Ocultar las fotos de perfil / iconos completamente */
[data-testid="stChatMessageAvatar"] { display: none !important; }

/* Hacer el fondo de la fila transparente */
[data-testid="stChatMessage"] { background-color: transparent !important; }

/* ----------------------------------------------------
   MENSAJES DEL USUARIO (Alineados a la derecha)
   ---------------------------------------------------- */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
    flex-direction: row-reverse;
}

div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stChatMessageContent"] {
    background-color: #007bff15; /* Azul claro */
    padding: 10px 15px;
    border-radius: 15px 15px 0px 15px; /* Pico apuntando a la derecha */
    max-width: 80%;
    margin-left: auto; /* Obliga a la burbuja a ir a la derecha */
}

/* ----------------------------------------------------
   MENSAJES DE LA IA (Alineados a la izquierda)
   ---------------------------------------------------- */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
    flex-direction: row;
}

div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) div[data-testid="stChatMessageContent"] {
    background-color: #f1f0f0; /* Gris claro */
    padding: 10px 15px;
    border-radius: 15px 15px 15px 0px; /* Pico apuntando a la izquierda */
    max-width: 80%;
    margin-right: auto; /* Obliga a la burbuja a ir a la izquierda */
}
</style>
""", unsafe_allow_html=True)

st.title("Neura AI")
st.caption("Desarrollado y programado por Aitor")
st.divider()

# 2. SISTEMA DE ROTACIÓN DE API KEYS (Load Balancing)
api_keys = [st.secrets["GEMINI_API_KEY_1"], st.secrets["GEMINI_API_KEY_2"]]

if "api_index" not in st.session_state:
    st.session_state.api_index = 0

# Configuramos la IA con la clave que toque en este turno
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
No digas tu nombre en todos los chats, los usuarios ya lo saben.
Tienes que ser preciso si te preguntan alguna fecha o cualquier otra cosa, tienes que estar actualizado.
No digas quien te ha creado a no ser que te lo pregunten.
"""

model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=instrucciones)

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
    st.caption(f"🔧 API en uso: Servidor {st.session_state.api_index + 1}")

# 4. Historial del chat actual
for mensaje in st.session_state.chats[st.session_state.chat_actual]:
    with st.chat_message(mensaje["rol"]):
        st.write(mensaje["texto"])

# 5. Interfaz de envío de mensajes
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    # Mensaje del usuario
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.chats[st.session_state.chat_actual].append({"rol": "user", "texto": prompt})
    
    contenido_a_enviar = [prompt]
    
    # Procesamiento de archivos adjuntos
    if archivo_subido is not None:
        if archivo_subido.name.endswith(('png', 'jpg', 'jpeg')):
            imagen = Image.open(archivo_subido)
            contenido_a_enviar.append(imagen)
        elif archivo_subido.name.endswith('txt'):
            texto_archivo = archivo_subido.read().decode('utf-8')
            contenido_a_enviar.append(f"\n[Contenido del archivo adjunto:]\n{texto_archivo}")

    # Respuesta de la IA con manejo de errores y rotación de API
    with st.chat_message("assistant"):
        with st.spinner("Analizando..."):
            try:
                response = model.generate_content(contenido_a_enviar)
                st.write(response.text)
                st.session_state.chats[st.session_state.chat_actual].append({"rol": "assistant", "texto": response.text})
                
                # Rotamos la clave para el próximo mensaje si todo va bien
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
                
            except Exception as e:
                st.error("⚠️ Hubo un error o la cuota se agotó. Cambiando de servidor... Por favor, vuelve a enviar tu mensaje.")
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
