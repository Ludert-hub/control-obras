from datetime import datetime
import pandas as pd
import streamlit as st
from supabase import create_client, Client

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Control de Obras - Nube", page_icon="🏗️", layout="wide"
)

# --- CONEXIÓN A SUPABASE CON TUS DATOS ---
URL = "https://ubfbyxlaakftmayftabc.supabase.co"
KEY = "sb_publishable_VqZW4HmqWV--BLGWIAu3cg_AhGUIYoZ"


@st.cache_resource
def init_supabase() -> Client:
  return create_client(URL, KEY)


supabase = init_supabase()

st.title("🏗️ Control de Obras y Materiales")
st.markdown(
    "Sistema sincronizado en tiempo real para múltiples dispositivos (PC y"
    " Teléfonos)."
)

# --- FORMULARIO LATERAL PARA NUEVOS REGISTROS ---
st.sidebar.header("➕ Nuevo Movimiento")

with st.sidebar.form("form_registro", clear_on_submit=True):
  fecha = st.date_input("Fecha", value=datetime.now())
  monto = st.number_input("Monto en Bs.", min_value=0.0, step=0.01, format="%.2f")
  obra = st.text_input("Obra / Destino (ej. ESOBADES)")
  descripcion = st.text_input("Descripción (ej. Materiales, Gasolina...)")
  estado = st.selectbox("Estado", ["PENDIENTE", "LISTO"])

  submit_button = st.form_submit_button(
      label="Guardar en la Nube", use_container_width=True
  )

  if submit_button:
    if not obra or monto <= 0:
      st.sidebar.error("El monto y la obra son obligatorios.")
    else:
      try:
        data = {
            "fecha": str(fecha),
            "monto": float(monto),
            "obra": obra,
            "descripcion": descripcion,
            "estado": estado,
        }
        supabase.table("registros").insert(data).execute()
        st.sidebar.success("¡Guardado y sincronizado con éxito!")
        st.rerun()
      except Exception as e:
        st.sidebar.error(f"Error al guardar: {e}")

# --- CONSULTA Y VISUALIZACIÓN DE DATOS ---
st.subheader("📋 Resumen de Registros Actuales")

try:
  response = (
      supabase.table("registros").select("*").order("id", desc=True).execute()
  )
  rows = response.data

  if rows:
    df = pd.DataFrame(rows)

    # Filtro rápido por Obra en la parte superior
    obras_disponibles = ["Todas"] + list(df["obra"].unique())
    obra_seleccionada = st.selectbox("Filtrar por Obra:", obras_disponibles)

    if obra_seleccionada != "Todas":
      df = df[df["obra"] == obra_seleccionada]

    # Mostrar métricas rápidas
    total_monto = df["monto"].sum()
    st.metric(
        label=(
            f"Monto Total Filtrado ({obra_seleccionada.upper()})"
            if obra_seleccionada != "Todas"
            else "Monto Total General"
        ),
        value=f"Bs. {total_monto:,.2f}",
    )

    # Tabla interactiva
    st.dataframe(df, use_container_width=True)

  else:
    st.info("No hay registros todavía en la base de datos.")

except Exception as e:
  st.error(f"Error al conectar con la base de datos: {e}")

# --- SECCIÓN PARA ELIMINAR ---
with st.expander("🗑️ Eliminar un registro"):
  try:
    response_del = (
        supabase.table("registros").select("id, obra, descripcion, monto").execute()
    )
    lista_reg = response_del.data
    if lista_reg:
      opciones = {
          f"ID {r['id']} - {r['obra']} - Bs. {r['monto']:,.2f} ({r['descripcion']})"
          : r["id"]
          for r in lista_reg
      }
      seleccion_a_borrar = st.selectbox(
          "Seleccione el registro a eliminar", list(opciones.keys())
      )

      if st.button(
          "Borrar Registro Seleccionado", type="primary", use_container_width=True
      ):
        id_a_borrar = opciones[seleccion_a_borrar]
        supabase.table("registros").delete().eq("id", id_a_borrar).execute()
        st.success("Registro eliminado correctamente.")
        st.rerun()
  except Exception:
    pass