import streamlit as st
from Tabs.inventario_tab import render_tab_inventario
from Tabs.registro_tab import render_tab_registro
from Tabs.alquiler_tab import render_tab_alquiler
from Tabs.delete_tab import render_tab_gestion_disfraces
from Tabs.editar_tab import render_tab_editar_inventario
import auth

st.set_page_config(
    page_title = "Gestion de Inventario Disfraces",
    page_icon = "🎭",
    layout= "wide",
    initial_sidebar_state = "expanded"
)

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 10px 20px;
        font-weight: 600;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
    }
    .success-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #28a745;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #dc3545;
    }
    </style>
""", unsafe_allow_html=True)


# ================================================
# MAIN
# ================================================

def main():
    # AUTENTICACIÓN - Proteger toda la aplicación
    if not auth.require_auth():
        return  # Si no está autenticado, solo muestra login
    
    # Mostrar información del usuario en sidebar
    auth.mostrar_info_usuario()
    
    st.markdown("""
    #  Sistema de Inventario de Alquiler de Disfraces
    ### Administracion completa de inventario y alquileres
    """)

    st.divider()

    # Crear los tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Inventario y Alquileres",
        "Registrar Disfraz",
        "Nuevo Alquiler",
        "Gestión de Disfraces",
        "Editar Inventario"
    ])

    with tab1:
        render_tab_inventario()
    
    with tab2:
        render_tab_registro()

    with tab3:
        render_tab_alquiler()
    
    with tab4:
        render_tab_gestion_disfraces()
    
    with tab5:
        render_tab_editar_inventario()

    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'> 
        <p>Sistema de Gestión de Disfraces | Powered by Streamlit + Supabase</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()