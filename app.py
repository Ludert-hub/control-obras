from datetime import datetime
import pandas as pd
import streamlit as st
from supabase import create_client, Client

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Control de Obras - Nube", page_icon="🏗️", layout="wide"
)

# --- CONEXIÓN A SUPABASE ---
URL = "https://ubfbyxlaakftmayftabc.supabase.co"
KEY = "sb_publishable_VqZW4HmqWV--BLGWIAu3cg_AhGUIYoZ"


@st.cache_resource
def init_supabase() -> Client:
  return create_client(URL, KEY)


supabase = init_supabase()

st.title("🏗️ Control de Obras y Materiales")
st.markdown("Sistema sincronizado en tiempo real (PC y Teléfonos).")

# --- CREACIÓN DE TESTAÑAS (PESTAÑAS PRINCIPALES) ---
tab_facturas, tab_tareas = st.tabs(
    ["💰 Facturas y Gastos", "📋 Tareas Programadas"]
)


# ==========================================
# SECCIÓN 1: FACTURAS Y GASTOS
# ==========================================
with tab_facturas:
  # Sidebar exclusivo para el formulario de Gastos
  st.sidebar.header("➕ Nuevo Movimiento (Gasto)")

  with st.sidebar.form("form_gasto", clear_on_submit=True):
    # 1. Fecha formateada visualmente amigable
    fecha_gasto = st.date_input("Fecha", value=datetime.now())

    # 2. Monto (campo optimizado para evitar ceros molestos)
    monto_str = st.text_input(
        "Monto en Bs.",
        value="0.00",
        help="Escribe la cifra directamente.",
    )

    # 3. Menú desplegable de Obras existentes + Opción de crear nueva
    try:
      res_obras = supabase.table("registros").select("obra").execute()
      lista_existente = (
          sorted(list(set([r["obra"] for r in res_obras.data if r["obra"]])))
          if res_obras.data
          else []
      )
    except Exception:
      lista_existente = []

    opciones_obra = lista_existente + ["➕ Agregar nueva obra..."]
    seleccion_obra = st.selectbox("Obra / Destino", opciones_obra)

    if seleccion_obra == "➕ Agregar nueva obra...":
      obra_final = st.text_input("Escribe el nombre de la nueva obra:")
    else:
      obra_final = seleccion_obra

    descripcion = st.text_input("Descripción (Materiales, equipos...)")

    submit_gasto = st.form_submit_button(
        label="Guardar Gasto", use_container_width=True
    )

    if submit_gasto:
      try:
        monto_val = float(monto_str.replace(",", "."))
      except ValueError:
        monto_val = 0.0

      if not obra_final or monto_val <= 0:
        st.sidebar.error("Verifica el monto y que la obra esté seleccionada.")
      else:
        try:
          data = {
              "fecha": str(fecha_gasto),
              "monto": monto_val,
              "obra": obra_final,
              "descripcion": descripcion,
              "estado": "REGISTRADO",  # Sin estados molestos en facturas
          }
          supabase.table("registros").insert(data).execute()
          st.sidebar.success("¡Gasto guardado con éxito!")
          st.rerun()
        except Exception as e:
          st.sidebar.error(f"Error al guardar: {e}")

  # Visualización de Gastos
  st.subheader("📋 Resumen de Gastos y Facturas")

  try:
    response = (
        supabase.table("registros")
        .select("*")
        .neq("estado", "TAREA")
        .order("id", desc=True)
        .execute()
    )
    rows = response.data

    if rows:
      df = pd.DataFrame(rows)

      # Filtro rápido por Obra
      obras_disp = ["Todas"] + list(df["obra"].unique())
      obra_sel = st.selectbox("Filtrar gastos por Obra:", obras_disp, key="filtro_gasto")

      if obra_sel != "Todas":
        df = df[df["obra"] == obra_sel]

      total_monto = df["monto"].sum()
      st.metric(
          label=(
              f"Total Filtrado ({obra_sel.upper()})"
              if obra_sel != "Todas"
              else "Total General de Gastos"
          ),
          value=f"Bs. {total_monto:,.2f}",
      )

      st.dataframe(df, use_container_width=True)
    else:
      st.info("No hay gastos registrados todavía.")
  except Exception as e:
    st.error(f"Error al cargar datos: {e}")

  # Sección para eliminar gastos
  with st.expander("🗑️ Eliminar un gasto registrado"):
    try:
      res_del = (
          supabase.table("registros")
          .select("id, obra, descripcion, monto")
          .execute()
      )
      if res_del.data:
        opciones_del = {
            f"ID {r['id']} - {r['obra']} - Bs. {r['monto']:,.2f} ({r['descripcion']})"
            : r["id"]
            for r in res_del.data
        }
        sel_borrar = st.selectbox(
            "Selecciona el registro a borrar",
            list(opciones_del.keys()),
            key="del_gasto",
        )
        if st.button("Borrar Gasto", type="primary", use_container_width=True):
          supabase.table("registros").delete().eq(
              "id", opciones_del[sel_borrar]
          ).execute()
          st.success("Gasto eliminado.")
          st.rerun()
    except Exception:
      pass


# ==========================================
# SECCIÓN 2: TAREAS PROGRAMADAS (PENDIENTE / LISTO)
# ==========================================
with tab_tareas:
  st.subheader("☑️ Gestión de Tareas Programadas de Obra")

  col1, col2 = st.columns([1, 2])

  with col1:
    st.markdown("### Nueva Tarea")
    with st.form("form_tarea", clear_on_submit=True):
      t_obra = st.text_input("Obra asociada")
      t_desc = st.text_input("Descripción de la tarea")
      t_estado = st.selectbox("Estado inicial", ["PENDIENTE", "LISTO"])

      btn_t = st.form_submit_button(
          "Agregar Tarea", use_container_width=True
      )
      if btn_t:
        if not t_desc:
          st.error("Escribe la descripción de la tarea.")
        else:
          try:
            data_t = {
                "fecha": str(datetime.now().strftime("%Y-%m-%d")),
                "monto": 0.0,
                "obra": t_obra if t_obra else "General",
                "descripcion": t_desc,
                "estado": f"TAREA_{t_estado}",  # Identificador para separarlas
            }
            supabase.table("registros").insert(data_t).execute()
            st.success("¡Tarea creada!")
            st.rerun()
          except Exception as e:
            st.error(f"Error: {e}")

  with col2:
    st.markdown("### Listado de Tareas Activas")
    try:
      res_tareas = (
          supabase.table("registros")
          .select("*")
          .like("estado", "TAREA_%")
          .order("id", desc=True)
          .execute()
      )
      if res_tareas.data:
        for t in res_tareas.data:
          # Limpiar etiqueta visual del estado
          estado_limpio = (
              "LISTO" if "LISTO" in t["estado"] else "PENDIENTE"
          )
          color_badge = "🟢" if estado_limpio == "LISTO" else "🟠"

          with st.container(border=True):
            st.write(
                f"**Obra:** {t['obra']} | **Tarea:** {t['descripcion']}"
            )
            col_a, col_b = st.columns(2)
            with col_a:
              st.write(f"Estado actual: {color_badge} **{estado_limpio}**")
            with col_b:
              nuevo_est = st.selectbox(
                  "Cambiar",
                  ["PENDIENTE", "LISTO"],
                  index=0 if estado_limpio == "PENDIENTE" else 1,
                  key=f"st_{t['id']}",
              )
              if st.button("Actualizar Estado", key=f"btn_{t['id']}"):
                nuevo_val = f"TAREA_{nuevo_est}"
                supabase.table("registros").update({"estado": nuevo_val}).eq(
                    "id", t["id"]
                ).execute()
                st.success("¡Estado actualizado!")
                st.rerun()

              if st.button("🗑️ Borrar Tarea", key=f"del_t_{t['id']}"):
                supabase.table("registros").delete().eq(
                    "id", t["id"]
                ).execute()
                st.rerun()
      else:
        st.info("No hay tareas programadas registradas.")
    except Exception as e:
      st.error(f"Error cargando tareas: {e}")