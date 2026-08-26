"""
pages/profesor.py
Panel del Profesor.
Funciones: ver clases asignadas y configurar disponibilidad horaria.
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import database as db

DIAS        = ["LU", "MA", "MI", "JU", "VI", "SA"]
DIAS_NOMBRE = {"LU": "Lunes", "MA": "Martes", "MI": "Miércoles",
               "JU": "Jueves", "VI": "Viernes", "SA": "Sábado"}
HORAS_TEXTO = [
    "08:30", "09:25", "10:20", "11:15", "12:10", "13:05",
    "14:00", "14:55", "15:50", "16:45", "17:40", "18:35",
    "19:30", "20:25"
]


def render():
    usuario = st.session_state["usuario"]
    st.title(f"👨‍🏫 Panel del Profesor — {usuario['nombre']}")

    # Buscar el perfil de profesor en la base de datos
    profesor = db.obtener_profesor_por_rut(usuario["username"])

    if not profesor:
        st.warning("Tu perfil de profesor no está configurado aún. Contacta al secretario académico.")
        return

    tabs = st.tabs(["📋 Mis Clases", "🗓️ Mi Disponibilidad"])

    with tabs[0]:
        _tab_clases(profesor)
    with tabs[1]:
        _tab_disponibilidad(profesor)


# ── Tab 1: Mis Clases ──────────────────────────────────────────────────
def _tab_clases(profesor):
    st.subheader("Mis clases asignadas")

    horarios = db.obtener_horarios()
    if not horarios:
        st.info("El secretario aún no ha generado un horario.")
        return

    opciones = {f"{h['nombre']} ({h['fecha'][:10]})": h["id"] for h in horarios}
    sel      = st.selectbox("Seleccionar horario", list(opciones.keys()))
    horario  = db.obtener_horario_por_id(opciones[sel])
    datos    = horario["datos"]

    # Filtrar solo los cursos de este profesor
    mis_cursos = [
        c for c in datos
        if str(c.get("RUT_Profesor", "")).strip() == str(profesor["rut"]).strip()
        or str(c.get("Profesor", "")).strip().lower() == str(profesor["nombre"]).strip().lower()
    ]

    if not mis_cursos:
        st.info("No tienes cursos asignados en este horario.")
        return

    st.success(f"Tienes **{len(mis_cursos)} sección(es)** asignadas.")

    df = pd.DataFrame(mis_cursos)[["NRC", "Asignatura", "Sala", "Semestre", "Horario Final"]]
    st.dataframe(df, use_container_width=True)

    # Vista semanal
    st.subheader("Vista semanal")
    _mostrar_grilla(mis_cursos)


def _mostrar_grilla(cursos):
    """Arma una tabla tipo grilla con los cursos distribuidos por día y hora."""
    DIAS_MAPA = {"LU": 0, "MA": 1, "MI": 2, "JU": 3, "VI": 4, "SA": 5}

    # Grilla vacía
    grilla = {dia: {h: "" for h in HORAS_TEXTO} for dia in DIAS}

    for curso in cursos:
        txt = curso.get("Horario Final", "")
        if not txt or txt == "SIN HORARIO":
            continue

        for parte in txt.split(" y "):
            parte  = parte.strip().lstrip(".")
            tokens = parte.split()
            if len(tokens) < 3:
                continue
            dia = tokens[0].upper()
            if dia not in DIAS_MAPA:
                continue
            try:
                ini    = tokens[1].replace(":", "")
                fin    = tokens[-1].replace(":", "")
                mi     = int(ini[:2]) * 60 + int(ini[2:])
                mf     = int(fin[:2]) * 60 + int(fin[2:])
                nombre = curso["Asignatura"][:20]
                for i, h_txt in enumerate(HORAS_TEXTO):
                    h_min = int(h_txt[:2]) * 60 + int(h_txt[3:])
                    if mi <= h_min < mf:
                        grilla[dia][h_txt] = nombre
            except Exception:
                pass

    df_grilla          = pd.DataFrame(grilla, index=HORAS_TEXTO)
    df_grilla.index.name = "Hora"
    df_grilla.columns  = [DIAS_NOMBRE[d] for d in DIAS]
    st.dataframe(df_grilla, use_container_width=True)


# ── Tab 2: Mi Disponibilidad ───────────────────────────────────────────
def _tab_disponibilidad(profesor):
    st.subheader("Configurar mi disponibilidad horaria")
    st.caption("Marca los bloques en los que **puedes** dar clases.")

    # Cargar disponibilidad guardada (si existe)
    disp_actual = db.obtener_disponibilidad(profesor["id"])

    nueva_disp = {}
    cols = st.columns(len(DIAS))

    for col, dia in zip(cols, DIAS):
        with col:
            st.markdown(f"**{DIAS_NOMBRE[dia]}**")
            for i, hora in enumerate(HORAS_TEXTO):
                clave   = (dia, i + 1)
                # Si no hay datos guardados, por defecto todo disponible
                default = disp_actual.get(clave, True)
                val     = st.checkbox(hora, value=default, key=f"disp_{dia}_{i}")
                nueva_disp[clave] = val

    if st.button("💾 Guardar disponibilidad", type="primary"):
        db.guardar_disponibilidad(profesor["id"], nueva_disp)
        disponibles = sum(1 for v in nueva_disp.values() if v)
        st.success(f"Disponibilidad guardada. {disponibles} bloques disponibles de 84 posibles.")

        if disponibles < 10:
            st.warning("⚠️ Tienes muy pocos bloques disponibles. Puede ser difícil asignarte cursos.")