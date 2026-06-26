# Malla completa ICF — extraída del Excel oficial MALLA.xlsx
# Los prerrequisitos usan el nombre exacto del ramo tal como aparece en el Excel
MALLA_ICF = [
    # SEMESTRE 1
    {"codigo": "S1-01", "nombre": "INTRODUCCIÓN A LAS MATEMÁTICAS",              "semestre": 1,  "creditos": 7,  "requisitos": []},
    {"codigo": "S1-02", "nombre": "FÍSICA GENERAL",                               "semestre": 1,  "creditos": 8,  "requisitos": []},
    {"codigo": "S1-03", "nombre": "INTRODUCCIÓN A LA PROGRAMACIÓN",               "semestre": 1,  "creditos": 8,  "requisitos": []},
    {"codigo": "S1-04", "nombre": "INTRODUCCIÓN A LA INGENIERÍA",                 "semestre": 1,  "creditos": 7,  "requisitos": []},

    # SEMESTRE 2
    {"codigo": "S2-01", "nombre": "CÁLCULO DIFERENCIAL",                          "semestre": 2,  "creditos": 7,  "requisitos": ["INTRODUCCIÓN A LAS MATEMÁTICAS"]},
    {"codigo": "S2-02", "nombre": "FÍSICA EXPERIMENTAL",                          "semestre": 2,  "creditos": 7,  "requisitos": ["INTRODUCCIÓN A LAS MATEMÁTICAS", "FÍSICA GENERAL"]},
    {"codigo": "S2-03", "nombre": "BASE DE DATOS",                                "semestre": 2,  "creditos": 7,  "requisitos": ["INTRODUCCIÓN A LA PROGRAMACIÓN"]},
    {"codigo": "S2-04", "nombre": "QUIMICA Y AMBIENTE",                           "semestre": 2,  "creditos": 5,  "requisitos": []},
    {"codigo": "S2-05", "nombre": "HABILIDADES COMUNICATIVAS",                    "semestre": 2,  "creditos": 4,  "requisitos": []},

    # SEMESTRE 3
    {"codigo": "S3-01", "nombre": "CÁLCULO INTEGRAL",                             "semestre": 3,  "creditos": 7,  "requisitos": ["CÁLCULO DIFERENCIAL"]},
    {"codigo": "S3-02", "nombre": "MÉCANICA",                                     "semestre": 3,  "creditos": 8,  "requisitos": ["CÁLCULO DIFERENCIAL", "FÍSICA EXPERIMENTAL"]},
    {"codigo": "S3-03", "nombre": "ALGORITMOS Y ESTRUCTURAS DE DATOS",            "semestre": 3,  "creditos": 5,  "requisitos": ["INTRODUCCIÓN A LA PROGRAMACIÓN"]},
    {"codigo": "S3-04", "nombre": "COMPLIANCE AND ACCOUNTABILITY",                "semestre": 3,  "creditos": 5,  "requisitos": ["INTRODUCCIÓN A LA INGENIERÍA"]},
    {"codigo": "S3-05", "nombre": "TALLER DE INNOVACIÓN Y EMPRENDIMIENTO 1",      "semestre": 3,  "creditos": 5,  "requisitos": ["INTRODUCCIÓN A LA INGENIERÍA"]},

    # SEMESTRE 4
    {"codigo": "S4-01", "nombre": "SISTEMAS Y ECUACIONES DIFERENCIALES LINEALES", "semestre": 4,  "creditos": 7,  "requisitos": ["CÁLCULO INTEGRAL"]},
    {"codigo": "S4-02", "nombre": "ELECTRICIDAD Y MAGNETISMO",                    "semestre": 4,  "creditos": 6,  "requisitos": ["CÁLCULO INTEGRAL", "MÉCANICA"]},
    {"codigo": "S4-03", "nombre": "PRACTICA 1",                                   "semestre": 4,  "creditos": 7,  "requisitos": ["CÁLCULO INTEGRAL", "MÉCANICA", "ALGORITMOS Y ESTRUCTURAS DE DATOS", "COMPLIANCE AND ACCOUNTABILITY", "TALLER DE INNOVACIÓN Y EMPRENDIMIENTO 1"]},
    {"codigo": "S4-04", "nombre": "TALLER DE INNOVACIÓN Y EMPRENDIMIENTO 2",      "semestre": 4,  "creditos": 5,  "requisitos": ["TALLER DE INNOVACIÓN Y EMPRENDIMIENTO 1"]},
    {"codigo": "S4-05", "nombre": "INGLES 1",                                     "semestre": 4,  "creditos": 5,  "requisitos": []},

    # SEMESTRE 5
    {"codigo": "S5-01", "nombre": "MÉTODOS CUANTITATIVOS",                        "semestre": 5,  "creditos": 9,  "requisitos": ["SISTEMAS Y ECUACIONES DIFERENCIALES LINEALES"]},
    {"codigo": "S5-02", "nombre": "FUNDAMENTOS DE COMPUTACIÓN DE ALTO DESEMPEÑO", "semestre": 5,  "creditos": 5,  "requisitos": ["ALGORITMOS Y ESTRUCTURAS DE DATOS"]},
    {"codigo": "S5-03", "nombre": "ANALISIS Y DISEÑOS DE ALGORITMOS",             "semestre": 5,  "creditos": 7,  "requisitos": ["ALGORITMOS Y ESTRUCTURAS DE DATOS"]},
    {"codigo": "S5-04", "nombre": "PARADIGMAS DE PROGRAMACIÓN",                   "semestre": 5,  "creditos": 4,  "requisitos": ["ALGORITMOS Y ESTRUCTURAS DE DATOS"]},
    {"codigo": "S5-05", "nombre": "INGLES 2",                                     "semestre": 5,  "creditos": 5,  "requisitos": ["INGLES 1"]},

    # SEMESTRE 6
    {"codigo": "S6-01", "nombre": "MINERÍA DE DATOS",                             "semestre": 6,  "creditos": 5,  "requisitos": ["MÉTODOS CUANTITATIVOS", "BASE DE DATOS"]},
    {"codigo": "S6-02", "nombre": "DESARROLLO WEB Y MÓVIL",                       "semestre": 6,  "creditos": 6,  "requisitos": ["PARADIGMAS DE PROGRAMACIÓN"]},
    {"codigo": "S6-03", "nombre": "INFRACTUCTURA TI",                             "semestre": 6,  "creditos": 5,  "requisitos": ["PARADIGMAS DE PROGRAMACIÓN"]},
    {"codigo": "S6-04", "nombre": "FUNDAMENTOS DE INTELIGENCIA ARTIFICIAL",       "semestre": 6,  "creditos": 9,  "requisitos": ["ANALISIS Y DISEÑOS DE ALGORITMOS"]},
    {"codigo": "S6-05", "nombre": "INGLES 3",                                     "semestre": 6,  "creditos": 5,  "requisitos": ["INGLES 2"]},

    # SEMESTRE 7
    {"codigo": "S7-01", "nombre": "OPTIMIZACIÓN",                                 "semestre": 7,  "creditos": 6,  "requisitos": ["ANALISIS Y DISEÑOS DE ALGORITMOS"]},
    {"codigo": "S7-02", "nombre": "INGENIERÍA DE SOFTWARE 1",                     "semestre": 7,  "creditos": 7,  "requisitos": ["PARADIGMAS DE PROGRAMACIÓN"]},
    {"codigo": "S7-03", "nombre": "TALLER DE INNOVACIÓN Y EMPRENDIMIENTO 3",      "semestre": 7,  "creditos": 5,  "requisitos": ["TALLER DE INNOVACIÓN Y EMPRENDIMIENTO 2"]},
    {"codigo": "S7-04", "nombre": "APRENDIZAJE DE MAQUINA",                       "semestre": 7,  "creditos": 7,  "requisitos": ["FUNDAMENTOS DE INTELIGENCIA ARTIFICIAL"]},
    {"codigo": "S7-05", "nombre": "INGLES 4",                                     "semestre": 7,  "creditos": 5,  "requisitos": ["INGLES 3"]},

    # SEMESTRE 8
    {"codigo": "S8-01", "nombre": "GESTIÓN DE LA TRANSFORMACIÓN DIGITAL",         "semestre": 8,  "creditos": 5,  "requisitos": ["COMPLIANCE AND ACCOUNTABILITY"]},
    {"codigo": "S8-02", "nombre": "CIBERSEGURIDAD",                               "semestre": 8,  "creditos": 6,  "requisitos": ["INFRACTUCTURA TI"]},
    {"codigo": "S8-03", "nombre": "INGENIERÍA DE SOFTWARE 2",                     "semestre": 8,  "creditos": 7,  "requisitos": ["INGENIERÍA DE SOFTWARE 1", "DESARROLLO WEB Y MÓVIL"]},
    {"codigo": "S8-04", "nombre": "SEMINARIO DE LICENCIATURA EN INGENIERIA",      "semestre": 8,  "creditos": 3,  "requisitos": ["FUNDAMENTOS DE INTELIGENCIA ARTIFICIAL", "INGENIERÍA DE SOFTWARE 1", "MINERÍA DE DATOS", "ELECTRICIDAD Y MAGNETISMO"]},
    {"codigo": "S8-05", "nombre": "TOPICOS DE ESPECIALIDAD 1",                    "semestre": 8,  "creditos": 6,  "requisitos": ["FUNDAMENTOS DE INTELIGENCIA ARTIFICIAL"]},
    {"codigo": "S8-06", "nombre": "RESPONSABILIDAD SOCIAL",                       "semestre": 8,  "creditos": 3,  "requisitos": []},

    # SEMESTRE 9
    {"codigo": "S9-01", "nombre": "PORTAFOLIO DE PROYECTOS",                      "semestre": 9,  "creditos": 7,  "requisitos": ["GESTIÓN DE LA TRANSFORMACIÓN DIGITAL", "INGENIERÍA DE SOFTWARE 2", "SEMINARIO DE LICENCIATURA EN INGENIERIA", "APRENDIZAJE DE MAQUINA"]},
    {"codigo": "S9-02", "nombre": "ADMINISTRACIÓN FINANCIERA DE PROYECTOS I+D+I", "semestre": 9,  "creditos": 5,  "requisitos": ["INGENIERÍA DE SOFTWARE 2"]},
    {"codigo": "S9-03", "nombre": "CIENCIA DE DATOS",                             "semestre": 9,  "creditos": 6,  "requisitos": ["MINERÍA DE DATOS", "FUNDAMENTOS DE INTELIGENCIA ARTIFICIAL"]},
    {"codigo": "S9-04", "nombre": "TOPICOS DE ESPECIALIDAD 2",                    "semestre": 9,  "creditos": 6,  "requisitos": ["FUNDAMENTOS DE INTELIGENCIA ARTIFICIAL"]},
    {"codigo": "S9-05", "nombre": "TOPICOS DE ESPECIALIDAD 3",                    "semestre": 9,  "creditos": 6,  "requisitos": ["FUNDAMENTOS DE INTELIGENCIA ARTIFICIAL"]},

    # SEMESTRE 10
    {"codigo": "S10-01", "nombre": "TALLER DE TRANSFERENCIA TECNOLÓGICA",         "semestre": 10, "creditos": 5,  "requisitos": ["ADMINISTRACIÓN FINANCIERA DE PROYECTOS I+D+I"]},
    {"codigo": "S10-02", "nombre": "PROYECTO DE TÍTULO",                          "semestre": 10, "creditos": 13, "requisitos": ["PORTAFOLIO DE PROYECTOS"]},
    {"codigo": "S10-03", "nombre": "PRACTICA 2",                                  "semestre": 10, "creditos": 12, "requisitos": ["PRACTICA 1", "PORTAFOLIO DE PROYECTOS", "ADMINISTRACIÓN FINANCIERA DE PROYECTOS I+D+I", "CIENCIA DE DATOS", "TOPICOS DE ESPECIALIDAD 2", "TOPICOS DE ESPECIALIDAD 3"]},
]

def obtener_ramos_disponibles(semestre_actual: int, codigos_aprobados: list) -> dict:
    """
    Dado el semestre actual del estudiante y la lista de códigos que ya aprobó,
    clasifica los ramos pendientes en tres grupos:
    - obligatorios: ramos del semestre actual con prerrequisitos cumplidos
    - pendientes:   ramos de semestres anteriores que aún no ha aprobado
    - adelantos:    ramos de semestres futuros cuyos prerrequisitos ya cumplió
    """
# Normalizamos todo a mayúsculas para evitar problemas de tildes o espacios
    aprobados = set(nombre.strip().upper() for nombre in codigos_aprobados)
    obligatorios, pendientes, adelantos = [], [], []

    for ramo in MALLA_ICF:
        # Si ya lo aprobó, no aparece en ninguna lista
        if ramo["nombre"].strip().upper() in aprobados:
            continue

        # Verificar si cumple los prerrequisitos
        requisitos_ok = all(r.strip().upper() in aprobados for r in ramo["requisitos"])

        if not requisitos_ok:
            continue  # no puede tomar este ramo todavía

        if ramo["semestre"] == semestre_actual:
            obligatorios.append({**ramo, "tipo_inscripcion": "OBLIGATORIO"})
        elif ramo["semestre"] < semestre_actual:
            pendientes.append({**ramo, "tipo_inscripcion": "OBLIGATORIO"})
        else:
            adelantos.append({**ramo, "tipo_inscripcion": "ADELANTADO"})

    return {
        "obligatorios": obligatorios,
        "pendientes":   pendientes,
        "adelantos":    adelantos,
    }


# Permite probar este archivo directamente desde la terminal
if __name__ == "__main__":
    # Ejemplo: estudiante de semestre 3 que aprobó todo el semestre 1 y 2
    aprobados = [
        "INTRODUCCIÓN A LAS MATEMÁTICAS", "FÍSICA GENERAL",
        "INTRODUCCIÓN A LA PROGRAMACIÓN", "INTRODUCCIÓN A LA INGENIERÍA",
        "CÁLCULO DIFERENCIAL", "FÍSICA EXPERIMENTAL",
        "BASE DE DATOS", "QUIMICA Y AMBIENTE", "HABILIDADES COMUNICATIVAS",
    ]
    resultado = obtener_ramos_disponibles(3, aprobados)

    print("=== RAMOS DISPONIBLES PARA SEMESTRE 3 ===")
    print("\nObligatorios:")
    for r in resultado["obligatorios"]:
        print(f"  {r['codigo']} — {r['nombre']} ({r['creditos']} créditos)")
    print("\nPendientes de semestres anteriores:")
    for r in resultado["pendientes"]:
        print(f"  {r['codigo']} — {r['nombre']}")
    print("\nPosibles adelantos:")
    for r in resultado["adelantos"]:
        print(f"  {r['codigo']} — {r['nombre']} (sem {r['semestre']})")