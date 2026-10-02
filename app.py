from datetime import datetime
import pandas as pd
import streamlit as st
from supabase import create_client, Client
import urllib.parse

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

st.title("🏗️️ Control de Obras y Materiales")
st.markdown("Sistema sincronizado en tiempo real (PC y Teléfonos).")

# --- BOTÓN DE ACTUALIZACIÓN RÁPIDA DE LA NUBE ---
col_top1, col_top2 = st.columns([6, 1])
with col_top2:
  if st.button("🔄 Actualizar", use_container_width=True):
    st.rerun()


# --- FUNCIÓN PARA FORMATEAR MONTO ESTILO ###.###,## ---
def formatear_monto_venezuela(valor):
  try:
    val_float = float(valor)
    s = f"{val_float:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s
  except Exception:
    return "0,00"


# ==========================================
# 🚨 ALERTA DE CRÉDITOS COMPACTA (>= 13 DÍAS)
# ==========================================
try:
  res_alertas = supabase.table("registros").select("*").not_.like("estado", "TAREA_%").execute()
  if res_alertas.data:
    df_alt = pd.DataFrame(res_alertas.data)
    df_alt["fecha_dt"] = pd.to_datetime(df_alt["fecha"], errors="coerce")
    hoy = pd.Timestamp.now().normalize()
    
    deudas_por_vencer = []
    for _, row in df_alt.iterrows():
      desc = str(row["descripcion"]).upper()
      if "CREDITO" in desc:
        f_gasto = row["fecha_dt"]
        if pd.notnull(f_gasto):
          dias_transcurridos = (hoy - f_gasto.normalize()).days
          if dias_transcurridos >= 13:
            dias_restantes = max(0, 15 - dias_transcurridos)
            
            obs_txt = ""
            if " | OBS:" in desc:
              obs_txt = f" ({desc.split(' | OBS:')[1].strip()})"
            elif " | OBSERVACIONES:" in desc:
              obs_txt = f" ({desc.split(' | OBSERVACIONES:')[1].strip()})"
            elif "MANGO CENTER" in desc:
              obs_txt = " (MANGO CENTER)"

            deudas_por_vencer.append({
                "fecha": f_gasto.strftime("%d/%m/%Y"),
                "obra": str(row["obra"]).upper(),
                "monto": formatear_monto_venezuela(row["monto"]),
                "dias": dias_transcurridos,
                "restantes": dias_restantes,
                "obs": obs_txt
            })

    if deudas_por_vencer:
      alertas_html = """
      <div style="background-color: #fff3f3; border-left: 4px solid #cc0000; padding: 8px 12px; margin-bottom: 15px; border-radius: 4px; font-size: 13px; color: #a80000;">
        <b>🚨 Alerta de Créditos (Próximos a cumplir 15 días):</b><ul style="margin: 0; padding-left: 15px;">
      """
      for deuda in deudas_por_vencer:
        estado_txt = "¡VENCIDO!" if deuda["restantes"] == 0 else f"Quedan {deuda['restantes']} día(s)"
        alertas_html += f"<li><b>{deuda['fecha']}</b> | Obra: <b>{deuda['obra']}</b>{deuda['obs']} | Bs. {deuda['monto']} | <b>{deuda['dias']} días transcurridos ({estado_txt})</b></li>"
      alertas_html += "</ul></div>"
      st.markdown(alertas_html, unsafe_allow_html=True)
except Exception as e:
  pass


# --- PESTAÑAS PRINCIPALES ---
tab_facturas, tab_tareas, tab_reportes = st.tabs(
    ["💰 Facturas y Gastos", "📋 Tareas Programadas", "📊 Reportes y Desglose"]
)


# ==========================================
# SECCIÓN 1: FACTURAS Y GASTOS
# ==========================================
with tab_facturas:
  st.sidebar.header("➕ Nuevo Movimiento (Gasto)")

  fecha_gasto = st.sidebar.date_input(
      "Fecha (Día / Mes / Año)",
      value=datetime.now(),
      format="DD/MM/YYYY",
  )

  monto_input = st.sidebar.number_input(
      "Monto en Bs.",
      min_value=0.0,
      value=None,
      step=0.01,
      format="%.2f",
      placeholder="Escribe el monto...",
  )

  # --- SELECTOR DINÁMICO DE OBRA ---
  try:
    res_obras = supabase.table("registros").select("obra").execute()
    lista_existente = (
        sorted(list(set([str(r["obra"]).upper() for r in res_obras.data if r["obra"]])))
        if res_obras.data else []
    )
  except Exception:
    lista_existente = []

  opciones_obra = ["-- SELECCIONAR OBRA --"] + lista_existente + ["➕ OTRA OBRA NUEVA..."]
  seleccion_obra = st.sidebar.selectbox("Obra / Destino", opciones_obra, key="sel_obra_gasto")

  if seleccion_obra == "➕ OTRA OBRA NUEVA...":
    obra_nueva_input = st.sidebar.text_input("Escribe el nombre de la NUEVA obra:", key="input_obra_nueva")
    obra_final = obra_nueva_input.strip().upper()
  elif seleccion_obra != "-- SELECCIONAR OBRA --":
    obra_final = seleccion_obra.strip().upper()
  else:
    obra_final = ""

  # --- SELECTOR DINÁMICO DE ORIGEN DE FONDOS ---
  try:
    res_orig = supabase.table("registros").select("descripcion").execute()
    lista_origenes = []
    if res_orig.data:
      for r in res_orig.data:
        desc_str = str(r["descripcion"])
        if desc_str.startswith("[") and "]" in desc_str:
          orig = desc_str.split("]")[0].replace("[", "").strip()
          if orig and not orig.startswith("CREDITO"):
            lista_origenes.append(orig)
    lista_origenes_existentes = sorted(list(set(lista_origenes)))
  except Exception:
    lista_origenes_existentes = []

  opciones_origen = ["-- SELECCIONAR ORIGEN --", "CREDITO"] + lista_origenes_existentes + ["➕ OTRO ORIGEN NUEVO..."]
  seleccion_origen = st.sidebar.selectbox("Origen de los Fondos", opciones_origen, key="sel_orig_gasto")

  if seleccion_origen == "➕ OTRO ORIGEN NUEVO...":
    origen_nuevo_input = st.sidebar.text_input("Escribe el NUEVO origen de fondos:", key="input_orig_nuevo")
    origen_final = origen_nuevo_input.strip().upper()
  elif seleccion_origen != "-- SELECCIONAR ORIGEN --":
    origen_final = seleccion_origen.strip().upper()
  else:
    origen_final = ""

  descripcion_input = st.sidebar.text_input("Descripción (Materiales, equipos...)", key="input_desc_gasto")
  descripcion_final = descripcion_input.strip().upper()

  observaciones_final = ""
  if origen_final == "CREDITO":
    observaciones_input = st.sidebar.text_input("Observaciones / Proveedor (Ej. MANGO CENTER)", value="MANGO CENTER", key="input_obs_gasto")
    observaciones_final = observaciones_input.strip().upper()

  archivo_adjunto = st.sidebar.file_uploader(
      "Adjuntar Recibo / Factura (Foto o Img)", type=["png", "jpg", "jpeg", "pdf"], key="file_gasto"
  )

  if st.sidebar.button("Guardar Gasto", type="primary", use_container_width=True):
    monto_val = float(monto_input) if monto_input is not None else 0.0

    if not obra_final:
      st.sidebar.error("Debes seleccionar o escribir una obra.")
    elif monto_val <= 0:
      st.sidebar.error("Ingresa un monto válido mayor a 0.")
    else:
      try:
        url_comprobante = ""
        if archivo_adjunto is not None:
          file_bytes = archivo_adjunto.getvalue()
          file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{archivo_adjunto.name}"
          supabase.storage.from_("comprobantes").upload(
              file_name, file_bytes, {"content-type": archivo_adjunto.type}
          )
          url_comprobante = supabase.storage.from_("comprobantes").get_public_url(file_name)

        if origen_final == "CREDITO":
          obs_text = f" | Obs: {observaciones_final}" if observaciones_final else ""
          desc_completa = f"[CREDITO] {descripcion_final}{obs_text}"
        else:
          desc_completa = f"[{origen_final}] {descripcion_final}" if origen_final else descripcion_final

        data = {
            "fecha": fecha_gasto.strftime("%Y-%m-%d"),
            "monto": monto_val,
            "obra": obra_final,
            "descripcion": desc_completa,
            "estado": f"REGISTRADO|URL:{url_comprobante}" if url_comprobante else "REGISTRADO",
        }
        supabase.table("registros").insert(data).execute()
        st.sidebar.success("¡Gasto guardado con éxito!")
        st.rerun()
      except Exception as e:
        st.sidebar.error(f"Error al guardar: {e}")

  # --- VISTA DE GASTOS ---
  st.subheader("📋 Resumen de Gastos y Facturas")

  try:
    response = supabase.table("registros").select("*").not_.like("estado", "TAREA_%").execute()
    rows = response.data

    if rows:
      df = pd.DataFrame(rows)
      df["fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
      df = df.sort_values(by=["fecha_dt", "id"], ascending=[False, False]).reset_index(drop=True)

      if "obra" in df.columns:
        df["obra"] = df["obra"].astype(str).str.upper()
      if "descripcion" in df.columns:
        df["descripcion"] = df["descripcion"].astype(str).str.upper()

      comprobantes_urls, estados_limpios = [], []
      for est in df["estado"]:
        if "URL:" in str(est):
          partes = str(est).split("URL:")
          estados_limpios.append(partes[0].strip("|"))
          comprobantes_urls.append(partes[1])
        else:
          estados_limpios.append(est)
          comprobantes_urls.append("")

      df["estado_limpio"] = estados_limpios
      df["comprobante_url"] = comprobantes_urls

      df_view = df[["id", "fecha_dt", "fecha", "monto", "obra", "descripcion", "comprobante_url"]].copy()
      df_view["fecha_fmt"] = df_view["fecha_dt"].dt.strftime("%d/%m/%Y")
      df_view["monto_fmt"] = df_view["monto"].apply(formatear_monto_venezuela)

      descripciones_limpias, observaciones_lista = [], []
      for d in df_view["descripcion"]:
        d_str = str(d)
        obs_val = ""
        if " | OBS:" in d_str:
          partes = d_str.split(" | OBS:")
          d_str = partes[0]
          obs_val = partes[1].strip()
        elif " | OBSERVACIONES:" in d_str:
          partes = d_str.split(" | OBSERVACIONES:")
          d_str = partes[0]
          obs_val = partes[1].strip()
        elif "CREDITO MANGO CENTER" in d_str:
          d_str = "[CREDITO]"
          obs_val = "MANGO CENTER"
        descripciones_limpias.append(d_str)
        observaciones_lista.append(obs_val)

      df_view["desc_limpia"] = descripciones_limpias
      df_view["observaciones"] = observaciones_lista

      obras_disp = ["Todas"] + list(df_view["obra"].unique())
      obra_sel = st.selectbox("Filtrar gastos por Obra:", obras_disp, key="filtro_gasto")

      if obra_sel != "Todas":
        df_view = df_view[df_view["obra"] == obra_sel]

      total_monto = df["monto"].sum() if obra_sel == "Todas" else df[df["obra"] == obra_sel]["monto"].sum()
      
      st.metric(
          label=f"Total Filtrado ({obra_sel.upper()})" if obra_sel != "Todas" else "Total General de Gastos",
          value=f"Bs. {formatear_monto_venezuela(total_monto)}",
      )

      df_final_display = df_view[["fecha_fmt", "obra", "monto_fmt", "desc_limpia", "observaciones", "comprobante_url"]].copy()
      df_final_display.columns = ["Fecha", "Obra", "Monto (Bs.)", "Descripción", "Observaciones", "Comprobante"]

      def color_rojo_si_credito(df_to_style):
          styles = pd.DataFrame('', index=df_to_style.index, columns=df_to_style.columns)
          for idx, row in df_to_style.iterrows():
              orig_real = str(df.loc[idx, "descripcion"]).upper()
              if orig_real.startswith("[CREDITO]") or "CREDITO MANGO CENTER" in orig_real:
                  styles.loc[idx, :] = 'background-color: #ffe6e6; color: #cc0000; font-weight: bold'
          return styles

      st.dataframe(df_final_display.style.apply(color_rojo_si_credito, axis=None), use_container_width=True, hide_index=True)

      st.markdown("### 🔍 Ver Comprobante Adjunto de un Gasto")
      with st.expander("Abrir imagen o factura de pago"):
        reg_con_foto = [r for r in rows if "URL:" in str(r["estado"])]
        if reg_con_foto:
          opciones_foto = {
              f"ID {r['id']} - {str(r['obra']).upper()} - Bs. {formatear_monto_venezuela(r['monto'])} ({str(r['descripcion']).upper()})"
              : r["estado"].split("URL:")[1] for r in reg_con_foto
          }
          sel_foto_key = st.selectbox("Selecciona el gasto para ver su recibo:", list(opciones_foto.keys()))
          url_imagen = opciones_foto[sel_foto_key]
          st.image(url_imagen, caption="Comprobante / Factura adjunta", use_container_width=True)
          st.markdown(f"[🔗 Abrir imagen en pestaña completa]({url_imagen})")
        else:
          st.info("No hay gastos con comprobantes adjuntos en este momento.")
    else:
      st.info("No hay gastos registrados todavía.")
  except Exception as e:
    st.error(f"Error al cargar datos: {e}")

  # --- MÓDULO DE MODIFICAR / EDITAR GASTO ---
  with st.expander("✏️ Modificar un Gasto Registrado (Corrección)"):
    try:
      res_edit = supabase.table("registros").select("*").not_.like("estado", "TAREA_%").execute()
      if res_edit.data:
        df_edit_tmp = pd.DataFrame(res_edit.data)
        df_edit_tmp["fecha_dt"] = pd.to_datetime(df_edit_tmp["fecha"], errors="coerce")
        df_edit_tmp = df_edit_tmp.sort_values(by=["fecha_dt", "id"], ascending=[False, False])

        opciones_edit = {
            f"ID {r['id']} - Fecha: {r['fecha']} - {str(r['obra']).upper()} - Bs. {formatear_monto_venezuela(r['monto'])} ({str(r['descripcion']).upper()})"
            : r for _, r in df_edit_tmp.iterrows()
        }
        sel_mod = st.selectbox("Selecciona el registro que deseas corregir:", list(opciones_edit.keys()), key="select_mod_gasto")
        gasto_actual = opciones_edit[sel_mod]

        desc_actual_str = str(gasto_actual['descripcion'])
        orig_actual = ""
        solo_desc = desc_actual_str
        obs_actual_val = ""
        
        if " | OBS:" in desc_actual_str:
            partes = desc_actual_str.split(" | OBS:")
            desc_part = partes[0]
            obs_actual_val = partes[1].strip()
            if desc_part.startswith("[") and "]" in desc_part:
                orig_actual = desc_part.split("]")[0].replace("[", "").strip()
                solo_desc = desc_part.split("]")[1].strip()
        elif "CREDITO MANGO CENTER" in desc_actual_str:
            orig_actual = "CREDITO"
            obs_actual_val = "MANGO CENTER"
            solo_desc = ""
        elif desc_actual_str.startswith("[") and "]" in desc_actual_str:
            orig_actual = desc_actual_str.split("]")[0].replace("[", "").strip()
            solo_desc = desc_actual_str.split("]")[1].strip()

        with st.form("form_edicion_gasto"):
            st.markdown(f"**Editando Registro ID: {gasto_actual['id']}**")
            
            try:
                fecha_dt = datetime.strptime(gasto_actual['fecha'], "%Y-%m-%d").date()
            except:
                fecha_dt = datetime.now().date()

            nueva_fecha = st.date_input("Fecha del gasto", value=fecha_dt, format="DD/MM/YYYY")
            nuevo_monto = st.number_input("Monto en Bs.", min_value=0.0, value=float(gasto_actual['monto']), step=0.01, format="%.2f")

            lista_obras_edit = sorted(list(set([str(r["obra"]).upper() for r in res_edit.data if r["obra"]])))
            obra_actual_val = str(gasto_actual['obra']).upper()
            
            if obra_actual_val in lista_obras_edit:
                idx_obra = lista_obras_edit.index(obra_actual_val) + 1
            else:
                idx_obra = 0

            opciones_obra_edit = ["-- SELECCIONAR OBRA --"] + lista_obras_edit + ["➕ OTRA OBRA NUEVA..."]
            sel_obra_edit = st.selectbox("Obra / Destino", opciones_obra_edit, index=idx_obra if idx_obra < len(opciones_obra_edit) else 0, key="edit_sel_obra")

            if sel_obra_edit == "➕ OTRA OBRA NUEVA...":
                input_obra_edit_nueva = st.text_input("Escribe el nombre de la NUEVA obra:", key="edit_input_obra_nueva")
                obra_final_edit = input_obra_edit_nueva.strip().upper()
            elif sel_obra_edit != "-- SELECCIONAR OBRA --":
                obra_final_edit = sel_obra_edit.strip().upper()
            else:
                obra_final_edit = obra_actual_val

            lista_origenes_edit = []
            for r in res_edit.data:
                d = str(r["descripcion"])
                if d.startswith("[") and "]" in d:
                    o = d.split("]")[0].replace("[", "").strip()
                    if o and o != "CREDITO": lista_origenes_edit.append(o)
            lista_origenes_edit = sorted(list(set(lista_origenes_edit)))

            opciones_orig_edit = ["-- SELECCIONAR ORIGEN --", "CREDITO"] + lista_origenes_edit + ["➕ OTRO ORIGEN NUEVO..."]
            
            if orig_actual in opciones_orig_edit:
                idx_orig = opciones_orig_edit.index(orig_actual)
            else:
                idx_orig = 0

            sel_orig_edit = st.selectbox("Origen de los Fondos", opciones_orig_edit, index=idx_orig, key="edit_sel_orig")

            if sel_orig_edit == "➕ OTRO ORIGEN NUEVO...":
                input_orig_edit_nuevo = st.text_input("Escribe el NUEVO origen de fondos:", key="edit_input_orig_nuevo")
                origen_final_edit = input_orig_edit_nuevo.strip().upper()
            elif sel_orig_edit != "-- SELECCIONAR ORIGEN --":
                origen_final_edit = sel_orig_edit.strip().upper()
            else:
                origen_final_edit = orig_actual

            nueva_desc_input = st.text_input("Descripción", value=solo_desc).strip().upper()
            
            nueva_obs_input = ""
            if origen_final_edit == "CREDITO":
                nueva_obs_input = st.text_input("Observaciones / Proveedor", value=obs_actual_val if obs_actual_val else "MANGO CENTER", key="edit_input_obs").strip().upper()

            btn_guardar_cambios = st.form_submit_button("💾 Guardar Cambios del Gasto", type="primary")
            
            if btn_guardar_cambios:
                if origen_final_edit == "CREDITO":
                    obs_text_edit = f" | Obs: {nueva_obs_input}" if nueva_obs_input else ""
                    desc_completa_edit = f"[CREDITO] {nueva_desc_input}{obs_text_edit}"
                else:
                    desc_completa_edit = f"[{origen_final_edit}] {nueva_desc_input}" if origen_final_edit else nueva_desc_input
                
                supabase.table("registros").update({
                    "fecha": nueva_fecha.strftime("%Y-%m-%d"),
                    "monto": nuevo_monto,
                    "obra": obra_final_edit,
                    "descripcion": desc_completa_edit
                }).eq("id", gasto_actual['id']).execute()
                
                st.success("¡Gasto modificado y actualizado con éxito!")
                st.rerun()
    except Exception as e:
      st.error(f"Error en módulo de edición: {e}")

  with st.expander("🗑️ Eliminar un gasto registrado"):
    try:
      res_del = supabase.table("registros").select("id, obra, descripcion, monto").not_.like("estado", "TAREA_%").execute()
      if res_del.data:
        opciones_del = {
            f"ID {r['id']} - {str(r['obra']).upper()} - Bs. {formatear_monto_venezuela(r['monto'])} ({str(r['descripcion']).upper()})"
            : r["id"] for r in res_del.data
        }
        sel_borrar = st.selectbox("Selecciona el registro a borrar", list(opciones_del.keys()), key="del_gasto")
        if st.button("Borrar Gasto", type="primary", use_container_width=True):
          supabase.table("registros").delete().eq("id", opciones_del[sel_borrar]).execute()
          st.success("Gasto eliminado.")
          st.rerun()
    except Exception:
      pass


# ==========================================
# SECCIÓN 2: TAREAS PROGRAMADAS
# ==========================================
with tab_tareas:
  st.subheader("☑️ Lista de Tareas y Pendientes de Obra")

  col_f1, col_f2, col_f3, col_f4 = st.columns([2, 3, 2, 1])

  with col_f1:
    try:
      res_obras_t = supabase.table("registros").select("obra").execute()
      lista_existente_t = (
          sorted(list(set([str(r["obra"]).upper() for r in res_obras_t.data if r["obra"]])))
          if res_obras_t.data else []
      )
    except Exception:
      lista_existente_t = []

    opciones_obra_t = ["-- SELECCIONAR --"] + lista_existente_t + ["➕ OTRA NUEVA..."]
    seleccion_obra_t = st.selectbox("Obra / Destino", opciones_obra_t, key="t_sel_obra")

    if seleccion_obra_t == "➕ OTRA NUEVA...":
      t_obra_nueva_input = st.text_input("Nueva obra:", key="t_input_obra_nueva")
      t_obra_final = t_obra_nueva_input.strip().upper()
    elif seleccion_obra_t != "-- SELECCIONAR --":
      t_obra_final = seleccion_obra_t.strip().upper()
    else:
      t_obra_final = ""

  with col_f2:
    t_desc_input = st.text_input("Descripción de la tarea", placeholder="Ej. Esmalte en columnas...", key="t_input_desc")
    t_desc_final = t_desc_input.strip().upper()

  with col_f3:
    t_estado = st.selectbox("Estado inicial", ["PENDIENTE", "LISTO"], key="t_sel_estado")

  with col_f4:
    st.write("")
    btn_t = st.button("➕ Agregar", use_container_width=True, key="btn_agregar_tarea")

  if btn_t:
    if not t_desc_final or not t_obra_final:
      st.error("Debes indicar la obra y la descripción de la tarea.")
    else:
      try:
        data_t = {
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "monto": 0.0,
            "obra": t_obra_final,
            "descripcion": t_desc_final,
            "estado": f"TAREA_{t_estado}",
        }
        supabase.table("registros").insert(data_t).execute()
        st.success("¡Tarea añadida!")
        st.rerun()
      except Exception as e:
        st.error(f"Error: {e}")

  st.markdown("---")

  try:
    res_tareas = supabase.table("registros").select("*").like("estado", "TAREA_%").execute()

    if res_tareas.data:
      df_t_raw = pd.DataFrame(res_tareas.data)
      df_t_raw["fecha_dt"] = pd.to_datetime(df_t_raw["fecha"], errors="coerce")
      df_t_raw["estado_limpio"] = df_t_raw["estado"].apply(lambda x: "LISTO" if "LISTO" in str(x) else "PENDIENTE")
      
      df_t_raw["orden_estado"] = df_t_raw["estado_limpio"].apply(lambda x: 0 if x == "PENDIENTE" else 1)
      df_t_raw = df_t_raw.sort_values(by=["orden_estado", "fecha_dt", "id"], ascending=[True, False, False]).reset_index(drop=True)

      lista_formateada = []
      for _, t in df_t_raw.iterrows():
        est_L = t["estado_limpio"]
        icono = "🔵" if est_L == "LISTO" else "⏳"
        fecha_fmt = t["fecha"]
        try:
          fecha_fmt = pd.to_datetime(t["fecha"]).strftime("%d/%m/%Y")
        except: pass

        lista_formateada.append({
            "id": t["id"],
            "obra": str(t["obra"]).upper(),
            "descripcion": str(t["descripcion"]).upper(),
            "estado": f"{icono} {est_L}",
            "fecha": fecha_fmt,
        })

      df_t = pd.DataFrame(lista_formateada)
      df_t_display = df_t[["descripcion", "estado", "obra", "fecha"]].copy()
      df_t_display.columns = ["Descripción", "Estado", "Obra", "Fecha"]
      st.dataframe(df_t_display, use_container_width=True, hide_index=True)

      st.markdown("### ⚙️ Gestionar o Cambiar Estados Individuales")
      opciones_tareas_gest = {
          f"[{'LISTO' if 'LISTO' in t['estado'] else 'PENDIENTE'}] {str(t['obra']).upper()} - {str(t['descripcion']).upper()} (ID: {t['id']})"
          : t for _, t in df_t_raw.iterrows()
      }
      sel_gestion = st.selectbox("Selecciona una tarea para modificar o borrar:", list(opciones_tareas_gest.keys()))
      tarea_seleccionada = opciones_tareas_gest[sel_gestion]

      col_btn1, col_btn2, col_btn3 = st.columns(3)
      with col_btn1:
        if st.button("🔄 Cambiar a PENDIENTE", use_container_width=True):
          supabase.table("registros").update({"estado": "TAREA_PENDIENTE"}).eq("id", tarea_seleccionada["id"]).execute()
          st.rerun()
      with col_btn2:
        if st.button("✅ Cambiar a LISTO", use_container_width=True):
          supabase.table("registros").update({"estado": "TAREA_LISTO"}).eq("id", tarea_seleccionada["id"]).execute()
          st.rerun()
      with col_btn3:
        if st.button("🗑️ Eliminar Tarea", type="primary", use_container_width=True):
          supabase.table("registros").delete().eq("id", tarea_seleccionada["id"]).execute()
          st.rerun()
    else:
      st.info("No hay tareas programadas registradas en este momento.")
  except Exception as e:
    st.error(f"Error cargando tareas: {e}")


# ==========================================
# SECCIÓN 3: REPORTES Y CONTROL DE CRÉDITOS
# ==========================================
tab_reportes_gastos, tab_reportes_creditos = st.tabs(["📊 Reportes de Gastos", "🚨 Control de Créditos / Deudas"])

with tab_reportes_gastos:
  st.subheader("📊 Reportes, Desglose y Exportación")

  try:
    res_rep = supabase.table("registros").select("*").not_.like("estado", "TAREA_%").execute()
    
    if res_rep.data:
      df_rep = pd.DataFrame(res_rep.data)
      df_rep["fecha_dt"] = pd.to_datetime(df_rep["fecha"], errors="coerce")
      df_rep = df_rep.sort_values(by=["fecha_dt", "id"], ascending=[False, False]).reset_index(drop=True)

      def extraer_origen(desc):
        desc_str = str(desc)
        if desc_str.startswith("[") and "]" in desc_str:
          return desc_str.split("]")[0].replace("[", "")
        return "GENERAL / OTROS"

      df_rep["origen_fondos"] = df_rep["descripcion"].apply(extraer_origen)
      df_rep["obra"] = df_rep["obra"].astype(str).str.upper()

      # --- FILTROS DE DESGLOSE INTERACTIVOS ---
      st.markdown("### 🎛 Filtrar Datos para Exportar")
      col_f1, col_f2 = st.columns(2)
      
      with col_f1:
        lista_obras_rep = ["TODAS"] + sorted(list(df_rep["obra"].unique()))
        filtro_obra = st.selectbox("Filtrar por Obra:", lista_obras_rep, key="rep_obra")
        
      with col_f2:
        lista_orig_rep = ["TODOS"] + sorted(list(df_rep["origen_fondos"].unique()))
        filtro_origen = st.selectbox("Filtrar por Origen de Fondos:", lista_orig_rep, key="rep_orig")

      df_filtrado = df_rep.copy()
      if filtro_obra != "TODAS":
        df_filtrado = df_filtrado[df_filtrado["obra"] == filtro_obra]
      if filtro_origen != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["origen_fondos"] == filtro_origen]

      total_filtrado = df_filtrado["monto"].sum()
      st.metric(label="Total del Reporte Actual", value=f"Bs. {formatear_monto_venezuela(total_filtrado)}")

      df_mostrar = df_filtrado[["fecha_dt", "obra", "monto", "descripcion"]].copy()
      df_mostrar["Fecha"] = df_mostrar["fecha_dt"].dt.strftime("%d/%m/%Y")
      df_mostrar["Monto (Bs.)"] = df_mostrar["monto"].apply(formatear_monto_venezuela)
      
      desc_rep, obs_rep = [], []
      for d in df_mostrar["descripcion"]:
        d_str = str(d)
        o_str = ""
        if " | OBS:" in d_str:
          p = d_str.split(" | OBS:")
          d_str = p[0]
          o_str = p[1].strip()
        elif " | OBSERVACIONES:" in d_str:
          p = d_str.split(" | OBSERVACIONES:")
          d_str = p[0]
          o_str = p[1].strip()
        elif "CREDITO MANGO CENTER" in d_str:
          d_str = "[CREDITO]"
          o_str = "MANGO CENTER"
        desc_rep.append(d_str)
        obs_rep.append(o_str)

      df_mostrar["desc_limpia"] = desc_rep
      df_mostrar["observaciones"] = obs_rep

      df_mostrar_final = df_mostrar[["Fecha", "obra", "Monto (Bs.)", "desc_limpia", "observaciones"]].copy()
      df_mostrar_final.columns = ["Fecha", "Obra", "Monto (Bs.)", "Descripción", "Observaciones"]

      def color_rojo_si_credito_rep(df_to_style):
          styles = pd.DataFrame('', index=df_to_style.index, columns=df_to_style.columns)
          for idx, row in df_to_style.iterrows():
              orig_real = str(df_rep.loc[idx, "descripcion"]).upper()
              if orig_real.startswith("[CREDITO]") or "CREDITO MANGO CENTER" in orig_real:
                  styles.loc[idx, :] = 'background-color: #ffe6e6; color: #cc0000; font-weight: bold'
          return styles

      st.dataframe(df_mostrar_final.style.apply(color_rojo_si_credito_rep, axis=None), use_container_width=True, hide_index=True)

      st.markdown("---")
      
      # --- BOTONES DE EXPORTACIÓN Y WHATSAPP ---
      st.markdown("### 📲 Exportar y Compartir")
      col_btn_exp1, col_btn_exp2 = st.columns(2)
      
      with col_btn_exp1:
        csv_data = df_filtrado[["fecha", "obra", "monto", "descripcion"]].to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button(
            label="📥 Descargar Reporte en Excel (CSV)",
            data=csv_data,
            file_name=f"Reporte_{filtro_obra}_{filtro_origen}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
      with col_btn_exp2:
        mensaje_wa = f"📊 *Reporte de Gastos*\n🏗️ Obra: {filtro_obra}\n💳 Origen: {filtro_origen}\n\n*Detalle de movimientos:*\n"
        
        for _, fila in df_filtrado.iterrows():
            fecha_str = pd.to_datetime(fila['fecha']).strftime("%d/%m/%Y") if pd.notnull(fila['fecha']) else ""
            desc_str = fila['descripcion']
            monto_str = formatear_monto_venezuela(fila['monto'])
            mensaje_wa += f"🔸 {fecha_str} - {desc_str}: Bs. {monto_str}\n"
            
        mensaje_wa += f"\n💰 *Total: Bs. {formatear_monto_venezuela(total_filtrado)}*"
        
        url_wa = f"https://wa.me/?text={urllib.parse.quote(mensaje_wa)}"
        
        boton_wa_html = f"""
        <a href="{url_wa}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 10px; border-radius: 5px; text-decoration: none; font-weight: bold; border: 1px solid #1DA851;">
          📲 Enviar Cuadrilla por WhatsApp
        </a>
        """
        st.markdown(boton_wa_html, unsafe_allow_html=True)

      st.markdown("---")
      st.markdown("### 🔍 Resumen Cruzado General (Todas las obras y orígenes)")
      df_cruzado = df_rep.groupby(["obra", "origen_fondos"])["monto"].sum().reset_index()
      df_cruzado["Monto Total (Bs.)"] = df_cruzado["monto"].apply(formatear_monto_venezuela)
      df_cruzado.columns = ["Obra", "Origen de Fondos", "Monto Total (Bs.)"]
      
      def color_rojo_cruzado(df_to_style):
          styles = pd.DataFrame('', index=df_to_style.index, columns=df_to_style.columns)
          for idx, row in df_to_style.iterrows():
              if str(df_to_style.loc[idx, "Origen de Fondos"]) == "CREDITO":
                  styles.loc[idx, :] = 'background-color: #ffe6e6; color: #cc0000; font-weight: bold'
          return styles

      st.dataframe(df_cruzado.style.apply(color_rojo_cruzado, axis=None), use_container_width=True, hide_index=True)

    else:
      st.info("No hay suficientes datos de gastos para generar reportes.")
  except Exception as e:
    st.error(f"Error generando reportes: {e}")

# ==========================================
# SECCIÓN 3.2: CONTROL ESPECÍFICO DE CRÉDITOS PENDIENTES
# ==========================================
with tab_reportes_creditos:
  st.subheader("🚨 Control y Seguimiento de Créditos Pendientes")
  st.markdown("Listado exclusivo de deudas activas con origen **CREDITO** y cálculo de días hacia el límite de 15 días.")

  try:
    res_cred = supabase.table("registros").select("*").not_.like("estado", "TAREA_%").execute()
    if res_cred.data:
      df_cred = pd.DataFrame(res_cred.data)
      df_cred["fecha_dt"] = pd.to_datetime(df_cred["fecha"], errors="coerce")
      
      df_cred = df_cred[df_cred["descripcion"].astype(str).str.upper().str.startswith("[CREDITO]") | df_cred["descripcion"].astype(str).str.upper().str.contains("CREDITO MANGO CENTER")].copy()

      if not df_cred.empty:
        hoy = pd.Timestamp.now().normalize()
        
        lista_creditos_gestion = []
        for _, row in df_cred.iterrows():
          f_gasto = row["fecha_dt"]
          dias = (hoy - f_gasto.normalize()).days if pd.notnull(f_gasto) else 0
          estado_venc = "⚠️ VENCIDO (>15 DÍAS)" if dias > 15 else ("🚨 POR VENCER (≥13 DÍAS)" if dias >= 13 else "⏳ AL DÍA")
          
          lista_creditos_gestion.append({
              "id": row["id"],
              "Fecha Compra": f_gasto.strftime("%d/%m/%Y") if pd.notnull(f_gasto) else "",
              "Obra": str(row["obra"]).upper(),
              "Descripción": str(row["descripcion"]).upper(),
              "Monto (Bs.)": formatear_monto_venezuela(row["monto"]),
              "Días Transcurridos": dias,
              "Estatus Crédito": estado_venc,
              "raw_monto": row["monto"]
          })

        df_cg = pd.DataFrame(lista_creditos_gestion)
        df_cg = df_cg.sort_values(by="Días Transcurridos", ascending=False).reset_index(drop=True)

        st.metric("Total Deuda Activa (Créditos)", f"Bs. {formatear_monto_venezuela(df_cg['raw_monto'].sum())}")

        df_cg_display = df_cg[["Fecha Compra", "Obra", "Descripción", "Monto (Bs.)", "Días Transcurridos", "Estatus Crédito"]]
        
        def resaltar_tabla_creditos(row):
            if row["Días Transcurridos"] >= 13:
                return ['background-color: #ffe6e6; color: #cc0000; font-weight: bold'] * len(row)
            return [''] * len(row)

        st.dataframe(df_cg_display.style.apply(resaltar_tabla_creditos, axis=1), use_container_width=True, hide_index=True)
      else:
        st.success("¡Excelente noticia! No hay créditos pendientes activos en este momento.")
    else:
      st.info("No hay registros disponibles.")
  except Exception as e:
    st.error(f"Error cargando control de créditos: {e}")