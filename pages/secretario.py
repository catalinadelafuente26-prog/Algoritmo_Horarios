"""
pages/secretario.py
Panel del Secretario Académico.
Funciones: generar horario, ver y editar, gestionar profesores, alertas.
iniciar con streamlit run app.py 
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import database as db

def render():
    st.title("🗂️ Panel del Secretario Académico")

    tabs = st.tabs([
        "📅 Generar Horario",
        "🔍 Ver y Editar Horario",
        "👨‍🏫 Gestionar Profesores",
        "🔔 Alertas",
    ])

    with tabs[0]:
        _tab_generar()
    with tabs[1]:
        _tab_ver_editar()
    with tabs[2]:
        _tab_profesores()
    with tabs[3]:
        _tab_alertas()


# ── Tab 1: Generar Horario ─────────────────────────────────────────────
def _tab_generar():
    st.subheader("Generar nueva programación académica")
    st.caption("El algoritmo genético leerá el archivo Excel y optimizará el horario.")

    ruta_excel = st.text_input(
        "Nombre del archivo Excel de cursos",
        value="datos_varas.xlsx",
        help="El archivo debe estar en la misma carpeta que app.py"
    )

    col1, col2 = st.columns(2)
    with col1:
        generaciones = st.slider("Generaciones del algoritmo", 100, 1000, 350, 50)
    with col2:
        poblacion = st.slider("Tamaño de población", 20, 100, 80, 10)

    nombre_horario = st.text_input("Nombre para identificar este horario", value="Semestre 2026-20")

    modo = st.radio(
        "¿Qué datos usar para generar el horario?",
        ["📄 Desde Excel existente", "📚 Desde Malla Curricular (generar desde cero)"],
        horizontal=True
    )

    if st.button("🚀 Ejecutar Optimizador", type="primary"):
        # Verificar que el archivo existe
        if not os.path.exists(ruta_excel):
            st.error(f"No se encontró el archivo '{ruta_excel}'. Verifica que esté en la carpeta del proyecto.")
            return

        # Importar el motor GA
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "algoritmo",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "algoritmo_horarios.py")
        )

        import main as ga
        ga.cursos_reales.clear()
        ga.profesores_reales.clear()

        if modo == "📄 Desde Excel existente":
            # Modo original — leer desde el Excel
            with st.spinner("Cargando datos desde Excel..."):
                ga.cargar_datos_desde_excel(ruta_excel)

            if not ga.cursos_reales:
                st.error("No se pudieron cargar cursos. Revisa el archivo Excel.")
                return
            st.success(f"✓ {len(ga.cursos_reales)} cursos cargados desde Excel.")

        else:
            # Modo malla — generar cursos desde malla.py con profesores de la BD
            with st.spinner("Generando cursos desde la malla curricular..."):
                from malla import MALLA_ICF

                profesores_bd = db.obtener_profesores()
                if not profesores_bd:
                    st.error("No hay profesores en la base de datos. Importa los profesores primero.")
                    return

                nrc_base = 90000
                nrc_contador = nrc_base
                cursos_generados = 0
                ramos_sin_profesor = []

                # Construir índice: nombre_asig → lista de profesores habilitados
                indice_habilitados = {}
                for prof in profesores_bd:
                    asigs = db.obtener_asignaturas_profesor(prof["id"])
                    for asig in asigs:
                        clave = asig.strip().upper()
                        if clave not in indice_habilitados:
                            indice_habilitados[clave] = []
                        indice_habilitados[clave].append(prof)

                def horas_a_bloques(horas):
                    if horas <= 0:
                        return 0
                    import math
                    return max(2, math.ceil(horas / 0.75))

                def calcular_chunks_componente(horas, tipo):
                    total = horas_a_bloques(horas)
                    if total == 0:
                        return []
                    if tipo in ("ayudantia", "lab"):
                        return [total]
                    else:
                        if total <= 2:
                            return [total]
                        else:
                            n_dias = total // 2
                            chunks = [2] * n_dias
                            if total % 2 != 0:
                                chunks[-1] += 1
                            return chunks

                # Rotación por ramo para distribuir carga entre habilitados
                rotacion_por_ramo = {}

                for ramo in MALLA_ICF:
                    nombre_ramo = ramo["nombre"].strip().upper()

                    # Buscar profesores habilitados para este ramo
                    habilitados = indice_habilitados.get(nombre_ramo, [])

                    if not habilitados:
                        ramos_sin_profesor.append(ramo["nombre"])
                        # Fallback: usar cualquier profesor disponible
                        habilitados = profesores_bd

                    # Inicializar rotación para este ramo
                    if nombre_ramo not in rotacion_por_ramo:
                        import itertools
                        rotacion_por_ramo[nombre_ramo] = itertools.cycle(habilitados)

                    componentes = [
                        ("catedral",  ramo["horas_catedral"],  f"{ramo['nombre']} (Cátedra)"),
                        ("ayudantia", ramo["horas_ayudantia"], f"{ramo['nombre']} (Ayudantía)"),
                        ("lab",       ramo["horas_lab"],       f"{ramo['nombre']} (Lab)"),
                    ]

                    for tipo, horas, nombre_comp in componentes:
                        if horas <= 0:
                            continue

                        chunks = calcular_chunks_componente(horas, tipo)
                        total_bloques = sum(chunks)

                        # Asignar el siguiente profesor habilitado en rotación
                        profe = next(rotacion_por_ramo[nombre_ramo])
                        rut   = str(profe["rut"]).strip()
                        nom   = str(profe["nombre"]).strip()

                        curso = ga.Curso(
                            nrc_contador,
                            nombre_comp,
                            rut,
                            nom,
                            f"VIRTUAL_{nrc_contador}",
                            ramo["semestre"],
                            "OBLIGATORIO",
                            []
                        )
                        curso.duracion_requerida = total_bloques
                        curso.un_solo_dia = (tipo in ("lab", "ayudantia"))

                        if rut not in ga.profesores_reales:
                            ga.profesores_reales[rut] = ga.Profesor(rut, nom)

                        ga.cursos_reales[nrc_contador] = curso
                        nrc_contador += 1
                        cursos_generados += 1

            if ramos_sin_profesor:
                st.warning(f"⚠️ {len(ramos_sin_profesor)} ramo(s) sin profesor habilitado (se usó fallback): {', '.join(ramos_sin_profesor)}")

            st.success(f"✓ {cursos_generados} componentes generados desde la malla curricular con profesores habilitados.")

            st.success(f"✓ {cursos_generados} componentes generados desde la malla curricular.")

        # Barra de progreso
        progress = st.progress(0)
        log_area  = st.empty()
        logs      = []
        resultados = {"mejor_fit": None, "datos": None}

        # Ejecutar el GA con los parámetros elegidos
        ga.GENERACIONES     = generaciones
        ga.TAMANO_POBLACION = poblacion

        import copy, random
        poblacion_ga = []
        for _ in range(ga.TAMANO_POBLACION):
            ind = ga.crear_individuo()
            fit, _, _ = ga.obtener_conflictos_y_fitness(ind)
            poblacion_ga.append((fit, ind))

        poblacion_ga.sort(key=lambda x: x[0])
        mejor_fit   = poblacion_ga[0][0]
        mejor_ind   = copy.deepcopy(poblacion_ga[0][1])
        estanc      = 0
        prob_mut    = ga.TASA_MUTACION_BASE
        reinicios   = 0

        for gen in range(1, ga.GENERACIONES + 1):
            nueva_pob = [poblacion_ga[0], poblacion_ga[1]]
            while len(nueva_pob) < ga.TAMANO_POBLACION:
                p1   = ga.seleccionar_padre_torneo(poblacion_ga)
                p2   = ga.seleccionar_padre_torneo(poblacion_ga)
                hijo = ga.cruzar_horarios(p1, p2)
                _, malos, _ = ga.obtener_conflictos_y_fitness(hijo)
                if estanc >= 20:
                    hijo = ga.swap_par_a_par(hijo, malos)
                    _, malos, _ = ga.obtener_conflictos_y_fitness(hijo)
                    hijo = ga.mutacion_inteligente_dirigida(hijo, malos, 0.85)
                else:
                    hijo = ga.mutacion_inteligente_dirigida(hijo, malos, prob_mut)
                fit_h, _, _ = ga.obtener_conflictos_y_fitness(hijo)
                nueva_pob.append((fit_h, hijo))

            poblacion_ga = sorted(nueva_pob, key=lambda x: x[0])

            if poblacion_ga[0][0] < mejor_fit:
                mejor_fit = poblacion_ga[0][0]
                mejor_ind = copy.deepcopy(poblacion_ga[0][1])
                estanc    = 0
                prob_mut  = ga.TASA_MUTACION_BASE
            else:
                estanc += 1

            if estanc >= 60 and mejor_fit > 0:
                reinicios += 1
                elite     = poblacion_ga[:5]
                nueva_div = []
                for _ in range(ga.TAMANO_POBLACION - 5):
                    ind_n = ga.crear_individuo()
                    fit_n, _, _ = ga.obtener_conflictos_y_fitness(ind_n)
                    nueva_div.append((fit_n, ind_n))
                poblacion_ga = sorted(elite + nueva_div, key=lambda x: x[0])
                estanc   = 0
                prob_mut = ga.TASA_MUTACION_BASE

            if gen % 10 == 0:
                pct = int(gen / ga.GENERACIONES * 100)
                progress.progress(pct)
                logs.append(f"Gen {gen:03d} | Fitness: {mejor_fit} | Estanc: {estanc} | Reinic: {reinicios}")
                log_area.text_area("Log del algoritmo", "\n".join(logs[-10:]), height=180)

            if mejor_fit == 0:
                break

        progress.progress(100)

        # Preparar datos para guardar
        datos_salida = []
        for nrc, curso in mejor_ind.items():
            sala_final = "" if "VIRTUAL" in curso.sala else curso.sala
            datos_salida.append({
                "NRC":           curso.nrc,
                "Asignatura":    curso.nombre,
                "Profesor":      curso.nombre_profesor,
                "RUT_Profesor":  curso.rut_profesor,
                "Sala":          sala_final,
                "Semestre":      curso.semestre,
                "Prioridad":     curso.tipo_inscripcion,
                "Horario Final": ga.traducir_enteros_a_texto(curso.bloques_enteros),
            })

        horario_id = db.guardar_horario(
            nombre_horario,
            mejor_fit,
            st.session_state["usuario"]["id"],
            datos_salida
        )

        if mejor_fit == 0:
            st.success(f"✅ Horario generado sin conflictos. Guardado como '{nombre_horario}'.")
        else:
            st.warning(f"⚠️ Fitness final: {mejor_fit}. Se guardó el mejor resultado encontrado.")

        st.session_state["horario_activo_id"] = horario_id


# ── Tab 2: Ver y Editar Horario ────────────────────────────────────────
def _tab_ver_editar():
    st.subheader("Ver y editar horario guardado")

    horarios = db.obtener_horarios()
    if not horarios:
        st.info("Aún no hay horarios generados.")
        return

    opciones = {
        f"[{h['id']}] {h['nombre']} — {h['fecha'][:10]} (fitness {h['fitness']})": h["id"]
        for h in horarios
    }
    seleccion  = st.selectbox("Seleccionar horario", list(opciones.keys()))
    horario_id = opciones[seleccion]
    horario    = db.obtener_horario_por_id(horario_id)
    datos      = horario["datos"]
    df         = pd.DataFrame(datos)

    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        sems = sorted(df["Semestre"].unique().tolist())
        sem_filtro = st.multiselect("Filtrar por semestre", sems, default=sems)
    with col2:
        buscar = st.text_input("Buscar asignatura o profesor")

    df_filtro = df[df["Semestre"].isin(sem_filtro)] if sem_filtro else df
    if buscar:
        mask = (
            df_filtro["Asignatura"].str.contains(buscar, case=False, na=False) |
            df_filtro["Profesor"].str.contains(buscar, case=False, na=False)
        )
        df_filtro = df_filtro[mask]

    st.dataframe(df_filtro, use_container_width=True, height=400)
    st.caption(f"Mostrando {len(df_filtro)} de {len(df)} cursos.")

    if st.button("📥 Exportar a Excel"):
        nombre_archivo = f"horario_{horario_id}.xlsx"
        df.to_excel(nombre_archivo, index=False)
        st.success(f"Exportado como '{nombre_archivo}'")

    # Edición manual de un NRC
    st.divider()
    st.subheader("✏️ Modificar horario de un NRC")
    nrc_edit      = st.number_input("NRC a modificar", min_value=0, step=1)
    nuevo_horario = st.text_input("Nuevo horario (ej: .LU 0830 - 1010 y .JU 0830 - 1010)")

    if nrc_edit:
        curso_actual = next((c for c in datos if c["NRC"] == nrc_edit), None)
        if curso_actual:
            st.info(f"**{curso_actual['Asignatura']}** | Horario actual: `{curso_actual['Horario Final']}`")
        else:
            st.warning("NRC no encontrado en este horario.")

    if st.button("💾 Guardar modificación"):
        if nrc_edit and nuevo_horario:
            ok = db.actualizar_nrc_horario(horario_id, nrc_edit, nuevo_horario)
            if ok:
                st.success(f"NRC {nrc_edit} actualizado.")
                st.rerun()
            else:
                st.error("No se pudo actualizar.")
        else:
            st.warning("Completa el NRC y el nuevo horario.")


# ── Tab 3: Gestionar Profesores ────────────────────────────────────────
def _tab_profesores():
    st.subheader("Gestión de profesores")

    profesores = db.obtener_profesores()

    col1, col2 = st.columns([2, 1])
    with col1:
        if profesores:
            df_prof = pd.DataFrame(profesores)[["rut", "nombre", "email"]]
            st.dataframe(df_prof, use_container_width=True)
        else:
            st.info("No hay profesores registrados aún.")

    with col2:
        st.markdown("**Agregar profesor manualmente**")
        rut_n   = st.text_input("RUT", key="prof_rut")
        nom_n   = st.text_input("Nombre", key="prof_nom")
        email_n = st.text_input("Email (opcional)", key="prof_email")

        if st.button("➕ Agregar"):
            if rut_n and nom_n:
                ok, _ = db.registrar_usuario(rut_n, rut_n, "profesor", nom_n)
                usuario_prof = db.login(rut_n, rut_n)
                uid = usuario_prof["id"] if usuario_prof else None
                db.crear_profesor(uid, rut_n, nom_n, email_n)
                st.success(f"Profesor '{nom_n}' agregado. Usuario: `{rut_n}`, Contraseña: `{rut_n}`")
            else:
                st.warning("Completa RUT y nombre.")

    # Detectar ramos sin profesor
    st.divider()
    if st.button("🔍 Detectar ramos sin profesor en el último horario"):
        horarios = db.obtener_horarios()
        if not horarios:
            st.warning("Primero genera un horario.")
            return
        ultimo  = db.obtener_horario_por_id(horarios[0]["id"])
        sin_rut = [
            c for c in ultimo["datos"]
            if not c.get("RUT_Profesor") or c.get("RUT_Profesor") == "nan"
        ]
        if sin_rut:
            st.warning(f"{len(sin_rut)} cursos sin profesor asignado:")
            for c in sin_rut:
                st.write(f"  • NRC {c['NRC']} — {c['Asignatura']}")
                db.crear_alerta("sin_profesor", f"NRC {c['NRC']} '{c['Asignatura']}' sin profesor.")
        else:
            st.success("Todos los cursos tienen profesor asignado.")


# ── Tab 4: Alertas ─────────────────────────────────────────────────────
def _tab_alertas():
    st.subheader("Centro de alertas")

    alertas = db.obtener_alertas(solo_pendientes=True)

    if not alertas:
        st.success("✅ No hay alertas pendientes.")
        return

    st.warning(f"{len(alertas)} alerta(s) pendiente(s)")

    for alerta in alertas:
        col1, col2 = st.columns([5, 1])
        with col1:
            icono = {"sin_profesor": "🔴"}.get(alerta["tipo"], "⚠️")
            st.write(f"{icono} {alerta['mensaje']}")
            st.caption(f"Generada: {alerta['fecha'][:16]}")
        with col2:
            if st.button("✓ Resolver", key=f"alerta_{alerta['id']}"):
                db.resolver_alerta(alerta["id"])
                st.rerun()
        st.divider()