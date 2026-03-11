import streamlit as st
import pandas as pd
from typing import Dict,List,Optional, Any
from Tabs.DB_function import supabase
import Tabs.DB_function as db

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
        return db.get_clientes_activos()
    
    try:
        texto = texto_busqueda.strip().lower()
        
        # Obtener todos los clientes activos
        clientes = db.get_clientes_activos()
        
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
