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
if not st.session_state.cedula:
    st.title("📺 Receptor TDA - Unetrans")
    ced = st.text_input("Ingrese su Cédula para sintonizar:")
    if st.button("CONECTAR"):
        if ced in df_est['cedula'].values:
            st.session_state.cedula = ced
            st.rerun()
        else:
            st.error("Cédula no registrada en el búnker.")
else:
    # EL ESTUDIANTE YA ESTÁ LOGUEADO
    # --- BLOQUE DE SINTONÍA DEL ALUMNO ---
    try:
        # 1. Intentamos leer la hoja CONTROL con ttl=0
        df_ctrl = conn.read(worksheet="CONTROL", ttl=0)
        
        if df_ctrl is not None and not df_ctrl.empty:
            # 2. Extraemos los datos (Asegúrate que los nombres coincidan con el Excel)
            # Usamos .iloc[0] para ver la primera fila de datos
            id_act = int(df_ctrl.iloc[0]['id_activa'])
            estado = str(df_ctrl.iloc[0]['estado']).strip()
            t_ini = float(df_ctrl.iloc[0]['inicio'])
            t_aire = time.time() - t_ini
            
            # 3. Verificamos si la señal es válida
            if estado == "ACTIVA" and t_aire < 60:
                st.warning(f"⚠️ ¡PREGUNTA EN EL AIRE! (Q#{id_act})")
                st.progress(int((60 - t_aire) * 1.66))
                
                # Aquí despliegas el formulario de la pregunta que ya tienes...
                p = df_pre.iloc[id_act]
                with st.form("form_respuesta"):
                    st.write(p['pregunta'])
                    # ... resto de tu código de respuesta ...
                    if st.form_submit_button("ENVIAR"):
                        # lógica de enviar_al_puente
                        st.success("¡Recibido!")
            else:
                st.info("📡 Escaneando... Esperando señal del Prof. Duque.")
        else:
            st.info("📡 El búnker está en silencio (Hoja CONTROL vacía).")

    except Exception as e:
        # Esto es lo que sale en rojo. Vamos a ver qué dice el error.
        st.error(f"Falla de sintonía: {e}")
        st.info("Sugerencia: El Prof. debe pulsar 'LANZAR PREGUNTA' para inicializar.")
