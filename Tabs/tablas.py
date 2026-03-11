import streamlit as st
import Tabs.DB_function as db
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
    df_inventario = db.get_inventraio_disponibilidad()

    if df_inventario.empty:
        st.info("No hay disfraces en el inventario")
        return
    
    # Métricas rápidas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_disfraces = len(df_inventario)
        st.metric("Total Disfraces", total_disfraces)
    
    with col2:
        sin_stock = len(df_inventario[df_inventario['stock_disponible'] == 0])
        st.metric("Sin Stock", sin_stock, delta=f"{sin_stock} críticos", delta_color="inverse")
    
    with col3:
        total_alquilados = df_inventario['unidades_alquiladas'].sum()
        st.metric("En Alquiler", int(total_alquilados))
    
    st.divider()
    
    # Configurar columnas para mostrar
    columnas_mostrar = [
        'nombre', 'categoria', 'talla', 'stock_total', 
        'stock_disponible', 'unidades_alquiladas', 
        'costo_compra', 'alerta_stock', 'estado_conservacion'
    ]
    
    df_mostrar = df_inventario[columnas_mostrar].copy()
    
    # Renombrar columnas PRIMERO
    df_mostrar.columns = [
        'Nombre', 'Categoría', 'Talla', 'Stock Total',
        'Disponible', 'En Alquiler', 'Precio de Compra', 'Estado Stock', 'Conservación'
    ]
    
    # Aplicar estilos condicionales usando el nombre de columna RENOMBRADO
    def resaltar_alertas(row):
        if row['Estado Stock'] == 'Sin stock':
            return ['background-color: #f8d7da'] * len(row)
        elif row['Estado Stock'] == 'Stock bajo':
            return ['background-color: #fff3cd'] * len(row)
        else:
            return [''] * len(row)
    
    styled_df = df_mostrar.style.apply(resaltar_alertas, axis=1)
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=400,
        hide_index=True
    )

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
                # Botón para marcar como retornado
                if st.button("✅ Retornar", key=f"retornar_{row['id']}", use_container_width=True):
                    with st.spinner("Procesando retorno..."):
                        if db.marcar_como_retornado(row['id']):
                            st.success("✅ Retorno registrado exitosamente")
                            st.balloons()
                            # Limpiar cache para actualizar datos
                            st.cache_data.clear()
                            st.rerun()
            
            st.divider()