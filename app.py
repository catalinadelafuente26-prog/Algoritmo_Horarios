"""
app.py
Punto de entrada de la aplicación.
Para ejecutarlo: streamlit run app.py
"""
import streamlit as st
import database as db
import extra_streamlit_components as stx
from datetime import datetime, timedelta
import base64

SUPERUSUARIOS = {"admin"}

# ── Configuración general de la página ────────────────────────────────
st.set_page_config(
    page_title="Planificación Académica UNAB",
    page_icon="logo_unab.png",
    layout="wide",
)

# ── Estilos institucionales UNAB ───────────────────────────────────────
st.markdown("""
<style>
h1 {
    border-bottom: 3px solid #A90429;
    padding-bottom: 0.3rem;
}
button[kind="primary"] {
    background-color: #A90429 !important;
    border-color: #A90429 !important;
}
[data-testid="stImage"] {
    display: flex;
    justify-content: center;
}
.ramo-badge {
    display: inline-block;
    background-color: #A90429;
    color: white;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    margin: 2px 4px 2px 0;
}
.tabla-profesores {
    width: 100%;
    border-collapse: collapse;
    margin-top: 0.5rem;
}
.tabla-profesores th {
    background-color: #13253F;
    color: white;
    text-align: left;
    padding: 10px 12px;
    font-size: 0.85rem;
    text-transform: uppercase;
}
.tabla-profesores td {
    padding: 8px 12px;
    border-bottom: 1px solid #2a3f5c;
    font-size: 0.9rem;
    vertical-align: top;
}
.tabla-profesores tr:nth-child(even) {
    background-color: #0d2035;
}
.tabla-profesores-contenedor {
    max-height: 500px;
    overflow-y: auto;
    border: 1px solid #2a3f5c;
    border-radius: 8px;
}
.tabla-profesores-contenedor::-webkit-scrollbar {
    width: 10px;
}
.tabla-profesores-contenedor::-webkit-scrollbar-track {
    background: #0d2035;
}
.tabla-profesores-contenedor::-webkit-scrollbar-thumb {
    background-color: #A90429;
    border-radius: 6px;
}
.tabla-profesores thead th {
    position: sticky;
    top: 0;
    z-index: 1;
}
</style>
""", unsafe_allow_html=True)

def obtener_cookie_manager():
    return stx.CookieManager(key="cookie_manager_global")

cookie_manager = obtener_cookie_manager()

@st.cache_resource
def _iniciar_bd():
    db.inicializar_db()

_iniciar_bd()

# ── Estado de sesión ───────────────────────────────────────────────────
# Streamlit guarda variables entre interacciones usando session_state.
# Aquí guardamos el usuario que inició sesión.
if "usuario" not in st.session_state:
    usuario_id_cookie = cookie_manager.get("usuario_id")
    usuario_recuperado = None
    if usuario_id_cookie:
        usuario_recuperado = db.obtener_usuario_por_id(int(usuario_id_cookie))
    st.session_state["usuario"] = usuario_recuperado


# ── Pantalla de login ──────────────────────────────────────────────────
def pantalla_login():
    with open("logo_unab.png", "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()

    st.markdown(f"""
    <div style='display: flex; justify-content: center; padding-top: 1rem; background-color: #03102C;'>
        <img src='data:image/png;base64,{logo_base64}' width='300'
             style='filter: invert(1); mix-blend-mode: screen;'>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center; padding: 2rem 0 1rem 0'>
        <h1>Sistema de Planificación Académica</h1>
        <h3 style='color:#B8C4D0'>Facultad de Ingeniería — Universidad Andrés Bello</h3>
        <p style='color:#8A97A6'>Ingeniería Civil Informática</p>
    </div>
    """, unsafe_allow_html=True)

    # Centramos el formulario con columnas
    col_izq, col_centro, col_der = st.columns([1, 2, 1])

    with col_centro:

        # ── Formulario de login ────────────────────────────────────────
        st.subheader("Iniciar sesión")
        with st.form("form_login"):
            username  = st.text_input("Usuario")
            password  = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar", width="stretch")

            if submitted:
                usuario = db.login(username, password)
                if usuario:
                    st.session_state["usuario"] = usuario
                    cookie_manager.set(
                        "usuario_id",
                        str(usuario["id"]),
                        expires_at=datetime.now() + timedelta(minutes=30),
                        key="set_cookie_login"
                    )
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

        st.divider()

        # ── Formulario de registro ─────────────────────────────────────
        st.subheader("Crear cuenta nueva")
        st.caption("Solo para profesores y estudiantes. El secretario es creado por administración.")

        with st.form("form_registro"):
            nuevo_nombre   = st.text_input("Nombre completo")
            nuevo_usuario  = st.text_input("Usuario (usa tu RUT sin puntos ni guión)")
            nuevo_pass     = st.text_input("Contraseña", type="password", key="reg_pass1")
            nuevo_pass2    = st.text_input("Repetir contraseña", type="password", key="reg_pass2")
            nuevo_perfil   = st.selectbox("Perfil", ["estudiante", "profesor"])
            nuevo_semestre = st.number_input(
                "Semestre actual (solo si te registras como estudiante)",
                min_value=1, max_value=10, step=1, value=1
            )
            reg_submitted  = st.form_submit_button("Crear cuenta", width="stretch")

            if reg_submitted:
                if not nuevo_nombre or not nuevo_usuario or not nuevo_pass:
                    st.error("Completa todos los campos.")
                elif nuevo_pass != nuevo_pass2:
                    st.error("Las contraseñas no coinciden.")
                elif len(nuevo_pass) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres.")
                else:
                    ok, mensaje = db.registrar_usuario(
                        nuevo_usuario, nuevo_pass, nuevo_perfil, nuevo_nombre
                    )
                    if ok:
                        st.success("Cuenta creada. Ya puedes iniciar sesión.")
                        usuario_nuevo = db.login(nuevo_usuario, nuevo_pass)
                        if usuario_nuevo:
                            if nuevo_perfil == "profesor":
                                db.crear_profesor(
                                    usuario_nuevo["id"], nuevo_usuario, nuevo_nombre
                                )
                            elif nuevo_perfil == "estudiante":
                                db.crear_estudiante(
                                    usuario_nuevo["id"], nuevo_usuario, nuevo_nombre, nuevo_semestre
                                )
                    else:
                        st.error(mensaje)

# ── Barra lateral cuando hay sesión activa ────────────────────────────
def mostrar_sidebar():
    usuario = st.session_state["usuario"]

    # El superusuario ve el menú según la vista elegida en "Ver el sistema como"
    perfil_mostrado = usuario["perfil"]
    if usuario["username"] in SUPERUSUARIOS:
        perfil_mostrado = st.session_state.get("su_vista", "Secretario").lower()

    with st.sidebar:
        st.markdown(f"### {usuario['nombre']}")
        st.caption(f"Perfil: **{perfil_mostrado.title()}**")
        st.divider()

        # Descripción de funciones según perfil
        if perfil_mostrado == "secretario":
            st.markdown("""
            **Funciones disponibles:**
            - Generar programación académica
            - Ver y editar horarios
            - Gestionar profesores
            - Revisar alertas
            """)
        elif perfil_mostrado == "profesor":
            st.markdown("""
            **Funciones disponibles:**
            - Ver mis clases asignadas
            - Configurar mi disponibilidad
            """)
        elif perfil_mostrado == "estudiante":
            st.markdown("""
            **Funciones disponibles:**
            - Ver mi malla curricular
            - Registrar ramos aprobados
            - Generar mi horario personal
            - Ver mi horario
            """)

        st.divider()

        if st.button("Cerrar sesión", width="stretch"):
            st.session_state["usuario"] = None
            cookie_manager.set(
                "usuario_id",
                "",
                expires_at=datetime.now() - timedelta(days=1),
                key="delete_cookie_logout"
            )
            st.rerun()

def _render_superusuario():
    """Vista del superusuario: secretario por defecto, o cualquier profesor/estudiante."""
    with st.sidebar:
        st.divider()
        st.markdown("**Modo superusuario**")
        vista = st.radio("Ver el sistema como", ["Secretario", "Profesor", "Estudiante"], key="su_vista")

        objetivo = None
        if vista == "Profesor":
            profs = [p for p in db.obtener_profesores() if p.get("usuario_id")]
            opciones = {f"{p['nombre']} ({p['rut']})": p for p in profs}
            if opciones:
                sel = st.selectbox("Profesor", list(opciones.keys()), key="su_prof")
                objetivo = db.obtener_usuario_por_id(opciones[sel]["usuario_id"])
        elif vista == "Estudiante":
            ests = db.obtener_estudiantes()
            opciones = {f"{e['nombre']} ({e['rut']})": e for e in ests}
            if opciones:
                sel = st.selectbox("Estudiante (puedes escribir para buscar)", list(opciones.keys()), key="su_est")
                objetivo = db.obtener_usuario_por_id(opciones[sel]["usuario_id"])

    if vista == "Secretario":
        from paneles import secretario
        secretario.render()
        return

    if objetivo is None:
        st.info("No hay usuarios de este tipo para mostrar.")
        return

    st.caption(f"Vista como: {objetivo['nombre']}")
    original = st.session_state["usuario"]
    st.session_state["usuario"] = objetivo
    try:
        if vista == "Profesor":
            from paneles import profesor
            profesor.render()
        else:
            from paneles import estudiante
            estudiante.render()
    finally:
        st.session_state["usuario"] = original

# ── Enrutador principal ────────────────────────────────────────────────
def main():
    if st.session_state["usuario"] is None:
        pantalla_login()
    else:
        cookie_manager.set(
            "usuario_id",
            str(st.session_state["usuario"]["id"]),
            expires_at=datetime.now() + timedelta(minutes=30),
            key="refresh_cookie_activity"
        )
        mostrar_sidebar()
        usuario = st.session_state["usuario"]
        perfil = usuario["perfil"]

        if usuario["username"] in SUPERUSUARIOS:
            _render_superusuario()
        elif perfil == "secretario":
            from paneles import secretario
            secretario.render()
        elif perfil == "profesor":
            from paneles import profesor
            profesor.render()
        elif perfil == "estudiante":
            from paneles import estudiante
            estudiante.render()


if __name__ == "__main__":
    main()
    