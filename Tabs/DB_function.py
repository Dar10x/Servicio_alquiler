import streamlit as st
from supabase import create_client, Client
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


def init_connection() -> Client:
    """
    Inicializa y retorna la conexión a Supabase.
    """
    
    # Intentar obtener credenciales de Streamlit secrets
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    
    # Validar que existan las credenciales
    if not url or not key:
        raise ValueError(
            "❌ Credenciales de Supabase no configuradas.\n\n"
            "Por favor configura SUPABASE_URL y SUPABASE_KEY en:\n"
            "- .streamlit/secrets.toml, o\n"
        )
    
    # Crear y retornar cliente
    try:
        supabase: Client = create_client(url, key)
        return supabase
    
    except Exception as e:
        raise ConnectionError(f"❌ Error al conectar con Supabase: {str(e)}")


# Inicializar conexión global
# Esta variable será importada por otros módulos: from db_connection import supabase
try:
    supabase = init_connection()
    print("✅ Conexión a Supabase establecida exitosamente")
except Exception as e:
    print(f"❌ Error al inicializar Supabase: {str(e)}")
    supabase = None


# ============================================================================
# FUNCIONES AUXILIARES DE BASE DE DATOS (OPCIONAL)
# ============================================================================

def test_connection() -> bool:
    """
    Prueba la conexión a Supabase ejecutando una query simple.
    
    Returns:
        bool: True si la conexión funciona, False en caso contrario
    """
    try:
        # Intentar listar las categorías como test
        response = supabase.table('categorias').select('*').limit(1).execute()
        print("✅ Test de conexión exitoso")
        return True
    
    except Exception as e:
        print(f"❌ Test de conexión falló: {str(e)}")
        return False


def get_table_info(table_name: str) -> dict:
    """
    Obtiene información básica de una tabla.
    
    Args:
        table_name: Nombre de la tabla
    
    Returns:
        dict: Información de la tabla
    """
    try:
        response = supabase.table(table_name).select('*').limit(1).execute()
        
        return {
            'table': table_name,
            'exists': True,
            'sample_record': response.data[0] if response.data else None
        }
    
    except Exception as e:
        return {
            'table': table_name,
            'exists': False,
            'error': str(e)
        }


if __name__ == "__main__":
    """
    Ejecutar este archivo directamente para probar la conexión
    """
    print("\n" + "="*60)
    print("PROBANDO CONEXIÓN A SUPABASE")
    print("="*60 + "\n")
    
    if supabase:
        print("✅ Cliente de Supabase inicializado")
        
        # Probar conexión
        if test_connection():
            print("\n✅ Conexión verificada exitosamente")
            
            # Mostrar info de tablas principales
            print("\nInformación de tablas:")
            for tabla in ['categorias', 'clientes', 'disfraces', 'alquileres']:
                info = get_table_info(tabla)
                if info['exists']:
                    print(f"  ✅ {tabla}: OK")
                else:
                    print(f"  ❌ {tabla}: Error - {info.get('error', 'Desconocido')}")
        else:
            print("\n❌ No se pudo verificar la conexión")
    else:
        print("❌ No se pudo inicializar el cliente de Supabase")
    
    print("\n" + "="*60)

# ==============================
# FUNCIONES DE BASE DE DATOS
# ==============================

@st.cache_data(ttl=30)
def get_inventraio_disponibilidad() -> pd.DataFrame:
    try:
        response = supabase.table('inventario_disponibilidad').select('*').execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            return df
        return pd.DataFrame()
    
    except Exception as e:
        st.error(f"❌ Error al obtener inventario: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def get_alquileres_activos() -> pd.DataFrame:
    """Obtiene los alquileres activos usando la vista"""
    try:
        response = supabase.table('alquileres_activos').select('*').execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            # Convertir fechas a datetime para mejor visualización
            if 'fecha_salida' in df.columns:
                df['fecha_salida'] = pd.to_datetime(df['fecha_salida'])
            if 'fecha_retorno_prevista' in df.columns:
                df['fecha_retorno_prevista'] = pd.to_datetime(df['fecha_retorno_prevista'])
            return df
        return pd.DataFrame()
    
    except Exception as e:
        st.error(f"❌ Error al obtener alquileres activos: {str(e)}")
        return pd.DataFrame()
    
def marcar_como_retornado(alquiler_id: str) -> bool:
    """
    Marca un alquiler como retornado.
    El trigger de la BD actualizará automáticamente el stock.
    """
    try:
        response = supabase.table('alquileres').update({
            'estado': 'retornado',
            'fecha_retorno_real': datetime.now().isoformat(),
            'deposito_devuelto': True
        }).eq('id', alquiler_id).execute()
        
        return True
    
    except Exception as e:
        st.error(f"❌ Error al marcar como retornado: {str(e)}")
        return False


@st.cache_data(ttl=60)
def get_categorias() -> List[Dict]:
    """Obtiene todas las categorías activas"""
    try:
        response = supabase.table('categorias').select('*').eq('activo', True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"❌ Error al obtener categorías: {str(e)}")
        return []


@st.cache_data(ttl=60)
def get_clientes_activos() -> List[Dict]:
    """Obtiene todos los clientes activos"""
    try:
        response = supabase.table('clientes').select('*').eq('activo', True).order('apellido').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"❌ Error al obtener clientes: {str(e)}")
        return []


@st.cache_data(ttl=60)
def get_disfraces_disponibles() -> List[Dict]:
    """Obtiene disfraces activos con stock disponible"""
    try:
        response = supabase.table('disfraces').select('*').eq('activo', True).gt('stock_disponible', 0).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"❌ Error al obtener disfraces: {str(e)}")
        return []


def verificar_stock_disponible(disfraz_id: str, cantidad_solicitada: int) -> tuple[bool, int]:
    """
    Verifica si hay stock suficiente para un alquiler.
    Retorna: (tiene_stock: bool, stock_actual: int)
    """
    try:
        response = supabase.table('disfraces').select('stock_disponible').eq('id', disfraz_id).single().execute()
        
        if response.data:
            stock_actual = response.data['stock_disponible']
            tiene_stock = stock_actual >= cantidad_solicitada
            return tiene_stock, stock_actual
        
        return False, 0
    
    except Exception as e:
        st.error(f"❌ Error al verificar stock: {str(e)}")
        return False, 0


def crear_alquiler(datos_alquiler: Dict) -> bool:
    """
    Crea un nuevo registro de alquiler.
    El trigger de la BD actualizará automáticamente el stock.
    """
    try:
        response = supabase.table('alquileres').insert(datos_alquiler).execute()
        return True
    
    except Exception as e:
        st.error(f"❌ Error al crear alquiler: {str(e)}")
        return False


def insertar_disfraz(datos_disfraz: Dict) -> bool:
    """Inserta un nuevo disfraz en el inventario"""
    try:
        response = supabase.table('disfraces').insert(datos_disfraz).execute()
        return True
    
    except Exception as e:
        st.error(f"❌ Error al insertar disfraz: {str(e)}")
        return False


# ============================================================================
# FUNCIONES DE GESTIÓN DE CLIENTES (NUEVO)
# ============================================================================

def buscar_cliente_por_dni(dni: str) -> Optional[Dict]:
    """
    Busca un cliente por DNI.
    Retorna el cliente si existe, None si no existe.
    """
    if not dni or dni.strip() == "":
        return None
    
    try:
        response = supabase.table('clientes').select('*').eq('dni', dni.strip()).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    
    except Exception as e:
        st.error(f"❌ Error al buscar cliente por DNI: {str(e)}")
        return None


def buscar_cliente_por_email(email: str) -> Optional[Dict]:
    """
    Busca un cliente por email.
    Retorna el cliente si existe, None si no existe.
    """
    if not email or email.strip() == "":
        return None
    
    try:
        response = supabase.table('clientes').select('*').eq('email', email.strip().lower()).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    
    except Exception as e:
        st.error(f"❌ Error al buscar cliente por email: {str(e)}")
        return None


def verificar_duplicados_cliente(dni: str = None, email: str = None, excluir_id: str = None) -> Dict[str, Any]:
    """
    Verifica si existe un cliente con el DNI o email proporcionado.
    
    Args:
        dni: DNI a verificar
        email: Email a verificar
        excluir_id: ID del cliente a excluir de la búsqueda (para actualizaciones)
    
    Returns:
        Dict con:
        - existe_duplicado: bool
        - campo_duplicado: 'dni' | 'email' | None
        - cliente_existente: Dict | None
    """
    resultado = {
        'existe_duplicado': False,
        'campo_duplicado': None,
        'cliente_existente': None
    }
    
    # Verificar DNI
    if dni and dni.strip() != "":
        cliente_dni = buscar_cliente_por_dni(dni)
        if cliente_dni and (not excluir_id or cliente_dni['id'] != excluir_id):
            resultado['existe_duplicado'] = True
            resultado['campo_duplicado'] = 'dni'
            resultado['cliente_existente'] = cliente_dni
            return resultado
    
    # Verificar Email
    if email and email.strip() != "":
        cliente_email = buscar_cliente_por_email(email)
        if cliente_email and (not excluir_id or cliente_email['id'] != excluir_id):
            resultado['existe_duplicado'] = True
            resultado['campo_duplicado'] = 'email'
            resultado['cliente_existente'] = cliente_email
            return resultado
    
    return resultado


def crear_cliente(datos_cliente: Dict) -> tuple[bool, Optional[str], Optional[Dict]]:
    """
    Crea un nuevo cliente en la base de datos.
    
    Returns:
        tuple: (exito: bool, mensaje: str, cliente_creado: Dict | None)
    """
    try:
        # Verificar duplicados antes de insertar
        verificacion = verificar_duplicados_cliente(
            dni=datos_cliente.get('dni'),
            email=datos_cliente.get('email')
        )
        
        if verificacion['existe_duplicado']:
            campo = verificacion['campo_duplicado']
            cliente_existente = verificacion['cliente_existente']
            
            mensaje = (
                f"⚠️ Ya existe un cliente con ese {campo.upper()}: "
                f"{cliente_existente['nombre']} {cliente_existente['apellido']} "
                f"(Tel: {cliente_existente['telefono']})"
            )
            
            return False, mensaje, cliente_existente
        
        # Insertar cliente
        response = supabase.table('clientes').insert(datos_cliente).execute()
        
        if response.data and len(response.data) > 0:
            return True, "✅ Cliente creado exitosamente", response.data[0]
        else:
            return False, "❌ Error al crear cliente", None
    
    except Exception as e:
        error_msg = str(e).lower()
        
        # Detectar violaciones de restricción única
        if 'unique' in error_msg or 'duplicate' in error_msg:
            if 'dni' in error_msg:
                return False, "❌ Ya existe un cliente con ese DNI", None
            elif 'email' in error_msg:
                return False, "❌ Ya existe un cliente con ese Email", None
        
        return False, f"❌ Error al crear cliente: {str(e)}", None


def actualizar_cliente(cliente_id: str, datos_actualizados: Dict) -> tuple[bool, str]:
    """
    Actualiza los datos de un cliente existente.
    
    Returns:
        tuple: (exito: bool, mensaje: str)
    """
    try:
        # Verificar duplicados excluyendo el cliente actual
        verificacion = verificar_duplicados_cliente(
            dni=datos_actualizados.get('dni'),
            email=datos_actualizados.get('email'),
            excluir_id=cliente_id
        )
        
        if verificacion['existe_duplicado']:
            campo = verificacion['campo_duplicado']
            return False, f"❌ Ya existe otro cliente con ese {campo.upper()}"
        
        # Actualizar cliente
        response = supabase.table('clientes').update(datos_actualizados).eq('id', cliente_id).execute()
        
        return True, "✅ Cliente actualizado exitosamente"
    
    except Exception as e:
        return False, f"❌ Error al actualizar cliente: {str(e)}"


def buscar_clientes_por_texto(texto_busqueda: str) -> List[Dict]:
    """
    Busca clientes por nombre, apellido, DNI, teléfono o email.
    Retorna una lista de clientes que coinciden con la búsqueda.
    """
    if not texto_busqueda or texto_busqueda.strip() == "":
        return get_clientes_activos()
    
    try:
        texto = texto_busqueda.strip().lower()
        
        # Obtener todos los clientes activos
        clientes = get_clientes_activos()
        
        # Filtrar por coincidencia en múltiples campos
        resultados = []
        for cliente in clientes:
            nombre_completo = f"{cliente.get('nombre', '')} {cliente.get('apellido', '')}".lower()
            dni = str(cliente.get('dni', '')).lower()
            telefono = str(cliente.get('telefono', '')).lower()
            email = str(cliente.get('email', '')).lower()
            
            if (texto in nombre_completo or 
                texto in dni or 
                texto in telefono or 
                texto in email):
                resultados.append(cliente)
        
        return resultados
    
    except Exception as e:
        st.error(f"❌ Error al buscar clientes: {str(e)}")
        return []
