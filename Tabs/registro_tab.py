import streamlit as st
import Tabs.DB_function as db

def render_tab_registro():
    st.title("Registro de Disfraz")

    st.markdown("""
    Completa el formulario:
    - Nombre del disfraz
    - Categoría
    - Descripción
    - Talla estimada
    - Precio de Compra
    
    Verifica antes de guardar en el inventario.
    """)

    st.divider()

    categorias = db.get_categorias()
    
    # Inicializar contador de reinicio si no existe
    if 'form_reset_counter' not in st.session_state:
        st.session_state.form_reset_counter = 0

    # Usar el contador para crear keys únicas cada vez que se reinicia
    reset_key = st.session_state.form_reset_counter

    with st.form("form_guardar_disfraz"):
        col1,col2 = st.columns(2)
        with col1:
            nombre = st.text_input(
                "Nombre del Atuendo *",
                value = "",
                key=f"input_nombre_{reset_key}",
                help="Nombre descriptivo del disfraz"
            )

            categoria_opciones = {cat['nombre']: cat['id'] for cat in categorias}
            categoria_nombre = st.selectbox(
                "Categoria *",
                options=list(categoria_opciones.keys()),
                key=f"input_categoria_{reset_key}",
                help="Categoría del disfraz"
            )

            categoria_id = categoria_opciones[categoria_nombre]

            talla = st.text_input(
                "Talla *",
                value="",
                key=f"input_talla_{reset_key}",
                help="Ej: S, M, L, 10, 12, 16, etc."
            )

            genero = st.selectbox(
                "Genero *",
                key=f"input_genero_{reset_key}",
                options=['Unisex','Masculino','Femenino'],
            )
        with col2:
            stock_total = st.number_input(
                "Cantidad (Stock Comprado) *",
                min_value=1,
                key=f"input_stock_{reset_key}",
                help="Cantidad de unidades comprados de este traje"
            )

            precio_compra = st.number_input(
                "Precio de Compra *",
                min_value=0.0,
                step=0.5,
                key=f"input_precio_{reset_key}",
                help="Precio al momento de comprar el disfraz"
            )

            estado_conservacion = st.selectbox(
                "Estado de Conservacion *",
                options=['Nuevo', 'Bueno', 'Regular', 'Requiere reparación'],
                key=f"input_conservacion_{reset_key}",
                index=0
            )
        descripcion = st.text_area(
            "Descripción",
            height=100,
            key=f"input_descripcion_{reset_key}",
            help="Descripción detallada del disfraz"
        )
                
        notas = st.text_area(
            "Notas Adicionales",
            height=60,
            key=f"input_notas_{reset_key}",
            help="Observaciones especiales"
        )

        col_btn1,col_btn2 = st.columns(2)

        with col_btn1:
            submit = st.form_submit_button(
                "💾 Guardar en Inventario",
                type="primary",
                use_container_width=True
            )
        
        with col_btn2:
            cancelar = st.form_submit_button(
                "❌ Cancelar",
                use_container_width=True
            )
        
        if submit:
            # Validamos campos requeridos
            if not nombre or not categoria_id or not talla or not precio_compra:
                st.error("Rellena los campos Obligatorios (*)")
            else:
                datos_disfraz = {
                    'nombre': nombre,
                    'descripcion': descripcion,
                    'categoria_id': categoria_id,
                    'talla': talla,
                    'genero': genero,
                    'stock_total': stock_total,
                    'stock_disponible': stock_total,  # Inicialmente todo disponible
                    'costo_compra': precio_compra,
                    'estado_conservacion': estado_conservacion,
                    'notas': notas,
                    'activo': True
                }

                with st.spinner("💾 Guardando en inventario..."):
                    if db.insertar_disfraz(datos_disfraz):
                        st.success(f"✅ Disfraz '{nombre}' agregado exitosamente al inventario")
                        st.balloons()
                        st.session_state.form_reset_counter += 1
                        st.cache_data.clear()
                        st.rerun()
        if cancelar:
            # Incrementar el contador para sertear el formulario
            st.session_state.form_reset_counter += 1
            st.rerun()