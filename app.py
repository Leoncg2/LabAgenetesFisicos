import streamlit as st
import google.generativeai as genai
import os

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO
# =============================================================================
st.set_page_config(page_title="Simulador Kine Pro", page_icon="🏥", layout="wide")

# Estilos CSS para compactar los inputs numéricos y dar look médico
st.markdown("""
<style>
    .stNumberInput input { padding: 5px; }
    div[data-testid="stExpander"] details summary p { font-weight: bold; font-size: 1.1em; color: #2563eb; }
    .success-box { padding: 1rem; background-color: #dcfce7; border-left: 5px solid #22c55e; border-radius: 5px; color: #14532d; }
    .error-box { padding: 1rem; background-color: #fee2e2; border-left: 5px solid #ef4444; border-radius: 5px; color: #7f1d1d; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. CONFIGURACIÓN DE IA (USANDO LIBRERÍA OFICIAL)
# =============================================================================
def consultar_ia_oficial(caso, respuesta_alumno, analisis_tecnico):
    # Intentamos obtener la API Key de los Secrets de Streamlit
    api_key = st.secrets.get("GEMINI_API_KEY")
    
    if not api_key:
        return "⚠️ Error Crítico: No se encontró la GEMINI_API_KEY en los Secrets."

    try:
        # Configuración segura usando la librería oficial
        genai.configure(api_key=api_key)
        
        # Usamos el modelo flash que es rápido y estable
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Actúa como un profesor experto de Kinesiología (Fisioterapia) de la Universidad de Chile.
        
        CONTEXTO CLÍNICO:
        {caso['desc']}
        
        CONFIGURACIÓN ELEGIDA POR EL ESTUDIANTE:
        {respuesta_alumno}
        
        VALIDACIÓN TÉCNICA DEL SISTEMA:
        {analisis_tecnico}
        
        TU TAREA:
        1. Basa tu juicio PRINCIPALMENTE en la 'Validación Técnica'.
        2. Si la validación dice que hay errores, explica brevemente la fisiología detrás del error (ej: por qué esa frecuencia no sirve).
        3. Si la validación es correcta, felicita y aporta un "Dato Clínico" curioso o un tip práctico breve.
        4. Sé conciso (máximo 50 palabras). Tono chileno académico pero cercano.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"⚠️ Error de conexión con Google: {str(e)}"

# =============================================================================
# 3. BASE DE DATOS DE CASOS (COMPLETA)
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
# 4. INTERFAZ Y LÓGICA PRINCIPAL (CON TODOS LOS PARÁMETROS RESTAURADOS)
# =============================================================================

# -- Sidebar: Selección de Caso --
st.sidebar.title("🏥 Simulador Kine Pro")
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

    nombre_completo_equipo = f"{equipo} ({subtipo})" if subtipo else equipo
    st.markdown(f"## Configurando: **{nombre_completo_equipo}**")
    st.markdown("---")

    # -- FORMULARIOS DINÁMICOS COMPLEJOS --
    params = {} # Diccionario para guardar lo que elija el usuario

    # Contenedor principal para los parámetros
    with st.container():
        
        # === TENS (Parámetros Completos) ===
        if equipo == "TENS":
            c1, c2, c3 = st.columns(3)
            with c1:
                params["onda"] = st.selectbox("Tipo de Onda", ["Bifásica Simétrica", "Bifásica Asimétrica"])
                params["freq"] = st.number_input("Frecuencia (Hz)", 0, 250, value=0)
            with c2:
                params["duracion"] = st.number_input("Duración de Fase (µs)", 0, 500, value=0)
                params["tiempo"] = st.number_input("Tiempo Total (min)", 0, 60, value=0)
            with c3:
                params["intensidad"] = st.number_input("Intensidad (mA)", 0, 100, value=0)
                params["modo"] = st.radio("Modo", ["CC (Corriente Constante)", "CV (Voltaje Constante)"])

            with st.expander("🎛️ Modulaciones y Burst (Avanzado)", expanded=True):
                mc1, mc2, mc3 = st.columns(3)
                with mc1: params["mod_freq"] = st.number_input("Mod. Frecuencia (Hz)", 0, 100, value=0)
                with mc2: params["mod_amp"] = st.number_input("Mod. Amplitud (%)", 0, 100, value=0)
                with mc3: params["burst"] = st.number_input("Burst / Recorrido", 0, 10, value=0)

        # === RUSA (Parámetros Completos) ===
        elif equipo == "Rusa":
            c1, c2 = st.columns(2)
            with c1:
                params["onda"] = st.selectbox("Onda", ["Rusa (Sinusoidal)", "Cuadrada"])
                params["portadora"] = st.number_input("Portadora (Hz)", value=2500, step=500)
                params["burst"] = st.number_input("Frec. Burst (Hz)", 0, 100, value=0)
            with c2:
                params["ratio"] = st.selectbox("Ratio (Ciclo Trabajo)", ["1:1", "1:2", "1:4", "1:5"])
                params["intensidad"] = st.number_input("Intensidad (mA)", 0, 120, value=0)
                params["tiempo"] = st.number_input("Tiempo (min)", 0, 60, value=0)
            
            with st.expander("⏱️ Tiempos de Ciclo (ON/OFF/Rampa)", expanded=True):
                t1, t2, t3 = st.columns(3)
                with t1: params["rampa"] = st.number_input("Rampa (s)", 0, 10, value=0)
                with t2: params["on"] = st.number_input("Tiempo ON (s)", 0, 60, value=0)
                with t3: params["off"] = st.number_input("Tiempo OFF (s)", 0, 60, value=0)

        # === TIF (Parámetros Completos) ===
        elif equipo == "TIF":
            c1, c2, c3 = st.columns(3)
            with c1:
                params["portadora"] = st.number_input("Portadora (Hz)", 0, 10000, value=0)
                params["amf"] = st.number_input("AMF (Hz)", 0, 250, value=0)
            with c2:
                params["espectro"] = st.number_input("Espectro de Frec.", 0, 200, value=0)
                params["vector"] = st.selectbox("Vector", ["Manual/Off", "6:6", "1:30:1:30"])
            with c3:
                params["intensidad"] = st.number_input("Intensidad (mA)", 0, 100, value=0)
                params["tiempo"] = st.number_input("Tiempo (min)", 0, 60, value=0)

        # === FARÁDICA (Parámetros Completos) ===
        elif equipo == "Farádica":
            c1, c2 = st.columns(2)
            with c1:
                params["polaridad"] = st.selectbox("Polaridad", ["Normal", "Inversión"])
                params["intensidad"] = st.number_input("Intensidad (mA)", 0, 80, value=0)
            with c2:
                params["tiempo"] = st.number_input("Tiempo Sesión (min)", 0, 60, value=0)
                params["modo"] = st.radio("Modo", ["CC", "CV"])
            
            with st.expander("⚡ Configuración de Pulsos (ms)", expanded=True):
                p1, p2 = st.columns(2)
                with p1: params["fase"] = st.number_input("Tiempo Fase (ms)", 0.0, 5000.0, value=0.0, step=10.0)
                with p2: params["pausa"] = st.number_input("Tiempo Pausa (ms)", 0.0, 5000.0, value=0.0, step=10.0)

        # === ULTRASONIDO (Parámetros Completos) ===
        elif equipo == "Ultrasonido":
            c1, c2 = st.columns(2)
            with c1:
                params["frecuencia"] = st.radio("Frecuencia", ["1 MHz", "3 MHz"])
                params["ciclo"] = st.selectbox("Duty Cycle", ["100% (Continuo)", "50% (1:1)", "20% (1:4)", "10%"])
            with c2:
                params["intensidad"] = st.number_input("Intensidad (W/cm²)", 0.0, 3.0, step=0.1)
                params["tiempo"] = st.number_input("Tiempo (min)", 0, 30, value=0)
                params["era"] = st.selectbox("Relación ERA", ["1x ERA", "2x ERA", "3x ERA"])

        # === ONDA CORTA (Parámetros Completos con Cálculo Auto) ===
        elif equipo == "Onda Corta":
            c1, c2 = st.columns(2)
            with c1:
                params["metodo"] = st.selectbox("Método", ["Capacitivo (Campo Eléctrico)", "Inductivo (Campo Magnético)"])
                params["tecnica"] = st.selectbox("Técnica", ["Coplanar", "Contraplanar", "Longitudinal", "Monodo"])
                params["modo"] = st.radio("Modo Emisión", ["Pulsado (PSWD)", "Continuo (CSWD)"])
            with c2:
                params["fase"] = st.number_input("Ancho Pulso (µs)", 0, 400, value=0) # Fase
                params["frec_pulso"] = st.number_input("Frecuencia (Hz)", 0, 1000, value=0)
                params["potencia"] = st.number_input("Potencia Pico (W)", 0, 1000, value=0)
                params["tiempo"] = st.number_input("Tiempo (min)", 0, 30, value=0)

            # Cálculo en vivo de la Potencia Media
            potencia_media = 0
            if params["modo"] == "Continuo (CSWD)":
                potencia_media = params["potencia"]
            else:
                # Fórmula: Pico * (Ancho * 10^-6) * Frecuencia
                potencia_media = round(params["potencia"] * (params["fase"] * 0.000001) * params["frec_pulso"], 1)
            
            st.metric(label="🔥 Potencia Media Resultante (Automático)", value=f"{potencia_media} W")
            params["media_resultante"] = potencia_media

        # === INFRARROJO ===
        elif equipo == "Infrarrojo":
            c1, c2 = st.columns(2)
            with c1:
                params["tipo"] = st.radio("Tipo Lámpara", ["Luminoso", "No Luminoso"])
            with c2:
                params["distancia"] = st.number_input("Distancia (cm)", 0, 100, value=0)
                params["tiempo"] = st.number_input("Tiempo (min)", 0, 60, value=0)

    st.markdown("---")
    justificacion = st.text_area("✍️ Justificación Clínica", placeholder="Explica aquí por qué elegiste estos parámetros...")
    validar_btn = st.button("✅ Validar Tratamiento", type="primary", use_container_width=True)

    # -- LÓGICA DE VALIDACIÓN --
    if validar_btn:
        feedback_tecnico = []
        es_correcto = True
        solucion = datos_caso["solucion"]
        equipos_validos = solucion.get("equipos", [])
        
        # 1. Validar Nombre del Equipo
        match_equipo = False
        for eq in equipos_validos:
            if eq in nombre_completo_equipo or (equipo == "Onda Corta" and eq == "Onda Corta"):
                match_equipo = True
                break
        
        if not match_equipo:
            es_correcto = False
            feedback_tecnico.append(f"❌ **Equipo:** Elegiste {nombre_completo_equipo}, pero se sugiere: {', '.join(equipos_validos)}.")
        else:
            feedback_tecnico.append(f"✅ **Equipo:** {nombre_completo_equipo} es una opción correcta.")
            
            # 2. VALIDACIONES ESPECÍFICAS (Lógica original completa)
            
            # --- ULTRASONIDO ---
            if equipo == "Ultrasonido" and "Ultrasonido" in solucion:
                reglas = solucion["Ultrasonido"]
                if "ciclo" in reglas and params["ciclo"] != reglas["ciclo"]:
                    es_correcto = False; feedback_tecnico.append(f"❌ **Ciclo:** Usaste {params['ciclo']}, correcto es {reglas['ciclo']}.")
                if "frecuencia" in reglas and params["frecuencia"] != reglas["frecuencia"]:
                    es_correcto = False; feedback_tecnico.append(f"❌ **Frecuencia:** Usaste {params['frecuencia']}, correcto es {reglas['frecuencia']}.")
                if "intensidad_max" in reglas and params["intensidad"] > reglas["intensidad_max"]:
                    feedback_tecnico.append(f"⚠️ **Intensidad:** {params['intensidad']} es un poco alta. Sugerido < {reglas['intensidad_max']}.")

            # --- TENS ---
            if equipo == "TENS" and "TENS" in solucion:
                reglas = solucion["TENS"]
                if "freq_min" in reglas and params["freq"] < reglas["freq_min"]: feedback_tecnico.append("❌ **Frecuencia:** Muy baja para el objetivo.")
                if "freq_max" in reglas and params["freq"] > reglas["freq_max"]: feedback_tecnico.append("❌ **Frecuencia:** Muy alta para el objetivo.")
                if "duracion_min" in reglas and params["duracion"] < reglas["duracion_min"]: feedback_tecnico.append("❌ **Duración de pulso:** Insuficiente.")

            # --- RUSA ---
            if equipo == "Rusa" and "Rusa" in solucion:
                reglas = solucion["Rusa"]
                if "ratio" in reglas and params["ratio"] not in reglas["ratio"]: feedback_tecnico.append(f"❌ **Ratio:** {params['ratio']} no es ideal aquí.")
                if "burst_min" in reglas and params["burst"] < reglas["burst_min"]: feedback_tecnico.append("❌ **Burst:** Muy bajo.")

            # --- ONDA CORTA ---
            if equipo == "Onda Corta" and "Onda Corta" in solucion:
                reglas = solucion["Onda Corta"]
                if "metodo" in reglas and params["metodo"] != reglas["metodo"]: feedback_tecnico.append(f"⚠️ **Método:** Se prefiere {reglas['metodo']}.")
                p_media = params.get("media_resultante", 0)
                if "dosis_min_potencia" in reglas and p_media < reglas["dosis_min_potencia"]:
                    es_correcto = False; feedback_tecnico.append(f"❌ **Dosis:** {p_media}W es atérmico/insuficiente. Mínimo {reglas['dosis_min_potencia']}W.")

            # --- TIF ---
            if equipo == "TIF" and "TIF" in solucion:
                reglas = solucion["TIF"]
                if "portadora_min" in reglas and params["portadora"] < reglas["portadora_min"]: feedback_tecnico.append("❌ **Portadora:** Muy baja (molestia sensitiva).")
                if "vector" in reglas and params["vector"] != reglas["vector"]: feedback_tecnico.append(f"⚠️ **Vector:** Se sugiere {reglas['vector']}.")

            # --- FARÁDICA ---
            if "Farádica" in equipo and equipo in solucion:
                reglas = solucion[equipo] # Busca por llave exacta ej "Farádica (Rectangular)"
                if "polaridad" in reglas and params["polaridad"] != reglas["polaridad"]: feedback_tecnico.append("❌ **Polaridad:** Incorrecta.")
                if "busqueda_tiempo" in reglas and params["fase"] > 100: feedback_tecnico.append("❌ **Estrategia:** Debes buscar tiempos más cortos (Cronaxia).")

        # Mostrar Resultados
        str_feedback = " | ".join(feedback_tecnico)
        
        if es_correcto:
            st.markdown(f'<div class="success-box"><h3>🎉 Muy Bien</h3>{str_feedback}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="error-box"><h3>⚠️ Atención</h3>{str_feedback}</div>', unsafe_allow_html=True)
            
        # Consultar IA
        if "GEMINI_API_KEY" in st.secrets:
            with st.spinner("🧠 Consultando al Profesor Virtual..."):
                res_ia = consultar_ia_oficial(datos_caso, f"Equipo: {nombre_completo_equipo}. Config: {params}. Justificación: {justificacion}", str_feedback)
                st.markdown("### 🎓 Feedback Docente")
                st.write(res_ia)
        else:
            st.warning("⚠️ No se ha configurado la API Key de Gemini, por lo que no puedo darte el feedback cualitativo.")
            
else:
    st.write("👈 Selecciona un caso en el menú lateral para empezar.")
