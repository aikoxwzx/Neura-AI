import streamlit as st
import google.generativeai as genai

# Configuración básica de la página
st.set_page_config(page_title="Chatbot de IA", page_icon="🤖")
st.title("🤖 Chatbot Inteligente")
st.write("¡Bienvenido! Pregúntame lo que quieras.")

# Aquí pones tu clave directamente en el código (como tu amigo)
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash',)

# Configuramos la IA
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# Interfaz del chat
prompt = st.text_area("Escribe tu mensaje aquí:")

if st.button("Enviar"):
    if prompt:
        with st.spinner("Pensando..."):
            response = model.generate_content(prompt)
            st.success("¡Respuesta lista!")
            st.write(response.text)
    else:
        st.warning("Por favor, escribe algo primero.")
