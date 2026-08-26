"""
importar_ramos_generales.py
Crea (si no existen) los profesores de ramos generales (inglés, talleres,
química, etc.) y les asigna los ramos que pueden dictar.
Ejecutar UNA sola vez: python importar_ramos_generales.py
"""
import database as db

# Profesores de esta tabla que YA existen en la BD, pero con el nombre
# escrito distinto (tilde, inicial, etc.) — mapea al nombre EXACTO de la BD.
PROFESORES_YA_EXISTENTES = {
    "JERRY JESUS PENA MORALES":        "JERRY JESUS PEÑA MORALES",
    "CINDY BETZABE CONTADOR CISTERNA": "CINDY B. CONTADOR CISTERNA",
    "EDUARDO DAVID CORREA MARCHANT":   "EDUARDO D. CORREA MARCHANT",
    "EMILIA MONICA AVILES LOPEZ":      "EMILIA M. AVILES LOPEZ",
    "CLAUDIA GWYNN GWYNN":             "CLAUDIA GWYNN MOYA",
    "MAURICIO OLIVER PIZARRO LEYTON":  "MAURICIO O. PIZARRO LEYTON",
}

# Ramo (con el nombre EXACTO de malla.py) → lista de profesores habilitados
HABILITACIONES_GENERALES = {
    "DESARROLLO WEB Y MÓVIL": [
        "CESAR IVAN GUTIERREZ HERNANDEZ", "ERNESTO VIVANCO TAPIA", "JERRY JESUS PENA MORALES",
    ],
    "HABILIDADES COMUNICATIVAS": [
        "PAULA FERNANDA SALINAS GUILLONES", "ROSEL DENISSE CASTILLO RUBILAR",
    ],
    "INFRACTUCTURA TI": [
        "CINDY BETZABE CONTADOR CISTERNA", "CONSTANZA ANTONIA IRARRAZABAL PUELLE",
        "EDUARDO DAVID CORREA MARCHANT", "JOSE ALEJANDRO PEREZ BAHAMONDES",
        "PEDRO PAULO QUIROZ ARAYA", "RODRIGO JOSE ESCOBAR ARAYA",
    ],
    "INGLES 1": [
        "ANA MARIA MUNOZ RAMIREZ", "BLANCA ESTEFANY ARELLANO FUENTES",
        "CESAR BOLIVAR JORGE ANDRES GUZMAN MANRIQUEZ", "CRISTIAN HERNAN BRAVO NAVARRO",
        "MARIA REINA MARABOLI LETELIER", "WALEZKA FONTECILLA APABLAZA",
    ],
    "INGLES 2": [
        "DANIELA ANTONIETA GONZALEZ SALFATE", "IVETTE ADELINNE ROHART NAVARRO",
        "LORENA SOLAR ROSALES", "MACARENA DURAN CASTRO",
        "PAULA LANZAROTTI LANZAROTTI", "WALEZKA FONTECILLA APABLAZA",
    ],
    "INGLES 3": [
        "ALEJANDRA LORETO GARRIDO GONZALEZ", "LORENA SOLAR ROSALES", "LUIS RICARDO CORNEJO MEZA",
    ],
    "INGLES 4": [
        "ALEJANDRA LORETO GARRIDO GONZALEZ", "CRISTIAN HERNAN BRAVO NAVARRO",
        "CRISTIAN LEONARDO ARRIAGADA DIAZ",
    ],
    "QUIMICA Y AMBIENTE": [
        "ADRIANA NATALIA GAUNA SANTANDER", "EMILIA MONICA AVILES LOPEZ", "ESTEBAN ALONSO CAMU MACAYA",
        "ESTELA SOLEDAD PEREZ PALMA", "FRANCISCO JAVIER SALGADO VALDES", "JUAN EUGENIO MERCHAN VELEZ",
        "PATRICIO ANTONIO MUNOZ CONCHA", "RODRIGO NICOLAS BAEZ GREZ", "ROSA MARGARITA HERRERA CISTERNA",
        "SAMIRNA RUIZ MANCHOLA",
    ],
    "RESPONSABILIDAD SOCIAL": [
        "DANIELA VALESKA MACAYA PARADA",
    ],
    "TALLER DE INNOVACIÓN Y EMPRENDIMIENTO 2": [
        "ALVARO REINALDO GONZALEZ HOLGADO", "ANGELICA MARIA ARIZA MENESES", "BERNARDO FELIPE JIL VARGAS",
        "CLAUDIA GWYNN GWYNN", "DANIELA LEPORI SEPULVEDA", "DIEGO NICOLAS ELORZA RIVERA",
        "EDUARDO ARMANDO CORDOVA DIAZ", "MARIA CAROLINA CACERES PENALOZA", "MARIA JOSE RIVERA JOFRE",
        "MARIANA FRAUENBERG VACCARO", "NADIA DEL ROCIO VILLOTA TAPIA", "NICOLE ALEJANDRA CASTRO BALLADARES",
        "NICOLAS FONTAINE SOLAR", "PAULA VITGINIA RODRIGUEZ CAMPOS", "RUBEN VEGA VALENZUELA",
        "SEBASTIAN ANDRES OLAVARRIA MADARIAGA",
    ],
    "TALLER DE TRANSFERENCIA TECNOLÓGICA": [
        "HUGO ALEJANDRO BELTRAN ALEJOS", "MAURICIO OLIVER PIZARRO LEYTON",
    ],
}


def importar():
    db.inicializar_db()
    profesores_bd = db.obtener_profesores()
    indice = {p["nombre"].strip().upper(): p["id"] for p in profesores_bd}

    creados   = 0
    asignados = 0
    rut_temporal = 900000

    for ramo, nombres in HABILITACIONES_GENERALES.items():
        for nombre in nombres:
            nombre_final = PROFESORES_YA_EXISTENTES.get(nombre, nombre)
            prof_id = indice.get(nombre_final.upper())

            if not prof_id:
                rut_temporal += 1
                rut = f"TEMP{rut_temporal}"
                db.registrar_usuario(rut, rut, "profesor", nombre_final)
                usuario = db.login(rut, rut)
                db.crear_profesor(usuario["id"], rut, nombre_final)
                prof_id = db.obtener_profesor_por_rut(rut)["id"]
                indice[nombre_final.upper()] = prof_id
                creados += 1
                print(f"  [CREADO] {nombre_final} (RUT temporal: {rut})")

            db.asignar_asignatura_profesor(prof_id, ramo)
            asignados += 1

    print(f"\nListo. {creados} profesores nuevos creados, {asignados} asignaciones de ramo realizadas.")


if __name__ == "__main__":
    importar()