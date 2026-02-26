import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="IUT-RC: Certificación TDA", page_icon="📡")

# --- 2. CONEXIÓN A GOOGLE SHEETS (NUEVO) ---
conn = st.connection("gsheets", type=GSheetsConnection)
URL_SHEET = "https://docs.google.com/spreadsheets/d/1DFneYggw8TZQ0PSAKWWeyhRGHW5HQbTJhD_-ThdfFfc/edit?usp=sharing"

def registrar_en_nube(nombre, cedula, nota, intento):
    try:
        # Leer datos actuales
        df_existente = conn.read(spreadsheet=URL_SHEET, ttl=0)
        
        # Crear nueva fila
        nuevo_registro = pd.DataFrame([{
            "nombre": nombre,
            "cedula": str(cedula),
            "nota": nota,
            "intento": intento,
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }])
        
from datetime import datetime, timedelta

def registrar_en_nube(nombre, cedula, nota, intento):
    try:
        # 1. Ajustamos la hora: Restamos 4 horas al servidor (UTC -> VET)
        hora_caracas = datetime.now() - timedelta(hours=4)
        fecha_formateada = hora_caracas.strftime("%d/%m/%Y %H:%M:%S")

        # 2. Leemos los datos actuales
        df_existente = conn.read(spreadsheet=URL_SHEET, ttl=0)
        
        # 3. Creamos la nueva fila con la hora corregida
        nuevo_registro = pd.DataFrame([{
            "nombre": nombre,
            "cedula": str(cedula),
            "nota": nota,
            "intento": intento,
            "fecha": fecha_formateada
        }])
        
        # 4. Concatenamos y actualizamos la hoja de Google
        df_final = pd.concat([df_existente, nuevo_registro], ignore_index=True)
        conn.update(spreadsheet=URL_SHEET, data=df_final)
    except Exception as e:
        st.error(f"Error al registrar en nube: {e}")

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

# --- 5. INTERFAZ POR PASOS ---

# PASO 1: IDENTIFICACIÓN
if st.session_state.paso == "identificacion":
    st.title("📡 Acceso al Sistema de Evaluación")
    ced_input = st.text_input("Ingrese su Cédula (Solo números):", placeholder="Ej: 87654321")
    
    if st.button("Validar Identidad"):
        c_limpia = re.sub(r"\D", "", ced_input)
        match = df_estudiantes[df_estudiantes['cedula'].str.strip() == c_limpia]
        
        if not match.empty:
            # Consultar intentos en la nube
            try:
                df_nube = conn.read(spreadsheet=URL_SHEET, ttl=0)
                intentos_previos = len(df_nube[df_nube['cedula'].astype(str) == c_limpia])
            except:
                intentos_previos = 0
                
            if intentos_previos >= 3:
                st.error(f"⚠️ Bachiller {match.iloc[0]['nombre'].title()}, ya ha agotado sus 3 intentos.")
            else:
                st.session_state.nombre = match.iloc[0]['nombre'].title()
                st.session_state.cedula = c_limpia
                st.session_state.intento_n = intentos_previos + 1
                st.session_state.paso = "confirmacion"
                st.rerun()
        else:
            st.error("⚠️ Cédula no registrada en la cátedra del Prof. Duque")

# PASO 2: CONFIRMACIÓN DE INTENTO
elif st.session_state.paso == "confirmacion":
    st.header("Confirmación de Intento")
    st.warning(f"Bachiller {st.session_state.nombre}, va a iniciar el **INTENTO {st.session_state.intento_n} de 3**.")
    st.write("Al generar el intento, las preguntas se mostrarán y la oportunidad será contada.")
    
    if st.button(f"🚀 GENERAR INTENTO {st.session_state.intento_n}"):
        st.session_state.paso = "examen"
        st.rerun()

# PASO 3: EL EXAMEN
elif st.session_state.paso == "examen":
    st.header("Examen de TV Digital Abierta")
    st.info(f"Bachiller: **{st.session_state.nombre}** | Intento: **{st.session_state.intento_n}/3**")
    
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
                aciertos = 0
                for i, p in enumerate(st.session_state.preguntas_examen):
                    letra_correcta = p['correcta'].strip().lower()
                    idx = [p['a'], p['b'], p['c'], p['d']].index(respuestas[i])
                    letra_user = chr(97 + idx)
                    if letra_user == letra_correcta:
                        aciertos += 1
                
                st.session_state.nota = aciertos * 4
                # REGISTRO AUTOMÁTICO EN LA NUBE
                registrar_en_nube(st.session_state.nombre, st.session_state.cedula, st.session_state.nota, st.session_state.intento_n)
                st.session_state.paso = "resultado"
                st.rerun()

# PASO 4: RESULTADO
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
        st.write(f"**Nota:** {st.session_state.nota}/20")
    
    if st.session_state.nota >= 10:
        st.success("ESTADO: APROBADO")
    else:
        st.error("ESTADO: REPROBADO")

    if st.button("Finalizar y Salir"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
