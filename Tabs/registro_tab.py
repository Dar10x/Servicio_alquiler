import streamlit as st
import Tabs.DB_function as db
import auth

def render_tab_registro():
    st.title("Registro de Disfraz")

    # Verificar permisos
    if auth.is_viewer():
        st.warning("⚠️ No tienes permisos para registrar disfraces")
        st.info("👁️ Solo los administradores pueden agregar nuevos disfraces al inventario")
        return

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
                key=f"input_nombre_registro_{reset_key}",
                help="Nombre descriptivo del disfraz"
            )

            categoria_opciones = {cat['nombre']: cat['id'] for cat in categorias}
            categoria_nombre = st.text_input(
                "Categoria *",
                value="",
                placeholder="Ej: Superhéroe, Princesa, Animales, etc.",
                key=f"input_categoria_registro_{reset_key}",
                help="Categoría general del disfraz"
            )

            talla = st.text_input(
                "Talla *",
                value="",
                key=f"input_talla_registro_{reset_key}",
                help="Ej: S, M, L, 10, 12, 16, etc."
            )

            genero = st.selectbox(
                "Genero *",
                key=f"input_genero_registro_{reset_key}",
                options=['Unisex','Masculino','Femenino'],
            )
        with col2:
            stock_total = st.number_input(
                "Cantidad (Stock Comprado) *",
                min_value=1,
                key=f"input_stock_registro_{reset_key}",
                help="Cantidad de unidades comprados de este traje"
            )

            precio_compra = st.number_input(
                "Precio de Compra *",
                min_value=0.0,
                step=0.5,
                key=f"input_precio_registro_{reset_key}",
                help="Precio al momento de comprar el disfraz"
            )

            estado_conservacion = st.selectbox(
                "Estado de Conservacion *",
                options=['Nuevo', 'Bueno', 'Regular', 'Requiere reparación'],
                key=f"input_conservacion_registro_{reset_key}",
                index=0
            )
        descripcion = st.text_area(
            "Descripción (Sugerencia: Ingrese el precio de venta y alquiler sugeridos aquí)",
            height=100,
            key=f"input_descripcion_registro_{reset_key}",
            help="Descripción detallada del disfraz"
        )
                
        notas = st.text_area(
            "Notas Adicionales",
            height=60,
            key=f"input_notas_registro_{reset_key}",
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
            # Validamos campos básicos de texto (sin usar el diccionario todavía)
            if not nombre or not categoria_nombre or not talla or not precio_compra:
                st.error("Rellena los campos Obligatorios (*)")
            else:
                with st.spinner("💾 Procesando..."):
                    # Lógica de Categoría: Verificar si existe o crearla
                    # Usamos .get() para evitar el KeyError si es una categoría nueva
                    categoria_id = categoria_opciones.get(categoria_nombre)

                    if categoria_id is None:
                        # Si no existe en el diccionario, intentamos insertarla
                        exito_cat = db.insertar_categoria(categoria_nombre)
                        if exito_cat:
                            # Recuperamos el ID recién creado
                            busqueda = db.get_categorias(categoria_nombre)
                            if busqueda and len(busqueda) > 0:
                                categoria_id = busqueda[0]['id']
                            else:
                                st.error(f"❌ No se encontró la categoría '{categoria_nombre}' tras crearla.")
                                st.stop()
                        else:
                            st.error("❌ Error al crear la nueva categoría")
                            st.stop()

                    # Preparar datos para el disfraz
                    datos_disfraz = {
                        'nombre': nombre,
                        'descripcion': descripcion,
                        'categoria_id': categoria_id,
                        'talla': talla,
                        'genero': genero,
                        'stock_total': stock_total,
                        'stock_disponible': stock_total,
                        'costo_compra': precio_compra,
                        'estado_conservacion': estado_conservacion,
                        'notas': notas,
                        'activo': True
                    }

                    # Insertar Disfraz
                    if db.insertar_disfraz(datos_disfraz):
                        st.success(f"✅ Disfraz '{nombre}' agregado exitosamente")
                        st.balloons()
                        st.session_state.form_reset_counter += 1
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar el disfraz en la base de datos")
        if cancelar:
            # Incrementar el contador para resetear el formulario
            st.session_state.form_reset_counter += 1
            st.rerun()