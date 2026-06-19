# Optimizador de Horarios — Algoritmo Genético

Herramienta para generar horarios académicos óptimos usando un **algoritmo genético**, minimizando conflictos de profesores, salas y malla curricular.

## ¿Qué hace?

Lee un Excel con cursos y profesores (`datos_varas.xlsx`) y busca una asignación de horarios que:

- ✅ Evite que un profesor tenga dos clases al mismo tiempo
- ✅ Evite que dos clases usen la misma sala simultáneamente
- ✅ Respete la malla curricular (no tope ramos del mismo semestre)
- ✅ Considere la disponibilidad horaria de los profesores
- ✅ Minimice las "horas ventana" (huecos) en el horario de los alumnos

## Archivos necesarios

| Archivo | Descripción |
|---|---|
| `datos_varas.xlsx` | Planilla con NRC, nombre del ramo, profesor, sala, semestre y horario actual |
| `horario_roles_auditado.xlsx` | Horario con roles de inscripción (obligatorio / electivo) |
| `malla_ICF_innovada.xlsx` | Malla curricular de referencia |

> Los archivos Excel **no se incluyen en el repositorio** por contener datos institucionales.

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/TU_USUARIO/algoritmo-horarios.git
cd algoritmo-horarios

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate       # macOS / Linux
.venv\Scripts\activate          # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

El programa imprime el progreso cada 10 generaciones y al final muestra el desglose de penalizaciones del mejor horario encontrado.

## Parámetros configurables

En la sección `1. PARÁMETROS DE CONFIGURACIÓN` de `main.py` puedes ajustar:

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `TAMANO_POBLACION` | 50 | Individuos por generación |
| `GENERACIONES` | 250 | Número máximo de generaciones |
| `TASA_MUTACION_BASE` | 0.50 | Probabilidad de mutar un curso |
| `TAMANO_TORNEO` | 6 | Tamaño del torneo de selección |

## Cómo funciona

```
Población inicial aleatoria
        ↓
  Evaluar fitness (penalizaciones)
        ↓
  Selección por torneo ──────────────────────────────────────┐
        ↓                                                     │
  Cruce de dos padres                                        │
        ↓                                                     │
  Mutación dirigida (repara conflictos duros primero)        │
        ↓                                                     │
  Nueva generación                                           │
        ↓                                                     │
  ¿Mejora? → guardar mejor global                            │
  ¿Estancado 60 gen? → reinicio con élite + diversidad nueva │
        └──────────────────────────────────────────────────── ┘
```

## Tecnologías

- Python 3.14
- [pandas](https://pandas.pydata.org/) — lectura de Excel
- Librería estándar: `random`, `copy`
