import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="IUT-RC: Evaluación TDA", layout="centered")

# --- 2. CARGA DE PREGUNTAS ---
@st.cache_data
def cargar_banco():
    # Intenta leer el CSV en la misma carpeta
    if os.path.exists("iut_mission/preguntas_tda.csv"):
        return pd.read_csv("iut_mission/preguntas_tda.csv")
    elif os.path.exists("preguntas_tda.csv"):
        return pd.read_csv("preguntas_tda.csv")
    else:
        # Banco de auxilio por si el CSV no carga
        data = {
            'pregunta': ["¿Estándar TDA en Venezuela?", "¿Modulación TDA?", "¿Middleware?"],
            'a': ["DVB-T", "8-VSB", "Ginga"],
            'b': ["ATSC", "COFDM", "Java"],
            'c': ["ISDB-Tb", "QAM", "Flash"],
            'd': ["DTMB", "SSB", "HTML5"],
            'correcta': ["c", "b", "a"]
        }
        return pd.DataFrame(data)

for i, p in enumerate(st.session_state.preguntas_examen):
            st.write(f"**{i+1}. {p['pregunta']}**")
            opciones = [p['a'], p['b'], p['c'], p['d']]
            
            # --- CAMBIO AQUÍ: index=None para que aparezca vacío ---
            resp = st.radio(
                f"Seleccione su respuesta (Q{i+1}):", 
                opciones, 
                key=f"q{i}", 
                index=None
            )
            
            # Validamos si respondió algo para no dar error de índice
            if resp:
                letra_resp = chr(97 + opciones.index(resp))
                respuestas_usuario.append(letra_resp)
            else:
                respuestas_usuario.append(None) # Si no marca nada, queda vacío

# --- 3. LÓGICA DE EXAMEN ---
st.title("📡 IUT-RC: TV Universitaria Interactiva")
st.markdown("### Evaluación de Televisión Digital Abierta")

try:
    df_preguntas = cargar_banco()
    
    # Seleccionamos 5 al azar y las guardamos en la sesión
    if 'preguntas_examen' not in st.session_state:
        st.session_state.preguntas_examen = df_preguntas.sample(min(5, len(df_preguntas))).to_dict('records')

    with st.form("examen_tda"):
        cedula = st.text_input("Ingrese su Cédula de Identidad:")
        respuestas_usuario = []
        
        st.divider()
        
        for i, p in enumerate(st.session_state.preguntas_examen):
            st.write(f"**{i+1}. {p['pregunta']}**")
            opciones = [p['a'], p['b'], p['c'], p['d']]
            resp = st.radio(f"Seleccione su respuesta (Q{i+1}):", opciones, key=f"q{i}")
            
            # Convertimos la opción seleccionada a letra (a, b, c, d)
            letra_resp = chr(97 + opciones.index(resp))
            respuestas_usuario.append(letra_resp)

        enviar = st.form_submit_button("Finalizar y Enviar Evaluación")

        if enviar:
            if not cedula:
                st.error("⚠️ La cédula es obligatoria para registrar la nota.")
            else:
                nota = 0
                for i, p in enumerate(st.session_state.preguntas_examen):
                    if respuestas_usuario[i] == p['correcta']:
                        nota += 4 # 5 preguntas x 4 pts = 20
                
                st.metric("CALIFICACIÓN", f"{nota}/20")
                
                if nota >= 10:
                    st.balloons()
                    st.success(f"¡Excelente trabajo, bachiller {cedula}!")
                else:
                    st.warning("Nota insuficiente. Repase los fundamentos de 2013.")

except Exception as e:
    st.error(f"Error en el búnker de datos: {e}")
