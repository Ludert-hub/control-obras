import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Control de Obras y Materiales - Ludert",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilos CSS con botones 3D estilo Neón / Brillo (Igual a tu referencia)
st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
    }
    
    /* Efecto 3D / Brillo tipo Píldora para los botones de Streamlit */
    .stButton>button {
        width: 100%;
        background: linear-gradient(to bottom, #2ea043, #1f7b31);
        color: white;
        font-size: 16px;
        font-weight: bold;
        padding: 14px 24px;
        border-radius: 30px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.4), 0 6px 12px rgba(0, 0, 0, 0.4);
        transition: all 0.2s ease;
        margin-top: 10px;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton>button:hover {
        background: linear-gradient(to bottom, #3fb950, #2ea043);
        box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.6), 0 8px 16px rgba(0, 0, 0, 0.6);
        transform: translateY(-2px);
    }

    /* Tarjetas KPI y Alertas flotantes */
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 20px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
    .alert-card {
        background-color: #2d1515;
        border-left: 6px solid #da3633;
        padding: 18px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
    h1, h2, h3, h4 {
        color: #f0f6fc;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Encabezado Principal
st.markdown(
    "<h1>🏗️ Control de Obras y Materiales</h1>", unsafe_allow_html=True
)
st.markdown(
    "<p style='color: #8b949e; font-size: 16px;'>⚡ Panel táctil optimizado con diseño moderno.</p>",
    unsafe_allow_html=True,
)

# Sección de Alerta de Créditos
with st.container():
  st.markdown(
      """
        <div class="alert-card">
            <h4 style="margin: 0 0 10px 0; color: #f85149;">🚨 Alerta de Créditos (Próximos a cumplir 15 días):</h4>
            <ul style="margin: 0; padding-left: 20px; color: #e6edf3; font-size: 15px;">
                <li><b>23/09/2026</b> | Obra: <span style="color: #ff7b72;">SRA. BARBARA (MANGO CENTER)</span> | Bs. 312.244,52 | <span style="color: #f85149;"><b>23 días (¡VENCIDO!)</b></span></li>
                <li><b>28/09/2026</b> | Obra: <span style="color: #ff7b72;">ESOBADES (MANGO CENTER)</span> | Bs. 84.615,49 | <span style="color: #f85149;"><b>18 días (¡VENCIDO!)</b></span></li>
                <li><b>29/09/2026</b> | Obra: <span style="color: #ff7b72;">ESOBADES (MANGO CENTER)</span> | Bs. 175.859,04 | <span style="color: #f85149;"><b>17 días (¡VENCIDO!)</b></span></li>
                <li><b>30/09/2026</b> | Obra: <span style="color: #ff7b72;">ESOBADES (MANGO CENTER)</span> | Bs. 49.998,45 | <span style="color: #f85149;"><b>16 días (¡VENCIDO!)</b></span></li>
                <li><b>02/10/2026</b> | Obra: <span style="color: #ff7b72;">ESOBADES (MANGO CENTER)</span> | Bs. 378.856,27 | <span style="color: #d29922;"><b>14 días (Quedan 1 día)</b></span></li>
            </ul>
        </div>
    """,
      unsafe_allow_html=True,
  )

# Pestañas de navegación
tab1, tab2, tab3 = st.tabs(
    ["💰 Facturas y Gastos", "📋 Tareas y Cuadrilla", "📊 Reportes y Gráficos"]
)

with tab1:
  st.markdown("### 📊 Resumen General de Gastos")

  col_m1, col_m2 = st.columns(2)
  with col_m1:
    st.markdown(
        """
        <div class="metric-card">
            <p style="color: #8b949e; margin:0; font-size: 14px;">TOTAL GENERAL</p>
            <h3 style="color: #3fb950; margin:8px 0 0 0;">Bs. 12.155.247,88</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with col_m2:
    st.markdown(
        """
        <div class="metric-card">
            <p style="color: #8b949e; margin:0; font-size: 14px;">ESTADO DEL SISTEMA</p>
            <h3 style="color: #58a6ff; margin:8px 0 0 0;">En Línea ⚡</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)
  obra_filtro = st.selectbox(
      "🔍 Filtrar gastos por Obra:", ["Todas", "ESOBADES", "SRA. BARBARA"]
  )

  data_gastos = {
      "Fecha": [
          "12/10/2026",
          "12/10/2026",
          "12/10/2026",
          "09/10/2026",
          "08/10/2026",
      ],
      "Obra": ["ESOBADES", "ESOBADES", "ESOBADES", "ESOBADES", "ESOBADES"],
      "Monto (Bs.)": ["7.451,78", "16.004,84", "83.834,36", "9.913,77", "481.199,98"],
      "Descripción": [
          "[ECOVIDA] INSUMOS DE LIMPIEZA",
          "[CREDITO]",
          "[CREDITO]",
          "[LUDERT] CLAVOS PARA MACHIMBRADO",
          "[CREDITO]",
      ],
      "Observaciones": ["", "MANGO CENTER", "MANGO CENTER", "", "MANGO CENTER"],
  }
  df_gastos = pd.DataFrame(data_gastos)
  st.dataframe(df_gastos, use_container_width=True)

  st.markdown("### ⚡ Botones de Acción Táctil")
  col_b1, col_b2, col_b3 = st.columns(3)
  with col_b1:
    btn_ver = st.button("👁️ Ver Comprobante")
  with col_b2:
    btn_mod = st.button("✏️ Modificar Gasto")
  with col_b3:
    btn_del = st.button("🗑️ Eliminar Gasto")

  if btn_ver:
    st.info("Abriendo visor de comprobante...")
  if btn_mod:
    st.warning("Panel de modificación activado...")
  if btn_del:
    st.error("Modo de eliminación seleccionado...")

with tab2:
  st.markdown("### 📋 Lista de Tareas y Pendientes de Obra")

  with st.form("form_tarea_tactil"):
    t_obra = st.selectbox(
        "Obra / Destino", ["-- SELECCIONAR --", "GENERAL", "PDVSA", "ECOVIDA"]
    )
    t_desc = st.text_input(
        "Descripción de la tarea", placeholder="Ej. Esmalte en columnas..."
    )
    t_estado = st.selectbox("Estado inicial", ["PENDIENTE", "LISTO"])
    submit_tarea = st.form_submit_button("➕ AGREGAR NUEVA TAREA")

  data_tareas = {
      "Descripción": [
          "REVISAR LO DEL CAMIÓN (FALLA)",
          "IR A LO DEL MUEBLE",
          "LLEVAR EL MOBILIARIO A LA OFICINA NUEVA",
      ],
      "Estado": ["⏳ PENDIENTE", "⏳ PENDIENTE", "✅ LISTO"],
      "Obra": ["GENERAL", "PDVSA", "ECOVIDA"],
      "Fecha": ["12/10/2026", "12/10/2026", "12/10/2026"],
  }
  df_tareas = pd.DataFrame(data_tareas)
  st.dataframe(df_tareas, use_container_width=True)

with tab3:
  st.markdown("### 📊 Reportes, Desglose y Exportación")

  col_f1, col_f2 = st.columns(2)
  with col_f1:
    st.selectbox("Filtrar por Obra:", ["TODAS", "ESOBADES", "SRA. BARBARA"])
  with col_f2:
    st.selectbox("Filtrar por Origen de Fondos:", ["TODOS", "CRÉDITO", "CONTADO"])

  col_e1, col_e2 = st.columns(2)
  with col_e1:
    if st.button("📥 Descargar Excel (CSV)"):
      st.success("¡Reporte generado!")
  with col_e2:
    if st.button("💬 Enviar WhatsApp"):
      st.success("¡Enlace de WhatsApp listo!")

  st.markdown("<br>", unsafe_allow_html=True)

  chart_data = pd.DataFrame(
      {
          "Obra": ["ESOBADES", "SRA. BARBARA", "PDVSA", "ECOVIDA"],
          "Gastos": [8500000, 2500000, 855247, 300000],
      }
  )

  fig = px.bar(
      chart_data,
      x="Obra",
      y="Gastos",
      text="Gastos",
      color="Obra",
      title="Distribución de Gastos por Obra (Bs.)",
  )
  fig.update_layout(
      plot_bgcolor="rgba(0,0,0,0)",
      paper_bgcolor="rgba(0,0,0,0)",
      font_color="#f0f6fc",
  )
  fig.update_traces(marker=dict(line=dict(width=1, color="white")))
  st.plotly_chart(fig, use_container_width=True)