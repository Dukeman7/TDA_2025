import streamlit as st
import pandas as pd
import time
import os
import requests
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="TDA Unetrans - Búnker", layout="wide")

URL_PUENTE = "https://script.google.com/macros/s/AKfycbwTLwwTTOCfhiK-GSz_aF4LUZxiwqV-W3zLqcKzdmbaHSIjg2FDoM6cqIJwy4jK0kFyJQ/exec"
PASS_PROF = "BunkerTDA2024"

# Conexión para lectura (Alumnos)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. FUNCIONES DE COMUNICACIÓN (UpLink) ---
def enviar_al_puente(payload):
    try:
        res = requests.post(URL_PUENTE, json=payload, timeout=10)
        return res.status_code == 200
    except:
        return False

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=600)
def cargar_csvs():
    # Detectamos la ruta donde está parado el archivo app.py
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Armamos la ruta completa a los archivos
    ruta_preguntas = os.path.join(BASE_DIR, "preguntas_tda_50.csv")
    ruta_estudiantes = os.path.join(BASE_DIR, "estudiantes_iut.csv")
    
    # Verificamos si existen antes de intentar leer
    if not os.path.exists(ruta_preguntas):
        st.error(f"❌ No se halló preguntas_tda_50.csv en {BASE_DIR}")
        st.stop()
        
    preguntas = pd.read_csv(ruta_preguntas)
    estudiantes = pd.read_csv(ruta_estudiantes, dtype=str)
    return preguntas, estudiantes

df_pre, df_est = cargar_csvs()

# --- 4. LÓGICA DE SESIÓN ---
if "cedula" not in st.session_state:
    st.session_state.cedula = None

# --- 5. SIDEBAR: PANEL DEL PROFESOR ---
with st.sidebar:
    st.title("📡 Master Control")
    clave = st.text_input("Acceso Maestro:", type="password")
    
    if clave == PASS_PROF:
        st.success("Modo Instructor")
        id_q = st.number_input("ID Pregunta (0-50):", 0, len(df_pre)-1)
        
        if st.button("🚀 LANZAR PREGUNTA"):
            payload = {"tipo": "CONTROL", "id_activa": id_q, "inicio": time.time(), "estado": "ACTIVA"}
            if enviar_al_puente(payload):
                st.toast("¡Señal en el aire!")
                st.balloons()
        
        if st.button("🛑 APAGAR SEÑAL"):
            payload = {"tipo": "CONTROL", "id_activa": 0, "inicio": 0, "estado": "OFF"}
            enviar_al_puente(payload)
            st.info("Transmisor apagado")

# --- 6. CUERPO PRINCIPAL: VISTA ESTUDIANTE ---
# --- REPARACIÓN DE EMERGENCIA ---
try:
    # DEFINIMOS LA URL AQUÍ MISMO PARA QUE NO HAYA PÉRDIDA
    URL_GSHEET = "https://docs.google.com/spreadsheets/d/1hSv4WuKk-1RR4PSjoV7peTGJksPok4PLAw0Wejy9hAM/edit?usp=sharing"
    
    # Forzamos la lectura usando la URL explícita
    df_ctrl = conn.read(spreadsheet=URL_GSHEET, worksheet="CONTROL", ttl=0)
    
    if df_ctrl is not None and not df_ctrl.empty:
        # ... (aquí sigue tu lógica de id_activa, estado, etc.)
        estado = str(df_ctrl.iloc[0]['estado']).strip()
        if estado == "ACTIVA":
            st.warning("⚠️ ¡PREGUNTA EN EL AIRE!")
            # (El resto del formulario...)
        else:
            st.info("📡 Escaneando... Esperando señal del Prof. Duque.")
    else:
        st.info("📡 Conexión establecida. Esperando que el Prof. lance la señal.")

except Exception as e:
    st.error(f"Falla de enlace: {e}")
