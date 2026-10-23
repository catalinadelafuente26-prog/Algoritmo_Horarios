"""
importar_estudiantes.py
Lee un Excel de alumnos (RUT, Nombre, Semestre Actual, Ramos Aprobados)
y crea un usuario + perfil de estudiante por cada fila, registrando
también sus ramos ya aprobados.
Ejecutar: python importar_estudiantes.py
"""
import pandas as pd
import database as db
from malla import MALLA_ICF

# Índice nombre de ramo → (codigo, semestre) para cruzar contra el Excel
INDICE_MALLA = {r["nombre"].strip().upper(): (r["codigo"], r["semestre"]) for r in MALLA_ICF}


def importar(ruta_excel="alumnos_prueba.xlsx"):
    db.inicializar_db()
    df = pd.read_excel(ruta_excel)

    creados = 0
    ya_existian = 0
    ramos_registrados = 0
    ramos_sin_match = set()

    for _, fila in df.iterrows():
        rut      = str(fila["RUT"]).strip()
        nombre   = str(fila["Nombre"]).strip()
        semestre = int(fila["Semestre Actual"])
        ramos_txt = "" if pd.isna(fila.get("Ramos Aprobados")) else str(fila["Ramos Aprobados"])

        ok, _ = db.registrar_usuario(rut, rut, "estudiante", nombre)
        usuario = db.login(rut, rut)
        if not usuario:
            print(f"  [ERROR] No se pudo crear/recuperar usuario para {nombre} ({rut})")
            continue

        db.crear_estudiante(usuario["id"], rut, nombre, semestre)
        estudiante = db.obtener_estudiante_por_usuario(usuario["id"])
        if not estudiante:
            print(f"  [ERROR] No se pudo crear perfil de estudiante para {nombre} ({rut})")
            continue

        if ok:
            creados += 1
        else:
            ya_existian += 1

        for ramo_nombre in [r.strip() for r in ramos_txt.split(";") if r.strip()]:
            match = INDICE_MALLA.get(ramo_nombre.upper())
            if match:
                codigo, semestre_ramo = match
                db.registrar_ramo_aprobado(estudiante["id"], codigo, ramo_nombre, semestre_ramo)
                ramos_registrados += 1
            else:
                ramos_sin_match.add(ramo_nombre)

    print(f"\nListo. {creados} estudiantes nuevos, {ya_existian} ya existían, {ramos_registrados} ramos aprobados registrados.")
    if ramos_sin_match:
        print(f"\nRamos del Excel que no encontraron match en malla.py ({len(ramos_sin_match)}):")
        for r in sorted(ramos_sin_match):
            print(f"  - {r}")


if __name__ == "__main__":
    importar()