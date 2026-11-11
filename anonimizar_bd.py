"""
anonimizar_bd.py
Crea una COPIA anonimizada de la base de datos para tomar capturas y presentar.
No modifica la base original.

Uso (desde la carpeta del proyecto, donde está tesis_planificacion.db):
    python anonimizar_bd.py
Resultado: tesis_planificacion_ANON.db
"""
import re
import shutil
import sqlite3

ORIGEN = "tesis_planificacion.db"
DESTINO = "tesis_planificacion_ANON.db"

shutil.copyfile(ORIGEN, DESTINO)
con = sqlite3.connect(DESTINO)
con.row_factory = sqlite3.Row
cur = con.cursor()

profes = cur.execute("SELECT id, usuario_id, rut, nombre FROM profesores ORDER BY id").fetchall()

# Reemplazos de texto: nombre completo y RUT -> valores ficticios
reemplazos = []
for p in profes:
    nuevo_nombre = f"Docente {p['id']:03d}"
    nuevo_rut = f"{10000000 + p['id']}-0"
    reemplazos.append((p["nombre"], nuevo_nombre))
    reemplazos.append((p["rut"], nuevo_rut))
    cur.execute("UPDATE profesores SET rut=?, nombre=?, email=NULL WHERE id=?",
                (f"TMP{p['id']}", nuevo_nombre, p["id"]))
    if p["usuario_id"]:
        cur.execute("UPDATE usuarios SET username=?, nombre=? WHERE id=?",
                    (f"TMP{p['id']}", nuevo_nombre, p["usuario_id"]))
# Segundo paso para respetar las restricciones UNIQUE
for p in profes:
    nuevo_rut = f"{10000000 + p['id']}-0"
    cur.execute("UPDATE profesores SET rut=? WHERE id=?", (nuevo_rut, p["id"]))
    if p["usuario_id"]:
        cur.execute("UPDATE usuarios SET username=? WHERE id=?", (nuevo_rut, p["usuario_id"]))

# Nombres más largos primero, para no dejar restos
reemplazos.sort(key=lambda x: len(x[0]), reverse=True)

def limpiar(texto):
    if texto is None:
        return texto
    for viejo, nuevo in reemplazos:
        if viejo:
            texto = re.sub(re.escape(viejo), nuevo, texto, flags=re.IGNORECASE)
    return texto

# Horarios guardados (campo Profesor y RUT dentro del JSON) y alertas
for fila in cur.execute("SELECT id, datos_json FROM horarios_generados").fetchall():
    cur.execute("UPDATE horarios_generados SET datos_json=? WHERE id=?",
                (limpiar(fila["datos_json"]), fila["id"]))
for fila in cur.execute("SELECT id, mensaje FROM alertas").fetchall():
    cur.execute("UPDATE alertas SET mensaje=? WHERE id=?", (limpiar(fila["mensaje"]), fila["id"]))

con.commit()

# Verificación: ¿queda algún nombre original?
restos = 0
textos = [r[0] for r in cur.execute("SELECT datos_json FROM horarios_generados")]
textos += [r[0] for r in cur.execute("SELECT mensaje FROM alertas")]
for viejo, _ in reemplazos:
    if viejo and any(viejo.lower() in (t or "").lower() for t in textos):
        restos += 1
print(f"Profesores anonimizados: {len(profes)}")
print("Restos de nombres originales:", restos)
con.close()
print(f"Listo: {DESTINO}")
