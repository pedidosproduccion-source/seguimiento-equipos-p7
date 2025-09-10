import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import xlsxwriter

# --- Configuración de la aplicación y archivos de datos ---
st.set_page_config(layout="wide", page_title="Seguimiento de Equipos")

DATABASE_FILE = "avance_equipos.json"
TERMINADOS_FILE = "equipos_terminados.json"

def cargar_datos(archivo):
    """Carga los datos de un archivo JSON."""
    if os.path.exists(archivo):
        with open(archivo, 'r', encoding='utf-8') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}

def guardar_datos(datos, archivo):
    """Guarda los datos en un archivo JSON."""
    with open(archivo, 'w', encoding='utf-8') as file:
        json.dump(datos, file, indent=4, ensure_ascii=False)

def calcular_porcentaje_total(equipo):
    """Calcula el porcentaje total de un equipo."""
    porcentajes = list(equipo.get('componentes', {}).values())
    return round(sum(porcentajes) / len(porcentajes)) if porcentajes else 0

def get_color_porcentaje(porcentaje):
    """Devuelve un color basado en el porcentaje."""
    if porcentaje == 100:
        return "#22C55E"  # Verde
    if porcentaje >= 50:
        return "#F97316"  # Naranja
    return "#EF4444"  # Rojo

# --- Inicialización del estado de la sesión ---
if 'equipos' not in st.session_state:
    st.session_state.equipos = cargar_datos(DATABASE_FILE)
if 'terminados' not in st.session_state:
    st.session_state.terminados = cargar_datos(TERMINADOS_FILE)
if 'editando' not in st.session_state:
    st.session_state.editando = None
if 'mostrar_terminados' not in st.session_state:
    st.session_state.mostrar_terminados = False

# --- Lógica de la interfaz de usuario ---
st.title("🚧 Seguimiento y Avance de Equipos")

# Mensaje de bienvenida y de ayuda
st.info("¡Bienvenido! Usa la barra lateral para registrar o editar equipos. En la sección principal verás el progreso de todos tus proyectos.")

# --- Sidebar para el formulario y opciones ---
with st.sidebar:
    st.header("📝 Opciones")

    # Botón para cambiar entre ver equipos activos y terminados
    if st.session_state.mostrar_terminados:
        if st.button("⏪ Volver a Equipos Activos"):
            st.session_state.mostrar_terminados = False
            st.rerun()
    else:
        if st.button("📦 Ver Historial de Terminados"):
            st.session_state.mostrar_terminados = True
            st.rerun()

    st.markdown("---")
    st.header("📝 Registrar/Editar Equipo")

    equipo_a_editar = None
    if st.session_state.editando:
        equipo_a_editar = st.session_state.equipos.get(st.session_state.editando)

    with st.form(key='registro_form', clear_on_submit=False):
        nombre_equipo = st.text_input(
            "Nombre del Equipo",
            value=equipo_a_editar['nombre'] if equipo_a_editar else ""
        )
        st.markdown("### Porcentaje de Avance:")
        componentes_sliders = {}
        componentes_lista = [
            "Sistema Eléctrico", "Sistema Neumático", "Sistema de Frenos",
            "Acabados", "Emblemas", "Hidráulico", "Accesorios"
        ]

        for comp in componentes_lista:
            valor_inicial = equipo_a_editar['componentes'].get(comp, 0) if equipo_a_editar and 'componentes' in equipo_a_editar else 0
            componentes_sliders[comp] = st.slider(
                comp, 0, 100,
                value=valor_inicial,
                key=f"slider_{st.session_state.editando}_{comp.replace(' ', '_')}"
            )

        comentarios = st.text_area(
            "Comentarios",
            value=equipo_a_editar.get('comentarios', '') if equipo_a_editar else ""
        )

        submit_button_text = "Actualizar Equipo" if st.session_state.editando else "Registrar Equipo"
        submitted = st.form_submit_button(submit_button_text)

        if submitted:
            if not nombre_equipo:
                st.warning("El nombre del equipo es obligatorio.")
            else:
                data = {
                    'nombre': nombre_equipo,
                    'componentes': componentes_sliders,
                    'comentarios': comentarios,
                    'ultima_actualizacion': datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                }
                if st.session_state.editando:
                    st.session_state.equipos[st.session_state.editando].update(data)
                    st.success("✅ Equipo actualizado con éxito.")
                else:
                    equipo_id = str(len(st.session_state.equipos) + 1)
                    data['id'] = equipo_id
                    st.session_state.equipos[equipo_id] = data
                    st.success("✅ Equipo registrado con éxito.")

                guardar_datos(st.session_state.equipos, DATABASE_FILE)
                st.session_state.editando = None
                st.rerun()

    # Botón para cancelar la edición
    if st.session_state.editando:
        if st.button("🚫 Cancelar Edición"):
            st.session_state.editando = None
            st.rerun()

    st.markdown("---")
    st.header("Exportar Datos")
    # Lógica para exportar a Excel
    if st.button("📊 Exportar a Excel"):
        data_para_df = []
        for equipo_data in st.session_state.equipos.values():
            fila = {
                "ID": equipo_data.get('id'),
                "Nombre del Equipo": equipo_data.get('nombre'),
                "Porcentaje Total": calcular_porcentaje_total(equipo_data),
                "Comentarios": equipo_data.get('comentarios', ''),
                "Última Actualización": equipo_data.get('ultima_actualizacion', 'N/A')
            }
            for comp, porc in equipo_data.get('componentes', {}).items():
                fila[comp] = porc
            data_para_df.append(fila)

        if data_para_df:
            df = pd.DataFrame(data_para_df)
            output = pd.ExcelWriter('avance_equipos.xlsx', engine='xlsxwriter')
            df.to_excel(output, index=False, sheet_name='Avance de Equipos')
            output.close()
            with open('avance_equipos.xlsx', 'rb') as f:
                st.download_button(
                    label="Descargar archivo",
                    data=f,
                    file_name="avance_equipos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("No hay datos para exportar.")

# --- Vista principal ---
if st.session_state.mostrar_terminados:
    st.header("📦 Historial de Equipos Terminados")
    equipos_a_mostrar = st.session_state.terminados
    if not equipos_a_mostrar:
        st.info("Aún no hay equipos en el historial de terminados.")
else:
    st.header("📋 Equipos en Proceso")
    
    # Campo de búsqueda
    filtro_nombre = st.text_input("🔍 Buscar equipo por nombre")
    
    equipos_a_mostrar = st.session_state.equipos
    if filtro_nombre:
        equipos_a_mostrar = {
            id: equipo for id, equipo in st.session_state.equipos.items()
            if filtro_nombre.lower() in equipo['nombre'].lower()
        }

    if not equipos_a_mostrar:
        st.info("No se encontraron equipos o aún no hay equipos registrados. Usa el formulario de la barra lateral.")
    else:
        # Gráfica del avance total
        df_equipos = pd.DataFrame(list(equipos_a_mostrar.values()))
        if not df_equipos.empty:
            df_equipos['Porcentaje Total'] = df_equipos.apply(calcular_porcentaje_total, axis=1)
            st.subheader("Avance General de Proyectos")
            st.bar_chart(df_equipos.set_index('nombre')[['Porcentaje Total']])

        # --- Visualización de la lista de equipos con expanders ---
        for equipo_id, equipo_data in equipos_a_mostrar.items():
            total_porcentaje = calcular_porcentaje_total(equipo_data)
            
            with st.expander(f"**{equipo_data['nombre']}** - Avance: **{total_porcentaje}%**"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    # Barras de progreso por componente
                    for comp, porc in equipo_data.get('componentes', {}).items():
                        color_barra_comp = get_color_porcentaje(porc)
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 5px;">
                            <span style="font-size: 12px; width: 120px;">{comp}:</span>
                            <div style="width: 100%; height: 6px; background-color: #e0e0e0; border-radius: 3px; overflow: hidden;">
                                <div style="width: {porc}%; height: 100%; background-color: {color_barra_comp};"></div>
                            </div>
                            <span style="font-size: 12px; font-weight: bold; margin-left: 5px;">{porc}%</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    if equipo_data.get('comentarios'):
                        st.caption(f"**Comentarios:** {equipo_data['comentarios']}")
                    st.caption(f"*Última actualización: {equipo_data.get('ultima_actualizacion', 'N/A')}*")
                
                with col2:
                    # Botones de acción
                    if st.button("✏️ Editar", key=f"edit_{equipo_id}"):
                        st.session_state.editando = equipo_id
                        st.rerun()
                    
                    if st.button("🗑️ Eliminar", key=f"delete_{equipo_id}"):
                        if st.session_state.editando == equipo_id:
                            st.session_state.editando = None  # Cierra el formulario si se elimina el equipo que se estaba editando
                        del st.session_state.equipos[equipo_id]
                        guardar_datos(st.session_state.equipos, DATABASE_FILE)
                        st.success("❌ Equipo eliminado con éxito.")
                        st.rerun()
                    
                    if st.button("✅ Terminado", key=f"done_{equipo_id}"):
                        if st.session_state.editando == equipo_id:
                            st.session_state.editando = None
                        
                        # Mover el equipo al archivo de terminados
                        equipo_a_terminar = st.session_state.equipos.pop(equipo_id)
                        st.session_state.terminados[equipo_id] = equipo_a_terminar
                        guardar_datos(st.session_state.equipos, DATABASE_FILE)
                        guardar_datos(st.session_state.terminados, TERMINADOS_FILE)
                        st.success("🎉 Equipo marcado como terminado y archivado.")
                        st.rerun()