import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Control de Obras y Materias - Ludert",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados para un look moderno y profesional
st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .alert-card {
        background-color: #2d1515;
        border-left: 5px solid #da3633;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    h1, h2, h3 {
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
    "<p style='color: #8b949e;'>Sistema sincronizado en tiempo real (PC y Teléfonos).</p>",
    unsafe_allow_html=True,
)

# Sección de Alerta de Créditos (Diseño Moderno)
with st.container():
    st.markdown(
        """
        <div class="alert-card">
            <h4 style="margin: 0 0 10px 0; color: #f85149;">🚨 Alerta de Créditos (Próximos a cumplir 15 días):</h4>
            <ul style="margin: 0; padding-left: 20px; color: #e6edf3;">
                <li><b>23/09/2026</b> | Obra: <span style="color: #ff7b72;">SRA. BARBARA (MANGO CENTER)</span> | Bs. 312.244,52 | <span style="color: #f85149;">23 días transcurridos (¡VENCIDO!)</span></li>
                <li><b>28/09/2026</b> | Obra: <span style="color: #ff7b72;">ESOBADES (MANGO CENTER)</span> | Bs. 84.615,49 | <span style="color: #f85149;">18 días transcurridos (¡VENCIDO!)</span></li>
                <li><b>29/09/2026</b> | Obra: <span style="color: #ff7b72;">ESOBADES (MANGO CENTER)</span> | Bs. 175.859,04 | <span style="color: #f85149;">17 días transcurridos (¡VENCIDO!)</span></li>
                <li><b>30/09/2026</b> | Obra: <span style="color: #ff7b72;">ESOBADES (MANGO CENTER)</span> | Bs. 49.998,45 | <span style="color: #f85149;">16 días transcurridos (¡VENCIDO!)</span></li>
                <li><b>02/10/2026</b> | Obra: <span style="color: #ff7b72;">ESOBADES (MANGO CENTER)</span> | Bs. 378.856,27 | <span style="color: #d29922;">14 días transcurridos (Quedan 1 día(s))</span></li>
            </ul>
        </div>
    """,
        unsafe_allow_html=True,
    )

# Pestañas principales de navegación
tab1, tab2, tab3 = st.tabs(
    ["💰 Facturas y Gastos", "📋 Tareas Programadas", "📊 Reportes y Desglose"]
)

with tab1:
  st.markdown("### 📊 Resumen de Gastos y Facturas")

  # Métrica principal en Tarjeta
  col1, col2 = st.columns([1, 2])
  with col1:
    st.metric(
        label="Total General de Gastos",
        value="Bs. 12.155.247,88",
        delta="Actualizado",
    )

  # Filtro
  obra_filtro = st.selectbox(
      "Filtrar gastos por Obra:", ["Todas", "ESOBADES", "SRA. BARBARA"]
  )

  # Simulación de datos de la tabla mejorada visualmente
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

  # Mostrar tabla limpia con soporte de Streamlit
  st.dataframe(df_gastos, use_container_width=True)

  with st.expander("🔍 Ver Comprobante Adjunto o Gestionar Gasto"):
    st.markdown(
        "Aquí puedes desplegar las opciones para **Abrir imagen/factura**, **Modificar** o **Eliminar** un registro de forma ordenada."
    )
    # Aquí puedes integrar tus botones de acción o formularios existentes.

with tab2:
  st.markdown("### 📋 Lista de Tareas y Pendientes de Obra")

  with st.form("form_tarea"):
    c1, c2, c3, c4 = st.columns([2, 3, 2, 1])
    with c1:
      t_obra = st.selectbox(
          "Obra / Destino", ["-- SELECCIONAR --", "GENERAL", "PDVSA", "ECOVIDA"]
      )
    with c2:
      t_desc = st.text_input("Descripción de la tarea", placeholder="Ej. Esmalte en columnas...")
    with c3:
      t_estado = st.selectbox("Estado inicial", ["PENDIENTE", "LISTO"])
    with c4:
      st.markdown("<br>", unsafe_allow_html=True)
      submit_tarea = st.form_submit_button("➕ Agregar")

  # Datos de ejemplo para tareas
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

  # Gráfico interactivo moderno con Plotly
  chart_data = pd.DataFrame(
      {
          "Obra": ["ESOBADES", "SRA. BARBARA", "PDVSA", "ECOVIDA"],
          "Gastos (Bs.)": [8500000, 2500000, 855247, 300000],
      }
  )

  fig = px.bar(
      chart_data,
      x="Obra",
      y="Gastos (Bs.)",
      text="Gastos (Bs.)",
      color="Obra",
      title="Distribución de Gastos por Obra",
  )
  fig.update_layout(
      plot_bgcolor="rgba(0,0,0,0)`, paper_bgcolor='rgba(0,0,0,0)'"
  )
  st.plotly_chart(fig, use_container_width=True)