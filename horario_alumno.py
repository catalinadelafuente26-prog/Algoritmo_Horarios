"""
horario_alumno.py
Lógica para armar el horario personal de un estudiante a partir de un
horario institucional ya generado: elige una sección por cada componente
(cátedra, ayudantía, laboratorio) de los ramos que el estudiante va a cursar,
sin que se topen entre sí.
"""

HORAS_INICIO = [510, 565, 620, 675, 730, 785, 840, 895, 950, 1005, 1060, 1115, 1170, 1225]
DIAS = {"LU": 0, "MA": 1, "MI": 2, "JU": 3, "VI": 4, "SA": 5}


def bloques_de_texto(txt):
    """Convierte '.LU 0830 - 1010 y .MI 1115 - 1255' en un conjunto de bloques (día*14 + índice)."""
    bloques = set()
    if not txt or txt == "SIN HORARIO":
        return bloques
    for parte in str(txt).split(" y "):
        tokens = parte.strip().lstrip(".").split()
        if len(tokens) < 3 or tokens[0].upper() not in DIAS:
            continue
        try:
            ini = tokens[1].replace(":", "")
            fin = tokens[-1].replace(":", "")
            mi = int(ini[:2]) * 60 + int(ini[2:])
            mf = int(fin[:2]) * 60 + int(fin[2:])
        except ValueError:
            continue
        for i, h in enumerate(HORAS_INICIO):
            if mi <= h < mf:
                bloques.add(DIAS[tokens[0].upper()] * 14 + i)
    return bloques


def agrupar_secciones(datos, nombres_ramos):
    """Devuelve {componente: [secciones]} para los ramos pedidos.
    componente = 'NOMBRE RAMO (Cátedra)' tal como aparece en el horario."""
    permitidos = {n.strip().upper() for n in nombres_ramos}
    componentes = {}
    for c in datos:
        asig = str(c.get("Asignatura", ""))
        base = asig.rsplit(" (", 1)[0].strip().upper()
        if base in permitidos:
            seccion = dict(c)
            seccion["_bloques"] = bloques_de_texto(c.get("Horario Final", ""))
            componentes.setdefault(asig, []).append(seccion)
    return componentes


def armar_horario(componentes, limite_pasos=200000):
    """Busca (con retroceso) una sección por componente sin topes.
    Devuelve (elegidas, sin_solucion): elegidas = {componente: sección},
    sin_solucion = lista de componentes que no se pudieron ubicar."""
    # Primero los componentes con menos opciones (más restrictivos)
    orden = sorted(componentes.keys(), key=lambda k: len(componentes[k]))
    pasos = [0]
    mejor = {"elegidas": {}}

    def dfs(i, ocupados, elegidas):
        pasos[0] += 1
        if len(elegidas) > len(mejor["elegidas"]):
            mejor["elegidas"] = dict(elegidas)
        if i == len(orden) or pasos[0] > limite_pasos:
            return i == len(orden)
        comp = orden[i]
        for sec in componentes[comp]:
            if sec["_bloques"] & ocupados:
                continue
            elegidas[comp] = sec
            if dfs(i + 1, ocupados | sec["_bloques"], elegidas):
                return True
            del elegidas[comp]
        return False

    ok = dfs(0, set(), {})
    elegidas = mejor["elegidas"]
    sin_solucion = [c for c in orden if c not in elegidas]
    return elegidas, sin_solucion