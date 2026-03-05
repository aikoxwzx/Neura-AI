import streamlit as st
import google.generativeai as genai

# 1. Configuración básica y estética de la página
st.set_page_config(page_title="Chat IA", page_icon="🤖", layout="centered")
st.title("Neura AI")
st.caption("Desarrollado y programado por Aitor") # Un toque profesional
st.divider() # Línea separadora

# 2. Configuración de la API
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# 3. Instrucciones del sistema (Aquí le decimos quién es su creador)
instrucciones = """
Eres un asistente de IA muy útil y educado. 
Fuiste creado, programado y desplegado por Aitor. 
Si cualquier persona te pregunta quién es tu creador, quién te hizo, o de dónde vienes, debes responder siempre con orgullo que fuiste creado por Aitor.
Eres un asistente talentoso que busca ayudar a los demás sea como sea buscando cualquier solución.
Si tienes un error discúlpate y busca una solución si es posible.
Sé buen asistente, saca temas de conversación, pregunta por los demás y haz que te importen sus temas.
No uses emojis.
Fuera de ser majo sé también profesional.
"""

# Inicializamos el modelo con tus instrucciones
model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=instrucciones)

# 4. Memoria del chat (Para que no se borren los mensajes anteriores)
if "historial" not in st.session_state:
    st.session_state.historial = []

# Imprimir los mensajes guardados en la memoria al recargar la página
for mensaje in st.session_state.historial:
    with st.chat_message(mensaje["rol"]):
        st.write(mensaje["texto"])

# 5. Interfaz del chat moderna (Barra inferior)
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    # Mostramos y guardamos lo que escribe el usuario
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.historial.append({"rol": "user", "texto": prompt})
    
    # Generamos, mostramos y guardamos la respuesta de la IA (Sin el cuadro verde)
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            response = model.generate_content(prompt)
            st.write(response.text)
    st.session_state.historial.append({"rol": "assistant", "texto": response.text})
