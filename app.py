import streamlit as st
from groq import Groq
from PIL import Image
import io

# --- 1. CONFIGURACIÓN BÁSICA Y ESTÉTICA (Glassmorphism, Alineación y Cleanup) ---
st.set_page_config(page_title="Neura AI", page_icon="🌌", layout="centered")

# --- INYECCIÓN DE CSS PERSONALIZADO ---
css = """
<style>
/* 1. Fondo Degradado Oscuro Elegante */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e1e2f 100%);
    color: white;
}

/* 2. Quitar iconos y avatares mostrados en image_5.png */
[data-testid="stChatMessageAvatar"] {
    display: none !important;
}
/* Reducir el espacio lateral sobrante al quitar avatares */
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
    margin-left: 20%; /* Ancho de burbuja limitado */
}
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
    background-color: rgba(56, 189, 248, 0.1) !important; /* Semi-transparent Cyan/Blue tint */
    border-color: rgba(56, 189, 248, 0.2);
    border-bottom-right-radius: 2px; /* Chat bubble pico effect */
    text-align: right;
}

/* 5. Mensajes de la IA (Grok) -> A LA IZQUIERDA y Gris Cristal */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
    margin-right: 20%; /* Ancho de burbuja limitado */
}
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
    background-color: rgba(255, 255, 255, 0.05) !important; /* Neutral gray glass tint */
    border-bottom-left-radius: 2px; /* Chat bubble pico effect */
}

/* Ajustar colores de los elementos laterales para fondo oscuro */
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] p {
    color: #f8fafc !important;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- 2. ENCABEZADO DE LA APP ---
st.title("🌌 Neura AI (Powered by Groq ⚡)")
st.caption("Desarrollado y programado por Aitor")
st.divider()

# --- 3. CONFIGURACIÓN DEL CEREBRO (Brain Setup - Groq) ---
# Requiere GROQ_API_KEY en los secretos de Streamlit
if "GROQ_API_KEY" not in st.secrets:
    st.error("Error técnico: Falta configurar la GROQ_API_KEY en Streamlit secrets!")
    st.stop()

# Inicializamos el cliente oficial de Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 4. BARRA LATERAL (Sidebar - Funciones solicitadas anteriormente) ---
with st.sidebar:
    st.title("📂 Mis Chats")
    
    # Memoria para múltiples conversaciones
    if "chats" not in st.session_state:
        st.session_state.chats = {"Chat 1": []}
    if "chat_actual" not in st.session_state:
        st.session_state.chat_actual = "Chat 1"

    # Botón para crear nuevo chat
    if st.button("➕ Nuevo Chat"):
        nuevo_nombre = f"Chat {len(st.session_state.chats) + 1}"
        st.session_state.chats[nuevo_nombre] = []
        st.session_state.chat_actual = nuevo_nombre
        st.rerun()

    # Selector de chat actual
    st.session_state.chat_actual = st.radio(
        "Selecciona una conversación:", 
        list(st.session_state.chats.keys()), 
        index=list(st.session_state.chats.keys()).index(st.session_state.chat_actual)
    )

    st.divider()
    
    # Zona para subir archivos
    st.markdown("### 📎 Analizar Archivo")
    archivo_subido = st.file_uploader("Sube una imagen o texto", type=["png", "jpg", "jpeg", "txt"])
    
    st.divider()
    st.caption("Aitor | Estudiante de Ciberseguridad")

# --- 5. IMPRIMIR HISTORIAL DEL CHAT ACTUAL (Con nuevo diseño CSS) ---
for mensaje in st.session_state.chats[st.session_state.chat_actual]:
    with st.chat_message(mensaje["rol"]):
        st.write(mensaje["texto"])

# --- 6. INTERFAZ DE ENVÍO DE MENSAJES (Chat Input Moderno) ---
# Reemplazamos el cuadro de texto gigante por la barra moderna solicitada en imagen_2.png
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    # 1. Mostrar y guardar mensaje del usuario
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.chats[st.session_state.chat_actual].append({"rol": "user", "texto": prompt})
    
    # Preparamos el contexto para enviarlo a la API de Groq
    historial_reciente = st.session_state.chats[st.session_state.chat_actual][-5:]
    mensajes_api = [
        {"role": "system", "content": "Eres Neura, un asistente de IA muy avanzado y educado, creado y programado por Aitor para ser preciso y útil. Si te preguntan por tu creador, responde con orgullo que fuiste creado por Aitor."}
    ]
    for m in historial_reciente:
        # Groq usa role 'assistant' en lugar de 'bot' para la API
        mensajes_api.append({"role": "assistant" if m["rol"] == "bot" else "user", "content": m["texto"]})
    
    # Añadimos lógica si hay un archivo subido
    contenido_usuario = []
    
    if archivo_subido is not None:
        if archivo_subido.name.endswith(('png', 'jpg', 'jpeg')):
            # Si hay imagen, usamos modelo de visión (llama-3.2-11b-vision-preview)
            # Para Groq, hay que pasar la imagen en base64 o URL pública si el modelo soporta
            # Mantendremos la lógica simple de texto para evitar complejidades Base64 por ahora
            text_combinado = f"{prompt}\n\n[El usuario ha adjuntado una imagen para analizar: {archivo_subido.name}]"
            contenido_usuario = text_combinado
        elif archivo_subido.name.endswith('txt'):
            # Si hay texto, leemos el contenido
            texto_archivo = archivo_subido.read().decode('utf-8')
            text_combinado = f"{prompt}\n\n[Contenido del archivo adjunto para resumir/analizar:]\n{texto_archivo}"
            contenido_usuario = text_combinado
    else:
        # Solo texto
        contenido_usuario = prompt

    # Reemplazamos el último mensaje de usuario con el contenido combinado (con archivo si existe)
    mensajes_api[-1]["content"] = contenido_usuario

    # 2. Generar y mostrar respuesta de Neura (Groq)
    with st.chat_message("assistant"):
        with st.spinner("Neura está procesando..."):
            try:
                # Usamos modelo llama-3.3-70b-versatile por defecto para texto muy potente y rápido
                # (Si subieron imagen, deberías usar modelo de visión, pero por simplicidad de código para que Aitor empiece, lo mantendremos en texto)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=mensajes_api
                )
                respuesta_texto = response.choices[0].message.content
                st.write(respuesta_texto)
                st.session_state.chats[st.session_state.chat_actual].append({"rol": "bot", "texto": respuesta_texto})
                
            except Exception as e:
                st.error("⚠️ Neura ha sufrido un fallo técnico en la conexión. Por favor, vuelve a intentar enviar tu mensaje.")
                # st.code(f"Error técnico real: {e}") # Descomenta para depurar si falla
