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

def calcular_horas_por_profesor(datos):
    """Suma las horas semanales totales asignadas a cada profesor, leyendo el texto de 'Horario Final'."""
    horas_por_profesor = {}
    for curso in datos:
        profesor = curso.get("Profesor", "Sin asignar")
        txt = curso.get("Horario Final", "")
        if not txt or txt == "SIN HORARIO":
            continue
        minutos_totales = 0
        for parte in txt.split(" y "):
            parte  = parte.strip().lstrip(".")
            tokens = parte.split()
            if len(tokens) < 3:
                continue
            try:
                ini = tokens[1].replace(":", "")
                fin = tokens[-1].replace(":", "")
                mi  = int(ini[:2]) * 60 + int(ini[2:])
                mf  = int(fin[:2]) * 60 + int(fin[2:])
                minutos_totales += (mf - mi)
            except Exception:
                pass
        horas_por_profesor[profesor] = horas_por_profesor.get(profesor, 0) + minutos_totales / 60
    return horas_por_profesor

def renderizar_tabla_profesores(profesores_filtrados):
    filas_html = ""
    for p in profesores_filtrados:
        if p["ramos_lista"]:
            ramos_html = "".join(f"<span class='ramo-badge'>{r}</span>" for r in p["ramos_lista"])
        else:
            ramos_html = "<span style='color:#999;'>— sin ramos —</span>"
        email = p.get("email") or "—"
        filas_html += f"<tr><td>{p['rut']}</td><td>{p['nombre']}</td><td>{email}</td><td>{ramos_html}</td></tr>"

    tabla_html = (
        "<table class='tabla-profesores'>"
        "<thead><tr><th>RUT</th><th>Nombre</th><th>Email</th><th>Ramos</th></tr></thead>"
        f"<tbody>{filas_html}</tbody>"
        "</table>"
    )
    st.markdown(f"<div class='tabla-profesores-contenedor'>{tabla_html}</div>", unsafe_allow_html=True)

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

    # ── Carga horaria por profesor ───────────────────────────────────
    st.divider()
    st.subheader("⚖️ Carga horaria por profesor")

    horas_max = st.slider("Horas semanales máximas recomendadas", 5, 40, 20)

    horas_prof = calcular_horas_por_profesor(datos)
    df_horas = pd.DataFrame([
        {"Profesor": p, "Horas semanales": round(h, 1), "Sobrecargado": "⚠️" if h > horas_max else ""}
        for p, h in sorted(horas_prof.items(), key=lambda x: x[1], reverse=True)
    ])

    st.dataframe(df_horas, use_container_width=True, height=300)

    sobrecargados = [p for p, h in horas_prof.items() if h > horas_max]
    if sobrecargados:
        st.warning(f"⚠️ {len(sobrecargados)} profesor(es) superan las {horas_max}h semanales: {', '.join(sobrecargados)}")
    else:
        st.success(f"✅ Ningún profesor supera las {horas_max}h semanales.")

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

    # ── Crear una nueva sección/paralelo manualmente ─────────────────
    st.divider()
    st.subheader("➕ Agregar nueva sección/paralelo")
    st.caption("Crea un NRC nuevo a mano — útil para un paralelo extra que el algoritmo no generó.")

    profesores_bd = db.obtener_profesores()
    opciones_prof = {f"{p['rut']} — {p['nombre']}": p for p in profesores_bd}

    with st.form("form_nueva_seccion"):
        nuevo_nrc = st.number_input(
            "NRC (debe ser único en este horario)",
            min_value=1, step=1,
            value=max([c["NRC"] for c in datos], default=90000) + 1
        )
        nueva_asig = st.text_input("Nombre de la asignatura")
        sel_prof = st.selectbox("Profesor", list(opciones_prof.keys())) if opciones_prof else None
        nueva_sala = st.text_input("Sala (deja vacío si es virtual)")
        nuevo_sem = st.number_input("Semestre", min_value=1, max_value=10, step=1)
        nueva_prioridad = st.selectbox("Prioridad", ["OBLIGATORIO", "ADELANTADO"])
        nuevo_horario_txt = st.text_input(
            "Horario (ej: .LU 0830 - 1010 y .JU 0830 - 1010)", value="SIN HORARIO"
        )
        crear_seccion = st.form_submit_button("➕ Crear sección", type="primary")

    if crear_seccion:
        if not nueva_asig or not sel_prof:
            st.warning("Completa al menos la asignatura y el profesor.")
        elif any(c["NRC"] == nuevo_nrc for c in datos):
            st.error(f"El NRC {nuevo_nrc} ya existe en este horario. Usa otro número.")
        else:
            profe = opciones_prof[sel_prof]
            curso_nuevo = {
                "NRC": nuevo_nrc,
                "Asignatura": nueva_asig,
                "Profesor": profe["nombre"],
                "RUT_Profesor": profe["rut"],
                "Sala": nueva_sala,
                "Semestre": nuevo_sem,
                "Prioridad": nueva_prioridad,
                "Horario Final": nuevo_horario_txt,
            }
            ok = db.agregar_curso_horario(horario_id, curso_nuevo)
            if ok:
                st.success(f"Sección NRC {nuevo_nrc} — {nueva_asig} agregada.")
                st.rerun()
            else:
                st.error("No se pudo agregar la sección.")

# ── Tab 3: Gestionar Profesores ────────────────────────────────────────
def _tab_profesores():
    st.subheader("Gestión de profesores")

    profesores = db.obtener_profesores()

    col1, col2 = st.columns([2, 1])
    with col1:
        if profesores:
            for p in profesores:
                p["ramos_lista"] = db.obtener_asignaturas_profesor(p["id"])
                p["ramos"] = ", ".join(p["ramos_lista"]) if p["ramos_lista"] else "— sin ramos asignados —"

            todos_los_ramos = sorted({r for p in profesores for r in p["ramos_lista"]})

            colf1, colf2, colf3 = st.columns(3)
            with colf1:
                buscar_prof = st.text_input("🔍 Buscar por nombre o RUT", key="buscar_profesor")
            with colf2:
                ramo_filtro = st.selectbox("Filtrar por ramo", ["Todos"] + todos_los_ramos, key="filtro_ramo")
            with colf3:
                solo_sin_ramos = st.checkbox("Solo sin ramos asignados", key="filtro_sin_ramos")

            profesores_filtrados = profesores
            if buscar_prof:
                bp = buscar_prof.lower()
                profesores_filtrados = [
                    p for p in profesores_filtrados
                    if bp in p["nombre"].lower() or bp in p["rut"].lower()
                ]
            if ramo_filtro != "Todos":
                profesores_filtrados = [p for p in profesores_filtrados if ramo_filtro in p["ramos_lista"]]
            if solo_sin_ramos:
                profesores_filtrados = [p for p in profesores_filtrados if not p["ramos_lista"]]

            if profesores_filtrados:
                renderizar_tabla_profesores(profesores_filtrados)
            else:
                st.info("No hay profesores que coincidan con el filtro.")

            st.caption(f"Mostrando {len(profesores_filtrados)} de {len(profesores)} profesores.")
        else:
            st.info("No hay profesores registrados aún.")

    # ── Editar, eliminar y asignar ramos a un profesor ──────────────────
    st.divider()
    st.subheader("✏️ Editar, eliminar o asignar ramos a un profesor")

    if profesores:
        opciones_editar = {f"{p['rut']} — {p['nombre']}": p["id"] for p in profesores}
        seleccion_editar = st.selectbox(
            "Selecciona un profesor", list(opciones_editar.keys()), key="sel_editar_profesor"
        )
        prof_id_editar = opciones_editar[seleccion_editar]
        prof_actual = next(p for p in profesores if p["id"] == prof_id_editar)

        from malla import MALLA_ICF
        ramos_malla    = sorted({r["nombre"] for r in MALLA_ICF})
        ramos_actuales = db.obtener_asignaturas_profesor(prof_id_editar)
        opciones_ramos = sorted(set(ramos_malla) | set(ramos_actuales))

        with st.form(f"form_editar_{prof_id_editar}"):
            rut_e   = st.text_input("RUT", value=prof_actual["rut"])
            nom_e   = st.text_input("Nombre", value=prof_actual["nombre"])
            email_e = st.text_input("Email", value=prof_actual.get("email") or "")
            ramos_e = st.multiselect("Ramos que puede dictar", opciones_ramos, default=ramos_actuales)

            col_g, col_e = st.columns(2)
            with col_g:
                guardar = st.form_submit_button("💾 Guardar cambios", type="primary")
            with col_e:
                eliminar = st.form_submit_button("🗑️ Eliminar profesor")

        if guardar:
            db.actualizar_profesor(prof_id_editar, rut_e, nom_e, email_e)

            ramos_quitar  = set(ramos_actuales) - set(ramos_e)
            ramos_agregar = set(ramos_e) - set(ramos_actuales)
            for r in ramos_quitar:
                db.quitar_asignatura_profesor(prof_id_editar, r)
            for r in ramos_agregar:
                db.asignar_asignatura_profesor(prof_id_editar, r)

            st.success(f"Profesor '{nom_e}' actualizado.")
            st.rerun()

        if eliminar:
            st.session_state["confirmar_eliminar_profesor"] = prof_id_editar

        if st.session_state.get("confirmar_eliminar_profesor") == prof_id_editar:
            st.warning(f"¿Seguro que quieres eliminar a **{prof_actual['nombre']}**? Esta acción no se puede deshacer.")
            col_si, col_no = st.columns(2)
            with col_si:
                if st.button("Sí, eliminar", key=f"confirmar_si_{prof_id_editar}"):
                    db.eliminar_profesor(prof_id_editar)
                    del st.session_state["confirmar_eliminar_profesor"]
                    st.success("Profesor eliminado.")
                    st.rerun()
            with col_no:
                if st.button("Cancelar", key=f"confirmar_no_{prof_id_editar}"):
                    del st.session_state["confirmar_eliminar_profesor"]
                    st.rerun()

        # Disponibilidad horaria declarada (solo lectura — la declara el propio profesor)
        with st.expander("🗓️ Ver disponibilidad horaria declarada"):
            disp = db.obtener_disponibilidad(prof_id_editar)
            if not disp:
                st.info("Este profesor aún no ha declarado su disponibilidad.")
            else:
                DIAS_D = ["LU", "MA", "MI", "JU", "VI", "SA"]
                NOMBRE_DIA = {"LU": "Lunes", "MA": "Martes", "MI": "Miércoles",
                              "JU": "Jueves", "VI": "Viernes", "SA": "Sábado"}
                HORAS_D = [
                    "08:30", "09:25", "10:20", "11:15", "12:10", "13:05",
                    "14:00", "14:55", "15:50", "16:45", "17:40", "18:35",
                    "19:30", "20:25"
                ]
                filas = []
                for i, hora in enumerate(HORAS_D):
                    fila = {"Hora": hora}
                    for dia in DIAS_D:
                        fila[NOMBRE_DIA[dia]] = "✅" if disp.get((dia, i + 1), True) else "—"
                    filas.append(fila)
                df_disp = pd.DataFrame(filas).set_index("Hora")
                st.dataframe(df_disp, use_container_width=True)
                bloques_disp = sum(1 for v in disp.values() if v)
                st.caption(f"{bloques_disp} de {len(disp)} bloques declarados como disponibles.")


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