import streamlit as st
import Tabs.DB_function as db
import auth
import pandas as pd

def render_tab_gestion_disfraces():
    """
    Pestaña para gestionar disfraces: desactivar (soft delete) y reactivar
    """
    st.title("🗂️ Desactivar Disfraces")
    
    # Verificar permisos - Solo admin
    if auth.is_viewer():
        st.warning("⚠️ No tienes permisos para gestionar disfraces")
        st.info("👁️ Solo los administradores pueden desactivar o reactivar disfraces")
        return
    
    st.markdown("""
    En esta sección puedes:
    - **Desactivar disfraces** que ya no uses (se ocultan del inventario activo)
    - **Ver disfraces desactivados** previamente
    - **Reactivar disfraces** si decides volver a usarlos
    
    Los disfraces desactivados mantienen su historial de alquileres.
    """)
    
    st.divider()
    
    # Crear tabs
    tab1, tab2 = st.tabs(["🗑️ Desactivar Disfraces", "♻️ Disfraces Desactivados"])
    
    # =============================================
    # TAB 1: DESACTIVAR DISFRACES
    # =============================================
    with tab1:
        st.subheader("Desactivar Disfraces del Inventario")
        
        st.info("""
        💡 **Desactivar vs Eliminar:**
        - ✅ Los disfraces desactivados se ocultan del inventario activo
        - ✅ Se conserva todo el historial de alquileres
        - ✅ Puedes reactivarlos cuando quieras
        - ❌ No se pueden desactivar si tienen alquileres activos
        """)
        
        # Obtener disfraces activos
        df_inventario = db.get_inventraio_disponibilidad()
        
        if df_inventario.empty:
            st.warning("⚠️ No hay disfraces activos en el inventario")
            return
        
        # Filtros para buscar el disfraz a desactivar
        col_filtro1, col_filtro2 = st.columns(2)
        
        with col_filtro1:
            buscar_nombre = st.text_input(
                "🔍 Buscar disfraz por nombre",
                placeholder="Ej: Spiderman, Princesa...",
                key="buscar_desactivar"
            )
        
        with col_filtro2:
            categorias_disponibles = ['Todas'] + sorted(df_inventario['categoria'].dropna().unique().tolist())
            filtrar_categoria = st.selectbox(
                "Filtrar por categoría",
                options=categorias_disponibles,
                key="filtrar_cat_desactivar"
            )
        
        # Aplicar filtros
        df_filtrado = df_inventario.copy()
        
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
            df_mostrar = df_filtrado[['nombre', 'categoria', 'talla', 'stock_total', 'stock_disponible', 'unidades_alquiladas']].copy()
            
            st.dataframe(
                df_mostrar,
                use_container_width=True,
                hide_index=True,
                height=300
            )
            
            st.divider()
            
            # Seleccionar disfraz para desactivar
            st.markdown("### Selecciona el disfraz a desactivar")
            
            disfraces_opciones = {
                f"{row['nombre']} - {row['categoria']} - Talla: {row['talla']} (Stock: {row['stock_total']})": row['id']
                for idx, row in df_filtrado.iterrows()
            }
            
            disfraz_seleccionado = st.selectbox(
                "Disfraz",
                options=list(disfraces_opciones.keys()),
                key="select_disfraz_desactivar"
            )
            
            disfraz_id = disfraces_opciones[disfraz_seleccionado]
            
            # Verificar si puede ser desactivado
            puede_eliminar, mensaje, info = db.verificar_puede_eliminar_disfraz(disfraz_id)
            
            # Mostrar información del disfraz
            col_info1, col_info2, col_info3 = st.columns(3)
            
            with col_info1:
                st.metric("Alquileres Activos", info.get('alquileres_activos', 0))
            
            with col_info2:
                st.metric("Total Histórico", info.get('total_alquileres', 0))
            
            with col_info3:
                st.metric("Stock Disponible", f"{info.get('stock_disponible', 0)}/{info.get('stock_total', 0)}")
            
            st.divider()
            
            # Mostrar estado
            if puede_eliminar:
                st.success(mensaje)
                
                # Confirmar desactivación
                st.warning("⚠️ **¿Estás seguro de desactivar este disfraz?**")
                st.markdown("""
                El disfraz:
                - ✅ Se ocultará del inventario activo
                - ✅ Mantendrá su historial de alquileres
                - ✅ Podrá ser reactivado después
                """)
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                
                with col_btn1:
                    if st.button("🗑️ Sí, Desactivar", type="primary", use_container_width=True):
                        with st.spinner("Desactivando disfraz..."):
                            exito, msg = db.soft_delete_disfraz(disfraz_id)
                            
                            if exito:
                                st.success(msg)
                                st.balloons()
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(msg)
                
                with col_btn2:
                    if st.button("❌ Cancelar", use_container_width=True):
                        st.info("Operación cancelada")
            else:
                st.error(mensaje)
                st.info("💡 Espera a que se completen los alquileres activos antes de desactivar el disfraz")
    
    # =============================================
    # TAB 2: DISFRACES DESACTIVADOS
    # =============================================
    with tab2:
        st.subheader("♻️ Disfraces Desactivados")
        
        st.info("""
        Aquí puedes ver todos los disfraces que han sido desactivados y reactivarlos si es necesario.
        """)
        
        # Obtener disfraces inactivos
        df_inactivos = db.get_disfraces_inactivos()
        
        if df_inactivos.empty:
            st.success("✅ No hay disfraces desactivados")
            st.info("Todos los disfraces del inventario están activos")
            return
        
        # Mostrar métricas
        col_met1, col_met2 = st.columns(2)
        
        with col_met1:
            st.metric("Disfraces Desactivados", len(df_inactivos))
        
        with col_met2:
            if 'stock_total' in df_inactivos.columns:
                total_stock = df_inactivos['stock_total'].sum()
                st.metric("Stock Total Desactivado", int(total_stock))
        
        st.divider()
        
        # Preparar datos para mostrar
        columnas_mostrar = ['nombre', 'categoria', 'talla', 'stock_total', 'stock_disponible', 'costo_compra', 'estado_conservacion']
        columnas_existentes = [col for col in columnas_mostrar if col in df_inactivos.columns]
        
        df_mostrar = df_inactivos[columnas_existentes].copy()
        
        # Renombrar columnas
        nombres_columnas = {
            'nombre': 'Nombre',
            'categoria': 'Categoría',
            'talla': 'Talla',
            'stock_total': 'Stock Total',
            'stock_disponible': 'Disponible',
            'costo_compra': 'Costo Compra',
            'estado_conservacion': 'Conservación'
        }
        
        df_mostrar = df_mostrar.rename(columns=nombres_columnas)
        
        st.dataframe(
            df_mostrar,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        st.divider()
        
        # Reactivar disfraz
        st.markdown("### ♻️ Reactivar Disfraz")
        
        disfraces_inactivos_opciones = {
            f"{row['nombre']} - {row.get('categoria', 'Sin categoría')} - Talla: {row['talla']}": row['id']
            for idx, row in df_inactivos.iterrows()
        }
        
        disfraz_reactivar = st.selectbox(
            "Selecciona el disfraz a reactivar",
            options=list(disfraces_inactivos_opciones.keys()),
            key="select_reactivar"
        )
        
        disfraz_id_reactivar = disfraces_inactivos_opciones[disfraz_reactivar]
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("♻️ Reactivar Disfraz", type="primary", use_container_width=True):
                with st.spinner("Reactivando disfraz..."):
                    exito, msg = db.reactivar_disfraz(disfraz_id_reactivar)
                    
                    if exito:
                        st.success(msg)
                        st.balloons()
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(msg)