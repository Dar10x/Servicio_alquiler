import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict,List,Optional, Any
from Tabs.inventario_tab import render_tab_inventario
from Tabs.registro_tab import render_tab_registro

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
    st.markdown("""
    #  Sistema de Inventario de Alquiler de Disfraces
    ### Administracion completa de inventario y alquileres
    """)

    st.divider()

    # Crear los tabs
    tab1, tab2, tab3 = st.tabs([
        "Inventario y Alquileres",
        "Registrar Disfraz",
        "Nuevo Alquiler"
    ])

    with tab1:
        render_tab_inventario()
    
    


    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>Sistema de Gestión de Disfraces v1.0 | Powered by Streamlit + Supabase + Google Gemini</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()