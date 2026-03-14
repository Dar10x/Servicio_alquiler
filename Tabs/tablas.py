import streamlit as st
import Tabs.DB_function as db
import auth

try:
    fragment = st.fragment
except AttributeError:
    try:
        fragment = st.experimental_fragment
    except AttributeError:
        def fragment(func):
            return func

@fragment
def mostrar_tabla_inventario():
    st.subheader("Inventario de Disfraces")
    
    # Inicializar estados de sesión para filtros
    if 'filtro_nombre' not in st.session_state:
        st.session_state.filtro_nombre = ""
    
    if 'filtro_categoria' not in st.session_state:
        st.session_state.filtro_categoria = "Todas"
    
    if 'filtros_aplicados' not in st.session_state:
        st.session_state.filtros_aplicados = False
    
    # Obtener datos del inventario
    df_inventario = db.get_inventraio_disponibilidad()
    
    if df_inventario.empty:
        st.info("No hay disfraces en el inventario")
        return
    
    # ============================================
    # SECCIÓN DE FILTROS
    # ============================================
    with st.container():
        st.markdown("**🔍 Filtros de Búsqueda**")
        
        col_filtro1, col_filtro2, col_btn1, col_btn2 = st.columns([3, 2, 1.5, 1.5])
        
        with col_filtro1:
            # Buscador por nombre
            nombre_busqueda = st.text_input(
                "Buscar por nombre",
                value=st.session_state.filtro_nombre,
                placeholder="Ej: Spiderman, Princesa, Vampiro...",
                label_visibility="collapsed",
                key="input_buscar_nombre"
            )
        
        with col_filtro2:
            # Obtener categorías únicas del DataFrame
            categorias_disponibles = ['Todas'] + sorted(df_inventario['categoria'].dropna().unique().tolist())
            
            categoria_seleccionada = st.selectbox(
                "Categoría",
                options=categorias_disponibles,
                index=categorias_disponibles.index(st.session_state.filtro_categoria) if st.session_state.filtro_categoria in categorias_disponibles else 0,
                label_visibility="collapsed",
                key="select_categoria"
            )
        
        with col_btn1:
            aplicar_filtros = st.button(
                "🔍 Aplicar Filtros",
                use_container_width=True,
                type="primary"
            )
        
        with col_btn2:
            limpiar_filtros = st.button(
                "🗑️ Limpiar Filtros",
                use_container_width=True
            )
        
        # Procesar botón "Aplicar Filtros"
        if aplicar_filtros:
            st.session_state.filtro_nombre = nombre_busqueda
            st.session_state.filtro_categoria = categoria_seleccionada
            st.session_state.filtros_aplicados = True
            st.rerun()
        
        # Procesar botón "Limpiar Filtros"
        if limpiar_filtros:
            st.session_state.filtro_nombre = ""
            st.session_state.filtro_categoria = "Todas"
            st.session_state.filtros_aplicados = False
            st.rerun()
    
    st.divider()
    
    # ============================================
    # APLICAR FILTROS AL DATAFRAME
    # ============================================
    df_filtrado = df_inventario.copy()
    
    # Filtrar por nombre (búsqueda insensible a mayúsculas)
    if st.session_state.filtros_aplicados and st.session_state.filtro_nombre:
        df_filtrado = df_filtrado[
            df_filtrado['nombre'].str.lower().str.contains(
                st.session_state.filtro_nombre.lower(),
                na=False
            )
        ]
    
    # Filtrar por categoría
    if st.session_state.filtros_aplicados and st.session_state.filtro_categoria != "Todas":
        df_filtrado = df_filtrado[
            df_filtrado['categoria'] == st.session_state.filtro_categoria
        ]
    
    # Mostrar mensaje si hay filtros activos
    if st.session_state.filtros_aplicados:
        filtros_texto = []
        if st.session_state.filtro_nombre:
            filtros_texto.append(f"Nombre: '{st.session_state.filtro_nombre}'")
        if st.session_state.filtro_categoria != "Todas":
            filtros_texto.append(f"Categoría: '{st.session_state.filtro_categoria}'")
        
        if filtros_texto:
            st.info(f"🔍 Filtros activos: {' | '.join(filtros_texto)} | Resultados: {len(df_filtrado)}")
    
    # ============================================
    # MÉTRICAS
    # ============================================
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_disfraces = len(df_filtrado)
        st.metric("Total Disfraces", total_disfraces)
    
    with col2:
        sin_stock = len(df_filtrado[df_filtrado['stock_disponible'] == 0])
        st.metric("Sin Stock", sin_stock, delta=f"{sin_stock} críticos", delta_color="inverse")
    
    with col3:
        total_alquilados = df_filtrado['unidades_alquiladas'].sum()
        st.metric("En Alquiler", int(total_alquilados))
    
    st.divider()
    
    # ============================================
    # TABLA DINÁMICA
    # ============================================
    
    # Verificar si hay datos después del filtrado
    if df_filtrado.empty:
        st.warning("⚠️ No se encontraron disfraces con los filtros aplicados")
        return
    
    # Configurar columnas para mostrar
    columnas_mostrar = [
        'nombre','descripcion', 'categoria', 'talla', 'stock_total', 
        'stock_disponible', 'unidades_alquiladas', 
        'costo_compra', 'alerta_stock', 'estado_conservacion'
    ]
    
    df_mostrar = df_filtrado[columnas_mostrar].copy()
    
    # Renombrar columnas
    df_mostrar.columns = [
        'Nombre', 'Descripción', 'Categoría', 'Talla', 'Stock Total',
        'Disponible', 'En Alquiler', 'Precio de Compra', 'Estado Stock', 'Conservación'
    ]
    
    # Aplicar estilos condicionales
    def resaltar_alertas(row):
        if row['Estado Stock'] == 'Sin stock':
            return ['background-color: #f8d7da'] * len(row)
        elif row['Estado Stock'] == 'Stock bajo':
            return ['background-color: #fff3cd'] * len(row)
        else:
            return [''] * len(row)
    
    styled_df = df_mostrar.style.apply(resaltar_alertas, axis=1)
    
    # Mostrar tabla
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=400,
        hide_index=True
    )
    
    # Información adicional
    st.caption(f"📊 Mostrando {len(df_filtrado)} de {len(df_inventario)} disfraces totales")


@fragment
def mostrar_alquileres_activos():
    """Fragment: Tabla de alquileres activos con botón de retorno"""
    st.subheader("🎭 Alquileres Activos")
    
    df_alquileres = db.get_alquileres_activos()
    
    # Métricas
    col1, col2, col3 = st.columns(3)

    if df_alquileres.empty:
        with col1:
            total_activos = len(df_alquileres)
            st.metric("Alquileres Activos", total_activos)
        
        with col3:
            ingresos_del_mes = db.get_ventas_del_mes()
            st.metric("Ingresos del Mes Actual", f"S/.{ingresos_del_mes:.2f}")
        st.success("✅ No hay alquileres activos en este momento")
        
        return
    
    with col1:
        total_activos = len(df_alquileres)
        st.metric("Alquileres Activos", total_activos)
    
    with col2:
        con_demora = len(df_alquileres[df_alquileres['tiene_demora'] == True])
        st.metric("Con Demora", con_demora, delta=f"{con_demora} retrasados", delta_color="inverse")
    
    with col3:
        ingresos_del_mes = db.get_ventas_del_mes()
        st.metric("Ingresos del Mes Actual", f"${ingresos_del_mes:.2f}")
    
    st.divider()
    
    # Mostrar cada alquiler con opción de retornar
    for idx, row in df_alquileres.iterrows():
        with st.container():
            col_info, col_accion = st.columns([4, 1])
            
            with col_info:
                # Indicador de demora
                demora_badge = "🔴" if row['tiene_demora'] else "🟢"
                
                st.markdown(f"""
                **{demora_badge} {row['disfraz_nombre']}** - {row['cliente_nombre']}
                - 📞 {row['cliente_telefono']}
                - 📅 Salida: {row['fecha_salida'].strftime('%d/%m/%Y %H:%M')}
                - 🔙 Retorno previsto: {row['fecha_retorno_prevista'].strftime('%d/%m/%Y')}
                - 💰 Monto: ${row['monto_alquiler']:.2f}
                - 📊 Estado: {row['estado'].upper()}
                """)
                
                if row['tiene_demora']:
                    dias_demora = int(row['dias_demora'])
                    st.warning(f"⚠️ DEMORA: {dias_demora} día(s) de retraso")
            
            with col_accion:
                # Botón para marcar como retornado - SOLO ADMIN
                if auth.is_admin():
                    if st.button("✅ Retornar", key=f"retornar_{row['id']}", use_container_width=True):
                        with st.spinner("Procesando retorno..."):
                            if db.marcar_como_retornado(row['id']):
                                st.success("✅ Retorno registrado exitosamente")
                                st.balloons()
                                # Limpiar cache para actualizar datos
                                st.cache_data.clear()
                                st.rerun()
                else:
                    st.button("🔒 Retornar", key=f"retornar_{row['id']}", use_container_width=True, disabled=True, help="Solo administradores pueden marcar retornos")
            
            st.divider()