import streamlit as st
import auth
import Tabs.DB_function as db

def render_tab_editar_inventario():
    """
    Pestaña para editar disfraces del inventario.
    Solo accesible para administradores.
    """
    st.title("✏️ Editar Inventario de Disfraces")
    
    # Verificar permisos
    if not auth.is_admin():
        st.warning("⚠️ No tienes permisos para editar el inventario")
        st.info("👁️ Solo los administradores pueden editar disfraces")
        return
    
    if auth.is_admin():
        st.markdown("""
        Aquí puedes editar la información de los disfraces existentes en el inventario.
        Busca el disfraz que deseas modificar y actualiza sus datos.
        """)
        
        st.divider()
        
        # =============================================
        # SECCIÓN DE BÚSQUEDA
        # =============================================
        st.subheader("🔍 Buscar Disfraz")
        
        col_search, col_btn = st.columns([4, 1])
        
        with col_search:
            texto_busqueda = st.text_input(
                "Buscar por nombre",
                placeholder="Ej: Spiderman, Princesa, Vampiro...",
                key="buscar_editar_inventario",
                label_visibility="collapsed"
            )
        
        with col_btn:
            buscar_btn = st.button("🔍 Buscar", key="btn_buscar_editar", use_container_width=True, type="primary")
        
        # Realizar búsqueda
        disfraces_encontrados = []
        
        if buscar_btn or texto_busqueda:
            disfraces_encontrados = db.buscar_disfraces_por_nombre(texto_busqueda)
        else:
            # Mostrar todos los disfraces activos si no hay búsqueda
            disfraces_encontrados = db.get_todos_disfraces_activos()
        
        # Verificar si hay disfraces
        if not disfraces_encontrados:
            st.warning("⚠️ No hay disfraces en el inventario para editar")
            return
        
        # Mostrar resultados de búsqueda
        if texto_busqueda:
            st.success(f"✅ {len(disfraces_encontrados)} disfraz(es) encontrado(s)")
        else:
            st.info(f"📋 Mostrando todos los disfraces ({len(disfraces_encontrados)} total)")
        
        st.divider()
        
        # =============================================
        # SELECCIÓN DE DISFRAZ
        # =============================================
        st.subheader("📦 Seleccionar Disfraz a Editar")
        
        # Crear opciones de selectbox con información detallada
        disfraces_opciones = {}
        for disfraz in disfraces_encontrados:
            # Obtener nombre de categoría
            categoria_nombre = "Sin categoría"
            if disfraz.get('categoria_id'):
                categorias = db.get_categorias()
                categoria = next((c for c in categorias if c['id'] == disfraz['categoria_id']), None)
                if categoria:
                    categoria_nombre = categoria['nombre']
            
            # Formato: Nombre - Categoría - Talla (Stock: X)
            opcion_texto = f"{disfraz['nombre']} - {categoria_nombre} - Talla: {disfraz['talla']} (Stock: {disfraz['stock_total']})"
            disfraces_opciones[opcion_texto] = disfraz['id']
        
        disfraz_seleccionado_texto = st.selectbox(
            "Selecciona el disfraz a editar",
            options=list(disfraces_opciones.keys()),
            key="select_disfraz_editar"
        )
        
        disfraz_id = disfraces_opciones[disfraz_seleccionado_texto]
        
        # Obtener datos completos del disfraz
        disfraz_actual = db.get_disfraz_por_id(disfraz_id)
        
        if not disfraz_actual:
            st.error("❌ Error al cargar los datos del disfraz")
            return
        
        # Mostrar información actual
        st.divider()
        st.markdown("### 📊 Información Actual")
        
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        
        with col_info1:
            st.metric("Stock Total", disfraz_actual['stock_total'])
        
        with col_info2:
            st.metric("Stock Disponible", disfraz_actual['stock_disponible'])
        
        with col_info3:
            unidades_alquiladas = disfraz_actual['stock_total'] - disfraz_actual['stock_disponible']
            st.metric("En Alquiler", unidades_alquiladas)
        
        with col_info4:
            st.metric("Precio Compra", f"S/.{disfraz_actual['costo_compra']:.2f}")
        
        st.divider()
        
        # =============================================
        # BOTÓN PARA MOSTRAR FORMULARIO DE EDICIÓN
        # =============================================
        
        # Estado para controlar si se muestra el formulario
        if 'mostrar_formulario_edicion' not in st.session_state:
            st.session_state.mostrar_formulario_edicion = False
        
        if 'disfraz_editando_id' not in st.session_state:
            st.session_state.disfraz_editando_id = None
        
        # Botón para mostrar/ocultar formulario
        col_btn1, col_btn2 = st.columns([1, 3])
        
        with col_btn1:
            if st.button(
                "✏️ Editar este Disfraz" if not st.session_state.mostrar_formulario_edicion else "❌ Cancelar Edición",
                use_container_width=True,
                type="primary" if not st.session_state.mostrar_formulario_edicion else "secondary",
                key="btn_toggle_formulario_edicion"
            ):
                st.session_state.mostrar_formulario_edicion = not st.session_state.mostrar_formulario_edicion
                st.session_state.disfraz_editando_id = disfraz_id if st.session_state.mostrar_formulario_edicion else None
                st.rerun()
        
        # =============================================
        # FORMULARIO DE EDICIÓN
        # =============================================
        
        if st.session_state.mostrar_formulario_edicion and st.session_state.disfraz_editando_id == disfraz_id:
            st.divider()
            st.markdown("### ✏️ Formulario de Edición")
            
            st.warning("⚠️ **Importante:** Los campos marcados con (*) son obligatorios")
            
            # Obtener categorías para el selectbox
            categorias = db.get_categorias()
            
            with st.form("form_editar_disfraz", clear_on_submit=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Nombre
                    nombre_editado = st.text_input(
                        "Nombre del Disfraz *",
                        value=disfraz_actual['nombre'],
                        key="edit_nombre",
                        help="Nombre descriptivo del disfraz"
                    )
                    
                    # Categoría
                    categoria_opciones = {cat['nombre']: cat['id'] for cat in categorias}
                    categoria_actual_nombre = next(
                        (cat['nombre'] for cat in categorias if cat['id'] == disfraz_actual['categoria_id']),
                        list(categoria_opciones.keys())[0] if categoria_opciones else None
                    )
                    
                    categoria_editada_nombre = st.selectbox(
                        "Categoría *",
                        options=list(categoria_opciones.keys()),
                        index=list(categoria_opciones.keys()).index(categoria_actual_nombre) if categoria_actual_nombre else 0,
                        key="edit_categoria",
                        help="Categoría del disfraz"
                    )
                    
                    categoria_editada_id = categoria_opciones[categoria_editada_nombre]
                    
                    # Talla
                    talla_editada = st.text_input(
                        "Talla *",
                        value=disfraz_actual['talla'],
                        key="edit_talla",
                        help="Ej: S, M, L, 10, 12, 16, etc."
                    )
                    
                    # Género
                    generos = ['Unisex', 'Masculino', 'Femenino']
                    genero_actual = disfraz_actual.get('genero', 'Unisex')
                    genero_index = generos.index(genero_actual) if genero_actual in generos else 0
                    
                    genero_editado = st.selectbox(
                        "Género *",
                        options=generos,
                        index=genero_index,
                        key="edit_genero"
                    )
                
                with col2:
                    # Stock Total
                    stock_actual = disfraz_actual['stock_total']
                    unidades_alquiladas_actual = disfraz_actual['stock_total'] - disfraz_actual['stock_disponible']
                    
                    stock_editado = st.number_input(
                        f"Stock Total * (Mínimo: {unidades_alquiladas_actual} - unidades alquiladas)",
                        min_value=unidades_alquiladas_actual,
                        value=stock_actual,
                        step=1,
                        key="edit_stock",
                        help=f"No puede ser menor a {unidades_alquiladas_actual} porque hay unidades alquiladas"
                    )
                    
                    # Precio de Compra
                    precio_editado = st.number_input(
                        "Precio de Compra *",
                        min_value=0.0,
                        value=float(disfraz_actual['costo_compra']),
                        step=0.5,
                        key="edit_precio",
                        help="Precio al momento de comprar el disfraz"
                    )
                    
                    # Estado de Conservación
                    estados = ['Nuevo', 'Bueno', 'Regular', 'Requiere reparación']
                    estado_actual = disfraz_actual.get('estado_conservacion', 'Bueno')
                    estado_index = estados.index(estado_actual) if estado_actual in estados else 1
                    
                    estado_editado = st.selectbox(
                        "Estado de Conservación *",
                        options=estados,
                        index=estado_index,
                        key="edit_estado_conservacion"
                    )
                
                # Descripción
                descripcion_editada = st.text_area(
                    "Descripción",
                    value=disfraz_actual.get('descripcion', ''),
                    height=100,
                    key="edit_descripcion",
                    help="Descripción detallada del disfraz"
                )
                
                # Notas
                notas_editadas = st.text_area(
                    "Notas Adicionales",
                    value=disfraz_actual.get('notas', ''),
                    height=60,
                    key="edit_notas",
                    help="Observaciones especiales"
                )
                
                st.divider()
                
                # Mostrar cambios propuestos
                st.markdown("### 📋 Resumen de Cambios")
                
                cambios = []
                if nombre_editado != disfraz_actual['nombre']:
                    cambios.append(f"**Nombre:** {disfraz_actual['nombre']} → {nombre_editado}")
                
                if categoria_editada_id != disfraz_actual['categoria_id']:
                    categoria_anterior = next((cat['nombre'] for cat in categorias if cat['id'] == disfraz_actual['categoria_id']), 'N/A')
                    cambios.append(f"**Categoría:** {categoria_anterior} → {categoria_editada_nombre}")
                
                if talla_editada != disfraz_actual['talla']:
                    cambios.append(f"**Talla:** {disfraz_actual['talla']} → {talla_editada}")
                
                if genero_editado != disfraz_actual.get('genero', 'Unisex'):
                    cambios.append(f"**Género:** {disfraz_actual.get('genero', 'Unisex')} → {genero_editado}")
                
                if stock_editado != disfraz_actual['stock_total']:
                    cambios.append(f"**Stock Total:** {disfraz_actual['stock_total']} → {stock_editado}")
                
                if precio_editado != float(disfraz_actual['costo_compra']):
                    cambios.append(f"**Precio Compra:** S/.{disfraz_actual['costo_compra']:.2f} → S/.{precio_editado:.2f}")
                
                if estado_editado != disfraz_actual.get('estado_conservacion', 'Bueno'):
                    cambios.append(f"**Conservación:** {disfraz_actual.get('estado_conservacion', 'Bueno')} → {estado_editado}")
                
                if descripcion_editada != disfraz_actual.get('descripcion', ''):
                    cambios.append(f"**Descripción:** Modificada")
                
                if notas_editadas != disfraz_actual.get('notas', ''):
                    cambios.append(f"**Notas:** Modificadas")
                
                if cambios:
                    for cambio in cambios:
                        st.markdown(f"- {cambio}")
                else:
                    st.info("ℹ️ No hay cambios pendientes")
                
                st.divider()
                
                # Botones del formulario
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                
                with col_btn1:
                    submit = st.form_submit_button(
                        "💾 Guardar Cambios",
                        type="primary",
                        use_container_width=True
                    )
                
                with col_btn2:
                    cancelar = st.form_submit_button(
                        "❌ Cancelar",
                        use_container_width=True
                    )
                
                # Procesar formulario
                if submit:
                    # Validar campos obligatorios
                    if not nombre_editado or not talla_editada or precio_editado < 0:
                        st.error("❌ Por favor completa todos los campos obligatorios (*)")
                    else:
                        # Validar stock
                        es_valido, mensaje_validacion, unidades_alq = db.validar_stock_para_edicion(disfraz_id, stock_editado)
                        
                        if not es_valido:
                            st.error(mensaje_validacion)
                        else:
                            # Preparar datos actualizados
                            datos_actualizados = {
                                'nombre': nombre_editado,
                                'descripcion': descripcion_editada,
                                'categoria_id': categoria_editada_id,
                                'talla': talla_editada,
                                'genero': genero_editado,
                                'stock_total': stock_editado,
                                'costo_compra': precio_editado,
                                'estado_conservacion': estado_editado,
                                'notas': notas_editadas
                            }
                            
                            # Calcular nuevo stock_disponible
                            diferencia_stock = stock_editado - disfraz_actual['stock_total']
                            nuevo_stock_disponible = disfraz_actual['stock_disponible'] + diferencia_stock
                            datos_actualizados['stock_disponible'] = max(0, nuevo_stock_disponible)
                            
                            # Guardar en base de datos
                            with st.spinner("💾 Guardando cambios..."):
                                exito, mensaje = db.actualizar_disfraz(disfraz_id, datos_actualizados)
                                
                                if exito:
                                    st.success(mensaje)
                                    st.balloons()
                                    
                                    # Limpiar cache y estado
                                    st.cache_data.clear()
                                    st.session_state.mostrar_formulario_edicion = False
                                    st.session_state.disfraz_editando_id = None
                                    
                                    st.rerun()
                                else:
                                    st.error(mensaje)
                
                if cancelar:
                    st.session_state.mostrar_formulario_edicion = False
                    st.session_state.disfraz_editando_id = None
                    st.info("Edición cancelada")
                    st.rerun()