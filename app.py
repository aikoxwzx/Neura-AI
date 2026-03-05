import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuración básica y estética
st.set_page_config(page_title="Chat IA", page_icon="🤖", layout="centered")

st.markdown("""
<style>
[data-testid="stChatMessageAvatar"] { display: none !important; }
[data-testid="stChatMessage"] { background-color: transparent !important; }

/* Mensajes del usuario a la derecha */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
    flex-direction: row-reverse;
    text-align: right;
}
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) .stMarkdown {
    background-color: #007bff15;
    padding: 10px 15px;
    border-radius: 15px;
    border-bottom-right-radius: 0;
    display: inline-block;
}

/* Mensajes de la IA a la izquierda */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) .stMarkdown {
    background-color: #f1f0f0;
    padding: 10px 15px;
    border-radius: 15px;
    border-bottom-left-radius: 0;
    display: inline-block;
    text-align: left;
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
Cada que empiezas un nuevo chat preséntate con tu nombre, Neura.
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
    # Pequeño indicador para saber qué API se está usando (opcional, útil para ti)
    st.caption(f"🔧 API en uso: Servidor {st.session_state.api_index + 1}")

# 4. Historial del chat actual
for mensaje in st.session_state.chats[st.session_state.chat_actual]:
    with st.chat_message(mensaje["rol"]):
        st.write(mensaje["texto"])

# 5. Interfaz de envío de mensajes
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.chats[st.session_state.chat_actual].append({"rol": "user", "texto": prompt})
    
    contenido_a_enviar = [prompt]
    
    if archivo_subido is not None:
        if archivo_subido.name.endswith(('png', 'jpg', 'jpeg')):
            imagen = Image.open(archivo_subido)
            contenido_a_enviar.append(imagen)
        elif archivo_subido.name.endswith('txt'):
            texto_archivo = archivo_subido.read().decode('utf-8')
            contenido_a_enviar.append(f"\n[Contenido del archivo adjunto:]\n{texto_archivo}")

    with st.chat_message("assistant"):
        with st.spinner("Analizando..."):
            try:
                # Intentamos generar la respuesta
                response = model.generate_content(contenido_a_enviar)
                st.write(response.text)
                st.session_state.chats[st.session_state.chat_actual].append({"rol": "assistant", "texto": response.text})
                
                # Si todo sale bien, rotamos la clave para el próximo mensaje
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
                
            except Exception as e:
                # Si la clave actual falla (ej. por límite de uso), avisamos y rotamos inmediatamente
                st.error("⚠️ La cuota de esta API se ha agotado o hubo un error. He cambiado a la clave de respaldo. Por favor, vuelve a enviar tu mensaje.")
                st.session_state.api_index = (st.session_state.api_index + 1) % len(api_keys)
