import streamlit as st
import Tabs.Clientes_functions as cl
import Tabs.DB_function as db
from datetime import datetime, timedelta

def render_tab_alquiler():
    st.header("Nuevo Alquiler")

    if 'modo_cliente' not in st.session_state:
        st.session_state['modo_cliente'] = 'seleccionar'

    if 'cliente_seleccionado_id' not in st.session_state:
        st.session_state['cliente_seleccionado_id'] = None
    
    if 'cliente_datos_temp' not in st.session_state:
        st.session_state['cliente_datos_temp'] = {}

    st.subheader("👤 Paso 1: Seleccionar o Registrar Cliente")

    tab_buscar, tab_nuevo = st.tabs(["🔍 Buscar Cliente Existente", "➕ Registrar Nuevo Cliente"])

    with tab_buscar:
        st.markdown("**Busca un cliente por nombre, apellido, DNI, teléfono o email**")

        # Búsqueda inteligente
        col_search, col_btn = st.columns([4, 1])
        
        with col_search:
            texto_busqueda = st.text_input(
                "Buscar cliente",
                placeholder="Ej: Juan, 12345678, 987654321, juan@email.com",
                label_visibility="collapsed",
                key="busqueda_cliente"
            )
        
        with col_btn:
            buscar_btn = st.button("🔍 Buscar", use_container_width=True, type="primary")

        # Realizar búsqueda
        if buscar_btn or texto_busqueda:
            clientes_encontrados = cl.buscar_clientes_por_texto(texto_busqueda)
            
            if clientes_encontrados:
                st.success(f"✅ {len(clientes_encontrados)} cliente(s) encontrado(s)")
                
                # Mostrar clientes en un selectbox
                clientes_opciones = {
                    f"{c['nombre']} {c['apellido']} - DNI: {c.get('dni', 'N/A')} - Tel: {c['telefono']}": c
                    for c in clientes_encontrados
                }
                
                cliente_seleccionado_texto = st.selectbox(
                    "Selecciona un cliente",
                    options=list(clientes_opciones.keys()),
                    key="cliente_select"
                )
                
                cliente_seleccionado = clientes_opciones[cliente_seleccionado_texto]
                
                # Mostrar información del cliente seleccionado
                st.markdown("---")
                st.markdown("**📋 Información del Cliente:**")
                
                col_info1, col_info2, col_info3 = st.columns(3)
                
                with col_info1:
                    st.markdown(f"**Nombre:** {cliente_seleccionado['nombre']} {cliente_seleccionado['apellido']}")
                    st.markdown(f"**DNI:** {cliente_seleccionado.get('dni', 'N/A')}")
                
                with col_info2:
                    st.markdown(f"**Teléfono:** {cliente_seleccionado['telefono']}")
                    st.markdown(f"**Email:** {cliente_seleccionado.get('email', 'N/A')}")
                
                with col_info3:
                    st.markdown(f"**Dirección:** {cliente_seleccionado.get('direccion', 'N/A')}")
                    if cliente_seleccionado.get('notas'):
                        st.markdown(f"**Notas:** {cliente_seleccionado['notas']}")
                
                # Botón para usar este cliente
                if st.button("✅ Usar este Cliente", type="primary", use_container_width=True):
                    st.session_state['modo_cliente'] = 'seleccionar'
                    st.session_state['cliente_seleccionado_id'] = cliente_seleccionado['id']
                    st.session_state['cliente_datos_temp'] = cliente_seleccionado
                    st.success(f"✅ Cliente seleccionado: {cliente_seleccionado['nombre']} {cliente_seleccionado['apellido']}")
                    st.rerun()
            
            else:
                st.warning("⚠️ No se encontraron clientes con ese criterio de búsqueda")
                st.info("💡 Puedes registrar un nuevo cliente en la pestaña 'Registrar Nuevo Cliente'")
        
        else:
            # Mostrar todos los clientes si no hay búsqueda
            clientes = db.get_clientes_activos()
            
            if clientes:
                st.info(f"📋 {len(clientes)} clientes registrados. Usa el buscador para filtrar.")
            else:
                st.warning("⚠️ No hay clientes registrados. Registra uno en la pestaña 'Registrar Nuevo Cliente'")
    with tab_nuevo:
        st.markdown("**Registra un nuevo cliente en el sistema**")
        
        # Inicializar contador de reinicio si no existe
        if 'form_reset_counter' not in st.session_state:
            st.session_state.form_reset_counter = 0
        
        # Usar el contador para crear keys únicas cada vez que se reinicia
        reset_key = st.session_state.form_reset_counter
        
        with st.form(f"form_nuevo_cliente_{reset_key}", clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre_nuevo = st.text_input(
                    "Nombre *",
                    key=f"input_nombre_{reset_key}",
                    help="Nombre del cliente"
                )
                
                dni_nuevo = st.text_input(
                    "DNI *",
                    key=f"input_dni_{reset_key}",
                    help="Documento de identidad (debe ser único)"
                )
                
                telefono_nuevo = st.text_input(
                    "Teléfono *",
                    key=f"input_telefono_{reset_key}",
                    help="Teléfono de contacto"
                )
            
            with col2:
                apellido_nuevo = st.text_input(
                    "Apellido *",
                    key=f"input_apellido_{reset_key}",
                    help="Apellido del cliente"
                )
                
                email_nuevo = st.text_input(
                    "Email",
                    key=f"input_email_{reset_key}",
                    help="Email (opcional, debe ser único si se proporciona)"
                )
                
                direccion_nuevo = st.text_input(
                    "Dirección",
                    key=f"input_direccion_{reset_key}",
                    help="Dirección (opcional)"
                )
            
            notas_nuevo = st.text_area(
                "Notas",
                key=f"input_notas_{reset_key}",
                height=80,
                help="Observaciones adicionales (opcional)"
            )
            
            # Botones
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                submit_cliente = st.form_submit_button("💾 Registrar Cliente", type="primary", use_container_width=True)
            
            with col_btn2:
                cancelar_cliente = st.form_submit_button("❌ Limpiar", use_container_width=True)
            

            # Procesar formulario
            if submit_cliente:
                # Validar campos obligatorios
                if not nombre_nuevo or not apellido_nuevo or not dni_nuevo or not telefono_nuevo:
                    st.error("❌ Por favor completa todos los campos obligatorios (*)")
                else:
                    # Preparar datos del cliente
                    datos_cliente = {
                        'nombre': nombre_nuevo.strip(),
                        'apellido': apellido_nuevo.strip(),
                        'dni': dni_nuevo.strip(),
                        'telefono': telefono_nuevo.strip(),
                        'email': email_nuevo.strip().lower() if email_nuevo else None,
                        'direccion': direccion_nuevo.strip() if direccion_nuevo else None,
                        'notas': notas_nuevo.strip() if notas_nuevo else None,
                        'activo': True
                    }
                    
                    # Crear cliente
                    with st.spinner("💾 Registrando cliente..."):
                        exito, mensaje, cliente_creado = cl.crear_cliente(datos_cliente)
                        
                        if exito:
                            st.success(mensaje)
                            st.balloons()
                            
                            # Incrementar el contador para resetear el formulario
                            st.session_state.form_reset_counter += 1
                            
                            # Seleccionar automáticamente el cliente recién creado
                            st.session_state['modo_cliente'] = 'seleccionar'
                            st.session_state['cliente_seleccionado_id'] = cliente_creado['id']
                            st.session_state['cliente_datos_temp'] = cliente_creado
                            
                            # Limpiar cache
                            st.cache_data.clear()
                            
                            import time
                            time.sleep(1)
                            st.rerun()
                        
                        else:
                            # Mostrar error con opción de cargar cliente existente
                            st.error(mensaje)
                            
                            if cliente_creado:  # Si se encontró un cliente existente
                                st.markdown("---")
                                st.markdown("**¿Deseas usar el cliente existente en su lugar?**")
                                
                                col_info1, col_info2 = st.columns(2)
                                
                                with col_info1:
                                    st.markdown(f"**Nombre:** {cliente_creado['nombre']} {cliente_creado['apellido']}")
                                    st.markdown(f"**DNI:** {cliente_creado.get('dni', 'N/A')}")
                                
                                with col_info2:
                                    st.markdown(f"**Teléfono:** {cliente_creado['telefono']}")
                                    st.markdown(f"**Email:** {cliente_creado.get('email', 'N/A')}")
                                
                                if st.form_submit_button("✅ Sí, usar cliente existente", type="primary"):
                                    st.session_state['modo_cliente'] = 'seleccionar'
                                    st.session_state['cliente_seleccionado_id'] = cliente_creado['id']
                                    st.session_state['cliente_datos_temp'] = cliente_creado
                                    st.success(f"✅ Cliente cargado: {cliente_creado['nombre']} {cliente_creado['apellido']}")
                                    st.rerun()
            
            if cancelar_cliente:
                # Incrementar el contador para resetear el formulario
                st.session_state.form_reset_counter += 1
                st.rerun()

    if st.session_state.get('cliente_seleccionado_id'):
        st.divider()
        st.success(f"✅ Cliente seleccionado: {st.session_state['cliente_datos_temp']['nombre']} {st.session_state['cliente_datos_temp']['apellido']}")
        
        if st.button("🔄 Cambiar Cliente"):
            st.session_state['cliente_seleccionado_id'] = None
            st.session_state['cliente_datos_temp'] = {}
            st.rerun()
        
        st.divider()
        st.subheader("🎭 Paso 2: Datos del Alquiler")
        
        # Obtener datos necesarios
        disfraces = db.get_disfraces_disponibles()
        
        if not disfraces:
            st.error("❌ No hay disfraces disponibles para alquilar")
            st.stop()
        
        # Formulario de alquiler
        with st.form("form_nuevo_alquiler"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Selector de disfraz - SIN PRECIO EN LA DESCRIPCIÓN
                disfraz_opciones = {
                    f"{d['nombre']} (Talla: {d['talla']}) - Stock: {d['stock_disponible']}": d['id']
                    for d in disfraces
                }
                
                disfraz_seleccionado = st.selectbox(
                    "Disfraz *",
                    options=list(disfraz_opciones.keys()),
                    help="Selecciona el disfraz a alquilar"
                )
                disfraz_id = disfraz_opciones[disfraz_seleccionado]
                
                # Obtener datos del disfraz seleccionado
                disfraz_data = next(d for d in disfraces if d['id'] == disfraz_id)
                
                cantidad = st.number_input(
                    "Cantidad *",
                    min_value=1,
                    max_value=disfraz_data['stock_disponible'],
                    value=1,
                    help=f"Stock disponible: {disfraz_data['stock_disponible']}"
                )
            
            with col2:
                # Fechas
                fecha_salida = st.date_input(
                    "Fecha de Salida *",
                    value=datetime.now().date(),
                    help="Fecha en que se entrega el disfraz"
                )
                
                dias_alquiler = st.number_input(
                    "Días de Alquiler *",
                    min_value=1,
                    value=3,
                    help="Cantidad de días del alquiler"
                )
                
                fecha_retorno = fecha_salida + timedelta(days=dias_alquiler)
                st.info(f"📅 Fecha de retorno prevista: {fecha_retorno.strftime('%d/%m/%Y')}")
            
            # Datos de precio y pago
            col3, col4 = st.columns(2)
            
            with col3:
                # Precio por día definido en esta transacción
                precio_dia = st.number_input(
                    "Precio por Día ($) *",
                    min_value=0.0,
                    value=20.0,  # Valor sugerido por defecto
                    step=1.0,
                    help="Define el precio por día para este alquiler específico"
                )
                
                metodo_pago = st.selectbox(
                    "Método de Pago",
                    options=['Efectivo', 'Tarjeta', 'Transferencia', 'Otro'],
                    help="Forma de pago del cliente"
                )
            
            with col4:
                deposito_cobrado = st.number_input(
                    "Depósito Cobrado ($)",
                    min_value=0.0,
                    value=0.0,  # Sin valor por defecto
                    step=5.0,
                    help="Depósito cobrado al cliente para esta transacción"
                )
                
                notas = st.text_area(
                    "Notas",
                    height=100,
                    help="Observaciones adicionales"
                )
            
            # Calcular monto total automáticamente
            monto_total = precio_dia * dias_alquiler * cantidad

            # Calcular saldo restante
            saldo_restante = monto_total - deposito_cobrado
            
            # Mostrar resumen antes de guardar
            st.divider()
            st.subheader("📊 Resumen del Alquiler")
            
            col_res1, col_res2, col_res3 = st.columns(3)
            
            with col_res1:
                st.metric("Cliente", f"{st.session_state['cliente_datos_temp']['nombre']} {st.session_state['cliente_datos_temp']['apellido']}")
                st.metric("Disfraz", disfraz_data['nombre'])
            
            with col_res2:
                st.metric("Cantidad", cantidad)
                st.metric("Días", dias_alquiler)
                st.metric("Precio/Día", f"S/.{precio_dia:.2f}")
            
            with col_res3:
                st.metric("Monto Total", f"S/.{monto_total:.2f}")
                st.metric("Depósito", f"S/.{deposito_cobrado:.2f}")
                st.metric("Saldo Restante", f"S/.{saldo_restante:.2f}")
            
            st.divider()
            
            # Botones de acción
            col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])
            
            with col_btn1:
                guardar_datos = st.form_submit_button(
                    "💾 Guardar Datos del Alquiler",
                    type="secondary",
                    use_container_width=True,
                    help="Actualiza el resumen con los datos ingresados"
                )
            
            with col_btn2:
                submit_normal = st.form_submit_button(
                    "✅ Crear Alquiler",
                    type="primary",
                    use_container_width=True
                )
            
            with col_btn3:
                cancelar = st.form_submit_button(
                    "❌ Cancelar",
                    use_container_width=True
                )
            
            # Procesar botón "Guardar Datos del Alquiler"
            if guardar_datos:
                # Guardar los datos en session_state para actualizar las métricas
                st.session_state['resumen_alquiler'] = {
                    'disfraz_nombre': disfraz_data['nombre'],
                    'disfraz_id': disfraz_id,
                    'cantidad': cantidad,
                    'dias_alquiler': dias_alquiler,
                    'precio_dia': precio_dia,
                    'deposito_cobrado': deposito_cobrado,
                    'monto_total': monto_total,
                    'fecha_salida': fecha_salida,
                    'fecha_retorno': fecha_retorno,
                    'metodo_pago': metodo_pago,
                    'notas': notas
                }
                st.success("✅ Datos del alquiler guardados. Las métricas se han actualizado.")
                st.rerun()
            
            # Procesar envío del formulario para crear alquiler
            if submit_normal:
                # Validar stock disponible
                tiene_stock, stock_actual = db.verificar_stock_disponible(disfraz_id, cantidad)
                
                if not tiene_stock:
                    st.error(
                        f"❌ Stock insuficiente. Disponible: {stock_actual}, Solicitado: {cantidad}"
                    )
                else:
                    # Preparar datos del alquiler
                    datos_alquiler = {
                        'cliente_id': st.session_state['cliente_seleccionado_id'],
                        'disfraz_id': disfraz_id,
                        'cantidad': cantidad,
                        'fecha_salida': datetime.combine(fecha_salida, datetime.now().time()).isoformat(),
                        'fecha_retorno_prevista': datetime.combine(fecha_retorno, datetime.now().time()).isoformat(),
                        'estado': 'activo',  # Estado fijo: siempre 'activo'
                        'precio_alquiler_dia': precio_dia,
                        'monto_alquiler': monto_total,  # Usar el monto calculado
                        'deposito_cobrado': deposito_cobrado,
                        'metodo_pago': metodo_pago,
                        'notas': notas,
                        'deposito_devuelto': False
                    }
                    
                    # Crear alquiler
                    with st.spinner("💾 Creando alquiler..."):
                        if db.crear_alquiler(datos_alquiler):
                            st.success(
                                f"✅ Alquiler creado exitosamente para {st.session_state['cliente_datos_temp']['nombre']} {st.session_state['cliente_datos_temp']['apellido']}"
                            )
                            st.balloons()
                            
                            # Limpiar session state
                            st.session_state['cliente_seleccionado_id'] = None
                            st.session_state['cliente_datos_temp'] = {}
                            if 'resumen_alquiler' in st.session_state:
                                del st.session_state['resumen_alquiler']
                            
                            # Limpiar cache
                            st.cache_data.clear()
                            
                            # Esperar un momento antes de recargar
                            import time
                            time.sleep(1)
                            st.rerun()
            
            if cancelar:
                st.info("Formulario cancelado")
                st.session_state['cliente_seleccionado_id'] = None
                st.session_state['cliente_datos_temp'] = {}
                if 'resumen_alquiler' in st.session_state:
                    del st.session_state['resumen_alquiler']
                st.rerun()
    
    else:
        st.info("👆 Selecciona o registra un cliente para continuar con el alquiler")