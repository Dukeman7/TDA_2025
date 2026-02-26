import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="IUT-RC: Certificación TDA", page_icon="📡")

# --- 2. CARGA DE DATOS ---
@st.cache_data
def cargar_estudiantes():
    if os.path.exists("iut_mission/estudiantes_iut.csv"):
        df = pd.read_csv("iut_mission/estudiantes_iut.csv", dtype=str)
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    return pd.DataFrame(columns=['nombre', 'cedula'])

@st.cache_data
def cargar_preguntas():
    if os.path.exists("iut_mission/preguntas_tda.csv"):
        return pd.read_csv("iut_mission/preguntas_tda.csv")
    return pd.DataFrame()

# --- 3. GESTIÓN DE ESTADO (SESIÓN) ---
if 'paso' not in st.session_state:
    st.session_state.paso = "identificacion" # identificación | examen | resultado
    st.session_state.nombre = ""
    st.session_state.cedula = ""

df_estudiantes = cargar_estudiantes()
df_preguntas = cargar_preguntas()

# --- 4. INTERFAZ POR PASOS ---

# PASO 1: IDENTIFICACIÓN RÍGIDA
if st.session_state.paso == "identificacion":
    st.title("📡 Acceso al Sistema de Evaluación")
    ced_input = st.text_input("Ingrese su Cédula (Solo números):", placeholder="Ej: 87654321")
    
    if st.button("Validar Identidad"):
        c_limpia = re.sub(r"\D", "", ced_input)
        match = df_estudiantes[df_estudiantes['cedula'].str.strip() == c_limpia]
        
        if not match.empty:
            st.session_state.nombre = match.iloc[0]['nombre'].title()
            st.session_state.cedula = c_limpia
            st.session_state.paso = "examen"
            st.rerun()
        else:
            st.error("⚠️ Cédula no registrada en la cátedra del Prof. Duque")

# PASO 2: EL EXAMEN (BLOQUEADO)
elif st.session_state.paso == "examen":
    st.header("Examen de TV Digital Abierta")
    st.info(f"Bachiller: **{st.session_state.nombre}** | Cédula: **{st.session_state.cedula}**")
    
    if 'preguntas_examen' not in st.session_state:
        st.session_state.preguntas_examen = df_preguntas.sample(min(5, len(df_preguntas))).to_dict('records')

    with st.form("quiz"):
        respuestas = []
        for i, p in enumerate(st.session_state.preguntas_examen):
            st.write(f"**{i+1}. {p['pregunta']}**")
            opciones = [p['a'], p['b'], p['c'], p['d']]
            resp = st.radio(f"Seleccione:", opciones, key=f"q{i}", index=None)
            respuestas.append(resp)

        if st.form_submit_button("FINALIZAR EVALUACIÓN"):
            if None in respuestas:
                st.warning("⚠️ Debe contestar todas las preguntas.")
            else:
                # Calcular nota
                aciertos = 0
                for i, p in enumerate(st.session_state.preguntas_examen):
                    letra_correcta = p['correcta'].strip().lower()
                    # Convertir respuesta seleccionada a letra (a, b, c, d)
                    idx = [p['a'], p['b'], p['c'], p['d']].index(respuestas[i])
                    letra_user = chr(97 + idx)
                    if letra_user == letra_correcta:
                        aciertos += 1
                
                st.session_state.nota = aciertos * 4
                st.session_state.paso = "resultado"
                st.rerun()

# PASO 3: RESULTADO LIMPIO (PARA PDF)
elif st.session_state.paso == "resultado":
    st.balloons()
    st.title("📄 Reporte de Evaluación")
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Estudiante:** {st.session_state.nombre}")
        st.write(f"**Cédula:** {st.session_state.cedula}")
    with col2:
        st.write(f"**Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        st.write(f"**Materia:** Telecomunicaciones (TDA)")

    st.subheader(f"Calificación Obtenida: {st.session_state.nota}/20")
    
    if st.session_state.nota >= 10:
        st.success("ESTADO: APROBADO")
    else:
        st.error("ESTADO: REPROBADO")
        
    st.caption("Este documento sirve como comprobante de participación. Puede imprimir esta pantalla en PDF.")
    
    if st.button("Finalizar y Salir"):
        # Limpiar todo y volver al inicio
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
