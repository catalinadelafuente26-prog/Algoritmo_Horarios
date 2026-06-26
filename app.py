"""
app.py
Punto de entrada de la aplicación.
Para ejecutarlo: streamlit run app.py
"""
import streamlit as st
import database as db

# ── Configuración general de la página ────────────────────────────────
st.set_page_config(
    page_title="Planificación Académica UNAB",
    page_icon="🎓",
    layout="wide",
)

# ── Inicializar la base de datos al arrancar ───────────────────────────
db.inicializar_db()

# ── Estado de sesión ───────────────────────────────────────────────────
# Streamlit guarda variables entre interacciones usando session_state.
# Aquí guardamos el usuario que inició sesión.
if "usuario" not in st.session_state:
    st.session_state["usuario"] = None


# ── Pantalla de login ──────────────────────────────────────────────────
def pantalla_login():
    st.markdown("""
    <div style='text-align:center; padding: 2rem 0 1rem 0'>
        <h1>🎓 Sistema de Planificación Académica</h1>
        <h3 style='color:#666'>Facultad de Ingeniería — Universidad Andrés Bello</h3>
        <p style='color:#999'>Ingeniería Civil Informática</p>
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
            submitted = st.form_submit_button("Ingresar", use_container_width=True)

            if submitted:
                usuario = db.login(username, password)
                if usuario:
                    st.session_state["usuario"] = usuario
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

        st.divider()

        # ── Formulario de registro ─────────────────────────────────────
        st.subheader("Crear cuenta nueva")
        st.caption("Solo para profesores y estudiantes. El secretario es creado por administración.")

        with st.form("form_registro"):
            nuevo_nombre  = st.text_input("Nombre completo")
            nuevo_usuario = st.text_input("Usuario (usa tu RUT sin puntos ni guión)")
            nuevo_pass    = st.text_input("Contraseña", type="password", key="reg_pass1")
            nuevo_pass2   = st.text_input("Repetir contraseña", type="password", key="reg_pass2")
            nuevo_perfil  = st.selectbox("Perfil", ["estudiante", "profesor"])
            reg_submitted = st.form_submit_button("Crear cuenta", use_container_width=True)

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
                        st.success(f"Cuenta creada. Ya puedes iniciar sesión.")
                        # Si es profesor, crear su perfil automáticamente
                        if nuevo_perfil == "profesor":
                            usuario_nuevo = db.login(nuevo_usuario, nuevo_pass)
                            if usuario_nuevo:
                                db.crear_profesor(
                                    usuario_nuevo["id"], nuevo_usuario, nuevo_nombre
                                )
                    else:
                        st.error(mensaje)

        # ── Credenciales de demostración ───────────────────────────────
        with st.expander("🔑 Credenciales de prueba"):
            st.markdown("""
            | Perfil | Usuario | Contraseña |
            |--------|---------|-----------|
            | Secretario | `secretario` | `admin123` |
            | Profesor | crear cuenta | la que elijas |
            | Estudiante | crear cuenta | la que elijas |
            """)


# ── Barra lateral cuando hay sesión activa ────────────────────────────
def mostrar_sidebar():
    usuario = st.session_state["usuario"]

    iconos = {
        "secretario": "🗂️",
        "profesor":   "👨‍🏫",
        "estudiante": "🎓",
    }
    icono = iconos.get(usuario["perfil"], "👤")

    with st.sidebar:
        st.markdown(f"### {icono} {usuario['nombre']}")
        st.caption(f"Perfil: **{usuario['perfil'].title()}**")
        st.divider()

        # Descripción de funciones según perfil
        if usuario["perfil"] == "secretario":
            st.markdown("""
            **Funciones disponibles:**
            - 📅 Generar programación académica
            - 🔍 Ver y editar horarios
            - 👨‍🏫 Gestionar profesores
            - 🔔 Revisar alertas
            """)
        elif usuario["perfil"] == "profesor":
            st.markdown("""
            **Funciones disponibles:**
            - 📋 Ver mis clases asignadas
            - 🗓️ Configurar mi disponibilidad
            """)
        elif usuario["perfil"] == "estudiante":
            st.markdown("""
            **Funciones disponibles:**
            - 📚 Ver mi malla curricular
            - ✅ Registrar ramos aprobados
            - 🗓️ Generar mi horario personal
            - 👁️ Ver mi horario
            """)

        st.divider()
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            st.session_state["usuario"] = None
            st.rerun()


# ── Enrutador principal ────────────────────────────────────────────────
def main():
    if st.session_state["usuario"] is None:
        pantalla_login()
    else:
        mostrar_sidebar()
        perfil = st.session_state["usuario"]["perfil"]

        # Por ahora mostramos un mensaje temporal hasta crear cada panel
        if perfil == "secretario":
            st.title("🗂️ Panel del Secretario Académico")
            st.info("Panel en construcción — próximo paso.")
        elif perfil == "profesor":
            st.title("👨‍🏫 Panel del Profesor")
            st.info("Panel en construcción — próximo paso.")
        elif perfil == "estudiante":
            st.title("🎓 Panel del Estudiante")
            st.info("Panel en construcción — próximo paso.")


if __name__ == "__main__":
    main()