import streamlit as st
import pandas as pd
import time
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
    # Asegúrate de que estos archivos estén en tu GitHub
    preguntas = pd.read_csv("preguntas_tda_50.csv")
    estudiantes = pd.read_csv("estudiantes_iut.csv", dtype=str)
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
    nombre = df_est[df_est['cedula'] == st.session_state.cedula]['nombre'].values[0]
    st.write(f"👤 Estudiante: **{nombre}**")

    # LECTURA DE LA SEÑAL (Sincronismo)
    try:
        df_ctrl = conn.read(worksheet="CONTROL", ttl=0)
        if not df_ctrl.empty and df_ctrl.iloc[0]['estado'] == "ACTIVA":
            id_act = int(df_ctrl.iloc[0]['id_activa'])
            t_ini = float(df_ctrl.iloc[0]['inicio'])
            t_aire = time.time() - t_ini
            
            if t_aire < 60:
                st.warning(f"⚠️ ¡PREGUNTA EN EL AIRE! (Q#{id_act})")
                st.progress(int((60 - t_aire) * 1.66), text=f"Tiempo: {int(60-t_ini)}s")
                
                # Formulario de Respuesta
                p = df_pre.iloc[id_act]
                with st.form("examen_tda"):
                    st.markdown(f"### {p['pregunta']}")
                    opc = st.radio("Seleccione:", [p['a'], p['b'], p['c'], p['d']])
                    if st.form_submit_button("📡 ENVIAR RESPUESTA"):
                        payload_resp = {
                            "tipo": "RESPUESTA",
                            "cedula": st.session_state.cedula,
                            "id_activa": id_act,
                            "respuesta": opc
                        }
                        if enviar_al_puente(payload_resp):
                            st.success("¡Respuesta grabada en el búnker!")
                        else:
                            st.error("Falla de retorno.")
            else:
                st.info("⌛ Señal expirada. Esperando nueva ráfaga...")
        else:
            st.info("📡 Escaneando espectro... Esperando al Prof. Duque.")
            
    except:
        st.error("Buscando portadora...")

    if st.button("🔄 RE-SINCRONIZAR"):
        st.rerun()
