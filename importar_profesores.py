"""
importar_profesores.py
Lee el Excel de datos_varas.xlsx y crea un usuario + perfil de profesor
por cada profesor único encontrado.
Ejecutar UNA sola vez: python importar_profesores.py
"""
import pandas as pd
import database as db

def importar():
    db.inicializar_db()

    df = pd.read_excel("datos_varas.xlsx", skiprows=6)
    profes = (
        df[["Rut Profesor", "Nombre Profesor"]]
        .dropna()
        .drop_duplicates()
    )

    creados  = 0
    saltados = 0

    for _, fila in profes.iterrows():
        rut    = str(fila["Rut Profesor"]).strip()
        nombre = str(fila["Nombre Profesor"]).strip()

        # Saltamos entradas inválidas
        if not rut or rut == "nan" or "/" in rut or rut == "888888888":
            print(f"  [SALTADO] {nombre} — RUT inválido: {rut}")
            saltados += 1
            continue

        # Crear usuario con RUT como usuario y contraseña
        ok, _ = db.registrar_usuario(rut, rut, "profesor", nombre)

        # Crear perfil de profesor (aunque el usuario ya exista)
        usuario = db.login(rut, rut)
        uid = usuario["id"] if usuario else None
        db.crear_profesor(uid, rut, nombre)

        if ok:
            creados += 1
            print(f"  [OK] {nombre} ({rut})")
        else:
            saltados += 1
            print(f"  [YA EXISTE] {nombre} ({rut})")

    print(f"\nListo. {creados} profesores creados, {saltados} saltados.")

if __name__ == "__main__":
    importar()