"""
paneles/horario_estudiante.py
Pestaña "Mi Horario" del panel del estudiante: arma un horario personal
sin topes a partir de un horario institucional generado.
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import database as db
import horario_alumno as ha
from malla import obtener_ramos_disponibles

DIAS_COL = ["LU", "MA", "MI", "JU", "VI", "SA"]
NOMBRE_DIA = {"LU": "Lunes", "MA": "Martes", "MI": "Miércoles",
              "JU": "Jueves", "VI": "Viernes", "SA": "Sábado"}
HORAS_TEXTO = ["08:30", "09:25", "10:20", "11:15", "12:10", "13:05", "14:00",
               "14:55", "15:50", "16:45", "17:40", "18:35", "19:30", "20:25"]


def _grilla(secciones):
    """Tabla día x hora con el nombre corto del ramo en cada bloque."""
    grilla = {d: {h: "" for h in HORAS_TEXTO} for d in DIAS_COL}
    for sec in secciones:
        nombre = str(sec["Asignatura"])
        base_n, _, comp = nombre.rpartition(" (")
        if not base_n:
            base_n, comp = nombre, ""
        sufijo = {"Cátedra)": "(C)", "Ayudantía)": "(A)", "Lab)": "(L)"}.get(comp, "")
        corto = f"{base_n[:22]} {sufijo}".strip()
        for b in ha.bloques_de_texto(sec.get("Horario Final", "")):
            dia, idx = divmod(b, 14)
            grilla[DIAS_COL[dia]][HORAS_TEXTO[idx]] = corto
    df = pd.DataFrame(grilla, index=HORAS_TEXTO)
    df.index.name = "Hora"
    df.columns = [NOMBRE_DIA[d] for d in DIAS_COL]
    return df


def _mostrar(secciones):
    filas = [{
        "NRC": s["NRC"],
        "Asignatura": s["Asignatura"],
        "Profesor": s["Profesor"],
        "Horario": s["Horario Final"],
    } for s in sorted(secciones, key=lambda x: str(x["Asignatura"]))]
    st.dataframe(pd.DataFrame(filas), width="stretch", hide_index=True)
    st.markdown("**Vista semanal**")
    st.dataframe(_grilla(secciones), width="stretch")


def render(estudiante):
    st.subheader("Mi horario personal")
    st.caption("Se arma eligiendo una sección de cada componente de tus ramos, sin topes de horario.")

    horarios = db.obtener_horarios()
    if not horarios:
        st.info("El secretario aún no ha generado un horario institucional.")
        return

    opciones = {f"{h['nombre']} ({h['fecha'][:10]})": h["id"] for h in horarios}
    sel = st.selectbox("Horario institucional", list(opciones.keys()), key="mh_horario")
    horario_id = opciones[sel]
    datos = db.obtener_horario_por_id(horario_id)["datos"]

    aprobados = [r["nombre_asig"] for r in db.obtener_ramos_aprobados(estudiante["id"])]
    disp = obtener_ramos_disponibles(estudiante["semestre_actual"], aprobados)
    base = [r["nombre"] for r in disp["obligatorios"] + disp["pendientes"]]
    adelantos = [r["nombre"] for r in disp["adelantos"]]

    ramos_sel = st.multiselect(
        "Ramos que quiero cursar",
        base + adelantos,
        default=base,
        help="Por defecto aparecen tus ramos obligatorios y pendientes. Puedes agregar adelantos."
    )

    if st.button("Generar mi horario", type="primary", key="mh_generar"):
        comps = ha.agrupar_secciones(datos, ramos_sel)
        elegidas, sin = ha.armar_horario(comps)
        bases_ofrecidas = {c.rsplit(" (", 1)[0].strip().upper() for c in comps}
        sin_oferta = [r for r in ramos_sel if r.strip().upper() not in bases_ofrecidas]
        st.session_state["mh_resultado"] = {
            "horario_id": horario_id,
            "secciones": [{k: v for k, v in s.items() if k != "_bloques"} for s in elegidas.values()],
            "sin_ubicar": sin,
            "sin_oferta": sin_oferta,
        }

    res = st.session_state.get("mh_resultado")
    if res and res["horario_id"] == horario_id:
        if res["sin_oferta"]:
            st.warning("Sin oferta en este horario: " + ", ".join(res["sin_oferta"]))
        if res["sin_ubicar"]:
            st.error("No se pudo ubicar sin topes: " + ", ".join(res["sin_ubicar"]))
        elif res["secciones"]:
            st.success(f"Horario armado sin topes: {len(res['secciones'])} secciones.")
        if res["secciones"]:
            _mostrar(res["secciones"])
            if st.button("Guardar este horario", key="mh_guardar"):
                db.guardar_horario_estudiante(
                    estudiante["id"], horario_id, [s["NRC"] for s in res["secciones"]]
                )
                st.success("Horario guardado.")

    guardado = db.obtener_horario_estudiante(estudiante["id"])
    if guardado:
        with st.expander(f"Mi horario guardado ({guardado['fecha'][:10]})"):
            datos_g = db.obtener_horario_por_id(guardado["horario_base_id"])["datos"]
            nrcs = set(guardado["nrcs"])
            _mostrar([c for c in datos_g if c["NRC"] in nrcs])