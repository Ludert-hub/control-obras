from datetime import datetime
import pandas as pd
import streamlit as st
from supabase import create_client, Client
import urllib.parse

# --- CONFIGURACION DE LA PAGINA ---
st.set_page_config(
    page_title="OPERACION ARO, C.A. - Control de Obras",
    page_icon="🏗️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS PERSONALIZADOS (ESTILO APPSHEET MOVIL) ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        max-width: 650px !important;
    }
    .top-bar {
        background-color: #155A9A;
        color: white;
        padding: 12px 16px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.15);
    }
    .top-bar-title {
        font-size: 20px;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin: 0;
    }
    .date-header {
        font-size: 15px;
        font-weight: 700;
        color: #222;
        margin-top: 16px;
        margin-bottom: 6px;
        padding-bottom: 4px;
        border-bottom: 2px solid #eee;
    }
    .subtotal-badge {
        background-color: #E2E5E9;
        color: #333;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 14px;
        font-weight: 700;
        margin-left: 8px;
    }
    .monto-azul {
        color: #155A9A;
        font-weight: 700;
        font-size: 14px;
        white-space: nowrap;
    }
    .concepto-txt {
        color: #333;
        font-size: 14px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .detail-label {
        color: #666;
        font-size: 13px;
        margin-top: 12px;
        margin-bottom: 2px;
    }
    .detail-value {
        color: #111;
        font-size: 20px;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .detail-monto {
        color: #155A9A;
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .menu-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        background: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 10px;
    }

    /* Corrección total para móviles: columnas horizontales sin solapamiento */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        flex-wrap: nowrap !important;
        gap: 2px !important;
    }
    div[data-testid="column"] {
        width: auto !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* Columnas más delgadas y compactas */
    div[data-testid="column"] {
        padding: 0 2px !important;
    }

    /* Forzar diseño horizontal en móviles y evitar apilamiento */
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            display: flex !important;
            align-items: center !important;
            flex-wrap: nowrap !important;
            gap: 2px !important;
        }
        div[data-testid="column"] {
            flex: 1 1 auto !important;
            min-width: 0 !important;
            width: auto !important;
            padding: 0 1px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXION A SUPABASE ---
URL = "https://ubfbyxlaakftmayftabc.supabase.co"
KEY = "sb_publishable_VqZW4HmqWV--BLGWIAu3cg_AhGUIYoZ"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(URL, KEY)

supabase = init_supabase()

# --- ESTADO DE NAVEGACION ---
if "vista" not in st.session_state:
    st.session_state.vista = "MENU"
if "orden_seleccionada" not in st.session_state:
    st.session_state.orden_seleccionada = None
if "modo_formulario" not in st.session_state:
    st.session_state.modo_formulario = "NUEVO"

def ir_a(nueva_vista, registro=None, modo="NUEVO"):
    st.session_state.vista = nueva_vista
    st.session_state.orden_seleccionada = registro
    st.session_state.modo_formulario = modo

# --- FUNCIONES DE FORMATO ---
def formatear_monto_venezuela(valor):
    try:
        val_float = float(valor)
        s = f"{val_float:,.2f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return s
    except Exception:
        return "0,00"

MESES_ES = {
    1: "ene.", 2: "feb.", 3: "mar.", 4: "abr.", 5: "may.", 6: "jun.",
    7: "jul.", 8: "ago.", 9: "sep.", 10: "oct.", 11: "nov.", 12: "dic."
}

def fecha_espanol(dt):
    if pd.isnull(dt):
        return "Sin fecha"
    return f"{dt.day} de {MESES_ES.get(dt.month, '')} de {dt.year}"

def desglosar_descripcion(desc_raw):
    desc_str = str(desc_raw or "")
    origen = "PUNTO"
    obs = ""
    concepto = desc_str

    if " | OBS:" in concepto:
        partes = concepto.split(" | OBS:")
        concepto = partes[0]
        obs = partes[1].strip()
    elif " | OBSERVACIONES:" in concepto:
        partes = concepto.split(" | OBSERVACIONES:")
        concepto = partes[0]
        obs = partes[1].strip()

    if concepto.startswith("[") and "]" in concepto:
        origen = concepto.split("]")[0].replace("[", "").strip()
        concepto = concepto.split("]", 1)[1].strip()

    return origen, concepto, obs


# ==========================================
# ALERTA DE CREDITOS COMPACTA (>= 13 DIAS)
# ==========================================
def mostrar_alerta_creditos():
    try:
        res_alertas = supabase.table("registros").select("*").not_.like("estado", "TAREA_%").execute()
        if res_alertas.data:
            df_alt = pd.DataFrame(res_alertas.data)
            df_alt["fecha_dt"] = pd.to_datetime(df_alt["fecha"], errors="coerce")
            hoy = pd.Timestamp.now().normalize()
            deudas = []
            for _, row in df_alt.iterrows():
                desc = str(row["descripcion"]).upper()
                if "CREDITO" in desc and pd.notnull(row["fecha_dt"]):
                    dias = (hoy - row["fecha_dt"].normalize()).days
                    if dias >= 13:
                        obra_txt = str(row["obra"]).upper().replace("SRA. BARBARA", "ESOBADES").replace("SRA BARBARA", "ESOBADES")
                        deudas.append(f"<li><b>{row['fecha_dt'].strftime('%d/%m/%Y')}</b> | {obra_txt} | Bs. {formatear_monto_venezuela(row['monto'])} ({dias} días)</li>")
            if deudas:
                st.markdown(f"""
                <div style="background-color: #fff3f3; border-left: 4px solid #cc0000; padding: 8px 12px; margin-bottom: 12px; border-radius: 4px; font-size: 13px; color: #a80000;">
                    <b>🚨 Créditos próximos a vencer (15 días):</b><ul style="margin:0; padding-left:15px;">{''.join(deudas)}</ul>
                </div>
                """, unsafe_allow_html=True)
    except Exception:
        pass


# ==============================================================================
# VISTA 1: MENU PRINCIPAL (Estilo Imagen 1)
# ==============================================================================
if st.session_state.vista == "MENU":
    st.markdown("""
    <div class="top-bar">
        <span class="top-bar-title">☰ &nbsp; SYSSA, C.A. - MENU</span>
        <span>🔍 &nbsp; ☑️</span>
    </div>
    """, unsafe_allow_html=True)

    mostrar_alerta_creditos()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="menu-card">
            <div style="font-size: 75px; line-height: 1.1;">📋🛒</div>
            <div style="font-weight: 600; color: #333; margin-top: 10px;">ORDEN DE COMPRA</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Abrir Órdenes de Compra", use_container_width=True, type="primary"):
            ir_a("ORDENES")
            st.rerun()

    with col2:
        st.markdown("""
        <div class="menu-card">
            <div style="font-size: 75px; line-height: 1.1;">👷‍♂️🧱</div>
            <div style="font-weight: 600; color: #333; margin-top: 10px;">ASISTENCIA / TAREAS</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Abrir Asistencia y Tareas", use_container_width=True):
            ir_a("TAREAS")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        if st.button("➕ Nueva Orden Directa", use_container_width=True):
            ir_a("FORMULARIO", None, "NUEVO")
            st.rerun()
    with col4:
        if st.button("📊 Ver Reportes / Exportar", use_container_width=True):
            ir_a("REPORTES")
            st.rerun()


# ==============================================================================
# VISTA 2: LISTADO DE ORDENES AGRUPADO POR FECHA (Estilo Imagen 2)
# ==============================================================================
elif st.session_state.vista == "ORDENES":
    c_nav1, c_nav2, c_nav3 = st.columns([1, 4, 1])
    with c_nav1:
        if st.button("⬅️", help="Volver al Menú"):
            ir_a("MENU")
            st.rerun()
    with c_nav2:
        st.markdown("<h3 style='margin:0; color:#155A9A;'>ORDENES</h3>", unsafe_allow_html=True)
    with c_nav3:
        if st.button("🔄", help="Sincronizar"):
            st.rerun()

    col_top_a, col_top_b = st.columns([2, 1])
    try:
        response = supabase.table("registros").select("*").not_.like("estado", "TAREA_%").execute()
        rows = response.data or []
    except Exception as e:
        st.error(f"Error conectando a la nube: {e}")
        rows = []

    if rows:
        df = pd.DataFrame(rows)
        df["obra"] = df["obra"].fillna("ESOBADES").astype(str).str.upper()
        df["obra"] = df["obra"].str.replace("SRA. BARBARA", "ESOBADES", regex=False).str.replace("SRA BARBARA", "ESOBADES", regex=False)
        df["fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
        df = df.sort_values(by=["fecha_dt", "id"], ascending=[False, False]).reset_index(drop=True)

        with col_top_a:
            obras_disp = ["TODAS LAS OBRAS"] + sorted(list(df["obra"].unique()))
            obra_filtro = st.selectbox("Filtrar Obra:", obras_disp, label_visibility="collapsed")
        with col_top_b:
            if st.button("➕ Nueva Orden", type="primary", use_container_width=True):
                ir_a("FORMULARIO", None, "NUEVO")
                st.rerun()

        if obra_filtro != "TODAS LAS OBRAS":
            df = df[df["obra"] == obra_filtro]

        st.markdown("""
        <div style="display:flex; font-weight:700; color:#333; padding:8px 0; border-bottom:2px solid #ccc; font-size:14px;">
            <div style="width:40%;">Monto</div>
            <div style="width:50%;">Concepto</div>
            <div style="width:10%; text-align:right;">Ver</div>
        </div>
        """, unsafe_allow_html=True)

        for fecha_val, grupo in df.groupby("fecha_dt", sort=False):
            subtotal_dia = grupo["monto"].sum()
            fecha_texto = fecha_espanol(fecha_val)
            
            st.markdown(f"""
            <div class="date-header">
                {fecha_texto} <span class="subtotal-badge">Bs.{formatear_monto_venezuela(subtotal_dia)}</span>
            </div>
            """, unsafe_allow_html=True)

            for _, row in grupo.iterrows():
                _, concepto_limpio, _ = desglosar_descripcion(row["descripcion"])
                if not concepto_limpio:
                    concepto_limpio = str(row["obra"])

                c2, c3, c4 = st.columns([2.2, 3.5, 0.6])
                with c2:
                    monto_str = f"Bs.{formatear_monto_venezuela(row['monto'])}" if row["monto"] > 0 else ""
                    st.markdown(f"<div class='monto-azul'>{monto_str}</div>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<div class='concepto-txt'>{concepto_limpio}</div>", unsafe_allow_html=True)
                with c4:
                    if st.button("✏️", key=f"open_{row['id']}", help="Ver detalles y modificar"):
                        ir_a("DETALLE", row.to_dict())
                        st.rerun()
                st.markdown("<hr style='margin: 4px 0; border: none; border-top: 1px solid #eee;'>", unsafe_allow_html=True)
    else:
        st.info("No hay órdenes registradas todavía.")
        if st.button("➕ Crear Primera Orden", type="primary"):
            ir_a("FORMULARIO", None, "NUEVO")
            st.rerun()


# ==============================================================================
# VISTA 3: DETALLES DE LA OPERACION ("Details" - Estilo Imagen 5)
# ==============================================================================
elif st.session_state.vista == "DETALLE":
    reg = st.session_state.orden_seleccionada
    if not reg:
        ir_a("ORDENES")
        st.rerun()

    c_top1, c_top2, c_top3 = st.columns([1, 4, 1.5])
    with c_top1:
        if st.button("⬅️", key="back_from_detail"):
            ir_a("ORDENES")
            st.rerun()
    with c_top2:
        st.markdown("<h3 style='margin:0; color:#155A9A;'>Details</h3>", unsafe_allow_html=True)
    with c_top3:
        if st.button("🗑️ Borrar", type="secondary", use_container_width=True):
            supabase.table("registros").delete().eq("id", reg["id"]).execute()
            st.toast("Orden eliminada correctamente")
            ir_a("ORDENES")
            st.rerun()

    st.markdown("---")

    estado_str = str(reg.get("estado", ""))
    url_foto = estado_str.split("URL:")[1] if "URL:" in estado_str else ""

    if url_foto:
        st.image(url_foto, use_container_width=True)
    else:
        st.caption("📷 *Sin recibo o foto adjunta en esta operación.*")

    origen_val, concepto_val, obs_val = desglosar_descripcion(reg.get("descripcion", ""))
    fecha_dt = pd.to_datetime(reg.get("fecha"), errors="coerce")
    obra_mostrar = str(reg.get("obra", "ESOBADES")).upper().replace("SRA. BARBARA", "ESOBADES").replace("SRA BARBARA", "ESOBADES")

    st.markdown(f"""
    <div class="detail-label">Concepto</div>
    <div class="detail-value">{concepto_val or 'Sin descripción'}</div>

    <div class="detail-label">ORDEN</div>
    <div class="detail-value">{reg.get('id')}</div>

    <div class="detail-label">Obra / Destino</div>
    <div class="detail-value">{obra_mostrar}</div>

    <div class="detail-label">Monto</div>
    <div class="detail-monto">Bs.{formatear_monto_venezuela(reg.get('monto', 0))}</div>

    <div class="detail-label">Fecha_Operacion</div>
    <div class="detail-value">{fecha_espanol(fecha_dt)}</div>

    <div class="detail-label">Metodo_Pago / Origen de Fondos</div>
    <div class="detail-value">{origen_val}</div>
    """, unsafe_allow_html=True)

    if obs_val:
        st.markdown(f"""
        <div class="detail-label">Observaciones</div>
        <div class="detail-value">{obs_val}</div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✏️ MODIFICAR ESTA OPERACIÓN", type="primary", use_container_width=True):
        ir_a("FORMULARIO", reg, "EDITAR")
        st.rerun()


# ==============================================================================
# VISTA 4: FORMULARIO NUEVA ORDEN / EDITAR ORDEN (Estilo Imagenes 3 y 4)
# ==============================================================================
elif st.session_state.vista == "FORMULARIO":
    es_edicion = (st.session_state.modo_formulario == "EDITAR" and st.session_state.orden_seleccionada is not None)
    reg_actual = st.session_state.orden_seleccionada if es_edicion else {}

    titulo_form = f"Editar Orden #{reg_actual.get('id')}" if es_edicion else "Nueva Orden de Compra"

    c_f1, c_f2 = st.columns([1, 5])
    with c_f1:
        if st.button("⬅️", key="back_form"):
            ir_a("DETALLE" if es_edicion else "ORDENES", reg_actual if es_edicion else None)
            st.rerun()
    with c_f2:
        st.markdown(f"<h3 style='margin:0; color:#155A9A;'>{titulo_form}</h3>", unsafe_allow_html=True)

    try:
        res_all = supabase.table("registros").select("id, obra").execute()
        if res_all.data:
            proximo_id = max([int(r["id"]) for r in res_all.data if r.get("id")]) + 1
            obras_raw = [str(r["obra"]).upper().replace("SRA. BARBARA", "ESOBADES").replace("SRA BARBARA", "ESOBADES") for r in res_all.data if r.get("obra")]
            obras_existentes = sorted(list(set(obras_raw)))
        else:
            proximo_id = 1
            obras_existentes = ["ESOBADES"]
    except Exception:
        proximo_id = 1
        obras_existentes = ["ESOBADES"]

    if "ESOBADES" not in obras_existentes:
        obras_existentes.insert(0, "ESOBADES")

    id_mostrar = reg_actual.get("id", proximo_id)
    monto_def = float(reg_actual.get("monto", 0.0)) if es_edicion else None
    origen_def, concepto_def, obs_def = desglosar_descripcion(reg_actual.get("descripcion", "")) if es_edicion else ("PUNTO", "", "")
    obra_def = str(reg_actual.get("obra", "ESOBADES")).upper().replace("SRA. BARBARA", "ESOBADES").replace("SRA BARBARA", "ESOBADES") if es_edicion else "ESOBADES"

    try:
        fecha_def = datetime.strptime(str(reg_actual.get("fecha")), "%Y-%m-%d").date() if es_edicion else datetime.now().date()
    except Exception:
        fecha_def = datetime.now().date()

    # --- CAMPOS DEL FORMULARIO ---
    st.text_input("ORDEN", value=str(id_mostrar), disabled=True)

    opciones_obra = obras_existentes + ["➕ OTRA OBRA NUEVA..."]
    idx_obra = opciones_obra.index(obra_def) if obra_def in opciones_obra else 0
    sel_obra = st.selectbox("Obra / Proyecto", opciones_obra, index=idx_obra)
    if sel_obra == "➕ OTRA OBRA NUEVA...":
        obra_guardar = st.text_input("Escribe el nombre de la nueva obra:", value="ESOBADES").strip().upper()
    else:
        obra_guardar = sel_obra.strip().upper()

    monto_guardar = st.number_input(
        "Monto (Bs.)",
        min_value=0.0,
        value=monto_def,
        step=0.01,
        format="%.2f",
        placeholder="Bs. 0.00"
    )

    concepto_guardar = st.text_input("Concepto", value=concepto_def, placeholder="Ej. 5 cabillas 1/2, Tornillos de drywall...")

    fecha_guardar = st.date_input("Fecha_Operacion", value=fecha_def, format="DD/MM/YYYY")
    hora_guardar = st.time_input("Hora_Operacion", value=datetime.now().time())

    metodos_base = ["PUNTO", "PAGO MOVIL", "INVERSION PROPIA", "ECOVIDA", "CREDITO"]
    if origen_def and origen_def.upper() not in metodos_base:
        metodos_base.append(origen_def.upper())

    idx_metodo = metodos_base.index(origen_def.upper()) if origen_def.upper() in metodos_base else 0
    metodo_guardar = st.radio(
        "Metodo_Pago / Origen de Fondos",
        metodos_base,
        index=idx_metodo,
        horizontal=True
    )

    obs_guardar = st.text_input(
        "Observaciones",
        value=obs_def if obs_def else ("MANGO CENTER" if metodo_guardar == "CREDITO" else ""),
        placeholder="Proveedor, nota o detalle adicional..."
    )

    st.markdown("**Recibo_Pago (Foto o Factura)**")
    foto_nueva = st.file_uploader("Toca para tomar foto o subir recibo", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed")

    st.markdown("<hr>", unsafe_allow_html=True)

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("Cancel", use_container_width=True):
            ir_a("DETALLE" if es_edicion else "ORDENES", reg_actual if es_edicion else None)
            st.rerun()

    with col_b2:
        if st.button("Save", type="primary", use_container_width=True):
            monto_val = float(monto_guardar) if monto_guardar is not None else 0.0
            if not concepto_guardar.strip():
                st.error("Por favor ingresa el Concepto.")
            else:
                try:
                    est_anterior = str(reg_actual.get("estado", "REGISTRADO"))
                    url_comprobante = est_anterior.split("URL:")[1] if "URL:" in est_anterior else ""

                    if foto_nueva is not None:
                        file_bytes = foto_nueva.getvalue()
                        file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{foto_nueva.name}"
                        supabase.storage.from_("comprobantes").upload(
                            file_name, file_bytes, {"content-type": foto_nueva.type}
                        )
                        url_comprobante = supabase.storage.from_("comprobantes").get_public_url(file_name)

                    obs_str = f" | OBS: {obs_guardar.strip().upper()}" if obs_guardar.strip() else ""
                    desc_final = f"[{metodo_guardar}] {concepto_guardar.strip().upper()}{obs_str}"
                    estado_final = f"REGISTRADO|URL:{url_comprobante}" if url_comprobante else "REGISTRADO"

                    datos_guardar = {
                        "fecha": fecha_guardar.strftime("%Y-%m-%d"),
                        "monto": monto_val,
                        "obra": obra_guardar,
                        "descripcion": desc_final,
                        "estado": estado_final
                    }

                    if es_edicion:
                        supabase.table("registros").update(datos_guardar).eq("id", reg_actual["id"]).execute()
                        datos_guardar["id"] = reg_actual["id"]
                        st.toast("¡Operación actualizada con éxito!")
                        ir_a("DETALLE", datos_guardar)
                    else:
                        supabase.table("registros").insert(datos_guardar).execute()
                        st.toast("¡Nueva orden registrada!")
                        ir_a("ORDENES")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")


# ==============================================================================
# VISTA 5: ASISTENCIA / TAREAS DE OBRA
# ==============================================================================
elif st.session_state.vista == "TAREAS":
    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("⬅️"):
            ir_a("MENU")
            st.rerun()
    with c2:
        st.markdown("<h3 style='margin:0; color:#155A9A;'>ASISTENCIA Y TAREAS</h3>", unsafe_allow_html=True)

    with st.form("nueva_tarea_form"):
        t_obra = st.text_input("Obra", value="ESOBADES").strip().upper()
        t_desc = st.text_input("Descripción de Actividad / Asistencia").strip().upper()
        if st.form_submit_button("➕ Registrar Actividad", type="primary", use_container_width=True):
            if t_desc:
                supabase.table("registros").insert({
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                    "monto": 0.0,
                    "obra": t_obra,
                    "descripcion": t_desc,
                    "estado": "TAREA_PENDIENTE"
                }).execute()
                st.rerun()

    res_t = supabase.table("registros").select("*").like("estado", "TAREA_%").execute()
    if res_t.data:
        for t in reversed(res_t.data):
            est = "✅ LISTO" if "LISTO" in str(t["estado"]) else "⏳ PENDIENTE"
            obra_t = str(t["obra"]).upper().replace("SRA. BARBARA", "ESOBADES").replace("SRA BARBARA", "ESOBADES")
            col_a, col_b, col_c = st.columns([4, 1.5, 1])
            col_a.write(f"**{obra_t}** - {t['descripcion']} ({t['fecha']})")
            if col_b.button(est, key=f"t_est_{t['id']}"):
                nuevo_est = "TAREA_PENDIENTE" if "LISTO" in str(t["estado"]) else "TAREA_LISTO"
                supabase.table("registros").update({"estado": nuevo_est}).eq("id", t["id"]).execute()
                st.rerun()
            if col_c.button("🗑️", key=f"t_del_{t['id']}"):
                supabase.table("registros").delete().eq("id", t["id"]).execute()
                st.rerun()


# ==============================================================================
# VISTA 6: REPORTES Y EXPORTACION EXCEL / WHATSAPP
# ==============================================================================
elif st.session_state.vista == "REPORTES":
    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("⬅️"):
            ir_a("MENU")
            st.rerun()
    with c2:
        st.markdown("<h3 style='margin:0; color:#155A9A;'>REPORTES Y EXPORTACIÓN</h3>", unsafe_allow_html=True)

    res_rep = supabase.table("registros").select("*").not_.like("estado", "TAREA_%").execute()
    if res_rep.data:
        df_rep = pd.DataFrame(res_rep.data)
        df_rep["obra"] = df_rep["obra"].fillna("ESOBADES").astype(str).str.upper()
        df_rep["obra"] = df_rep["obra"].str.replace("SRA. BARBARA", "ESOBADES", regex=False).str.replace("SRA BARBARA", "ESOBADES", regex=False)
        st.metric("Total General Registrado", f"Bs. {formatear_monto_venezuela(df_rep['monto'].sum())}")
        
        csv_data = df_rep[["id", "fecha", "obra", "monto", "descripcion"]].to_csv(index=False, sep=";", encoding="utf-8-sig")
        st.download_button("📥 Descargar Base de Datos en Excel (CSV)", data=csv_data, file_name="Ordenes_ESOBADES.csv", mime="text/csv", use_container_width=True)

# --- BARRA INFERIOR FIJA PARA VOLVER AL MENU ---
st.markdown("---")
if st.button("🏠 MENU PRINCIPAL", use_container_width=True):
    ir_a("MENU")
    st.rerun()
