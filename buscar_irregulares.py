import pandas as pd
from malla import calcular_atraso_alumno

df = pd.read_excel("alumnos_prueba.xlsx")
n = 0
for _, f in df.iterrows():
    texto = "" if pd.isna(f["Ramos Aprobados"]) else str(f["Ramos Aprobados"])
    aprobados = [r.strip() for r in texto.split(";") if r.strip()]
    res = calcular_atraso_alumno(int(f["Semestre Actual"]), aprobados)
    if res["va_atrasado"]:
        print(f["RUT"], f["Nombre"], "| sem", f["Semestre Actual"],
              "|", res["total_atrasados"], "pendientes |",
              res["semestres_estimados_atraso"], "sem. estimados")
        n += 1
        if n == 8:
            break
        