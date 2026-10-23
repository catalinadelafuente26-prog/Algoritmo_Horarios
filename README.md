# Planificación Automática de Horarios

Sistema de planificación académica para la Facultad de Ingeniería de la Universidad Andrés Bello, sede Antonio Varas (Ingeniería Civil Informática). Proyecto de tesis.

Genera la programación académica de un semestre con un algoritmo genético, a partir de la malla curricular, los profesores habilitados por ramo y la demanda estimada de estudiantes.

## Funcionalidades

**Secretario académico**

- Generación de la programación desde un Excel o desde la malla curricular.
- Cálculo de la demanda por ramo y del número de secciones según el cupo (cátedra y ayudantía, laboratorio).
- Visualización y edición del horario, carga horaria por profesor y creación manual de secciones.
- Gestión de profesores y de los ramos que están habilitados para dictar.
- Alertas automáticas de sobrecarga de profesores.

**Profesor**

- Consulta de sus clases asignadas y vista semanal.
- Declaración de su disponibilidad horaria.

**Estudiante**

- Situación académica con alerta de atraso, considerando ramos de oferta anual.
- Registro de ramos aprobados y consulta de ramos disponibles.
- Armado de un horario personal sin topes a partir de la programación generada.

**Superusuario**

- Acceso al panel del secretario y vista de cualquier profesor o estudiante.

## Tecnologías

Python, Streamlit, SQLite, pandas, openpyxl. Algoritmo genético implementado en `main.py`.

## Instalación

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Carga inicial de datos

Ejecutar en este orden, una sola vez cada uno:

1. `python importar_profesores.py` crea los profesores desde `datos_varas.xlsx`.
2. `python importar_ramos.py` carga los ramos que puede dictar cada profesor.
3. `python importar_ramos_generales.py` carga los ramos de servicio y generales.
4. `python importar_estudiantes.py` carga los estudiantes y sus ramos aprobados (por defecto desde `alumnos_prueba.xlsx`).
5. `python crear_superusuario.py` crea el usuario `admin`, pidiendo la contraseña por terminal.

El usuario `secretario` se crea automáticamente al iniciar la base de datos. Debe cambiarse su contraseña antes de un uso real.

Los profesores y estudiantes importados ingresan con su RUT como usuario y contraseña inicial.

## Ejecución

```
streamlit run app.py
```

## Estructura del proyecto

| Archivo               | Descripción                                                  |
| --------------------- | ------------------------------------------------------------- |
| `app.py`            | Punto de entrada, inicio de sesión y enrutamiento por perfil |
| `main.py`           | Algoritmo genético: cursos, función de fitness, operadores  |
| `database.py`       | Acceso a datos SQLite                                         |
| `malla.py`          | Malla curricular, ramos disponibles y estimación de atraso   |
| `demanda.py`        | Demanda por ramo y cálculo de secciones                      |
| `horario_alumno.py` | Armado del horario personal del estudiante                    |
| `paneles/`          | Interfaz de cada perfil                                       |
| `importar_*.py`     | Scripts de carga inicial de datos                             |

## Supuestos y limitaciones

- La demanda se estima a partir del semestre y los ramos aprobados de cada estudiante. No considera cadenas de prerrequisitos en la estimación de atraso.
- Los ramos de oferta anual considerados son Química y Ambiente, Práctica 1 y 2, e Ingeniería de Software 1 y 2.
- No se asignan salas físicas: todos los cursos se programan con sala virtual.
- Las secciones de un mismo grupo (sección 1 de cada ramo, sección 2, etc.) no deben tener topes entre sí.
- La disponibilidad de los profesores proviene de lo que declaran en su panel. Si no declaran nada, se asume disponibilidad total.
- Las contraseñas se almacenan con hash SHA-256 sin sal. Es adecuado para un prototipo académico, pero un despliegue real debería usar un algoritmo con sal y costo ajustable, como bcrypt.
