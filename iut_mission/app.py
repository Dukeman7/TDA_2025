import streamlit as st
import pandas as pd
import os
import re

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="IUT-RC: Evaluación TDA", page_icon="📡")

# --- 2. CARGA DE DATOS ---
@st.cache_data
def cargar_estudiantes():
    if os.path.exists("iut_mission/estudiantes_iut.csv"):
        df = pd.read_csv("iut_mission/estudiantes_iut.csv", dtype=str)
        df.columns = [str(c).strip().lower() for c in df.columns]
        # Normalizamos nombres de columnas comunes
        df = df.rename(columns={'nombres y apellido': 'nombre', 'nombres y apellidos': 'nombre', 'cedula ': 'cedula'})
        return df
    return pd.DataFrame(columns=['nombre', 'cedula'])

@st.cache_data
def cargar_preguntas():
    if os.path.exists("iut_mission/preguntas_tda.csv"):
        return pd.read_csv("iut_mission/preguntas_tda.csv")
    return pd.DataFrame()

# --- 3. INTERFAZ ---
st.title("📡 IUT-RC: Evaluación TDA")
df_estudiantes = cargar_estudiantes()
df_preguntas = cargar_preguntas()

# Selección de preguntas (se queda fija en la sesión)
if 'preguntas_examen' not in st.session_state:
    st.session_state.preguntas_examen = df_preguntas.sample(min(5, len(df_preguntas))).to_dict('records')

# FORMULARIO ABIERTO
with st.form("examen_abierto"):
    st.subheader("Identificación del Estudiante")
    cedula_input = st.text_input("Ingrese su Cédula (solo números):")
    
    st.divider()
    st.info("Responda las siguientes preguntas sobre la norma ISDB-Tb:")
    
    respuestas_usuario = []
    for i, p in enumerate(st.session_state.preguntas_examen):
        st.write(f"**{i+1}. {p['pregunta']}**")
        opciones = [p['a'], p['b'], p['c'], p['d']]
        resp = st.radio(f"Opción para Q{i+1}:", opciones, key=f"q{i}", index=None)
        
        if resp:
            letra_resp = chr(97 + opciones.index(resp))
            respuestas_usuario.append(letra_resp)
        else:
            respuestas_usuario.append(None)

    enviar = st.form_submit_button("FINALIZAR Y ENVIAR")

    if enviar:
        if not cedula_input:
            st.error("⚠️ La cédula es obligatoria para registrar la nota.")
        elif None in respuestas_usuario:
            st.warning("⚠️ Por favor, responda todas las preguntas.")
        else:
            # LIMPIEZA Y BÚSQUEDA DEL NOMBRE (EL PUENTE)
            c_limpia = re.sub(r"\D", "", cedula_input)
            match = df_estudiantes[df_estudiantes['cedula'].str.strip() == c_limpia]
            
            # Si lo encuentra, usa el nombre; si no, usa la cédula
            identidad = match.iloc[0]['nombre'].split()[0] if not match.empty else f"Bachiller {c_limpia}"
            
            # CÁLCULO DE NOTA
            nota = sum(4 for i, p in enumerate(st.session_state.preguntas_examen) if respuestas_usuario[i] == p['correcta'])
            
            st.divider()
            st.header(f"Calificación: {nota}/20")
            
            if nota >= 10:
                st.balloons()
                st.success(f"¡Excelente trabajo, {identidad}!")
            else:
                st.warning(f"{identidad}, necesita repasar los parámetros de modulación.")
