import streamlit as st
import Tabs.DB_function as db
import auth
import pandas as pd

def render_tab_gestion_disfraces():
    """
    Pestaña para gestionar disfraces: desactivar y reactivar cantidades específicas de stock
    """
    st.title("🗂️ Gestión de Stock de Disfraces")
    
    # Verificar permisos - Solo admin
    if auth.is_viewer():
        st.warning("⚠️ No tienes permisos para gestionar disfraces")
        st.info("👁️ Solo los administradores pueden desactivar o reactivar stock de disfraces")
        return
    
    st.markdown("""
    En esta sección puedes:
    - **Desactivar cantidades específicas** de stock de disfraces que ya no uses
    - **Reactivar cantidades específicas** de stock cuando vuelvan a estar disponibles
    
    El stock desactivado se resta del inventario pero mantiene todo el historial de alquileres.
    """)
    
    st.divider()
    
    # Crear tabs
    tab1, tab2 = st.tabs(["🗑️ Desactivar Stock", "♻️ Reactivar Stock"])
    
    # =============================================
    # TAB 1: DESACTIVAR STOCK
    # =============================================
    with tab1:
        st.subheader("Desactivar Unidades de Stock")
        
        st.info("""
        💡 **¿Cómo funciona?**
        - Selecciona un disfraz y especifica cuántas unidades deseas desactivar
        - Solo puedes desactivar unidades que estén **disponibles** (no alquiladas)
        - El stock total y disponible se reducirán por la cantidad especificada
        - Si el stock total llega a 0, el disfraz se marcará automáticamente como inactivo
        """)
        
        # Obtener disfraces activos con stock
        df_disfraces = db.get_disfraces_con_stock()
        
        if df_disfraces.empty:
            st.warning("⚠️ No hay disfraces activos con stock en el inventario")
            return
        
        # Filtros para buscar el disfraz
        col_filtro1, col_filtro2 = st.columns(2)
        
        with col_filtro1:
            buscar_nombre = st.text_input(
                "🔍 Buscar disfraz por nombre",
                placeholder="Ej: Spiderman, Princesa...",
                key="buscar_desactivar_stock"
            )
        
        with col_filtro2:
            categorias_disponibles = ['Todas']
            if 'categoria' in df_disfraces.columns:
                categorias_disponibles += sorted(df_disfraces['categoria'].dropna().unique().tolist())
            
            filtrar_categoria = st.selectbox(
                "Filtrar por categoría",
                options=categorias_disponibles,
                key="filtrar_cat_desactivar_stock"
            )
        
        # Aplicar filtros
        df_filtrado = df_disfraces.copy()
        
        if buscar_nombre:
            df_filtrado = df_filtrado[
                df_filtrado['nombre'].str.lower().str.contains(buscar_nombre.lower(), na=False)
            ]
        
        if filtrar_categoria != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['categoria'] == filtrar_categoria]
        
        if df_filtrado.empty:
            st.warning("⚠️ No se encontraron disfraces con esos criterios")
        else:
            st.success(f"✅ {len(df_filtrado)} disfraz(es) encontrado(s)")
            
            # Mostrar tabla resumida
            columnas_mostrar = ['nombre', 'categoria', 'talla', 'stock_total', 'stock_disponible']
            columnas_existentes = [col for col in columnas_mostrar if col in df_filtrado.columns]
            
            df_mostrar = df_filtrado[columnas_existentes].copy()
            df_mostrar['unidades_alquiladas'] = df_mostrar['stock_total'] - df_mostrar['stock_disponible']
            
            # Renombrar columnas
            df_mostrar = df_mostrar.rename(columns={
                'nombre': 'Nombre',
                'categoria': 'Categoría',
                'talla': 'Talla',
                'stock_total': 'Stock Total',
                'stock_disponible': 'Disponible',
                'unidades_alquiladas': 'Alquiladas'
            })
            
            st.dataframe(
                df_mostrar,
                use_container_width=True,
                hide_index=True,
                height=300
            )
            
            st.divider()
            
            # Seleccionar disfraz para desactivar stock
            st.markdown("### Selecciona el disfraz y cantidad a desactivar")
            
            disfraces_opciones = {
                f"{row['nombre']} - {row.get('categoria', 'Sin categoría')} - Talla: {row['talla']} (Total: {row['stock_total']}, Disponible: {row['stock_disponible']})": row['id']
                for idx, row in df_filtrado.iterrows()
            }
            
            disfraz_seleccionado = st.selectbox(
                "Disfraz",
                options=list(disfraces_opciones.keys()),
                key="select_disfraz_desactivar_stock"
            )
            
            disfraz_id = disfraces_opciones[disfraz_seleccionado]
            
            # Verificar stock disponible para desactivar
            puede_desactivar, mensaje, info = db.verificar_stock_para_desactivar(disfraz_id)
            
            # Mostrar información del disfraz
            col_info1, col_info2, col_info3, col_info4 = st.columns(4)
            
            with col_info1:
                st.metric("Stock Total", info.get('stock_total', 0))
            
            with col_info2:
                st.metric("Stock Disponible", info.get('stock_disponible', 0))
            
            with col_info3:
                st.metric("En Alquiler", info.get('unidades_alquiladas', 0))
            
            with col_info4:
                st.metric("Alquileres Activos", info.get('alquileres_activos_count', 0))
            
            st.divider()
            
            # Input para cantidad a desactivar
            if puede_desactivar:
                st.success(mensaje)
                
                max_desactivable = info.get('max_desactivable', 0)
                
                col_input, col_btn = st.columns([2, 1])
                
                with col_input:
                    cantidad_desactivar = st.number_input(
                        f"Cantidad a desactivar (máximo: {max_desactivable})",
                        min_value=1,
                        max_value=max_desactivable,
                        value=1,
                        step=1,
                        key="input_cantidad_desactivar"
                    )
                
                st.warning(f"⚠️ **¿Estás seguro de desactivar {cantidad_desactivar} unidad(es)?**")
                st.markdown(f"""
                Esto hará que:
                - ✅ Stock total: {info.get('stock_total', 0)} → **{info.get('stock_total', 0) - cantidad_desactivar}**
                - ✅ Stock disponible: {info.get('stock_disponible', 0)} → **{info.get('stock_disponible', 0) - cantidad_desactivar}**
                """)
                
                if info.get('stock_total', 0) - cantidad_desactivar == 0:
                    st.error("🔴 El disfraz se marcará como **INACTIVO** (stock = 0)")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                
                with col_btn1:
                    if st.button("🗑️ Sí, Desactivar", type="primary", use_container_width=True, key="btn_confirmar_desactivar"):
                        with st.spinner("Desactivando stock..."):
                            exito, msg = db.soft_delete_stock_disfraz(disfraz_id, cantidad_desactivar)
                            
                            if exito:
                                st.success(msg)
                                st.balloons()
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(msg)
                
                with col_btn2:
                    if st.button("❌ Cancelar", use_container_width=True, key="btn_cancelar_desactivar"):
                        st.info("Operación cancelada")
            else:
                st.error(mensaje)
                st.info("💡 Solo puedes desactivar stock que esté disponible (no alquilado)")
    
    # =============================================
    # TAB 2: REACTIVAR STOCK
    # =============================================
    with tab2:
        st.subheader("♻️ Reactivar Unidades de Stock")
        
        st.info("""
        💡 **¿Cómo funciona?**
        - Selecciona un disfraz y especifica cuántas unidades deseas reactivar
        - El stock total y disponible aumentarán por la cantidad especificada
        - Si el disfraz estaba inactivo (stock = 0), se marcará automáticamente como activo
        - Las unidades reactivadas estarán inmediatamente disponibles para alquiler
        """)
        
        # Obtener TODOS los disfraces (incluyendo inactivos)
        df_todos_disfraces = db.get_disfraces_todos_incluyendo_inactivos()
        
        if df_todos_disfraces.empty:
            st.warning("⚠️ No hay disfraces en la base de datos")
            return
        
        # Filtros
        col_filtro1, col_filtro2 = st.columns(2)
        
        with col_filtro1:
            buscar_nombre_reactivar = st.text_input(
                "🔍 Buscar disfraz por nombre",
                placeholder="Ej: Spiderman, Princesa...",
                key="buscar_reactivar_stock"
            )
        
        with col_filtro2:
            categorias_disponibles_reactivar = ['Todas']
            if 'categoria' in df_todos_disfraces.columns:
                categorias_disponibles_reactivar += sorted(df_todos_disfraces['categoria'].dropna().unique().tolist())
            
            filtrar_categoria_reactivar = st.selectbox(
                "Filtrar por categoría",
                options=categorias_disponibles_reactivar,
                key="filtrar_cat_reactivar_stock"
            )
        
        # Aplicar filtros
        df_filtrado_reactivar = df_todos_disfraces.copy()
        
        if buscar_nombre_reactivar:
            df_filtrado_reactivar = df_filtrado_reactivar[
                df_filtrado_reactivar['nombre'].str.lower().str.contains(buscar_nombre_reactivar.lower(), na=False)
            ]
        
        if filtrar_categoria_reactivar != 'Todas':
            df_filtrado_reactivar = df_filtrado_reactivar[df_filtrado_reactivar['categoria'] == filtrar_categoria_reactivar]
        
        if df_filtrado_reactivar.empty:
            st.warning("⚠️ No se encontraron disfraces con esos criterios")
        else:
            st.success(f"✅ {len(df_filtrado_reactivar)} disfraz(es) encontrado(s)")
            
            # Mostrar tabla
            columnas_mostrar_reactivar = ['nombre', 'categoria', 'talla', 'stock_total', 'stock_disponible', 'activo']
            columnas_existentes_reactivar = [col for col in columnas_mostrar_reactivar if col in df_filtrado_reactivar.columns]
            
            df_mostrar_reactivar = df_filtrado_reactivar[columnas_existentes_reactivar].copy()
            
            # Renombrar columnas
            df_mostrar_reactivar = df_mostrar_reactivar.rename(columns={
                'nombre': 'Nombre',
                'categoria': 'Categoría',
                'talla': 'Talla',
                'stock_total': 'Stock Total',
                'stock_disponible': 'Disponible',
                'activo': 'Activo'
            })
            
            st.dataframe(
                df_mostrar_reactivar,
                use_container_width=True,
                hide_index=True,
                height=300
            )
            
            st.divider()
            
            # Seleccionar disfraz para reactivar
            st.markdown("### Selecciona el disfraz y cantidad a reactivar")

            # Creamos un dataframe para tener solo a los inactivos
            df_inactivos = df_filtrado_reactivar[df_filtrado_reactivar['activo'] == False]
            
            if df_inactivos.empty:
                st.warning("⚠️ No hay disfraces inactivos que puedan ser reactivados")
            
            else:
                disfraces_opciones_reactivar = {
                    f"{row['nombre']} - {row.get('categoria', 'Sin categoría')} - Talla: {row['talla']} (Stock actual: {row['stock_total']}, {'INACTIVO' if not row['activo'] else 'ACTIVO'})": row['id']
                    for idx, row in df_inactivos.iterrows()
                }
                
                disfraz_seleccionado_reactivar = st.selectbox(
                    "Disfraz",
                    options=list(disfraces_opciones_reactivar.keys()),
                    key="select_disfraz_reactivar_stock"
                )
                
                disfraz_id_reactivar = disfraces_opciones_reactivar[disfraz_seleccionado_reactivar]
                
                # Obtener info del disfraz
                disfraz_info = df_inactivos[df_inactivos ['id'] == disfraz_id_reactivar].iloc[0]
                
                # Mostrar información actual
                col_info1, col_info2, col_info3 = st.columns(3)
                
                with col_info1:
                    st.metric("Stock Total Actual", disfraz_info['stock_total'])
                
                with col_info2:
                    st.metric("Stock Disponible Actual", disfraz_info['stock_disponible'])
                
                with col_info3:
                    estado_badge = "🟢 Activo" if disfraz_info['activo'] else "🔴 Inactivo"
                    st.metric("Estado", estado_badge)
                
                st.divider()
                
                # Input para cantidad a reactivar
                col_input_reactivar, col_btn_reactivar = st.columns([2, 1])
                
                with col_input_reactivar:
                    cantidad_reactivar = st.number_input(
                        "Cantidad a reactivar",
                        min_value=1,
                        value=1,
                        step=1,
                        key="input_cantidad_reactivar"
                    )
                
                st.info(f"ℹ️ **Se reactivarán {cantidad_reactivar} unidad(es)**")
                st.markdown(f"""
                Esto hará que:
                - ✅ Stock total: {disfraz_info['stock_total']} → **{disfraz_info['stock_total'] + cantidad_reactivar}**
                - ✅ Stock disponible: {disfraz_info['stock_disponible']} → **{disfraz_info['stock_disponible'] + cantidad_reactivar}**
                """)
                
                if not disfraz_info['activo']:
                    st.success("🟢 El disfraz se marcará como **ACTIVO**")
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button("♻️ Reactivar Stock", type="primary", use_container_width=True, key="btn_confirmar_reactivar"):
                        with st.spinner("Reactivando stock..."):
                            exito, msg = db.reactivar_stock_disfraz(disfraz_id_reactivar, cantidad_reactivar)
                            
                            if exito:
                                st.success(msg)
                                st.balloons()
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(msg)
                
                with col_btn2:
                    if st.button("❌ Cancelar", use_container_width=True, key="btn_cancelar_reactivar"):
                        st.info("Operación cancelada")