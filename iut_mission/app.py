import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="IUT-RC: Certificación TDA", page_icon="📡")

# --- 2. CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)
URL_SHEET = "https://docs.google.com/spreadsheets/d/1DFneYggw8TZQ0PSAKWWeyhRGHW5HQbTJhD_-ThdfFfc/edit?usp=sharing"

def registrar_en_nube(nombre, cedula, nota, intento):
    try:
        # Sincronización con Hora Venezuela (UTC-4)
        hora_venezuela = datetime.now() - timedelta(hours=4)
        fecha_str = hora_venezuela.strftime("%d/%m/%Y %H:%M:%S")

        # Leer datos actuales para no sobreescribir
        df_existente = conn.read(spreadsheet=URL_SHEET, ttl=0)
        
        # Crear la nueva fila
        nuevo_registro = pd.DataFrame([{
            "nombre": nombre,
            "cedula": str(cedula),
            "nota": nota,
            "intento": intento,
            "fecha": fecha_str
        }])
        
        # Concatenar y subir
        df_final = pd.concat([df_existente, nuevo_registro], ignore_index=True)
        conn.update(spreadsheet=URL_SHEET, data=df_final)
    except Exception as e:
        st.error(f"Error en el registro: {e}")

# --- 3. CARGA DE DATOS LOCALES ---
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

# --- 4. GESTIÓN DE ESTADO ---
if 'paso' not in st.session_state:
    st.session_state.paso = "identificacion"
    st.session_state.nombre = ""
    st.session_state.cedula = ""
    st.session_state.intento_n = 0

df_estudiantes = cargar_estudiantes()
df_preguntas = cargar_preguntas()

# --- 5. INTERFAZ ---

if st.session_state.paso == "identificacion":
    st.title("📡 Sistema de Evaluación TDA")
    ced_input = st.text_input("Cédula (Solo números):")
    
    if st.button("Validar"):
        c_limpia = re.sub(r"\D", "", ced_input)
        match = df_estudiantes[df_estudiantes['cedula'].str.strip() == c_limpia]
        
        if not match.empty:
            try:
                df_nube = conn.read(spreadsheet=URL_SHEET, ttl=0)
                intentos_v = len(df_nube[df_nube['cedula'].astype(str) == c_limpia])
            except:
                intentos_v = 0
                
            if intentos_v >= 3:
                st.error("⚠️ Ya agotó sus 3 intentos.")
            else:
                st.session_state.nombre = match.iloc[0]['nombre'].title()
                st.session_state.cedula = c_limpia
                st.session_state.intento_n = intentos_v + 1
                st.session_state.paso = "confirmacion"
                st.rerun()
        else:
            st.error("⚠️ Cédula no registrada.")

elif st.session_state.paso == "confirmacion":
    st.header("Confirmar Intento")
    st.warning(f"Bachiller {st.session_state.nombre}, va por el **INTENTO {st.session_state.intento_n}/3**.")
    if st.button(f"🚀 INICIAR EVALUACIÓN"):
        st.session_state.paso = "examen"
        st.rerun()

elif st.session_state.paso == "examen":
    st.header("Examen TDA")
    if 'preguntas_examen' not in st.session_state:
        st.session_state.preguntas_examen = df_preguntas.sample(min(5, len(df_preguntas))).to_dict('records')

    with st.form("quiz"):
        respuestas = []
        for i, p in enumerate(st.session_state.preguntas_examen):
            st.write(f"**{i+1}. {p['pregunta']}**")
            opciones = [p['a'], p['b'], p['c'], p['d']]
            resp = st.radio(f"Opción:", opciones, key=f"q{i}", index=None)
            respuestas.append(resp)

        if st.form_submit_button("ENVIAR"):
            if None in respuestas:
                st.warning("Responda todo.")
            else:
                aciertos = sum(1 for i, p in enumerate(st.session_state.preguntas_examen) 
                             if chr(97 + [p['a'], p['b'], p['c'], p['d']].index(respuestas[i])) == p['correcta'].strip().lower())
                st.session_state.nota = aciertos * 4
                registrar_en_nube(st.session_state.nombre, st.session_state.cedula, st.session_state.nota, st.session_state.intento_n)
                st.session_state.paso = "resultado"
                st.rerun()

elif st.session_state.paso == "resultado":
    st.balloons()
    st.title("Reporte Final")
    st.write(f"**Bachiller:** {st.session_state.nombre}")
    st.write(f"**Nota:** {st.session_state.nota}/20")
    if st.button("Salir"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
