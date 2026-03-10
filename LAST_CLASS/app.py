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
