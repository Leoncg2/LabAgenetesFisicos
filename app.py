import streamlit as st
import requests
import json

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO
# =============================================================================
st.set_page_config(page_title="Simulador Kine", page_icon="🏥", layout="wide")

# CSS para ocultar elementos innecesarios y dar estilo
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; }
    .success-box { padding: 1rem; background-color: #dcfce7; border: 1px solid #22c55e; border-radius: 10px; color: #14532d; }
    .error-box { padding: 1rem; background-color: #fee2e2; border: 1px solid #ef4444; border-radius: 10px; color: #7f1d1d; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. BASE DE DATOS (Tu misma lógica)
# =============================================================================
DB_CASOS = {
    "1. Ruptura LCA (Post-Op)": {
        "desc": "Paciente de 24 años, deportista, 6ta semana postop LCA. Presenta atrofia visible en cuádriceps y dificultad para realizar extensión completa activa.",
        "solucion": {"equipos": ["Rusa", "TIF", "TENS"], "Rusa": {"portadora": 2500, "burst_min": 20, "ratio": ["1:4", "1:5"]}, "TIF": {"portadora_min": 2000, "portadora_max": 2500, "amf_min": 20}, "TENS": {"freq_min": 20, "duracion_min": 200}}
    },
    "2. Esguince Tobillo Agudo": {
        "desc": "Paciente de 19 años, inversión forzada hace 24 hrs. Edema ++ en zona perimaleolar externa y dolor a la palpación (EVA 8/10).",
        "solucion": {"equipos": ["TIF", "TENS", "Farádica (Träbert)"], "TIF": {"portadora": 4000, "amf_min": 80, "vector": "6:6"}, "TENS": {"freq_min": 50, "duracion_max": 150}, "Farádica (Träbert)": {"polaridad": "Normal"}}
    },
    "3. Lesión Nerviosa Brazo": {
        "desc": "Paciente con herida cortopunzante en cara posterior del brazo. Presenta mano caída y anestesia en dorso de la mano.",
        "solucion": {"equipos": ["Farádica (Triangular)"], "Farádica (Triangular)": {"fase": [1000, 500], "pausa": [2000]}}
    },
    "4. Lumbalgia Crónica": {
        "desc": "Paciente de 55 años, dolor lumbar sordo y difuso de 8 meses de evolución. Refiere que 'siente el dolor todo el día'.",
        "solucion": {"equipos": ["TENS"], "TENS": {"freq_max": 10, "duracion_min": 150}}
    },
    "5. Debilidad Muscular (Encamado)": {
        "desc": "Paciente 70 años, encamado por neumonía durante 3 semanas. Pérdida significativa de masa muscular en extremidades inferiores.",
        "solucion": {"equipos": ["Rusa", "TIF", "TENS"], "Rusa": {"portadora": 2500, "burst_min": 20, "ratio": ["1:4", "1:5"]}, "TIF": {"portadora_min": 2000, "portadora_max": 2500}, "TENS": {"freq_min": 20, "duracion_min": 200}}
    },
    "6. Edema Post-Traumático": {
        "desc": "Paciente acude por aumento de volumen persistente en pantorrilla tras desgarro cicatrizado hace 2 meses. Sensación de pesadez.",
        "solucion": {"equipos": ["Rusa", "TIF"], "Rusa": {"burst_max": 10}, "TIF": {"amf_max": 15}}
    },
    "7. Úlcera Talón": {
        "desc": "Paciente diabético con lesión ulcerosa en talón de 3 semanas de evolución, bordes irregulares y fondo pálido. No avanza el cierre.",
        "solucion": {"equipos": ["Microcorriente", "Alto Voltaje", "TENS"]}
    },
    "8. Epicondilitis Lateral": {
        "desc": "Tenista de 40 años, dolor punzante en codo derecho al realizar extensión de muñeca contra resistencia. 4 meses de evolución.",
        "solucion": {"equipos": ["TIF", "TENS"], "TIF": {"portadora": 4000, "amf_min": 80, "vector": "6:6"}, "TENS": {"freq_min": 50}}
    },
    "9. Evaluación Post-Hernia Discal": {
        "desc": "Paciente post-operado de hernia lumbar. Refiere debilidad residual al caminar de puntillas. Se solicita evaluación electrodiagnóstica específica.",
        "solucion": {"equipos": ["Farádica (Rectangular)"], "Farádica (Rectangular)": {"busqueda_tiempo": True}}
    },
    "10. Dolor Post-Menisectomía": {
        "desc": "Paciente en cama, 6 horas post-cirugía de meniscos. Refiere dolor agudo e intenso que le impide el descanso.",
        "solucion": {"equipos": ["TIF", "TENS"], "TIF": {"portadora": 4000, "amf_min": 80, "vector": "6:6"}, "TENS": {"freq_min": 80, "duracion_max": 100}}
    },
    "11. Parestesia Mano Medial": {
        "desc": "Paciente con fractura de húmero consolidada. Refiere sensación de hormigueo constante en el 4to y 5to dedo de la mano.",
        "solucion": {"equipos": ["Farádica (Rectangular)"], "Farádica (Rectangular)": {"fase": [1000, 500]}}
    },
    "12. Tendinopatía Rotuliana": {
        "desc": "Jugador de voleibol, dolor localizado en polo inferior de la rótula. EVA 7/10 al saltar. 3 semanas de evolución.",
        "solucion": {"equipos": ["TIF", "TENS"], "TIF": {"portadora": 4000, "amf_min": 80}, "TENS": {"freq_min": 50}}
    },
    "13. Lesión Sacra por Presión": {
        "desc": "Paciente post-operado de cadera. Presenta lesión en piel zona sacra estadio II, sin signos de infección activa, pero estancada.",
        "solucion": {"equipos": ["Microcorriente", "Alto Voltaje"]}
    },
    "14. Fractura Escafoides": {
        "desc": "Paciente con fractura de escafoides de 4 meses de evolución. La radiografía de control muestra línea de fractura visible (retardo de consolidación).",
        "solucion": {"equipos": ["Ultrasonido"], "Ultrasonido": {"ciclo": "20% (1:4)", "intensidad_max": 0.5, "frecuencia": "1 MHz"}}
    },
    "15. Síndrome Banda Iliotibial": {
        "desc": "Corredora de fondo. Dolor quemante en cara lateral de rodilla. A la palpación, la banda se siente rígida y dolorosa.",
        "solucion": {"equipos": ["Onda Corta", "Infrarrojo"], "Onda Corta": {"metodo": "Capacitivo (Campo Eléctrico)", "dosis_min_potencia": 6}, "Infrarrojo": {"distancia_min": 40}}
    },
    "16. Rigidez Articular Manos": {
        "desc": "Paciente diagnosticado con patología reumática. Refiere rigidez importante en las mañanas y manos frías. Piel con atrofia.",
        "solucion": {"equipos": ["Infrarrojo"], "Infrarrojo": {"distancia_min": 30, "tiempo_min": 20}}
    },
    "17. Esguince Tobillo (Fase Inicial)": {
        "desc": "Deportista, trauma en inversión hace 20 horas. Dolor 4/10 en reposo. Edema leve.",
        "solucion": {"equipos": ["Ultrasonido"], "Ultrasonido": {"ciclo": "20% (1:4)", "intensidad_max": 0.5}}
    },
    "18. Tortícolis": {
        "desc": "Paciente despierta con cuello rígido y cabeza inclinada hacia la derecha. Dolor agudo a la movilización activa.",
        "solucion": {"equipos": ["Onda Corta", "Infrarrojo"], "Onda Corta": {"dosis_max_potencia": 15}, "Infrarrojo": {"distancia_min": 40}}
    },
    "19. Lesión Muscular Isquiotibial": {
        "desc": "Velocista, sintió 'pinchazo' hace 10 días. Actualmente sin dolor en reposo, molestia leve al estiramiento máximo. Sin hematoma visible.",
        "solucion": {"equipos": ["Onda Corta"], "Onda Corta": {"metodo": "Inductivo (Campo Magnético)", "dosis_min_potencia": 8}}
    },
    "20. Adherencia Post-Quirúrgica": {
        "desc": "Paciente con cicatriz en cara anterior de muñeca post-cirugía (3 meses). La piel está retraída y limita la extensión completa.",
        "solucion": {"equipos": ["Ultrasonido"], "Ultrasonido": {"frecuencia": "3 MHz", "ciclo": "100% (Continuo)"}}
    },
    "21. Dorsalgia por Tensión": {
        "desc": "Trabajador de construcción. Palpación revela musculatura paravertebral dorsal indurada y sensible. Dolor tipo cansancio al final del día.",
        "solucion": {"equipos": ["Onda Corta"], "Onda Corta": {"metodo": "Inductivo (Campo Magnético)", "dosis_min_potencia": 30}}
    }
}

# =============================================================================
# 3. LÓGICA DE IA (Gemini API)
# =============================================================================
def consultar_ia(caso, respuesta_alumno, analisis_tecnico):
    # En Streamlit las claves se sacan de st.secrets
    if "GEMINI_API_KEY" not in st.secrets:
        return "⚠️ Error: Falta configurar el Secret 'GEMINI_API_KEY'."
    
    api_key = st.secrets["GEMINI_API_KEY"]
    
    prompt = f"""
    Actúa como docente de Kinesiología.
    CASO: {caso['desc']}
    DECISIÓN ALUMNO: {respuesta_alumno}
    ANÁLISIS TÉCNICO: {analisis_tecnico}
    
    INSTRUCCIONES:
    Evalúa basándote en el Análisis Técnico.
    Si falló, explica brevemente la fisiología.
    Si acertó, felicita y da un dato curioso.
    Máximo 40 palabras. Tono chileno neutro.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error Google: {response.status_code}"
    except Exception as e:
        return f"Error conexión: {e}"

# =============================================================================
# 4. INTERFAZ Y LÓGICA PRINCIPAL
# =============================================================================

# -- Sidebar: Selección de Caso --
st.sidebar.title("🏥 Simulador Kine")
caso_seleccionado = st.sidebar.selectbox("Selecciona un Caso Clínico:", ["Seleccionar..."] + list(DB_CASOS.keys()))

if caso_seleccionado != "Seleccionar...":
    datos_caso = DB_CASOS[caso_seleccionado]
    st.info(f"📋 **Caso:** {datos_caso['desc']}")
    
    # -- Sidebar: Selección de Equipo --
    st.sidebar.markdown("---")
    categoria = st.sidebar.radio("Categoría:", ["Electroterapia", "Termoterapia"])
    
    equipo = None
    subtipo = None
    
    if categoria == "Electroterapia":
        equipo = st.sidebar.selectbox("Equipo:", ["TENS", "Rusa", "TIF", "Farádica"])
        if equipo == "Farádica":
            subtipo = st.sidebar.selectbox("Tipo de Farádica:", ["Träbert", "Rectangular", "Triangular"])
    else:
        equipo = st.sidebar.selectbox("Equipo:", ["Ultrasonido", "Onda Corta", "Infrarrojo"])

    st.markdown(f"## Configurando: **{equipo}** {f'({subtipo})' if subtipo else ''}")
    st.markdown("---")

    # -- FORMULARIOS DINÁMICOS --
    params = {} # Diccionario para guardar lo que elija el usuario

    col1, col2 = st.columns(2)
    
    with col1:
        if equipo == "TENS":
            params["freq"] = st.number_input("Frecuencia (Hz)", 0, 200)
            params["duracion"] = st.number_input("Duración de Fase (µs)", 0, 500)
        
        elif equipo == "Rusa":
            params["portadora"] = st.number_input("Portadora (Hz)", value=2500)
            params["burst"] = st.number_input("Burst (Hz)", 0, 100)
            params["ratio"] = st.selectbox("Ratio", ["1:1", "1:2", "1:4", "1:5"])
            
        elif equipo == "TIF":
            params["portadora"] = st.number_input("Portadora (Hz)", 0, 10000)
            params["amf"] = st.number_input("AMF (Hz)", 0, 200)
            params["vector"] = st.selectbox("Vector", ["Manual/Off", "6:6", "Auto"])

        elif equipo == "Farádica":
            params["polaridad"] = st.selectbox("Polaridad", ["Normal", "Inversión"])
            params["fase"] = st.number_input("Tiempo Fase (ms)", 0, 2000)
            
        elif equipo == "Ultrasonido":
            params["frecuencia"] = st.radio("Frecuencia", ["1 MHz", "3 MHz"])
            params["ciclo"] = st.selectbox("Duty Cycle", ["100% (Continuo)", "50% (1:1)", "20% (1:4)", "10%"])
            params["intensidad"] = st.number_input("Intensidad (W/cm²)", 0.0, 3.0, step=0.1)

        elif equipo == "Onda Corta":
            params["metodo"] = st.selectbox("Método", ["Capacitivo (Campo Eléctrico)", "Inductivo (Campo Magnético)"])
            params["potencia"] = st.number_input("Potencia Media (W)", 0, 200)

        elif equipo == "Infrarrojo":
            params["distancia"] = st.number_input("Distancia (cm)", 0, 100)

    with col2:
        justificacion = st.text_area("Justificación Clínica", placeholder="¿Por qué elegiste estos parámetros?")
        validar_btn = st.button("✅ Validar Tratamiento", type="primary")

    # -- LÓGICA DE VALIDACIÓN (Al presionar botón) --
    if validar_btn:
        feedback_tecnico = []
        es_correcto = True
        solucion = datos_caso["solucion"]
        equipos_validos = solucion.get("equipos", [])
        
        # 1. Validar Nombre del Equipo
        nombre_completo = equipo if not subtipo else f"{equipo} ({subtipo})"
        match_equipo = False
        for eq in equipos_validos:
            if eq in nombre_completo or (equipo == "Onda Corta" and eq == "Onda Corta"):
                match_equipo = True
                break
        
        if not match_equipo:
            es_correcto = False
            feedback_tecnico.append(f"❌ Equipo incorrecto. Elegiste {nombre_completo}, se sugiere: {', '.join(equipos_validos)}")
        else:
            feedback_tecnico.append(f"✅ Equipo {nombre_completo} correcto.")
            
            # 2. Validar Parámetros Específicos (Lógica Simplificada para Streamlit)
            if equipo == "Ultrasonido" and "Ultrasonido" in solucion:
                reglas = solucion["Ultrasonido"]
                if "ciclo" in reglas and params["ciclo"] != reglas["ciclo"]:
                    es_correcto = False; feedback_tecnico.append(f"❌ Ciclo incorrecto. Usaste {params['ciclo']}, sugerido: {reglas['ciclo']}")
                if "frecuencia" in reglas and params["frecuencia"] != reglas["frecuencia"]:
                    es_correcto = False; feedback_tecnico.append(f"❌ Frecuencia incorrecta.")
                if "intensidad_max" in reglas and params["intensidad"] > reglas["intensidad_max"]:
                    feedback_tecnico.append(f"⚠️ Intensidad un poco alta.")

            if equipo == "TENS" and "TENS" in solucion:
                reglas = solucion["TENS"]
                if "freq_min" in reglas and params["freq"] < reglas["freq_min"]: feedback_tecnico.append("❌ Frecuencia muy baja.")
                if "duracion_min" in reglas and params["duracion"] < reglas["duracion_min"]: feedback_tecnico.append("❌ Duración de pulso muy corta.")

            if equipo == "Rusa" and "Rusa" in solucion:
                reglas = solucion["Rusa"]
                if "ratio" in reglas and params["ratio"] not in reglas["ratio"]: feedback_tecnico.append("❌ Ratio inadecuado.")

            if equipo == "Onda Corta" and "Onda Corta" in solucion:
                reglas = solucion["Onda Corta"]
                if "metodo" in reglas and params["metodo"] != reglas["metodo"]: feedback_tecnico.append(f"⚠️ Se prefiere método {reglas['metodo']}.")
                if "dosis_min_potencia" in reglas and params["potencia"] < reglas["dosis_min_potencia"]: es_correcto = False; feedback_tecnico.append("❌ Dosis térmica insuficiente.")
                
            if equipo == "Infrarrojo" and "Infrarrojo" in solucion:
                reglas = solucion["Infrarrojo"]
                if "distancia_min" in reglas and params["distancia"] < reglas["distancia_min"]: feedback_tecnico.append("⚠️ ¡Cuidado! Muy cerca (riesgo quemadura).")

        # Mostrar Feedback Técnico
        str_feedback = " | ".join(feedback_tecnico)
        if es_correcto:
            st.success(f"Resultado Técnico: {str_feedback}")
        else:
            st.error(f"Resultado Técnico: {str_feedback}")
            
        # Consultar IA
        with st.spinner("🤖 Consultando al profesor..."):
            res_ia = consultar_ia(datos_caso, f"Equipo: {nombre_completo}. Params: {params}. Justificación: {justificacion}", str_feedback)
            st.markdown("### 🎓 Feedback Docente")
            st.info(res_ia)

else:
    st.write("👈 Selecciona un caso en el menú lateral para empezar.")
