import gradio as gr
import os
import google.generativeai as genai

# =============================================================================
# 🤖 CONFIGURACIÓN DE IA (GOOGLE GEMINI)
# =============================================================================
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("⚠️ ADVERTENCIA: No se encontró el secret 'GEMINI_API_KEY'.")
    modelo_ia = None
else:
    try:
        genai.configure(api_key=api_key)
        # Usamos Gemini Pro (Estándar y Estable)
        modelo_ia = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        print(f"Error al configurar Gemini: {e}")
        modelo_ia = None

def consultar_ia_profesor(caso, respuesta_alumno, analisis_tecnico):
    if modelo_ia is None:
        return "⚠️ Error: No se ha configurado la API Key. Revisa las variables de entorno en Render."

    prompt = f"""
    Actúa como un profesor experto de Kinesiología y Fisioterapia.
    
    CONTEXTO DEL CASO CLÍNICO:
    {caso['desc']}
    
    SOLUCIÓN ESPERADA:
    Equipos: {caso['solucion'].get('equipos')}
    Objetivos: {caso['solucion'].get('objetivos')}
    
    RESPUESTA DEL ALUMNO:
    {respuesta_alumno}
    
    ANÁLISIS TÉCNICO PREVIO:
    {analisis_tecnico}
    
    TU TAREA:
    1. Evalúa si el alumno entendió el objetivo clínico.
    2. Explica brevemente la fisiología si hay errores.
    3. Felicita si está bien y da un dato curioso clínico.
    4. Máximo 4 líneas.
    """
    
    try:
        response = modelo_ia.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ La IA no pudo responder. Error técnico: {str(e)}"

# =============================================================================
# 🗂️ BASE DE DATOS DE CASOS CLÍNICOS
# =============================================================================
DB_CASOS = {
    "Seleccionar Caso...": {"desc": "Por favor, selecciona un caso clínico para comenzar la simulación.", "solucion": {}},
    
    "1. Ruptura LCA (Debilidad M3)": {
        "desc": "Paciente de 24 años, deportista, 6ta semana postop LCA. Debilidad en extensores de rodilla por desuso (M3).",
        "solucion": {
            "equipos": ["Rusa", "TIF", "TENS"],
            "objetivos": ["fortalec", "tetaniz", "fuerza", "atrofia"],
            "Rusa": {"portadora": 2500, "burst_min": 20, "ratio": ["1:4", "1:5"]},
            "TIF": {"portadora_min": 2000, "portadora_max": 2500, "amf_min": 20},
            "TENS": {"freq_min": 20, "duracion_min": 200}
        }
    },
    "2. Esguince Tobillo Agudo (24h)": {
        "desc": "Paciente de 19 años, esguince hace 24 hrs. Edema en zona articular y dolor intenso (EVA 8/10).",
        "solucion": {
            "equipos": ["TIF", "TENS", "Farádica (Träbert)"],
            "objetivos": ["analgesia", "edema", "gate control", "drenaje"],
            "TIF": {"portadora": 4000, "amf_min": 80, "vector": "6:6"}, 
            "TENS": {"freq_min": 50, "duracion_max": 150},
            "Farádica (Träbert)": {"polaridad": "Normal"}
        }
    },
    "3. Denervación Radial (M1)": {
        "desc": "Paciente herido con arma blanca en brazo. Debilidad extensores muñeca (M1) y parestesia. Realice prueba UGT.",
        "solucion": {
            "equipos": ["Farádica (Triangular)"],
            "objetivos": ["ugt", "curva", "acomodacion", "triangular"],
            "Farádica (Triangular)": {"fase": [1000, 500], "pausa": [2000]}
        }
    },
    "4. Lumbalgia Crónica (8 meses)": {
        "desc": "Paciente de 55 años, dolor lumbar sordo de 8 meses. No responde a analgésicos comunes.",
        "solucion": {
            "equipos": ["TENS"],
            "objetivos": ["endorfinas", "descendente", "cronico", "analgesia", "burst"],
            "TENS": {"freq_max": 10, "duracion_min": 150}
        }
    },
    "5. Atrofia Cuádriceps (Encamado)": {
        "desc": "Paciente 70 años, encamado por neumonía. Debilidad generalizada, predominio cuádriceps (M2).",
        "solucion": {
            "equipos": ["Rusa", "TIF", "TENS"],
            "objetivos": ["fortalec", "tetaniz", "atrofia"],
            "Rusa": {"portadora": 2500, "burst_min": 20, "ratio": ["1:4", "1:5"]},
            "TIF": {"portadora_min": 2000, "portadora_max": 2500},
            "TENS": {"freq_min": 20, "duracion_min": 200}
        }
    },
    "6. Edema Pantorrilla Post-Traumático": {
        "desc": "Edema importante en gastrocnemios tras desgarro cicatrizado. Dolor 6/10.",
        "solucion": {
            "equipos": ["Rusa", "TIF"],
            "objetivos": ["bombeo", "drenaje", "edema", "fasciculacion"],
            "Rusa": {"burst_max": 10},
            "TIF": {"amf_max": 15}
        }
    },
    "7. Úlcera Talón (No cicatriza)": {
        "desc": "Úlcera en talón de 3 semanas. Dolor y debilidad.",
        "solucion": {
            "equipos": ["Microcorriente", "Alto Voltaje", "TENS"],
            "objetivos": ["cicatriz", "reparacion", "ulcera", "microcorriente"],
            "explicacion_extra": "Se recomienda Microcorrientes (MENS) o Alto Voltaje."
        }
    },
    "8. Epicondilitis Crónica (4 meses)": {
        "desc": "Tenista de 40 años, dolor epicóndilo lateral de 4 meses.",
        "solucion": {
            "equipos": ["TIF", "TENS"],
            "objetivos": ["analgesia", "dolor", "gate control"],
            "TIF": {"portadora": 4000, "amf_min": 80, "vector": "6:6"},
            "TENS": {"freq_min": 50}
        }
    },
    "9. Monitoreo Reinervación (Cronaxia)": {
        "desc": "Post-op hernia lumbar. Dificultad para elevar talones. Comprobar Cronaxia (Reobase 30mA).",
        "solucion": {
            "equipos": ["Farádica (Rectangular)"],
            "objetivos": ["cronaxia", "evaluacion", "diagnostico", "tiempo"],
            "Farádica (Rectangular)": {"busqueda_tiempo": True} 
        }
    },
    "10. Dolor Post-Qx Meniscos (Inmediato)": {
        "desc": "Operado hace 6 horas. Dolor agudo (EVA 9/10).",
        "solucion": {
            "equipos": ["TIF", "TENS"],
            "objetivos": ["analgesia", "agudo", "gate control"],
            "TIF": {"portadora": 4000, "amf_min": 80, "vector": "6:6"},
            "TENS": {"freq_min": 80, "duracion_max": 100}
        }
    },
    "11. Lesión Nervio Ulnar (Reobase)": {
        "desc": "Fractura consolidada húmero. Hormigueo mano medial. Obtener Reobase.",
        "solucion": {
            "equipos": ["Farádica (Rectangular)"],
            "objetivos": ["reobase", "umbral", "diagnostico"],
            "Farádica (Rectangular)": {"fase": [1000, 500]}
        }
    },
    "12. Tendinopatía Rotuliana Subaguda": {
        "desc": "Dolor tendón rotuliano, 3 semanas evolución. EVA 8/10.",
        "solucion": {
            "equipos": ["TIF", "TENS"],
            "objetivos": ["analgesia", "dolor", "gate control"],
            "TIF": {"portadora": 4000, "amf_min": 80},
            "TENS": {"freq_min": 50}
        }
    },
    "13. Úlcera Sacro (Post-op Cadera)": {
        "desc": "UPP en zona sacra, 2 semanas, no cicatriza.",
        "solucion": {
            "equipos": ["Microcorriente", "Alto Voltaje"],
            "objetivos": ["cicatriz", "ulcera", "reparacion"],
            "explicacion_extra": "Requiere corrientes de reparación tisular (Microcorriente/Alto Voltaje)."
        }
    },
    "14. Fractura Escafoides (No consolidada)": {
        "desc": "Fractura 4 meses, falta de consolidación.",
        "solucion": {
            "equipos": ["Ultrasonido"],
            "objetivos": ["lipus", "consolidacion", "oseo", "fractura"],
            "Ultrasonido": {"ciclo": "20% (1:4)", "intensidad_max": 0.5, "frecuencia": "1 MHz"} 
        }
    },
    "15. Acortamiento Banda Iliotibial": {
        "desc": "Corredora, dolor lateral rodilla. Banda tensa y acortada.",
        "solucion": {
            "equipos": ["Onda Corta", "Infrarrojo"],
            "objetivos": ["calor", "termico", "elongacion", "relajacion"],
            "Onda Corta": {"metodo": "Capacitivo (Campo Eléctrico)", "dosis_min_potencia": 6},
            "Infrarrojo": {"distancia_min": 40}
        }
    },
    "16. Artritis Reumatoide (Manos)": {
        "desc": "AR larga data, rigidez matutina. Piel delgada.",
        "solucion": {
            "equipos": ["Infrarrojo"],
            "objetivos": ["rigidez", "dolor", "calor superficial"],
            "Infrarrojo": {"distancia_min": 30, "tiempo_min": 20}
        }
    },
    "17. Esguince Talofibular Anterior (1 día)": {
        "desc": "Esguince agudo hace 1 día. Dolor 4/10. Sin edema importante.",
        "solucion": {
            "equipos": ["Ultrasonido"],
            "objetivos": ["reparacion", "regeneracion", "agudo", "lipus"],
            "Ultrasonido": {"ciclo": "20% (1:4)", "intensidad_max": 0.5} 
        }
    },
    "18. Tortícolis Aguda": {
        "desc": "Espasmo severo hace 48 hrs. Dolor trapecio/elevador.",
        "solucion": {
            "equipos": ["Onda Corta", "Infrarrojo"],
            "objetivos": ["relaja", "espasmo", "calor suave"],
            "Onda Corta": {"dosis_max_potencia": 15}, # Dosis II
            "Infrarrojo": {"distancia_min": 40}
        }
    },
    "19. Desgarro Isquiotibial (10 días)": {
        "desc": "Desgarro grado 1, hace 10 días. Sin edema.",
        "solucion": {
            "equipos": ["Onda Corta"],
            "objetivos": ["regeneracion", "flujo", "reparacion"],
            "Onda Corta": {"metodo": "Inductivo (Campo Magnético)", "dosis_min_potencia": 8} # Dosis II
        }
    },
    "20. Cicatriz Adherida Muñeca": {
        "desc": "Post fractura radio. Cicatriz fibrosa adherida.",
        "solucion": {
            "equipos": ["Ultrasonido"],
            "objetivos": ["adherencia", "fibrosis", "cicatriz"],
            "Ultrasonido": {"frecuencia": "3 MHz", "ciclo": "100% (Continuo)"}
        }
    },
    "21. Espasmo Dorsal Crónico": {
        "desc": "Obrero, espasmo crónico dorsal extenso.",
        "solucion": {
            "equipos": ["Onda Corta"],
            "objetivos": ["termico", "calor profundo", "relajacion"],
            "Onda Corta": {"metodo": "Inductivo (Campo Magnético)", "dosis_min_potencia": 30} # Dosis III/IV
        }
    }
}

# ==========================================
# 🧮 FUNCIONES AUXILIARES
# ==========================================
def calcular_media_live(modo, fase, freq, peak):
    if peak is None: peak = 0
    if fase is None: fase = 0
    if freq is None: freq = 0
    if modo == "Continuo (CSWD)": return peak
    else: return round(peak * (fase * 0.000001) * freq, 1)

# ==========================================
# 🧠 CEREBRO DE VALIDACIÓN
# ==========================================
def validar_tratamiento(
    caso_seleccionado, active_device, f_subtipo, 
    # PARAMETROS ELECTRO
    t_onda, t_tiempo, t_freq, t_duracion, t_mod_freq, t_recorrido, t_modo_cc, t_mod_amp, t_intensidad,
    r_onda, r_tiempo, r_freq_portadora_khz, r_freq_trabajo, r_freq_amf, r_ratio, r_modo_cc, r_ramp, r_on, r_off, r_intensidad,
    i_portadora, i_tiempo, i_amf, i_espectro, i_vector, i_ratio, i_ramp, i_on, i_off, i_intensidad,
    f_tiempo_sesion, f_polaridad, f_tiempo_fase, f_tiempo_pausa, f_modo_cc, f_intensidad,
    # PARAMETROS TERMO
    u_frecuencia, u_ciclo, u_intensidad, u_tiempo, u_era_ratio,
    oc_metodo, oc_tecnica, oc_modo, oc_fase, oc_frecuencia, oc_potencia, oc_media_resultante, oc_tiempo,
    ir_tipo, ir_distancia, ir_tiempo,
    # TEXTO
    p_respuesta_usuario
):
    feedback = []
    es_correcto_tecnico = True
    
    # 1. RECUPERAR DATOS DEL CASO
    if caso_seleccionado not in DB_CASOS or caso_seleccionado == "Seleccionar Caso...":
        return "<div style='background-color:#ef4444; color:white; padding:20px;'>⚠️ <b>Error:</b> Por favor selecciona un Caso Clínico en el menú superior antes de validar.</div>"
    
    datos_caso = DB_CASOS[caso_seleccionado]
    solucion_caso = datos_caso["solucion"]
    
    feedback.append(f"📂 **Evaluando sobre:** {caso_seleccionado}")

    # 2. VALIDACIÓN DE EQUIPO CORRECTO
    equipos_aceptados = solucion_caso.get("equipos", [])
    equipo_actual_normalizado = active_device
    if "Farádica" in active_device: equipo_actual_normalizado = f"Farádica ({f_subtipo})"
    
    equipo_valido = False
    for eq in equipos_aceptados:
        if eq in equipo_actual_normalizado or (active_device == "Onda Corta" and eq == "Onda Corta"):
            equipo_valido = True
            break
            
    if not equipo_valido:
        es_correcto_tecnico = False
        feedback.append(f"❌ **Equipo Incorrecto:** Has seleccionado **{active_device}**, pero este caso clínico se trata mejor con: **{', '.join(equipos_aceptados)}**.")
    else:
        feedback.append(f"✅ **Equipo Correcto:** {active_device} es una buena elección para este caso.")

    # 3. VALIDACIÓN DE PARÁMETROS TÉCNICOS (SI EL EQUIPO ES EL CORRECTO)
    if equipo_valido:
        if active_device == "Ultrasonido" and "Ultrasonido" in solucion_caso:
            rules = solucion_caso["Ultrasonido"]
            if "ciclo" in rules and u_ciclo != rules["ciclo"]:
                es_correcto_tecnico = False
                feedback.append(f"❌ **Duty Cycle:** Usaste {u_ciclo}, pero el caso requiere **{rules['ciclo']}**.")
            if "frecuencia" in rules and u_frecuencia != rules["frecuencia"]:
                es_correcto_tecnico = False
                feedback.append(f"❌ **Frecuencia:** Usaste {u_frecuencia}, pero la profundidad requiere **{rules['frecuencia']}**.")
            if "intensidad_max" in rules and u_intensidad > rules["intensidad_max"]:
                feedback.append(f"⚠️ **Intensidad:** {u_intensidad} W/cm² es alta. Sugerido: <{rules['intensidad_max']}.")

        elif active_device == "Onda Corta" and "Onda Corta" in solucion_caso:
            rules = solucion_caso["Onda Corta"]
            p_media = oc_media_resultante if oc_media_resultante else 0
            if "metodo" in rules and oc_metodo != rules["metodo"]:
                feedback.append(f"⚠️ **Método:** Se sugiere **{rules['metodo']}**.")
            if "dosis_min_potencia" in rules and p_media < rules["dosis_min_potencia"]:
                es_correcto_tecnico = False
                feedback.append(f"❌ **Dosis Insuficiente:** {p_media}W. Mínimo requerido: {rules['dosis_min_potencia']}W.")
            elif "dosis_max_potencia" in rules and p_media > rules["dosis_max_potencia"]:
                es_correcto_tecnico = False
                feedback.append(f"🛑 **Dosis Excesiva:** {p_media}W. Máximo sugerido: {rules['dosis_max_potencia']}W.")

        elif active_device == "TENS" and "TENS" in solucion_caso:
            rules = solucion_caso["TENS"]
            if "freq_min" in rules and t_freq < rules["freq_min"]: feedback.append("❌ **Frecuencia:** Muy baja.")
            elif "freq_max" in rules and t_freq > rules["freq_max"]: feedback.append("❌ **Frecuencia:** Muy alta.")

        elif active_device == "TIF" and "TIF" in solucion_caso:
            rules = solucion_caso["TIF"]
            if "portadora" in rules and i_portadora != rules["portadora"]: feedback.append("❌ **Portadora:** Incorrecta.")
            if "portadora_min" in rules and i_portadora < rules["portadora_min"]: feedback.append("❌ **Portadora:** Muy baja.")

        elif "Farádica" in active_device and active_device in solucion_caso:
            rules = solucion_caso[active_device]
            if "polaridad" in rules and f_polaridad != rules["polaridad"]: feedback.append("❌ **Polaridad:** Incorrecta.")
            if "busqueda_tiempo" in rules and f_tiempo_fase > 100: feedback.append("❌ **Estrategia:** Debes buscar tiempos bajos (Cronaxia).")

    # 4. CONSULTA A LA IA (FEEDBACK PROFESOR)
    feedback_str = "\n".join(feedback)
    config_alumno = f"Equipo: {active_device}. "
    if active_device == "Ultrasonido": config_alumno += f"Frec: {u_frecuencia}, Ciclo: {u_ciclo}, Int: {u_intensidad}"
    elif active_device == "Onda Corta": config_alumno += f"Método: {oc_metodo}, Media: {oc_media_resultante}W"
    
    mensaje_ia = consultar_ia_profesor(
        caso=datos_caso,
        respuesta_alumno=f"{config_alumno}. Justificación: {p_respuesta_usuario}",
        analisis_tecnico=feedback_str
    )

    # 5. GENERACIÓN HTML FINAL
    color_borde = "#10B981" if es_correcto_tecnico else "#EF4444"
    icono = "🎉" if es_correcto_tecnico else "⚠️"
    
    html = f"""
    <div style="background-color: #0f172a !important; color: #f8fafc !important; padding: 25px; border-radius: 12px; border: 3px solid {color_borde}; font-family: sans-serif;">
        <h3 style="margin-top:0; border-bottom:1px solid #334155; padding-bottom:10px; color: #f8fafc !important;">{icono} Resultado: {caso_seleccionado}</h3>
        
        <div style="margin-bottom:20px;">
            <h4 style="color:#38bdf8 !important; margin:10px 0;">📊 Validación Técnica</h4>
            <ul style="padding-left: 20px; color:#e2e8f0 !important; font-size: 1.05em;">
                {''.join([f"<li style='margin-bottom:5px;'>{item}</li>" for item in feedback])}
            </ul>
        </div>
        
        <div style="background-color: #1e293b !important; padding: 20px; border-radius: 10px; border-left: 5px solid #8b5cf6;">
            <h4 style="color: #a78bfa !important; margin-top: 0; margin-bottom: 10px;">🤖 Feedback Docente (IA)</h4>
            <p style="font-size: 1.1em; line-height: 1.6; color: #f1f5f9 !important;">{mensaje_ia}</p>
        </div>
    </div>
    """
    return html

# ==========================================
# 🎨 INTERFAZ GRÁFICA (CSS REFORZADO)
# ==========================================
theme = gr.themes.Soft(primary_hue="cyan", secondary_hue="slate", neutral_hue="slate").set(
    body_background_fill="#f1f5f9", block_background_fill="#ffffff", input_background_fill="#f8fafc"
)

# CSS que fuerza el texto negro en inputs y arregla el error de los campos calculados
custom_css = """
body, .gradio-container { background-color: #f8fafc; color: #1e293b !important; }
.prose, .markdown, label, span, p, h1, h2, h3 { color: #1e293b !important; }

/* INPUTS NORMALES */
input, textarea, .gr-input { 
    color: #000000 !important; 
    background-color: #ffffff !important; 
    opacity: 1 !important;
}

/* INPUTS DESHABILITADOS (Calculados): Fondo gris, texto negro FUERTE */
input:disabled, input[disabled], textarea:disabled {
    color: #000000 !important;
    background-color: #e2e8f0 !important;
    -webkit-text-fill-color: #000000 !important;
    opacity: 1 !important;
    font-weight: 800 !important; /* Más negrita para que se lea bien */
}

/* COMPONENTES OSCUROS */
.menu-card { background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%) !important; color: white !important; font-weight: 600 !important; }
.cat-card { background: linear-gradient(135deg, #475569 0%, #64748b 100%) !important; color: white !important; font-weight: 700 !important; }
.validar-btn { background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important; color: white !important; font-weight: bold !important; font-size: 1.1em !important; }
.menu-card *, .cat-card *, .validar-btn * { color: white !important; }

/* CAJA INFO CASO */
.info-bar { 
    background-color: #fef9c3 !important; 
    color: #854d0e !important; 
    padding: 15px; 
    border: 1px solid #fde047; 
    margin-bottom: 15px; 
    font-weight: 500; 
}
.info-bar p, .info-bar strong { color: #854d0e !important; }
"""

with gr.Blocks(theme=theme, css=custom_css, title="Simulador Clínico") as demo:
    
    active_device_state = gr.State(value="Ninguno")
    f_subtipo_state = gr.State(value="")
    
    with gr.Group(visible=True) as case_screen:
        gr.Markdown("# 🏥 Simulador de Agentes Físicos\n### Selecciona un Caso Clínico para comenzar:")
        case_dropdown = gr.Dropdown(choices=list(DB_CASOS.keys()), value="Seleccionar Caso...", label="📚 Lista de Casos", interactive=True)
        case_desc_display = gr.Markdown(value="ℹ️ Selecciona un caso para ver su descripción...", elem_classes=["info-bar"])
        btn_start_simulation = gr.Button("🚀 Iniciar Simulación", variant="primary")

    with gr.Group(visible=False) as main_interface:
        with gr.Row():
            btn_change_case = gr.Button("🔄 Cambiar Caso", size="sm", variant="secondary")
            current_case_banner = gr.Markdown(value="", elem_classes=["info-bar"])

        with gr.Group(visible=True) as main_selection:
            with gr.Row():
                btn_cat_electro = gr.Button("⚡ Electroterapia", elem_classes=["cat-card"])
                btn_cat_thermo = gr.Button("🔥 Termoterapia", elem_classes=["cat-card"])

        with gr.Group(visible=False) as menu_electro:
            with gr.Row(): btn_back_home_el = gr.Button("⬅ Volver", variant="secondary", size="sm"); gr.Markdown("### ⚡ Electroterapia")
            with gr.Row(): btn_tens = gr.Button("⚡ TENS", elem_classes=["menu-card"]); btn_rusa = gr.Button("💪 Rusa", elem_classes=["menu-card"])
            with gr.Row(): btn_tif = gr.Button("〰️ TIF", elem_classes=["menu-card"]); btn_faradica_menu = gr.Button("📉 Farádica", elem_classes=["menu-card"])

        with gr.Group(visible=False) as menu_faradica:
            with gr.Row(): btn_back_electro = gr.Button("⬅ Volver", variant="secondary", size="sm"); gr.Markdown("### 🔍 Farádica")
            with gr.Row(): btn_trabert = gr.Button("Träbert", elem_classes=["menu-card"]); btn_rectangular = gr.Button("Rectangular", elem_classes=["menu-card"]); btn_triangular = gr.Button("Triangular", elem_classes=["menu-card"])

        with gr.Group(visible=False) as menu_thermo:
            with gr.Row(): btn_back_home_th = gr.Button("⬅ Volver", variant="secondary", size="sm"); gr.Markdown("### 🔥 Termoterapia")
            with gr.Row(): btn_us = gr.Button("💧 Ultrasonido", elem_classes=["menu-card"]); btn_oc = gr.Button("📻 Onda Corta", elem_classes=["menu-card"]); btn_ir = gr.Button("🔴 Infrarrojo", elem_classes=["menu-card"])

        # INTERFACES DE EQUIPOS (Todas ocultas al inicio)
        with gr.Group(visible=False) as interface_tens:
            with gr.Row(): btn_back_tens = gr.Button("⬅ Menú", variant="secondary", size="sm"); gr.Markdown("### TENS")
            with gr.Column():
                t_onda = gr.Dropdown(["Bifásica Simétrica", "Bifásica Asimétrica"], label="Onda")
                t_tiempo = gr.Number(label="Tiempo (min)", value=0)
                with gr.Row(): t_freq = gr.Number(label="Frecuencia (Hz)", value=0); t_duracion = gr.Number(label="Duración (µs)", value=0)
                with gr.Row(): t_mod_freq = gr.Number(label="Mod. Frec", value=0); t_mod_amp = gr.Number(label="Mod. Amp", value=0); t_recorrido = gr.Number(label="Recorrido", value=0)
                t_modo_cc = gr.Radio(["CC", "CV"], label="Modo", value="CC"); t_intensidad = gr.Number(label="Intensidad (mA)", value=0)

        with gr.Group(visible=False) as interface_rusa:
            with gr.Row(): btn_back_rusa = gr.Button("⬅ Menú", variant="secondary", size="sm"); gr.Markdown("### Rusa")
            with gr.Column():
                r_onda = gr.Dropdown(["Rusa (Sinusoidal)", "Cuadrada"], label="Onda", value="Rusa (Sinusoidal)"); r_tiempo = gr.Number(label="Tiempo", value=0)
                with gr.Row(): r_freq_portadora_khz = gr.Number(label="Portadora (kHz)", value=0); r_freq_trabajo = gr.Number(label="Trabajo (Hz)", value=0); r_freq_amf = gr.Number(label="AMF", value=0)
                r_ratio = gr.Dropdown(["1:1", "1:2", "1:4", "1:5"], label="Ratio", value="1:2"); r_modo_cc = gr.Radio(["CC", "CV"], label="Modo", value="CC")
                with gr.Row(): r_ramp = gr.Number(label="Rampa", value=0); r_on = gr.Number(label="ON", value=0); r_off = gr.Number(label="OFF", value=0)
                r_intensidad = gr.Number(label="Intensidad", value=0)

        with gr.Group(visible=False) as interface_tif:
            with gr.Row(): btn_back_tif = gr.Button("⬅ Menú", variant="secondary", size="sm"); gr.Markdown("### TIF")
            with gr.Column():
                i_portadora = gr.Number(label="Portadora (Hz)", value=0); i_tiempo = gr.Number(label="Tiempo", value=0)
                with gr.Row(): i_amf = gr.Number(label="AMF (Hz)", value=0); i_espectro = gr.Number(label="Espectro (Hz)", value=0); i_vector = gr.Dropdown(["Manual/Off", "6:6", "1:30:1:30", "1:1"], label="Vector", value="Manual/Off")
                with gr.Row(): i_ratio = gr.Dropdown(["Seleccionar...", "1:1", "1:2", "1:4"], label="Ratio", value="Seleccionar..."); i_ramp = gr.Number(label="Rampa", value=0); i_on = gr.Number(label="ON", value=0); i_off = gr.Number(label="OFF", value=0)
                i_intensidad = gr.Number(label="Intensidad (mA)", value=0)

        with gr.Group(visible=False) as interface_faradica:
            with gr.Row(): btn_back_faradica = gr.Button("⬅ Menú", variant="secondary", size="sm"); lbl_titulo_faradica = gr.Markdown("#### Farádica")
            with gr.Column():
                f_polaridad = gr.Dropdown(["Normal", "Inversión Automática"], label="Polaridad", value="Normal"); f_tiempo_sesion = gr.Number(label="Tiempo", value=0)
                with gr.Row(): f_tiempo_fase = gr.Number(label="Fase (ms)", value=0, interactive=True); f_tiempo_pausa = gr.Number(label="Pausa (ms)", value=0, interactive=True)
                f_modo_cc = gr.Radio(["CC", "CV"], label="Modo", value="CC"); f_intensidad = gr.Number(label="Intensidad (mA)", value=0)

        with gr.Group(visible=False) as interface_us:
            with gr.Row(): btn_back_us = gr.Button("⬅ Menú", variant="secondary", size="sm"); gr.Markdown("### Ultrasonido")
            with gr.Column():
                with gr.Row(): u_frecuencia = gr.Radio(["1 MHz", "3 MHz"], label="Frecuencia"); u_tiempo = gr.Number(label="Tiempo", value=0)
                with gr.Row(): u_ciclo = gr.Dropdown(["100% (Continuo)", "50% (1:1)", "20% (1:4)", "10%"], label="Duty Cycle"); u_era_ratio = gr.Dropdown(["1x ERA", "2x ERA", "> 3x ERA"], label="Área")
                u_intensidad = gr.Number(label="Intensidad (W/cm²)", value=0.0, step=0.1)

        with gr.Group(visible=False) as interface_oc:
            with gr.Row(): btn_back_oc = gr.Button("⬅ Menú", variant="secondary", size="sm"); gr.Markdown("### Onda Corta")
            with gr.Column():
                with gr.Row(): oc_metodo = gr.Dropdown(["Seleccionar...", "Capacitivo (Campo Eléctrico)", "Inductivo (Campo Magnético)"], label="Método", value="Seleccionar..."); oc_tecnica = gr.Dropdown(["Coplanar", "Contraplanar", "Longitudinal", "Monodo/Tambor"], label="Técnica", value="Coplanar")
                with gr.Row(): oc_modo = gr.Radio(["Pulsado (PSWD)", "Continuo (CSWD)"], label="Modo", value="Pulsado (PSWD)"); oc_tiempo = gr.Number(label="Tiempo (min)", value=0)
                with gr.Row(): oc_fase = gr.Number(label="Ancho Pulso (µs)", value=0); oc_frecuencia = gr.Number(label="Frecuencia (Hz)", value=0)
                with gr.Row(): oc_potencia = gr.Number(label="Potencia Pico (W)", value=0); oc_media_resultante = gr.Number(label="Media (W)", value=0, interactive=False)

        with gr.Group(visible=False) as interface_ir:
            with gr.Row(): btn_back_ir = gr.Button("⬅ Menú", variant="secondary", size="sm"); gr.Markdown("### Infrarrojo")
            with gr.Column():
                ir_tipo = gr.Radio(["Luminoso", "No Luminoso"], label="Tipo"); ir_tiempo = gr.Number(label="Tiempo", value=0); ir_distancia = gr.Number(label="Distancia (cm)", value=0)

        with gr.Group(visible=False) as zona_validacion:
            gr.Markdown("---")
            gr.Markdown("### 📝 Validación del Caso")
            with gr.Row():
                p_respuesta_usuario = gr.Textbox(label="Justificación Clínica", placeholder="Escribe aquí por qué elegiste este tratamiento...", lines=2)
                btn_validar = gr.Button("✅ Validar Decisión", elem_classes=["validar-btn"])
            output_feedback = gr.HTML()

    # EVENTOS DE LA INTERFAZ
    def update_case_info(case_name): 
        if case_name in DB_CASOS:
            return f"ℹ️ **Descripción:** {DB_CASOS[case_name]['desc']}"
        return ""
    
    case_dropdown.change(fn=update_case_info, inputs=case_dropdown, outputs=case_desc_display)

    def start_sim(case_name):
        if case_name == "Seleccionar Caso...": return {case_screen: gr.update(visible=True)}
        
        texto_completo = f"""
        <div style="color: #854d0e;">
        <strong>📂 CASO ACTIVO:</strong> {case_name}<br><br>
        <strong>📝 Historia y Síntomas:</strong><br>
        {DB_CASOS[case_name]['desc']}
        </div>
        """
        return {
            case_screen: gr.update(visible=False), main_interface: gr.update(visible=True),
            current_case_banner: gr.update(value=texto_completo),
            main_selection: gr.update(visible=True), menu_electro: gr.update(visible=False), menu_thermo: gr.update(visible=False),
            zona_validacion: gr.update(visible=False), output_feedback: gr.update(value="")
        }
    btn_start_simulation.click(fn=start_sim, inputs=case_dropdown, outputs=[case_screen, main_interface, current_case_banner, main_selection, menu_electro, menu_thermo, zona_validacion, output_feedback])

    btn_change_case.click(lambda: {case_screen: gr.update(visible=True), main_interface: gr.update(visible=False)}, outputs=[case_screen, main_interface])

    # Cálculos en tiempo real
    oc_fase.change(fn=calcular_media_live, inputs=[oc_modo, oc_fase, oc_frecuencia, oc_potencia], outputs=oc_media_resultante)
    oc_frecuencia.change(fn=calcular_media_live, inputs=[oc_modo, oc_fase, oc_frecuencia, oc_potencia], outputs=oc_media_resultante)
    oc_potencia.change(fn=calcular_media_live, inputs=[oc_modo, oc_fase, oc_frecuencia, oc_potencia], outputs=oc_media_resultante)
    oc_modo.change(fn=calcular_media_live, inputs=[oc_modo, oc_fase, oc_frecuencia, oc_potencia], outputs=oc_media_resultante)

    # Navegación entre menús
    def hide_all():
        return {
            main_selection: gr.update(visible=False), menu_electro: gr.update(visible=False), menu_faradica: gr.update(visible=False), menu_thermo: gr.update(visible=False),
            interface_tens: gr.update(visible=False), interface_rusa: gr.update(visible=False), interface_tif: gr.update(visible=False), interface_faradica: gr.update(visible=False),
            interface_us: gr.update(visible=False), interface_oc: gr.update(visible=False), interface_ir: gr.update(visible=False),
            zona_validacion: gr.update(visible=False), output_feedback: gr.update(value="")
        }
    
    all_panels = [main_selection, menu_electro, menu_faradica, menu_thermo, interface_tens, interface_rusa, interface_tif, interface_faradica, interface_us, interface_oc, interface_ir, zona_validacion, output_feedback]

    def to_el(): res = hide_all(); res[menu_electro] = gr.update(visible=True); return [res[c] for c in all_panels]
    def to_th(): res = hide_all(); res[menu_thermo] = gr.update(visible=True); return [res[c] for c in all_panels]
    btn_cat_electro.click(to_el, outputs=all_panels); btn_cat_thermo.click(to_th, outputs=all_panels)

    def open_iface(name, panel):
        res = hide_all(); res[panel] = gr.update(visible=True); res[zona_validacion] = gr.update(visible=True)
        return [res[c] for c in all_panels] + [name]

    btn_tens.click(lambda: open_iface("TENS", interface_tens), outputs=all_panels + [active_device_state])
    btn_rusa.click(lambda: open_iface("Rusa", interface_rusa), outputs=all_panels + [active_device_state])
    btn_tif.click(lambda: open_iface("TIF", interface_tif), outputs=all_panels + [active_device_state])
    btn_us.click(lambda: open_iface("Ultrasonido", interface_us), outputs=all_panels + [active_device_state])
    btn_oc.click(lambda: open_iface("Onda Corta", interface_oc), outputs=all_panels + [active_device_state])
    btn_ir.click(lambda: open_iface("Infrarrojo", interface_ir), outputs=all_panels + [active_device_state])

    btn_faradica_menu.click(lambda: (hide_all().update({menu_faradica: gr.update(visible=True)}) and [hide_all()[c] if c != menu_faradica else gr.update(visible=True) for c in all_panels] + ["Farádica"]), outputs=all_panels + [active_device_state])

    def open_fara(sub, tit, f, p):
        res = hide_all(); res[interface_faradica] = gr.update(visible=True); res[zona_validacion] = gr.update(visible=True)
        return [res[c] for c in all_panels] + [gr.update(value=tit), f, p, sub]

    btn_trabert.click(lambda: open_fara("Träbert", "### ⚡ Config: Träbert", 2, 5), outputs=all_panels + [lbl_titulo_faradica, f_tiempo_fase, f_tiempo_pausa, f_subtipo_state])
    btn_rectangular.click(lambda: open_fara("Rectangular", "### 📉 Config: Rectangular", 0, 0), outputs=all_panels + [lbl_titulo_faradica, f_tiempo_fase, f_tiempo_pausa, f_subtipo_state])
    btn_triangular.click(lambda: open_fara("Triangular", "### 🔺 Config: Triangular", 0, 0), outputs=all_panels + [lbl_titulo_faradica, f_tiempo_fase, f_tiempo_pausa, f_subtipo_state])

    def back_home(): res = hide_all(); res[main_selection] = gr.update(visible=True); return [res[c] for c in all_panels]
    def back_el(): res = hide_all(); res[menu_electro] = gr.update(visible=True); return [res[c] for c in all_panels]
    def back_th(): res = hide_all(); res[menu_thermo] = gr.update(visible=True); return [res[c] for c in all_panels]
    def back_fa(): res = hide_all(); res[menu_faradica] = gr.update(visible=True); return [res[c] for c in all_panels]

    btn_back_home_el.click(back_home, outputs=all_panels); btn_back_home_th.click(back_home, outputs=all_panels)
    btn_back_tens.click(back_el, outputs=all_panels); btn_back_rusa.click(back_el, outputs=all_panels); btn_back_tif.click(back_el, outputs=all_panels); btn_back_electro.click(back_el, outputs=all_panels)
    btn_back_us.click(back_th, outputs=all_panels); btn_back_oc.click(back_th, outputs=all_panels); btn_back_ir.click(back_th, outputs=all_panels)
    btn_back_faradica.click(back_fa, outputs=all_panels)

    # Botón de validación
    btn_validar.click(
        fn=validar_tratamiento,
        inputs=[
            case_dropdown, active_device_state, f_subtipo_state,
            t_onda, t_tiempo, t_freq, t_duracion, t_mod_freq, t_recorrido, t_modo_cc, t_mod_amp, t_intensidad,
            r_onda, r_tiempo, r_freq_portadora_khz, r_freq_trabajo, r_freq_amf, r_ratio, r_modo_cc, r_ramp, r_on, r_off, r_intensidad,
            i_portadora, i_tiempo, i_amf, i_espectro, i_vector, i_ratio, i_ramp, i_on, i_off, i_intensidad,
            f_tiempo_sesion, f_polaridad, f_tiempo_fase, f_tiempo_pausa, f_modo_cc, f_intensidad,
            u_frecuencia, u_ciclo, u_intensidad, u_tiempo, u_era_ratio,
            oc_metodo, oc_tecnica, oc_modo, oc_fase, oc_frecuencia, oc_potencia, oc_media_resultante, oc_tiempo,
            ir_tipo, ir_distancia, ir_tiempo,
            p_respuesta_usuario
        ],
        outputs=output_feedback
    )

if __name__ == "__main__":
    # IMPORTANTE PARA RENDER: Escuchar en 0.0.0.0
    demo.launch(server_name="0.0.0.0", server_port=7860)