import streamlit as st
import pandas as pd
import time
import requests
import os

# --- 1. CONFIGURACIÓN Y PARÁMETROS ---
st.set_page_config(page_title="TDA Unetrans - Búnker", layout="wide")

# URL de tu Apps Script (Última versión generada)
URL_PUENTE = "https://script.google.com/macros/s/AKfycbwTLwwTTOCfhiK-GSz_aF4LUZxiwqV-W3zLqcKzdmbaHSIjg2FDoM6cqIJwy4jK0kFyJQ/exec"
# ID de tu Google Sheet
SHEET_ID = "1hSv4WuKk-1RR4PSjoV7peTGJksPok4PLAw0Wejy9hAM"
# Clave del profesor
PASS_PROF = "BunkerTDA2024"

# --- 2. CARGA DE DATOS (CSV LOCALES) ---
@st.cache_data(ttl=600)
def cargar_datos_locales():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    try:
        p_path = os.path.join(BASE_DIR, "preguntas_tda_50.csv")
        e_path = os.path.join(BASE_DIR, "estudiantes_iut.csv")
        df_p = pd.read_csv(p_path)
        df_e = pd.read_csv(e_path, dtype=str)
        return df_p, df_e
    except Exception as e:
        st.error(f"Error cargando archivos base: {e}")
        st.stop()

df_pre, df_est = cargar_datos_locales()

# --- 3. MANEJO DE SESIÓN ---
if "cedula" not in st.session_state:
    st.session_state.cedula = None

# --- 4. PANEL DE CONTROL (PROFESOR) ---
with st.sidebar:
    st.title("📡 Master Control")
    llave = st.text_input("Acceso Maestro:", type="password")
    
    if llave == PASS_PROF:
        st.success("Modo Instructor Activo")
        idx_pregunta = st.number_input("Seleccione ID de Pregunta:", 0, len(df_pre)-1)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 LANZAR"):
                payload = {
                    "tipo": "CONTROL", 
                    "id_activa": int(idx_pregunta), 
                    "inicio": time.time(), 
                    "estado": "ACTIVA"
                }
                requests.post(URL_PUENTE, json=payload)
                st.balloons()
        with col2:
            if st.button("🛑 APAGAR"):
                payload = {"tipo": "CONTROL", "id_activa": 0, "inicio": 0, "estado": "OFF"}
                requests.post(URL_PUENTE, json=payload)
                st.info("Señal apagada")

# --- 5. INTERFAZ DE ESTUDIANTES ---
if not st.session_state.cedula:
    st.title("📺 Receptor TDA - Unetrans")
    ced_ingresada = st.text_input("Cédula del Estudiante:").strip()
    if st.button("SINTONIZAR"):
        if ced_ingresada in df_est['cedula'].values:
            st.session_state.cedula = ced_ingresada
            st.rerun()
        else:
            st.error("Cédula no registrada en el búnker.")
else:
    # Identificamos al alumno
    nombre_est = df_est[df_est['cedula'] == st.session_state.cedula].iloc[0]['nombre']
    st.write(f"👤 Estudiante: **{nombre_est}** | Cédula: **{st.session_state.cedula}**")

    # --- LECTURA DE SEÑAL DESDE EL GOOGLE SHEET ---
    try:
        # Bypass directo vía CSV para evitar Error 400
        url_lectura = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=CONTROL"
        df_ctrl = pd.read_csv(url_lectura)
        
        # Limpiamos nombres de columnas (Pandas a veces agrega espacios)
        df_ctrl.columns = [c.lower().strip() for c in df_ctrl.columns]
        
        if not df_ctrl.empty:
            mando = df_ctrl.iloc[0]
            estado_actual = str(mando['estado']).strip()
            
            if estado_actual == "ACTIVA":
                id_q = int(mando['id_activa'])
                t_inicio = float(mando['inicio'])
                t_restante = 60 - (time.time() - t_inicio)
                
                if t_restante > 0:
                    st.warning(f"⚠️ PREGUNTA #{id_q} EN EL AIRE")
                    st.progress(int(t_restante * 1.66), text=f"Tiempo restante: {int(t_restante)}s")
                    
                    # BUSCAR Y MOSTRAR PREGUNTA
                    p = df_pre.iloc[id_q]
                    with st.form("form_examen"):
                        st.subheader(p['pregunta'])
                        opciones = [p['a'], p['b'], p['c'], p['d']]
                        respuesta_chamo = st.radio("Seleccione la correcta:", opciones)
                        
                        if st.form_submit_button("📡 ENVIAR RESPUESTA AL BÚNKER"):
                            # PAQUETE DE RETORNO
                            paquete = {
                                "tipo": "RESPUESTA",
                                "cedula": str(st.session_state.cedula),
                                "id_activa": int(id_q),
                                "respuesta": str(respuesta_chamo)
                            }
                            # Envío vía POST al Apps Script
                            try:
                                res = requests.post(URL_PUENTE, json=paquete, timeout=10)
                                if res.status_code == 200:
                                    st.success("✅ ¡Recibido! Tu respuesta está en el búnker.")
                                else:
                                    st.error("❌ Error de retorno. Intenta de nuevo.")
                            except:
                                st.error("❌ Falla de conexión con el búnker.")
                else:
                    st.info("⌛ La señal expiró. Esperando nueva ráfaga del profesor.")
            else:
                st.info("📡 Escaneando... Esperando señal del Prof. Duque.")
        
    except Exception as e:
        st.error(f"Falla de sintonía: {e}")

    if st.button("🔄 RE-SINCRONIZAR"):
        st.rerun()
