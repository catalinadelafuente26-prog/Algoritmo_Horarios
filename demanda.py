"""
demanda.py
Calcula la demanda de ramos según los estudiantes cargados y las secciones necesarias.
"""
import math
from malla import MALLA_ICF, obtener_ramos_disponibles
import database as db


def calcular_demanda(semestre_calendario_impar):
    """Cuenta cuántos estudiantes necesitan cada ramo en el período indicado.
    semestre_calendario_impar=True  -> primer semestre del año
    semestre_calendario_impar=False -> segundo semestre del año"""
    estudiantes = db.obtener_estudiantes_con_ramos()
    demanda = {r["nombre"]: 0 for r in MALLA_ICF}
    adelantos = {r["nombre"]: 0 for r in MALLA_ICF}
    no_ofrecido = {}

    for e in estudiantes:
        disp = obtener_ramos_disponibles(e["semestre_actual"], e["aprobados"])
        for r in disp["obligatorios"] + disp["pendientes"]:
            if r.get("oferta_anual") and ((r["semestre"] % 2 == 1) != semestre_calendario_impar):
                no_ofrecido[r["nombre"]] = no_ofrecido.get(r["nombre"], 0) + 1
            else:
                demanda[r["nombre"]] += 1
        for r in disp["adelantos"]:
            adelantos[r["nombre"]] += 1

    return {
        "total_estudiantes": len(estudiantes),
        "demanda": demanda,
        "adelantos": adelantos,
        "no_ofrecido": no_ofrecido,
    }


def calcular_secciones(demanda, adelantos, cupo_general=50, cupo_lab=30):
    """Convierte la demanda de cada ramo en número de secciones por componente."""
    filas = []
    for ramo in MALLA_ICF:
        d = demanda.get(ramo["nombre"], 0)
        if d == 0:
            continue
        sec_cat = math.ceil(d / cupo_general) if ramo["horas_catedral"] > 0 else 0
        sec_ayu = math.ceil(d / cupo_general) if ramo["horas_ayudantia"] > 0 else 0
        sec_lab = math.ceil(d / cupo_lab)     if ramo["horas_lab"] > 0 else 0
        filas.append({
            "Semestre":                 ramo["semestre"],
            "Ramo":                     ramo["nombre"],
            "Demanda":                  d,
            "Secc. cátedra":            sec_cat,
            "Secc. ayudantía":          sec_ayu,
            "Secc. laboratorio":        sec_lab,
            "Total NRC":                sec_cat + sec_ayu + sec_lab,
            "Elegibles para adelantar": adelantos.get(ramo["nombre"], 0),
        })
    return filas


def secciones_por_ramo(filas):
    """Devuelve {NOMBRE_RAMO: {"catedral": n, "ayudantia": n, "lab": n}}"""
    return {
        f["Ramo"].strip().upper(): {
            "catedral":  f["Secc. cátedra"],
            "ayudantia": f["Secc. ayudantía"],
            "lab":       f["Secc. laboratorio"],
        }
        for f in filas
    }