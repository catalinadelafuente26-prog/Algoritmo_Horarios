"""
database.py
Capa de persistencia del sistema. Aquí se guardan todos los datos:
usuarios, profesores, estudiantes, horarios y disponibilidades.
Usamos SQLite porque es una base de datos que vive en un solo archivo
local — no necesitas instalar nada extra en el servidor.
"""
import sqlite3
import hashlib
import json

# El archivo de base de datos se crea automáticamente la primera vez
DB_PATH = "tesis_planificacion.db"


def get_connection():
    """Abre una conexión a la base de datos y la retorna."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # permite acceder a columnas por nombre
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_db():
    """
    Crea todas las tablas si no existen todavía.
    Se llama una sola vez al iniciar la aplicación.
    """
    with get_connection() as conn:
        conn.executescript("""

        -- Tabla de usuarios: los 3 perfiles del sistema
        CREATE TABLE IF NOT EXISTS usuarios (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            perfil    TEXT NOT NULL CHECK(perfil IN ('secretario','profesor','estudiante')),
            nombre    TEXT NOT NULL,
            creado_en TEXT DEFAULT (datetime('now'))
        );

        -- Tabla de profesores (vinculados a un usuario)
        CREATE TABLE IF NOT EXISTS profesores (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER REFERENCES usuarios(id),
            rut        TEXT UNIQUE NOT NULL,
            nombre     TEXT NOT NULL,
            email      TEXT
        );

        -- Qué asignaturas puede dictar cada profesor
        CREATE TABLE IF NOT EXISTS profesor_asignaturas (
            profesor_id INTEGER REFERENCES profesores(id),
            nombre_asig TEXT NOT NULL,
            PRIMARY KEY (profesor_id, nombre_asig)
        );

        -- Disponibilidad horaria del profesor (un registro por bloque)
        CREATE TABLE IF NOT EXISTS disponibilidad_profesor (
            profesor_id INTEGER REFERENCES profesores(id),
            dia         TEXT NOT NULL,
            bloque      INTEGER NOT NULL,
            disponible  INTEGER DEFAULT 1,
            PRIMARY KEY (profesor_id, dia, bloque)
        );

        -- Estudiantes (vinculados a un usuario)
        CREATE TABLE IF NOT EXISTS estudiantes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id      INTEGER REFERENCES usuarios(id),
            rut             TEXT UNIQUE NOT NULL,
            nombre          TEXT NOT NULL,
            semestre_actual INTEGER DEFAULT 1,
            email           TEXT
        );

        -- Ramos que el estudiante ya aprobó
        CREATE TABLE IF NOT EXISTS ramos_aprobados (
            estudiante_id   INTEGER REFERENCES estudiantes(id),
            codigo_asig     TEXT NOT NULL,
            nombre_asig     TEXT NOT NULL,
            semestre_cursado INTEGER,
            PRIMARY KEY (estudiante_id, codigo_asig)
        );

        -- Horarios generados por el algoritmo genético
        CREATE TABLE IF NOT EXISTS horarios_generados (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL,
            fecha       TEXT DEFAULT (datetime('now')),
            fitness     INTEGER DEFAULT 0,
            creado_por  INTEGER REFERENCES usuarios(id),
            datos_json  TEXT NOT NULL
        );

        -- Horario personal de cada estudiante
        CREATE TABLE IF NOT EXISTS horario_estudiante (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id   INTEGER REFERENCES estudiantes(id),
            horario_base_id INTEGER REFERENCES horarios_generados(id),
            fecha           TEXT DEFAULT (datetime('now')),
            nrcs_json       TEXT NOT NULL
        );

        -- Alertas para el secretario (ej: ramos sin profesor)
        CREATE TABLE IF NOT EXISTS alertas (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo     TEXT NOT NULL,
            mensaje  TEXT NOT NULL,
            resuelta INTEGER DEFAULT 0,
            fecha    TEXT DEFAULT (datetime('now'))
        );
        """)

        # Crear el usuario secretario por defecto si no existe
        existe = conn.execute(
            "SELECT id FROM usuarios WHERE username='secretario'"
        ).fetchone()

        if existe is None:
            pwd = hashlib.sha256("admin123".encode()).hexdigest()
            conn.execute(
                "INSERT INTO usuarios(username, password, perfil, nombre) VALUES (?,?,?,?)",
                ("secretario", pwd, "secretario", "Secretaría Académica")
            )

    print("Base de datos lista.")


# ── Autenticación ──────────────────────────────────────────────────────

def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


def login(username: str, password: str):
    """Retorna el usuario si las credenciales son correctas, o None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE username=? AND password=?",
            (username, hash_password(password))
        ).fetchone()
    return dict(row) if row else None

def obtener_usuario_por_id(usuario_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE id=?", (usuario_id,)
        ).fetchone()
    return dict(row) if row else None

def registrar_usuario(username, password, perfil, nombre):
    """Crea un usuario nuevo. Retorna (True, mensaje) o (False, error)."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO usuarios(username, password, perfil, nombre) VALUES (?,?,?,?)",
                (username, hash_password(password), perfil, nombre)
            )
        return True, "Usuario creado correctamente."
    except sqlite3.IntegrityError:
        return False, "Ese nombre de usuario ya existe."


# ── Profesores ─────────────────────────────────────────────────────────

def crear_profesor(usuario_id, rut, nombre, email=""):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO profesores(usuario_id, rut, nombre, email) VALUES (?,?,?,?)",
            (usuario_id, rut, nombre, email)
        )


def obtener_profesores():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM profesores").fetchall()
    return [dict(r) for r in rows]


def obtener_profesor_por_rut(rut):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM profesores WHERE rut=?", (rut,)
        ).fetchone()
    return dict(row) if row else None


def guardar_disponibilidad(profesor_id, disponibilidad: dict):
    """
    Guarda la disponibilidad horaria de un profesor.
    disponibilidad es un dict con clave (dia, bloque) y valor True/False.
    """
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM disponibilidad_profesor WHERE profesor_id=?", (profesor_id,)
        )
        for (dia, bloque), disponible in disponibilidad.items():
            conn.execute(
                "INSERT INTO disponibilidad_profesor(profesor_id, dia, bloque, disponible) VALUES (?,?,?,?)",
                (profesor_id, dia, bloque, 1 if disponible else 0)
            )


def obtener_disponibilidad(profesor_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT dia, bloque, disponible FROM disponibilidad_profesor WHERE profesor_id=?",
            (profesor_id,)
        ).fetchall()
    return {(r["dia"], r["bloque"]): bool(r["disponible"]) for r in rows}


# ── Estudiantes ────────────────────────────────────────────────────────

def crear_estudiante(usuario_id, rut, nombre, semestre_actual=1, email=""):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO estudiantes(usuario_id, rut, nombre, semestre_actual, email) VALUES (?,?,?,?,?)",
            (usuario_id, rut, nombre, semestre_actual, email)
        )


def obtener_estudiante_por_usuario(usuario_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM estudiantes WHERE usuario_id=?", (usuario_id,)
        ).fetchone()
    return dict(row) if row else None


def registrar_ramo_aprobado(estudiante_id, codigo, nombre, semestre_cursado):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO ramos_aprobados(estudiante_id, codigo_asig, nombre_asig, semestre_cursado) VALUES (?,?,?,?)",
            (estudiante_id, codigo, nombre, semestre_cursado)
        )


def eliminar_ramo_aprobado(estudiante_id, codigo):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM ramos_aprobados WHERE estudiante_id=? AND codigo_asig=?",
            (estudiante_id, codigo)
        )


def obtener_ramos_aprobados(estudiante_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM ramos_aprobados WHERE estudiante_id=?", (estudiante_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Horarios ───────────────────────────────────────────────────────────

def guardar_horario(nombre, fitness, creado_por, datos: list):
    """Guarda un horario generado por el GA. Retorna el ID asignado."""
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO horarios_generados(nombre, fitness, creado_por, datos_json) VALUES (?,?,?,?)",
            (nombre, fitness, creado_por, json.dumps(datos, ensure_ascii=False))
        )
        return cur.lastrowid


def obtener_horarios():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, nombre, fecha, fitness FROM horarios_generados ORDER BY fecha DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def obtener_horario_por_id(horario_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM horarios_generados WHERE id=?", (horario_id,)
        ).fetchone()
    if row:
        d = dict(row)
        d["datos"] = json.loads(d["datos_json"])
        return d
    return None


def actualizar_nrc_horario(horario_id, nrc, nuevo_horario_texto):
    """Permite editar manualmente el horario de un NRC específico."""
    horario = obtener_horario_por_id(horario_id)
    if not horario:
        return False
    datos = horario["datos"]
    for curso in datos:
        if curso["NRC"] == nrc:
            curso["Horario Final"] = nuevo_horario_texto
            break
    with get_connection() as conn:
        conn.execute(
            "UPDATE horarios_generados SET datos_json=? WHERE id=?",
            (json.dumps(datos, ensure_ascii=False), horario_id)
        )
    return True

def agregar_curso_horario(horario_id, curso: dict):
    """Agrega una sección/NRC nueva a un horario ya guardado."""
    horario = obtener_horario_por_id(horario_id)
    if not horario:
        return False
    datos = horario["datos"]
    datos.append(curso)
    with get_connection() as conn:
        conn.execute(
            "UPDATE horarios_generados SET datos_json=? WHERE id=?",
            (json.dumps(datos, ensure_ascii=False), horario_id)
        )
    return True

# ── Alertas ────────────────────────────────────────────────────────────

def crear_alerta(tipo, mensaje):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO alertas(tipo, mensaje) VALUES (?,?)", (tipo, mensaje)
        )


def obtener_alertas(solo_pendientes=True):
    with get_connection() as conn:
        q = "SELECT * FROM alertas"
        if solo_pendientes:
            q += " WHERE resuelta=0"
        q += " ORDER BY fecha DESC"
        rows = conn.execute(q).fetchall()
    return [dict(r) for r in rows]


def resolver_alerta(alerta_id):
    with get_connection() as conn:
        conn.execute(
            "UPDATE alertas SET resuelta=1 WHERE id=?", (alerta_id,)
        )

def asignar_asignatura_profesor(profesor_id, nombre_asig):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO profesor_asignaturas(profesor_id, nombre_asig) VALUES (?,?)",
            (profesor_id, nombre_asig)
        )

def obtener_asignaturas_profesor(profesor_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT nombre_asig FROM profesor_asignaturas WHERE profesor_id=?",
            (profesor_id,)
        ).fetchall()
    return [r["nombre_asig"] for r in rows]

def quitar_asignatura_profesor(profesor_id, nombre_asig):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM profesor_asignaturas WHERE profesor_id=? AND nombre_asig=?",
            (profesor_id, nombre_asig)
        )


def actualizar_profesor(profesor_id, rut, nombre, email=""):
    with get_connection() as conn:
        conn.execute(
            "UPDATE profesores SET rut=?, nombre=?, email=? WHERE id=?",
            (rut, nombre, email, profesor_id)
        )


def eliminar_profesor(profesor_id):
    """Elimina al profesor y todo lo que dependa de él (ramos, disponibilidad)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM profesor_asignaturas WHERE profesor_id=?", (profesor_id,))
        conn.execute("DELETE FROM disponibilidad_profesor WHERE profesor_id=?", (profesor_id,))
        conn.execute("DELETE FROM profesores WHERE id=?", (profesor_id,))

# Esto permite probar el archivo directamente desde la terminal
if __name__ == "__main__":
    inicializar_db()