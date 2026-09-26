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

# --- PESTAÑAS PRINCIPALES ---
tab_facturas, tab_tareas = st.tabs(
    ["💰 Facturas y Gastos", "📋 Tareas Programadas"]
)


# ==========================================
# SECCIÓN 1: FACTURAS Y GASTOS
# ==========================================
with tab_facturas:
  st.sidebar.header("➕ Nuevo Movimiento (Gasto)")

  with st.sidebar.form("form_gasto", clear_on_submit=True):
    fecha_gasto = st.date_input(
        "Fecha (Día / Mes / Año)",
        value=datetime.now(),
        format="DD/MM/YYYY",
    )

    monto_str = st.text_input("Monto en Bs.", value="0.00")

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
              "fecha": fecha_gasto.strftime("%Y-%m-%d"),  # Formato estándar para que la base de datos no falle
              "monto": monto_val,
              "obra": obra_final,
              "descripcion": descripcion,
              "estado": "REGISTRADO",
          }
          supabase.table("registros").insert(data).execute()
          st.sidebar.success("¡Gasto guardado con éxito!")
          st.rerun()
        except Exception as e:
          st.sidebar.error(f"Error al guardar: {e}")

  st.subheader("📋 Resumen de Gastos y Facturas")

  try:
    response = (
        supabase.table("registros")
        .select("*")
        .not_.like("estado", "TAREA_%")
        .order("id", desc=True)
        .execute()
    )
    rows = response.data

    if rows:
      df = pd.DataFrame(rows)

      # Formatear la fecha para verla como DD/MM/YYYY en la tabla
      if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.strftime(
            "%d/%m/%Y"
        )

      obras_disp = ["Todas"] + list(df["obra"].unique())
      obra_sel = st.selectbox(
          "Filtrar gastos por Obra:", obras_disp, key="filtro_gasto"
      )

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

  with st.expander("🗑️ Eliminar un gasto registrado"):
    try:
      res_del = (
          supabase.table("registros")
          .select("id, obra, descripcion, monto")
          .not_.like("estado", "TAREA_%")
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
# SECCIÓN 2: TAREAS PROGRAMADAS
# ==========================================
with tab_tareas:
  st.subheader("☑️ Lista de Tareas y Pendientes de Obra")

  with st.form("form_tarea", clear_on_submit=True):
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 3, 2, 1])
    with col_f1:
      t_obra = st.text_input("Obra / Destino", placeholder="Ej. Pdvsa")
    with col_f2:
      t_desc = st.text_input(
          "Descripción de la tarea", placeholder="Ej. Esmalte en columnas..."
      )
    with col_f3:
      t_estado = st.selectbox("Estado inicial", ["PENDIENTE", "LISTO"])
    with col_f4:
      st.write("")
      btn_t = st.form_submit_button("➕ Agregar", use_container_width=True)

    if btn_t:
      if not t_desc:
        st.error("La descripción de la tarea es obligatoria.")
      else:
        try:
          data_t = {
              "fecha": datetime.now().strftime("%Y-%m-%d"),
              "monto": 0.0,
              "obra": t_obra if t_obra else "General",
              "descripcion": t_desc,
              "estado": f"TAREA_{t_estado}",
          }
          supabase.table("registros").insert(data_t).execute()
          st.success("¡Tarea añadida!")
          st.rerun()
        except Exception as e:
          st.error(f"Error: {e}")

  st.markdown("---")

  try:
    res_tareas = (
        supabase.table("registros")
        .select("*")
        .like("estado", "TAREA_%")
        .order("id", desc=True)
        .execute()
    )

    if res_tareas.data:
      lista_formateada = []
      for t in res_tareas.data:
        estado_limpio = "LISTO" if "LISTO" in t["estado"] else "PENDIENTE"
        icono = "🔵" if estado_limpio == "LISTO" else "⏳"
        
        # Formatear fecha para la lista
        fecha_fmt = t["fecha"]
        try:
          fecha_fmt = datetime.strptime(t["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
          pass

        lista_formateada.append({
            "id": t["id"],
            "obra": t["obra"],
            "descripcion": t["descripcion"],
            "estado": f"{icono} {estado_limpio}",
            "fecha": fecha_fmt,
        })

      df_t = pd.DataFrame(lista_formateada)

      # Mostrar tabla limpia
      st.dataframe(
          df_t[["descripcion", "estado", "obra", "fecha"]],
          use_container_width=True,
          hide_index=True,
      )

      st.markdown("### ⚙️ Gestionar o Cambiar Estados Individuales")

      opciones_tareas_gest = {
          f"[{'LISTO' if 'LISTO' in t['estado'] else 'PENDIENTE'}] {t['obra']} - {t['descripcion']} (ID: {t['id']})"
          : t
          for t in res_tareas.data
      }

      sel_gestion = st.selectbox(
          "Selecciona una tarea para modificar o borrar:",
          list(opciones_tareas_gest.keys()),
      )
      tarea_seleccionada = opciones_tareas_gest[sel_gestion]

      col_btn1, col_btn2, col_btn3 = st.columns(3)
      with col_btn1:
        if st.button("🔄 Cambiar a PENDIENTE", use_container_width=True):
          supabase.table("registros").update(
              {"estado": "TAREA_PENDIENTE"}
          ).eq("id", tarea_seleccionada["id"]).execute()
          st.rerun()
      with col_btn2:
        if st.button("✅ Cambiar a LISTO", use_container_width=True):
          supabase.table("registros").update({"estado": "TAREA_LISTO"}).eq(
              "id", tarea_seleccionada["id"]
          ).execute()
          st.rerun()
      with col_btn3:
        if st.button("🗑️ Eliminar Tarea", type="primary", use_container_width=True):
          supabase.table("registros").delete().eq(
              "id", tarea_seleccionada["id"]
          ).execute()
          st.rerun()

    else:
      st.info("No hay tareas programadas registradas en este momento.")
  except Exception as e:
    st.error(f"Error cargando tareas: {e}")