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
try:
    supabase = init_connection()
    print("✅ Conexión a Supabase establecida exitosamente")
except Exception as e:
    print(f"❌ Error al inicializar Supabase: {str(e)}")
    supabase = None


# ============================================================================
# FUNCIONES AUXILIARES DE BASE DE DATOS
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

def insertar_categoria(nombre: str) -> bool:
    """Inserta una nueva categoría en la base de datos"""
    try:
        datos_categoria = {
            'nombre': nombre,
            'activo': True
        }
        response = supabase.table('categorias').insert(datos_categoria).execute()
        return True
    
    except Exception as e:
        st.error(f"❌ Error al insertar categoría: {str(e)}")
        return False

def insertar_disfraz(datos_disfraz: Dict) -> bool:
    """Inserta un nuevo disfraz en el inventario"""
    try:
        response = supabase.table('disfraces').insert(datos_disfraz).execute()
        return True
    
    except Exception as e:
        st.error(f"❌ Error al insertar disfraz: {str(e)}")
        return False


def get_ventas_del_mes() -> float:
    """
    Retorna la suma total de los montos de alquiler del mes actual.
    """
    try:
        # Obtener el primer y último día del mes actual
        hoy = datetime.now()
        primer_dia_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calcular el último día del mes
        if hoy.month == 12:
            ultimo_dia_mes = hoy.replace(year=hoy.year + 1, month=1, day=1, hour=23, minute=59, second=59)
        else:
            ultimo_dia_mes = hoy.replace(month=hoy.month + 1, day=1, hour=23, minute=59, second=59)
        
        # Consultar alquileres del mes actual
        response = supabase.table('alquileres').select(
            'monto_alquiler'
        ).gte(
            'created_at', primer_dia_mes.isoformat()
        ).lte(
            'created_at', ultimo_dia_mes.isoformat()
        ).execute()
        
        if not response.data:
            return 0.0
        
        # Sumar todos los montos de alquiler
        total_ventas = sum(alquiler['monto_alquiler'] for alquiler in response.data)
        
        return round(total_ventas, 2)
    
    except Exception as e:
        st.error(f"❌ Error al obtener ventas del mes: {str(e)}")
        return 0.0


# ============================================================================
# FUNCIONES DE SOFT DELETE POR CANTIDAD DE STOCK
# ============================================================================
# Agregar estas funciones al archivo DB_function.py
# Reemplazan las funciones anteriores de soft delete

def soft_delete_stock_disfraz(disfraz_id: str, cantidad: int) -> tuple[bool, str]:
    """
    Desactiva una cantidad específica de stock de un disfraz.
    Reduce el stock_total y stock_disponible.
    
    Args:
        disfraz_id: UUID del disfraz
        cantidad: Cantidad de unidades a desactivar
    
    Returns:
        tuple: (exito: bool, mensaje: str)
    """
    try:
        # Obtener información actual del disfraz
        response = supabase.table('disfraces').select('*').eq('id', disfraz_id).single().execute()
        
        if not response.data:
            return False, "❌ Disfraz no encontrado"
        
        disfraz = response.data
        stock_total_actual = disfraz['stock_total']
        stock_disponible_actual = disfraz['stock_disponible']
        
        # Validaciones
        if cantidad <= 0:
            return False, "❌ La cantidad debe ser mayor a 0"
        
        if cantidad > stock_disponible_actual:
            return False, f"❌ No hay suficiente stock disponible. Disponible: {stock_disponible_actual}, Solicitado: {cantidad}"
        
        # Verificar alquileres activos
        unidades_alquiladas = stock_total_actual - stock_disponible_actual
        
        if cantidad > stock_disponible_actual:
            return False, f"❌ No se puede desactivar: {unidades_alquiladas} unidad(es) están actualmente alquiladas"
        
        # Calcular nuevos valores
        nuevo_stock_total = stock_total_actual - cantidad
        nuevo_stock_disponible = stock_disponible_actual - cantidad
        
        # Actualizar el disfraz
        response_update = supabase.table('disfraces').update({
            'stock_total': nuevo_stock_total,
            'stock_disponible': nuevo_stock_disponible,
            'updated_at': datetime.now().isoformat()
        }).eq('id', disfraz_id).execute()
        
        if response_update.data:
            # Si el stock total llega a 0, marcar como inactivo
            if nuevo_stock_total == 0:
                supabase.table('disfraces').update({
                    'activo': False
                }).eq('id', disfraz_id).execute()
                return True, f"✅ {cantidad} unidad(es) desactivada(s). Disfraz marcado como inactivo (stock = 0)"
            else:
                return True, f"✅ {cantidad} unidad(es) desactivada(s). Stock restante: {nuevo_stock_total}"
        else:
            return False, "❌ Error al actualizar el stock"
    
    except Exception as e:
        return False, f"❌ Error al desactivar stock: {str(e)}"


def reactivar_stock_disfraz(disfraz_id: str, cantidad: int) -> tuple[bool, str]:
    """
    Reactiva una cantidad específica de stock de un disfraz.
    Aumenta el stock_total y stock_disponible.
    
    Args:
        disfraz_id: UUID del disfraz
        cantidad: Cantidad de unidades a reactivar
    
    Returns:
        tuple: (exito: bool, mensaje: str)
    """
    try:
        # Obtener información actual del disfraz
        response = supabase.table('disfraces').select('*').eq('id', disfraz_id).single().execute()
        
        if not response.data:
            return False, "❌ Disfraz no encontrado"
        
        disfraz = response.data
        stock_total_actual = disfraz['stock_total']
        stock_disponible_actual = disfraz['stock_disponible']
        
        # Validaciones
        if cantidad <= 0:
            return False, "❌ La cantidad debe ser mayor a 0"
        
        # Calcular nuevos valores
        nuevo_stock_total = stock_total_actual + cantidad
        nuevo_stock_disponible = stock_disponible_actual + cantidad
        
        # Actualizar el disfraz
        response_update = supabase.table('disfraces').update({
            'stock_total': nuevo_stock_total,
            'stock_disponible': nuevo_stock_disponible,
            'activo': True,  # Asegurar que esté activo
            'updated_at': datetime.now().isoformat()
        }).eq('id', disfraz_id).execute()
        
        if response_update.data:
            return True, f"✅ {cantidad} unidad(es) reactivada(s). Stock total ahora: {nuevo_stock_total}"
        else:
            return False, "❌ Error al reactivar el stock"
    
    except Exception as e:
        return False, f"❌ Error al reactivar stock: {str(e)}"


def verificar_stock_para_desactivar(disfraz_id: str) -> tuple[bool, str, dict]:
    """
    Verifica el stock disponible para desactivar de un disfraz.
    
    Args:
        disfraz_id: UUID del disfraz
    
    Returns:
        tuple: (puede_desactivar: bool, mensaje: str, info: dict)
    """
    try:
        # Obtener info del disfraz
        response_disfraz = supabase.table('disfraces').select('*').eq('id', disfraz_id).single().execute()
        
        if not response_disfraz.data:
            return False, "❌ Disfraz no encontrado", {}
        
        disfraz = response_disfraz.data
        
        stock_total = disfraz['stock_total']
        stock_disponible = disfraz['stock_disponible']
        unidades_alquiladas = stock_total - stock_disponible
        
        # Verificar alquileres activos
        response_activos = supabase.table('alquileres').select('id, cantidad').eq(
            'disfraz_id', disfraz_id
        ).in_('estado', ['activo', 'reservado']).execute()
        
        alquileres_activos_count = len(response_activos.data) if response_activos.data else 0
        
        # Contar total de alquileres históricos
        response_total = supabase.table('alquileres').select('id').eq('disfraz_id', disfraz_id).execute()
        total_alquileres = len(response_total.data) if response_total.data else 0
        
        info = {
            'nombre': disfraz['nombre'],
            'stock_total': stock_total,
            'stock_disponible': stock_disponible,
            'unidades_alquiladas': unidades_alquiladas,
            'alquileres_activos_count': alquileres_activos_count,
            'total_alquileres': total_alquileres,
            'max_desactivable': stock_disponible
        }
        
        if stock_disponible == 0:
            return False, f"❌ No hay stock disponible para desactivar (todo está alquilado: {unidades_alquiladas} unidades)", info
        
        return True, f"✅ Puedes desactivar hasta {stock_disponible} unidad(es)", info
    
    except Exception as e:
        return False, f"❌ Error al verificar: {str(e)}", {}


@st.cache_data(ttl=30)
def get_disfraces_con_stock() -> pd.DataFrame:
    """
    Obtiene todos los disfraces activos con su información de stock.
    Incluye disfraces con stock_total > 0.
    
    Returns:
        DataFrame con disfraces activos
    """
    try:
        response = supabase.table('disfraces').select('*').eq('activo', True).gt('stock_total', 0).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Obtener nombres de categorías
            if not df.empty and 'categoria_id' in df.columns:
                categorias = get_categorias()
                cat_map = {cat['id']: cat['nombre'] for cat in categorias}
                df['categoria'] = df['categoria_id'].map(cat_map)
            
            return df
        
        return pd.DataFrame()
    
    except Exception as e:
        st.error(f"❌ Error al obtener disfraces: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=30)
def get_disfraces_todos_incluyendo_inactivos() -> pd.DataFrame:
    """
    Obtiene TODOS los disfraces (activos e inactivos) para poder reactivar stock.
    
    Returns:
        DataFrame con todos los disfraces
    """
    try:
        response = supabase.table('disfraces').select('*').execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Obtener nombres de categorías
            if not df.empty and 'categoria_id' in df.columns:
                categorias = get_categorias()
                cat_map = {cat['id']: cat['nombre'] for cat in categorias}
                df['categoria'] = df['categoria_id'].map(cat_map)
            
            return df
        
        return pd.DataFrame()
    
    except Exception as e:
        st.error(f"❌ Error al obtener disfraces: {str(e)}")
        return pd.DataFrame()
    
# ============================================================================
# FUNCIONES PARA EDITAR DISFRACES
# ============================================================================
# Agregar estas funciones al archivo DB_function.py

def get_disfraz_por_id(disfraz_id: str) -> Optional[Dict]:
    """
    Obtiene información completa de un disfraz por su ID.
    
    Args:
        disfraz_id: UUID del disfraz
    
    Returns:
        Dict con toda la información del disfraz o None si no existe
    """
    try:
        response = supabase.table('disfraces').select('*').eq('id', disfraz_id).single().execute()
        return response.data if response.data else None
    except Exception as e:
        st.error(f"❌ Error al obtener disfraz: {str(e)}")
        return None


def buscar_disfraces_por_nombre(texto_busqueda: str) -> List[Dict]:
    """
    Busca disfraces activos por nombre (búsqueda parcial).
    
    Args:
        texto_busqueda: Texto a buscar en el nombre del disfraz
    
    Returns:
        Lista de disfraces que coinciden con la búsqueda
    """
    try:
        if not texto_busqueda or texto_busqueda.strip() == "":
            # Si no hay búsqueda, retornar todos los disfraces activos
            response = supabase.table('disfraces').select('*').eq('activo', True).order('nombre').execute()
        else:
            # Búsqueda por nombre (case insensitive)
            response = supabase.table('disfraces').select('*').eq('activo', True).ilike('nombre', f'%{texto_busqueda}%').order('nombre').execute()
        
        return response.data if response.data else []
    
    except Exception as e:
        st.error(f"❌ Error al buscar disfraces: {str(e)}")
        return []


def actualizar_disfraz(disfraz_id: str, datos_actualizados: Dict) -> tuple[bool, str]:
    """
    Actualiza la información de un disfraz existente.
    
    Args:
        disfraz_id: UUID del disfraz a actualizar
        datos_actualizados: Diccionario con los campos a actualizar
    
    Returns:
        tuple: (exito: bool, mensaje: str)
    """
    try:
        # Agregar timestamp de actualización
        datos_actualizados['updated_at'] = datetime.now().isoformat()
        
        # Actualizar en la base de datos
        response = supabase.table('disfraces').update(datos_actualizados).eq('id', disfraz_id).execute()
        
        if response.data:
            return True, "✅ Disfraz actualizado exitosamente"
        else:
            return False, "❌ Error al actualizar el disfraz"
    
    except Exception as e:
        return False, f"❌ Error al actualizar disfraz: {str(e)}"


def validar_stock_para_edicion(disfraz_id: str, nuevo_stock_total: int) -> tuple[bool, str, int]:
    """
    Valida que el nuevo stock_total sea válido considerando las unidades alquiladas.
    
    Args:
        disfraz_id: UUID del disfraz
        nuevo_stock_total: Nuevo valor de stock_total propuesto
    
    Returns:
        tuple: (es_valido: bool, mensaje: str, unidades_alquiladas: int)
    """
    try:
        # Obtener información actual del disfraz
        disfraz = get_disfraz_por_id(disfraz_id)
        
        if not disfraz:
            return False, "❌ Disfraz no encontrado", 0
        
        stock_actual_total = disfraz['stock_total']
        stock_disponible = disfraz['stock_disponible']
        unidades_alquiladas = stock_actual_total - stock_disponible
        
        # Validar que el nuevo stock_total no sea menor que las unidades alquiladas
        if nuevo_stock_total < unidades_alquiladas:
            return False, f"❌ El stock total no puede ser menor que las unidades alquiladas ({unidades_alquiladas})", unidades_alquiladas
        
        # Validar que sea mayor a 0
        if nuevo_stock_total < 0:
            return False, "❌ El stock total debe ser mayor o igual a 0", unidades_alquiladas
        
        return True, f"✅ Stock válido. Unidades alquiladas: {unidades_alquiladas}", unidades_alquiladas
    
    except Exception as e:
        return False, f"❌ Error al validar stock: {str(e)}", 0


@st.cache_data(ttl=30)
def get_todos_disfraces_activos() -> List[Dict]:
    """
    Obtiene todos los disfraces activos sin filtro de stock.
    Útil para el editor de inventario.
    
    Returns:
        Lista de disfraces activos
    """
    try:
        response = supabase.table('disfraces').select('*').eq('activo', True).order('nombre').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"❌ Error al obtener disfraces: {str(e)}")
        return []