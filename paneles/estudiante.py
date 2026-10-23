"""
paneles/estudiante.py
Panel del Estudiante.
Funciones: ver situación académica (incluyendo alerta de atraso),
gestionar ramos aprobados, y ver ramos disponibles para el próximo semestre.
"""
import streamlit as st
import pandas as pd
import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import database as db
from malla import MALLA_ICF, obtener_ramos_disponibles, calcular_atraso_alumno
from paneles import horario_estudiante

def render():
    usuario = st.session_state["usuario"]
    st.title(f"Panel del Estudiante — {usuario['nombre']}")

    estudiante = db.obtener_estudiante_por_usuario(usuario["id"])
    if not estudiante:
        st.warning("Tu perfil de estudiante no está configurado aún. Contacta al secretario académico.")
        return

    tabs = st.tabs(["Mi Situación Académica", "Ramos Aprobados", "Ramos Disponibles", "Mi Horario"])

    with tabs[0]:
        _tab_situacion(estudiante)
    with tabs[1]:
        _tab_ramos_aprobados(estudiante)
    with tabs[2]:
        _tab_ramos_disponibles(estudiante)
    with tabs[3]:
        horario_estudiante.render(estudiante)


# ── Tab 1: Situación académica y alerta de atraso ──────────────────────
def _tab_situacion(estudiante):
    st.subheader("Mi situación académica")
    st.caption(f"Semestre actual (según tu cohorte): {estudiante['semestre_actual']}")

    mes_actual = datetime.date.today().month
    default_impar = mes_actual <= 7  # marzo-julio ≈ primer semestre; agosto-diciembre ≈ segundo

    semestre_calendario = st.radio(
        "¿En qué mitad del año académico estamos?",
        ["Primer semestre", "Segundo semestre"],
        index=0 if default_impar else 1,
        horizontal=True,
        help="Se usa para saber si un ramo anual (como Ingeniería de Software o Práctica) se ofrece ahora o hay que esperar."
    )
    es_impar = (semestre_calendario == "Primer semestre")

    aprobados = [r["nombre_asig"] for r in db.obtener_ramos_aprobados(estudiante["id"])]

    resultado = calcular_atraso_alumno(
        estudiante["semestre_actual"], aprobados, semestre_actual_es_impar=es_impar
    )

    if not resultado["va_atrasado"]:
        st.success("Estás al día. No tienes ramos pendientes de semestres anteriores.")
        return

    st.warning(
        f"Tienes {resultado['total_atrasados']} ramo(s) pendiente(s) de semestres anteriores."
    )

    st.markdown("**Detalle por semestre:**")
    for sem in sorted(resultado["atrasados_por_semestre"].keys()):
        ramos = resultado["atrasados_por_semestre"][sem]
        st.write(f"- Semestre {sem}: {', '.join(ramos)}")

    if resultado["ramos_anuales_atrasados"]:
        st.error(
            "Ojo: entre tus pendientes hay ramo(s) que solo se dictan una vez al año — "
            f"{', '.join(resultado['ramos_anuales_atrasados'])}. Si no coincide con la mitad "
            "de año seleccionada arriba, tendrás que esperar al próximo período en que se ofrezcan."
        )

    st.info(
        f"Estimación: este atraso podría significarte al menos "
        f"**{resultado['semestres_estimados_atraso']} semestre(s) adicional(es)** para regularizarte, "
        "asumiendo que puedes tomar como máximo 2 ramos atrasados por semestre además de tu carga normal. "
        "Esto es una estimación orientativa, no un cálculo curricular oficial."
    )


# ── Tab 2: Ramos aprobados ──────────────────────────────────────────────
def _tab_ramos_aprobados(estudiante):
    st.subheader("Mis ramos aprobados")

    aprobados = db.obtener_ramos_aprobados(estudiante["id"])
    nombres_aprobados = {r["nombre_asig"] for r in aprobados}

    if aprobados:
        df = pd.DataFrame(aprobados)[["codigo_asig", "nombre_asig", "semestre_cursado"]]
        df.columns = ["Código", "Ramo", "Semestre cursado"]
        st.dataframe(df, width="stretch")
    else:
        st.info("Aún no tienes ramos aprobados registrados.")

    st.divider()
    st.caption("Registrar un ramo aprobado")

    ramos_no_aprobados = [r for r in MALLA_ICF if r["nombre"] not in nombres_aprobados]
    opciones = {r["nombre"]: r for r in ramos_no_aprobados}

    if opciones:
        sel = st.selectbox("Ramo", list(opciones.keys()))
        if st.button("Marcar como aprobado"):
            ramo = opciones[sel]
            db.registrar_ramo_aprobado(estudiante["id"], ramo["codigo"], ramo["nombre"], ramo["semestre"])
            st.success(f"{ramo['nombre']} marcado como aprobado.")
            st.rerun()
    else:
        st.info("Ya tienes todos los ramos de la malla marcados como aprobados.")


# ── Tab 3: Ramos disponibles ─────────────────────────────────────────────
def _tab_ramos_disponibles(estudiante):
    st.subheader("Ramos disponibles para el próximo período")

    aprobados = [r["nombre_asig"] for r in db.obtener_ramos_aprobados(estudiante["id"])]
    resultado = obtener_ramos_disponibles(estudiante["semestre_actual"], aprobados)

    if resultado["obligatorios"]:
        st.markdown("**Obligatorios de tu semestre:**")
        for r in resultado["obligatorios"]:
            st.write(f"- {r['nombre']} ({r['creditos']} créditos)")

    if resultado["pendientes"]:
        st.markdown("**Pendientes de semestres anteriores (ya puedes tomarlos):**")
        for r in resultado["pendientes"]:
            st.write(f"- {r['nombre']} (semestre {r['semestre']})")

    if resultado["adelantos"]:
        st.markdown("**Posibles adelantos:**")
        for r in resultado["adelantos"]:
            st.write(f"- {r['nombre']} (semestre {r['semestre']})")

    if not any(resultado.values()):
        st.info("No hay ramos disponibles para mostrar — revisa tus ramos aprobados.")