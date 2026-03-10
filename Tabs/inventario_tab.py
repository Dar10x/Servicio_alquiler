import Tabs.tablas as tb
import streamlit as st
def render_tab_inventario():
    st.title("Inventario y Alquileres Activos")

    col_izq,col_der = st.columns([1,1])

    with col_izq:
        tb.mostrar_tabla_inventario()

    with col_der:
        tb.mostrar_alquileres_activos()

    if st.button("Actualizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()