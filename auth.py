import streamlit as st
import bcrypt
from typing import Optional, Dict
from Tabs.DB_function import supabase


# ============================================================================
# FUNCIONES DE AUTENTICACIÓN
# ============================================================================

def hash_password(password: str) -> str:
    """
    Genera un hash de la contraseña usando bcrypt.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifica si la contraseña coincide con el hash.
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        print(f"Error verificando contraseña: {e}")
        return False


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """
    Autentica un usuario con su username y password.
    
    Returns:
        Dict con datos del usuario si la autenticación es exitosa, None si falla
    """
    try:
        # Buscar usuario por username
        response = supabase.table('usuarios').select('*').eq('username', username).eq('activo', True).execute()
        
        if not response.data or len(response.data) == 0:
            return None
        
        usuario = response.data[0]
        
        # Verificar contraseña
        if verify_password(password, usuario['password_hash']):
            return {
                'id': usuario['id'],
                'username': usuario['username'],
                'nombre_completo': usuario['nombre_completo'],
                'rol': usuario['rol']
            }
        
        return None
    
    except Exception as e:
        st.error(f"❌ Error en autenticación: {str(e)}")
        return None


def crear_usuario_inicial(username: str, password: str, nombre_completo: str, rol: str) -> bool:
    """
    Crea un usuario en la base de datos con contraseña hasheada.
    Útil para crear usuarios iniciales.
    """
    try:
        password_hash = hash_password(password)
        
        datos_usuario = {
            'username': username,
            'password_hash': password_hash,
            'nombre_completo': nombre_completo,
            'rol': rol,
            'activo': True
        }
        
        response = supabase.table('usuarios').insert(datos_usuario).execute()
        
        if response.data:
            print(f"✅ Usuario {username} creado exitosamente")
            return True
        else:
            print(f"❌ Error al crear usuario {username}")
            return False
    
    except Exception as e:
        print(f"❌ Error al crear usuario: {str(e)}")
        return False


# ============================================================================
# GESTIÓN DE SESIÓN
# ============================================================================

def inicializar_sesion():
    """
    Inicializa las variables de sesión para autenticación.
    """
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None


def login_usuario(usuario: Dict):
    """
    Marca al usuario como autenticado en la sesión.
    """
    st.session_state.autenticado = True
    st.session_state.usuario = usuario


def logout_usuario():
    """
    Cierra la sesión del usuario.
    """
    st.session_state.autenticado = False
    st.session_state.usuario = None


def is_authenticated() -> bool:
    """
    Verifica si hay un usuario autenticado.
    """
    return st.session_state.get('autenticado', False)


def get_current_user() -> Optional[Dict]:
    """
    Obtiene los datos del usuario actual.
    """
    return st.session_state.get('usuario', None)


def is_admin() -> bool:
    """
    Verifica si el usuario actual es administrador.
    """
    usuario = get_current_user()
    if usuario:
        return usuario.get('rol') == 'admin'
    return False


def is_viewer() -> bool:
    """
    Verifica si el usuario actual es viewer (solo lectura).
    """
    usuario = get_current_user()
    if usuario:
        return usuario.get('rol') == 'viewer'
    return False


# ============================================================================
# COMPONENTES UI DE AUTENTICACIÓN
# ============================================================================

def mostrar_pagina_login():
    """
    Muestra la página de login.
    """
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background-color: #f8f9fa;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# 🎭 Sistema de Disfraces")
        st.markdown("### Iniciar Sesión")
        st.divider()
        
        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Ingresa tu usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
            
            submit = st.form_submit_button("🔐 Iniciar Sesión", use_container_width=True, type="primary")
            
            if submit:
                if not username or not password:
                    st.error("❌ Por favor ingresa usuario y contraseña")
                else:
                    with st.spinner("Verificando credenciales..."):
                        usuario = authenticate_user(username, password)
                        
                        if usuario:
                            login_usuario(usuario)
                            st.success(f"✅ Bienvenido {usuario['nombre_completo']}!")
                            st.rerun()
                        else:
                            st.error("❌ Usuario o contraseña incorrectos")
        
        st.divider()
        


def mostrar_info_usuario():
    """
    Muestra información del usuario en la sidebar.
    """
    usuario = get_current_user()
    
    if usuario:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**👤 Usuario:** {usuario['nombre_completo']}")
        
        if usuario['rol'] == 'admin':
            st.sidebar.markdown("**🔑 Rol:** Administrador")
            st.sidebar.success("Permisos completos")
        else:
            st.sidebar.markdown("**👁️ Rol:** Visualizador")
            st.sidebar.info("Solo lectura")
        
        if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
            logout_usuario()
            st.rerun()


# ============================================================================
# FUNCIÓN PRINCIPAL DE PROTECCIÓN
# ============================================================================

def require_auth():
    """
    Requiere autenticación. Si no está autenticado, muestra login.
    Esta función debe llamarse al inicio de la app.
    
    Returns:
        True si está autenticado, False si no (y muestra login)
    """
    inicializar_sesion()
    
    if not is_authenticated():
        mostrar_pagina_login()
        return False
    
    return True


