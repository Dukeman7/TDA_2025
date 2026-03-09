import requests
import streamlit as st
import pandas as pd
import os
import re
import time
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="UNETRANS: Certificación TDA", page_icon="📡", layout="wide")

# --- 2. CONEXIÓN Y CONSTANTES ---
conn = st.connection("gsheets", type=GSheetsConnection)
URL_PUENTE = "https://script.google.com/macros/s/AKfycbyiq-eYHWP4sJKo1zMBwbB0Nx3XaHw_a4HEtm8dz48w6huJKWq-mwJYDJnp2cpLda5q0A/exec"
PASS_PROF = "BunkerTDA2024" # Contraseña para activar preguntas en vivo

def registrar_en_nube(datos):
    try:
        df_existente = conn.read(spreadsheet=URL_SHEET, ttl=0)
        df_final = pd.concat([df_existente, pd.DataFrame([datos])], ignore_index=True)
        conn.update(spreadsheet=URL_SHEET, data=df_final)
    except Exception as e:
        st.error(f"Error de sincronización: {e}")

# --- 3. CARGA DE DATOS ---
@st.cache_data
def cargar_todo():
    # Obtenemos la ruta de la carpeta donde está este script (app.py)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    ruta_est = os.path.join(BASE_DIR, "estudiantes_iut.csv")
    ruta_pre = os.path.join(BASE_DIR, "preguntas_tda_50.csv")
    
    if not os.path.exists(ruta_est) or not os.path.exists(ruta_pre):
        st.error(f"❌ Error: No se encuentran los archivos en: {BASE_DIR}")
        st.stop()
        
    estudiantes = pd.read_csv(ruta_est, dtype=str)
    preguntas = pd.read_csv(ruta_pre)
    return estudiantes, preguntas

df_est, df_pre = cargar_todo()

# --- 4. GESTIÓN DE ESTADO ---
if 'fase' not in st.session_state:
    st.session_state.update({
        'fase': "login", 'user': None, 'nota_interactiva': 0, 
        'preguntas_vivas': 0, 'bonus': 0, 'inicio_clase': False
    })

# --- 5. PANEL DEL PROFESOR (Hidden) ---
# --- 5. PANEL DEL PROFESOR (Master Control) ---
with st.sidebar:
    st.title("🎮 Panel de Control TDA")
    
    # Llave de acceso para que los alumnos no traviesen el panel
    clave = st.text_input("Clave del Profesor:", type="password")
    
    if clave == "BunkerTDA2024":
        st.success("Conexión Maestra Activa")
        
        # Selector de la pregunta (basado en tu CSV de preguntas)
        id_q = st.number_input("Seleccione ID de Pregunta (0-50):", 0, 50, key="selector_maestro")
        
        # BOTÓN DE DISPARO (LANZAR)
        if st.button("🚀 LANZAR PREGUNTA AL AIRE"):
            payload = {
                "id_activa": int(id_q),
                "inicio": time.time(),
                "estado": "ACTIVA"
            }
            try:
                # Aquí es donde ocurre la magia: enviamos al Apps Script
                envio = requests.post(URL_PUENTE, json=payload, timeout=10)
                if envio.status_code == 200:
                    st.toast("¡Señal transmitida con éxito!", icon="📡")
                    st.balloons()
                else:
                    st.error("Error: El repetidor no respondió.")
            except Exception as e:
                st.error(f"Falla de red: {e}")

        # BOTÓN DE APAGADO (RESET)
        if st.button("🛑 APAGAR SEÑAL"):
            payload_off = {"id_activa": 0, "inicio": 0, "estado": "OFF"}
            requests.post(URL_PUENTE, json=payload_off)
            st.info("Transmisor en Standby")

# --- 6. FLUJO ESTUDIANTE ---
if st.session_state.fase == "login":
    st.title("📡 Sistema de Certificación TDA - UNETRANS")
    ced = st.text_input("Cédula de Identidad:")
    if st.button("Ingresar al Búnker"):
        match = df_est[df_est['cedula'] == ced]
        if not match.empty:
            st.session_state.user = match.iloc[0].to_dict()
            st.session_state.fase = "diagnostico"
            st.rerun()

elif st.session_state.fase == "diagnostico":
    st.header("📝 Evaluación Diagnóstica")
    st.info("Responda estas 10 preguntas para medir su conocimiento previo.")
    if 'pool_diag' not in st.session_state:
        st.session_state.pool_diag = df_pre.sample(10).to_dict('records')
    
    with st.form("diag"):
        resps = []
        for i, p in enumerate(st.session_state.pool_diag):
            st.write(f"{i+1}. {p['pregunta']}")
            resps.append(st.radio("Opciones:", [p['a'], p['b'], p['c'], p['d']], key=f"d{i}"))
        
        if st.form_submit_button("Enviar Diagnóstico"):
            # Cálculo rápido de nota inicial
            st.session_state.fase = "espera_clase"
            st.rerun()

elif st.session_state.fase == "espera_clase":
    st.title(f"📱 Clase en Vivo: {st.session_state.user['nombre']}")
    st.markdown("### Esperando que el Prof. Duque habilite una pregunta...")
    
    # Simulación de escucha de pregunta activa
    if hasattr(st.session_state, 'q_viva') and st.session_state.q_viva:
        tiempo_restante = 60 - (time.time() - st.session_state.start_timer)
        if tiempo_restante > 0:
            st.warning(f"⏳ TIEMPO RESTANTE: {int(tiempo_restante)}s")
            p = df_pre.iloc[st.session_state.active_q]
            st.subheader(p['pregunta'])
            resp = st.radio("Tu respuesta:", [p['a'], p['b'], p['c'], p['d']], key=f"live_{st.session_state.preguntas_vivas}")
            if st.button("Enviar Respuesta"):
                # Validar y sumar nota
                letra_user = chr(97 + [p['a'], p['b'], p['c'], p['d']].index(resp))
                if letra_user == p['correcta'].strip().lower():
                    st.session_state.nota_interactiva += 1
                st.session_state.preguntas_vivas += 1
                st.session_state.q_viva = False
                st.success("Respuesta capturada.")
                if st.session_state.preguntas_vivas >= 7:
                    st.session_state.fase = "bonus"
                st.rerun()
        else:
            st.session_state.q_viva = False
            st.error("Tiempo agotado.")

elif st.session_state.fase == "bonus":
    st.title("🎯 Examen Final y Bonus")
    st.write(f"Has completado la clase. Nota acumulada: **{st.session_state.nota_interactiva}/7**")
    if st.button("Tomar Examen de Certificación (Opcional +2 pts)"):
        # Lógica de examen final similar al diagnóstico
        pass
