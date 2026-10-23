import pandas as pd
import random
import copy

# -----------------------------------------------------------------------
# PESOS DE PENALIZACIÓN
# El algoritmo evalúa cada horario sumando "puntos malos".
# Mientras más alto el número, peor es ese tipo de conflicto.
# Al final queremos que el puntaje total sea lo más cercano a 0 posible.
# -----------------------------------------------------------------------

# Estos tres son inaceptables, por eso tienen pesos altísimos
PESO_CHOQUE_DOCENTE = 1000  # un profe no puede estar en dos salas a la vez
PESO_CHOQUE_SALA    = 1000  # tampoco dos cursos pueden usar la misma sala
PESO_MALLA_DURO     = 500   # dos ramos obligatorios del mismo semestre no pueden topar

# Estos son "ojalá no pasen" pero no invalidan el horario
PESO_MALLA_BLANDO   = 50    # tope de malla cuando el alumno va adelantado
PESO_DISPONIBILIDAD = 100   # el profe tiene ese día ocupado
PESO_VENTANAS       = 20    # hora libre en medio de clases (ej: clase a las 8, nada hasta las 12)

# -----------------------------------------------------------------------
# ESTRUCTURA DE TIEMPO
# Representamos cada bloque horario como un número entero.
# Hay 14 bloques por día × 6 días = 84 bloques en la semana.
# Bloque 0 = lunes 08:30, bloque 13 = lunes 20:25, bloque 14 = martes 08:30, etc.
# -----------------------------------------------------------------------
BLOQUES_POR_DIA      = 14
TOTAL_BLOQUES_SEMANA = 84

DIAS_MAPA    = {"LU": 0, "MA": 1, "MI": 2, "JU": 3, "VI": 4, "SA": 5}
DIAS_INVERSO = {v: k for k, v in DIAS_MAPA.items()}

# Cada fila es (número de bloque, minutos desde medianoche, texto para mostrar)
HORAS_INICIO_MINUTOS = [
    (1,  8*60 + 30, "08:30"), (2,  9*60 + 25, "09:25"),
    (3,  10*60 + 20, "10:20"), (4, 11*60 + 15, "11:15"),
    (5,  12*60 + 10, "12:10"), (6, 13*60 + 5,  "13:05"),
    (7,  14*60 + 0,  "14:00"), (8, 14*60 + 55, "14:55"),
    (9,  15*60 + 50, "15:50"), (10, 16*60 + 45, "16:45"),
    (11, 17*60 + 40, "17:40"), (12, 18*60 + 35, "18:35"),
    (13, 19*60 + 30, "19:30"), (14, 20*60 + 25, "20:25"),
]

# -----------------------------------------------------------------------
# PARÁMETROS DEL ALGORITMO GENÉTICO
# Si el algoritmo es muy lento, bajar TAMANO_POBLACION o GENERACIONES.
# Si encuentra poca diversidad de soluciones, subir TAMANO_TORNEO.
# -----------------------------------------------------------------------
TAMANO_POBLACION   = 50
GENERACIONES       = 250
TASA_MUTACION_BASE = 0.50   # probabilidad de que un curso "mute" su horario
TAMANO_TORNEO      = 6      # cuántos candidatos compiten en cada selección

# -----------------------------------------------------------------------
# CLASES DE DATOS
# -----------------------------------------------------------------------
class Curso:
    def __init__(self, nrc, nombre, rut_profesor, nombre_profesor, sala,
                 semestre, tipo_inscripcion="OBLIGATORIO", bloques_enteros=None):
        self.nrc             = nrc
        self.nombre          = nombre
        self.rut_profesor    = rut_profesor
        self.nombre_profesor = nombre_profesor
        self.sala            = sala
        self.tipo_inscripcion = tipo_inscripcion.upper()

        # El semestre viene a veces como "3.0" o "3S", así que extraemos solo el número
        try:
            self.semestre = int(''.join(filter(str.isdigit, str(semestre))))
        except ValueError:
            self.semestre = 0

        self.bloques_enteros    = bloques_enteros if bloques_enteros else []
        
        # Si no tenemos horario de referencia asumimos 2 bloques (lo más común)
        self.duracion_requerida = len(self.bloques_enteros) if self.bloques_enteros else 2

        self.un_solo_dia = False  # True para labs y ayudantías
        self.grupo = 0            # grupo de sección: solo choca con cursos del mismo grupo

class Profesor:
    def __init__(self, rut, nombre):
        self.rut    = rut
        self.nombre = nombre
        self.bloques_no_disponibles = set()

        # TODO: cargar esto desde el Excel de disponibilidad real.
        # Por ahora simulamos que cada profe tiene 1 o 2 días completamente ocupados.
        dias_ocupados = random.sample(range(6), random.randint(1, 2))
        for d in dias_ocupados:
            for b in range(BLOQUES_POR_DIA):
                self.bloques_no_disponibles.add((d * BLOQUES_POR_DIA) + b)

# Se llenan cuando se llama a cargar_datos_desde_excel()
profesores_reales: dict = {}
cursos_reales: dict     = {}

# -----------------------------------------------------------------------
# TRADUCCIÓN DE HORARIOS
# El Excel guarda el horario como texto (".LU 0830 - 1010").
# Necesitamos convertirlo a nuestra representación de bloques enteros,
# y también poder hacer el proceso inverso para mostrar resultados.
# -----------------------------------------------------------------------
def traducir_horario_a_enteros(texto_horario: str) -> list[int]:
    # Si la celda está vacía o no es texto, no hay nada que traducir
    if pd.isna(texto_horario) or not isinstance(texto_horario, str):
        return []

    bloques_encontrados = []
    texto_limpio = texto_horario.upper().replace(".", "").strip()

    # Buscar qué día es (LU, MA, MI...)
    dia_encontrado = None
    for dia_str, indice_dia in DIAS_MAPA.items():
        if dia_str in texto_limpio:
            dia_encontrado = indice_dia
            break

    if dia_encontrado is None:
        return []

    try:
        # Los números en el texto son la hora de inicio y fin, ej: "0830" y "1010"
        partes_hora = [s for s in texto_limpio.split() if s.isdigit()]
        if len(partes_hora) < 2:
            return []

        hora_ini_str, hora_fin_str = partes_hora[0], partes_hora[1]
        min_inicio = int(hora_ini_str[:2]) * 60 + int(hora_ini_str[2:])
        min_fin    = int(hora_fin_str[:2]) * 60 + int(hora_fin_str[2:])

        # Ver qué bloques de nuestra tabla caen dentro de ese rango
        for num_bloque, minutos_bloque, _ in HORAS_INICIO_MINUTOS:
            if min_inicio <= minutos_bloque < min_fin:
                bloques_encontrados.append((dia_encontrado * BLOQUES_POR_DIA) + (num_bloque - 1))

    except Exception:
        pass

    return bloques_encontrados

def traducir_enteros_a_texto(lista_bloques: list[int]) -> str:
    if not lista_bloques:
        return "SIN HORARIO"

    # Agrupar los bloques por día para armar el texto día a día
    bloques_por_dia: dict = {}
    for b in sorted(lista_bloques):
        d, blq = divmod(b, BLOQUES_POR_DIA)
        bloques_por_dia.setdefault(d, []).append(blq)

    textos = []
    for d, blqs in bloques_por_dia.items():
        nombre_dia  = DIAS_INVERSO.get(d, "LU")
        idx_min, idx_max = min(blqs), max(blqs)
        hora_inicio = HORAS_INICIO_MINUTOS[idx_min][2].replace(":", "")
        
        # La clase termina 45 minutos después del inicio del último bloque
        minutos_fin = HORAS_INICIO_MINUTOS[idx_max][1] + 45
        hora_fin    = f"{minutos_fin // 60:02d}{minutos_fin % 60:02d}"
        textos.append(f".{nombre_dia} {hora_inicio} - {hora_fin}")

    return " y ".join(textos)

def cargar_datos_desde_excel(ruta: str = "datos_varas.xlsx"):
    try:
        # Las primeras 6 filas del Excel son encabezado institucional, no datos
        df = pd.read_excel(ruta, skiprows=6)
        df = df.dropna(subset=["NRC", "Nombre Asignatura", "Rut Profesor"])

        for _, fila in df.iterrows():
            rut_prof  = str(fila["Rut Profesor"]).strip()
            nom_prof  = str(fila["Nombre Profesor"]).strip()
            nrc_curso = int(fila["NRC"])

            # Si la sala está vacía o es "COMUN" (sala compartida sin asignar), la marcamos como virtual
            sala_raw = str(fila["Sala"]).strip().upper()
            sala = (
                f"VIRTUAL_{nrc_curso}"
                if not sala_raw or sala_raw == "NAN" or "COMUN" in sala_raw
                else sala_raw
            )

            tipo_inscripcion = (
                str(fila["Tipo Inscripcion"]).strip()
                if "Tipo Inscripcion" in df.columns
                else "OBLIGATORIO"
            )

            # Agregamos el profe solo si no lo habíamos visto antes
            if rut_prof not in profesores_reales:
                profesores_reales[rut_prof] = Profesor(rut_prof, nom_prof)

            # Lo mismo con los cursos (puede haber filas duplicadas en el Excel)
            if nrc_curso not in cursos_reales:
                cursos_reales[nrc_curso] = Curso(
                    nrc_curso,
                    str(fila["Nombre Asignatura"]).strip(),
                    rut_prof,
                    nom_prof,
                    sala,
                    fila["Semestre que Paga"],
                    tipo_inscripcion,
                    traducir_horario_a_enteros(fila["Horario"]),
                )

        print(f"Datos cargados — {len(cursos_reales)} cursos, {len(profesores_reales)} profesores")

    except Exception as e:
        print(f"Error al leer el Excel: {e}")

# -----------------------------------------------------------------------
# GENERACIÓN DE HORARIOS ALEATORIOS
# -----------------------------------------------------------------------
def calcular_chunks(duracion_requerida: int) -> list[int]:
    # Dividimos la duración en bloques de máximo 2 horas.
    # Ej: un curso de 5 horas → [2, 2, 1], que se ubican en días distintos.
    chunks = []
    temp   = duracion_requerida
    while temp > 0:
        if temp >= 2:
            chunks.append(2)
            temp -= 2
        else:
            chunks.append(1)
            temp -= 1
    return chunks

def generar_bloques_al_azar(duracion_requerida: int, un_solo_dia: bool = False) -> list[int]:
    if un_solo_dia:
        # Todo en un mismo día de corrido
        dia       = random.randint(0, 5)
        block_max = BLOQUES_POR_DIA - duracion_requerida
        inicio    = random.randint(0, max(0, block_max))
        return [(dia * BLOQUES_POR_DIA) + inicio + i for i in range(duracion_requerida)]

    chunks        = calcular_chunks(duracion_requerida)
    dias_elegidos = random.sample(range(6), min(len(chunks), 6))
    bloques       = []

    for dia, size in zip(dias_elegidos, chunks):
        block_max = BLOQUES_POR_DIA - size
        inicio    = random.randint(0, block_max) if block_max > 0 else 0
        bloques.extend([(dia * BLOQUES_POR_DIA) + inicio + i for i in range(size)])

    return bloques

# -----------------------------------------------------------------------
# FUNCIÓN DE FITNESS
# Recorre todos los cursos y cuenta cuántos conflictos hay.
# Retorna el puntaje total (0 = horario perfecto), los NRCs con problemas graves,
# y un desglose por tipo de conflicto.
# -----------------------------------------------------------------------
def obtener_conflictos_y_fitness(lista_cursos: dict) -> tuple[int, set, dict]:
    c_duro, c_malla_blanda, c_disp, c_ventanas = 0, 0, 0, 0
    nrcs_malos = set()

    # Registros para detectar colisiones: qué profe/sala/semestre está en cada bloque
    r_prof, r_sala, r_malla = {}, {}, {}

    for nrc, c in lista_cursos.items():
        for b in c.bloques_enteros:

            # Choque de profe: si ya hay otro curso con este profe en este bloque
            r_prof.setdefault(b, {})
            if c.rut_profesor in r_prof[b]:
                r_prof[b][c.rut_profesor].append(nrc)
                c_duro += PESO_CHOQUE_DOCENTE
            else:
                r_prof[b][c.rut_profesor] = [nrc]

            # Choque de sala: misma lógica
            r_sala.setdefault(b, {})
            if c.sala in r_sala[b]:
                r_sala[b][c.sala].append(nrc)
                c_duro += PESO_CHOQUE_SALA
            else:
                r_sala[b][c.sala] = [nrc]

            # Choque de malla: revisamos si hay algún otro ramo del semestre adyacente
            # (±1 semestre para cubrir a alumnos adelantados o atrasados)
            # Solo cuentan los cursos del mismo grupo de sección.
            if c.semestre > 0:
                r_malla.setdefault(b, [])
                for s_occ, tipo_occ, nom_occ, g_occ in r_malla[b]:
                    if abs(c.semestre - s_occ) <= 1 and c.nombre != nom_occ and c.grupo == g_occ:
                        if c.tipo_inscripcion == "OBLIGATORIO" and tipo_occ == "OBLIGATORIO":
                            c_duro += PESO_MALLA_DURO
                            nrcs_malos.add(nrc)
                        else:
                            c_malla_blanda += PESO_MALLA_BLANDO
                r_malla[b].append((c.semestre, c.tipo_inscripcion, c.nombre, c.grupo))

            # Disponibilidad del profe: simplemente revisamos si ese bloque está bloqueado
            prof = profesores_reales.get(c.rut_profesor)
            if prof and b in prof.bloques_no_disponibles:
                c_disp += PESO_DISPONIBILIDAD

    # Segundo pasada: agregar a nrcs_malos todos los que tienen choque de profe o sala
    # (los de malla obligatoria ya se marcaron arriba)
    for b, profs in r_prof.items():
        for p, nrcs in profs.items():
            if len(nrcs) > 1:
                nrcs_malos.update(nrcs)
    for b, salas in r_sala.items():
        for s, nrcs in salas.items():
            if len(nrcs) > 1:
                nrcs_malos.update(nrcs)

    # Horas ventana: por cada semestre, revisamos si hay huecos en el día
    # Ej: si un semestre tiene clases en bloques 1, 2 y 5 → hay 2 bloques de hueco
    horarios_semestre: dict = {}
    for nrc, c in lista_cursos.items():
        if c.semestre > 0:
            for b in c.bloques_enteros:
                dia, blq = divmod(b, BLOQUES_POR_DIA)
                horarios_semestre.setdefault((c.semestre, c.grupo), {}).setdefault(dia, set()).add(blq)
    for sem, dias in horarios_semestre.items():
        for dia, blqs in dias.items():
            if len(blqs) > 1:
                huecos = (max(blqs) - min(blqs) + 1) - len(blqs)
                c_ventanas += huecos * PESO_VENTANAS

    costo_total = c_duro + c_malla_blanda + c_disp + c_ventanas
    detalles    = {"Duro": c_duro, "MBlanda": c_malla_blanda, "Profe": c_disp, "Huecos": c_ventanas}
    return costo_total, nrcs_malos, detalles

# -----------------------------------------------------------------------
# OPERADORES DEL ALGORITMO GENÉTICO
# -----------------------------------------------------------------------
def seleccionar_padre_torneo(poblacion_actual: list) -> dict:
    # Tomamos TAMANO_TORNEO candidatos al azar y nos quedamos con el mejor
    return min(random.sample(poblacion_actual, TAMANO_TORNEO), key=lambda x: x[0])[1]

def cruzar_horarios(padre1: dict, padre2: dict) -> dict:
    # Cruce de un punto: el hijo toma los primeros N cursos del padre1
    # y el resto del padre2. El punto de corte es aleatorio.
    hijo = copy.deepcopy(padre1)
    nrcs = list(padre1.keys())
    corte = random.randint(1, len(nrcs) - 1)
    for nrc in nrcs[corte:]:
        hijo[nrc].bloques_enteros = copy.deepcopy(padre2[nrc].bloques_enteros)
    return hijo

def swap_par_a_par(horario: dict, nrcs_malos: set) -> dict:
    # Operador de reparación rápida: toma un curso con conflicto y lo intercambia
    # con uno que no tiene problemas (si tienen la misma duración).
    # Es menos invasivo que reasignar desde cero.
    h_swap = copy.deepcopy(horario)
    if not nrcs_malos:
        return h_swap

    libres = [nrc for nrc in h_swap if nrc not in nrcs_malos]
    if not libres:
        return h_swap

    for nrc_malo in list(nrcs_malos):
        if nrc_malo not in h_swap:
            continue
        c_malo     = h_swap[nrc_malo]
        candidatos = [
            n for n in libres
            if len(h_swap[n].bloques_enteros) == len(c_malo.bloques_enteros) and n != nrc_malo
        ]
        if candidatos:
            socio = random.choice(candidatos)
            c_malo.bloques_enteros, h_swap[socio].bloques_enteros = (
                h_swap[socio].bloques_enteros, c_malo.bloques_enteros
            )
    return h_swap

def mutacion_inteligente_dirigida(horario: dict, nrcs_malos: set, prob: float) -> dict:
    # Mutación dirigida: en vez de cambiar un horario al azar, buscamos activamente
    # un hueco libre donde el curso conflictivo pueda ir sin generar nuevos problemas.
    # Si ya no hay conflictos duros, mutamos a todos para mejorar las ventanas.
    h_mutado = copy.deepcopy(horario)
    objetivos = list(nrcs_malos) if nrcs_malos else list(h_mutado.keys())

    # Construimos un mapa de qué está ocupado en los cursos que NO tienen conflictos
    # (esos no los tocamos, solo movernos alrededor de ellos)
    o_prof, o_sala, o_malla = set(), set(), {}
    for n, c in h_mutado.items():
        if n not in nrcs_malos:
            for b in c.bloques_enteros:
                o_prof.add((c.rut_profesor, b))
                o_sala.add((c.sala, b))
                if c.semestre > 0:
                    o_malla.setdefault(b, []).append((c.semestre, c.nombre, c.grupo))

    for nrc in objetivos:
        if nrc not in h_mutado or random.random() >= prob:
            continue

        c      = h_mutado[nrc]
        chunks = calcular_chunks(c.duracion_requerida)

        dias_disponibles = list(range(6))
        random.shuffle(dias_disponibles)

        # Si el curso debe ir en un solo día, forzamos 1 solo chunk
        if getattr(c, 'un_solo_dia', False):
            for dia in dias_disponibles:
                block_max = BLOQUES_POR_DIA - c.duracion_requerida
                if block_max < 0:
                    continue
                inicio = random.randint(0, block_max)
                ventana = [(dia * BLOQUES_POR_DIA) + inicio + i for i in range(c.duracion_requerida)]
                c_prof = any((c.rut_profesor, b) in o_prof for b in ventana)
                c_sala = any((c.sala, b) in o_sala for b in ventana)
                if not c_prof and not c_sala:
                    c.bloques_enteros = ventana
                    for b in ventana:
                        o_prof.add((c.rut_profesor, b))
                        o_sala.add((c.sala, b))
                    break
            continue  # saltar el resto de la mutación para este curso

        nuevos_bloques = []
        dias_usados    = []
        exito_total    = True

        # Para cada "pedazo" del curso, buscamos un día y bloque donde quepa sin conflicto
        for size in chunks:
            espacio_encontrado = False

            for dia in dias_disponibles:
                if dia in dias_usados:
                    continue

                max_b = BLOQUES_POR_DIA - size
                for b_ini in range(max_b + 1):
                    ventana = [(dia * BLOQUES_POR_DIA) + b_ini + i for i in range(size)]

                    conflicto_prof  = any((c.rut_profesor, b) in o_prof for b in ventana)
                    conflicto_sala  = any((c.sala, b) in o_sala for b in ventana)
                    conflicto_malla = False

                    if c.semestre > 0:
                        for b in ventana:
                            if b in o_malla:
                                for s_occ, nom_occ, g_occ in o_malla[b]:
                                    if abs(c.semestre - s_occ) <= 1 and nom_occ != c.nombre and g_occ == c.grupo:
                                        conflicto_malla = True
                                        break
                            if conflicto_malla:
                                break

                    if not conflicto_prof and not conflicto_sala and not conflicto_malla:
                        nuevos_bloques.extend(ventana)
                        dias_usados.append(dia)
                        espacio_encontrado = True
                        
                        # Marcamos estos bloques como ocupados para los siguientes chunks
                        for b in ventana:
                            o_prof.add((c.rut_profesor, b))
                            o_sala.add((c.sala, b))
                        break

                if espacio_encontrado:
                    break

            if not espacio_encontrado:
                exito_total = False
                break

        if exito_total and nuevos_bloques:
            c.bloques_enteros = nuevos_bloques
        else:
            # Si no encontramos espacio, hacemos un swap de emergencia con algún otro curso
            socio = random.choice(list(h_mutado.keys()))
            if socio != nrc and len(h_mutado[socio].bloques_enteros) == len(c.bloques_enteros):
                c.bloques_enteros, h_mutado[socio].bloques_enteros = (
                    h_mutado[socio].bloques_enteros, c.bloques_enteros
                )

    return h_mutado

# -----------------------------------------------------------------------
# FUNCIÓN AUXILIAR: crea un horario completamente aleatorio
# (cada "individuo" de la población inicial se crea así)
# -----------------------------------------------------------------------
def crear_individuo() -> dict:
    ind = copy.deepcopy(cursos_reales)
    for c in ind.values():
        c.bloques_enteros = generar_bloques_al_azar(c.duracion_requerida, c.un_solo_dia)
    return ind

# -----------------------------------------------------------------------
# MAIN: acá corre todo el algoritmo genético
# -----------------------------------------------------------------------
if __name__ == "__main__":
    print("=== OPTIMIZADOR DE HORARIOS — ALGORITMO GENÉTICO ===\n")

    cargar_datos_desde_excel()

    # Crear la población inicial con horarios completamente aleatorios
    poblacion = []
    for _ in range(TAMANO_POBLACION):
        ind = crear_individuo()
        fit, _, det = obtener_conflictos_y_fitness(ind)
        poblacion.append((fit, ind, det))

    poblacion.sort(key=lambda x: x[0])
    mejor_fit              = poblacion[0][0]
    mejor_individuo_global = copy.deepcopy(poblacion[0][1])
    estancamiento          = 0
    prob_mut               = TASA_MUTACION_BASE
    reinicios              = 0

    print(f"Puntaje inicial (todo aleatorio): {mejor_fit}  |  {poblacion[0][2]}\n")

    # Ciclo principal del algoritmo genético
    for gen in range(1, GENERACIONES + 1):
        # Elitismo: los 2 mejores pasan directo a la siguiente generación
        nueva_poblacion = [poblacion[0], poblacion[1]]

        while len(nueva_poblacion) < TAMANO_POBLACION:
            p1   = seleccionar_padre_torneo(poblacion)
            p2   = seleccionar_padre_torneo(poblacion)
            hijo = cruzar_horarios(p1, p2)

            _, malos, _ = obtener_conflictos_y_fitness(hijo)

            # Si llevamos muchas generaciones sin mejorar, mutamos más agresivo
            if estancamiento >= 20:
                hijo = swap_par_a_par(hijo, malos)
                _, malos, _ = obtener_conflictos_y_fitness(hijo)
                hijo = mutacion_inteligente_dirigida(hijo, malos, 0.85)
            else:
                hijo = mutacion_inteligente_dirigida(hijo, malos, prob_mut)

            fit_h, _, det_h = obtener_conflictos_y_fitness(hijo)
            nueva_poblacion.append((fit_h, hijo, det_h))

        poblacion = sorted(nueva_poblacion, key=lambda x: x[0])

        # Actualizar el mejor histórico
        if poblacion[0][0] < mejor_fit:
            mejor_fit              = poblacion[0][0]
            mejor_individuo_global = copy.deepcopy(poblacion[0][1])
            estancamiento          = 0
            prob_mut               = TASA_MUTACION_BASE
        else:
            estancamiento += 1

        # Si llevamos 60 generaciones sin mejorar, reiniciamos la población
        # pero guardamos los 5 mejores para no perder lo que ya encontramos
        if estancamiento >= 60 and mejor_fit > 0:
            reinicios += 1
            print(f"  [Reinicio #{reinicios}] en generación {gen} — inyectando diversidad...")
            elite     = poblacion[:5]
            nueva_div = []
            for _ in range(TAMANO_POBLACION - 5):
                ind_nuevo = crear_individuo()
                fit_n, _, det_n = obtener_conflictos_y_fitness(ind_nuevo)
                nueva_div.append((fit_n, ind_nuevo, det_n))
            poblacion     = sorted(elite + nueva_div, key=lambda x: x[0])
            estancamiento = 0
            prob_mut      = TASA_MUTACION_BASE

        # Imprimir progreso cada 10 generaciones
        if gen % 10 == 0:
            det = poblacion[0][2]
            print(
                f"Gen {gen:03d} → Fit: {poblacion[0][0]:6d} | "
                f"Duros: {det['Duro']} | "
                f"Malla (adelanto): {det['MBlanda']} | "
                f"Profe (disponibilidad): {det['Profe']} | "
                f"Huecos alumnos: {det['Huecos']}"
            )

    # Resultado final
    print("\n" + "=" * 60)
    print("Proceso terminado. Evaluando el mejor horario encontrado...")
    _, _, det_final = obtener_conflictos_y_fitness(mejor_individuo_global)
    
    print(f"\nPuntaje final: {mejor_fit} puntos de penalización")
    print(
        f"  Choques críticos:       {det_final['Duro']}\n"
        f"  Topes de adelanto:      {det_final['MBlanda']}\n"
        f"  Bloques no disponibles: {det_final['Profe']}\n"
        f"  Horas ventana alumnos:  {det_final['Huecos']}"
    )