import streamlit as st
import math
import json
from datetime import datetime
import pandas as pd
import os
import tempfile
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np

st.set_page_config(page_title="Calculadora de inversión inmobiliaria", layout="centered")

st.markdown("""
<style>
.big-title { 
    font-size: 2.2em; 
    font-weight: 800; 
    text-align: center; 
    margin-bottom: 0.15em; 
    margin-top: 0.4em;
}
.step-header {
    font-size: 1.5em; 
    font-weight: bold; 
    color: #4CAF50;
}
.block-title { 
    font-size: 1.13em; 
    font-weight: bold; 
    color: #207ca5; 
    margin-bottom: 0.3em; 
    margin-top:0.2em;
}
.block-box { 
    border: 2px solid #e7e8fa; 
    border-radius: 10px; 
    background: #f8fafb; 
    padding: 1.1em 1.2em 0.8em 1.2em; 
    margin-bottom: 1.2em;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
    .big-title { 
        font-size: 1.8em; 
        line-height: 1.2;
    }
    .step-header { 
        font-size: 1.3em; 
    }
    .block-box { 
        padding: 0.8em 1em 0.6em 1em; 
        margin-bottom: 1em;
    }
    /* Stack columns on mobile */
    .element-container .row-widget.stColumns {
        flex-direction: column !important;
    }
    .element-container .row-widget.stColumns > div {
        width: 100% !important;
        margin-bottom: 1rem;
    }
}

/* Better button styling */
.stButton > button {
    width: 100%;
    border-radius: 8px;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* Improved expander styling */
.streamlit-expanderHeader {
    font-weight: 600;
    border-radius: 8px;
}

/* Better spacing for mobile forms */
@media (max-width: 768px) {
    .stNumberInput > div > div > input {
        font-size: 16px; /* Prevents zoom on iOS */
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
}
</style>
""", unsafe_allow_html=True)

# Simplified persistence using file-based storage

def get_scenarios_file_path():
    """Get the path for scenarios file in temp directory"""
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, 'calculadora_inmueble_scenarios.json')

def load_scenarios_from_file():
    """Load scenarios from file"""
    try:
        file_path = get_scenarios_file_path()
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                scenarios = json.load(f)
                return scenarios
    except Exception as e:
        st.error(f"Error loading scenarios: {e}")
    return {}

def save_scenarios_to_file(scenarios):
    """Save scenarios to file"""
    try:
        file_path = get_scenarios_file_path()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(scenarios, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving scenarios: {e}")
        return False

# Validation functions
def validate_inputs(precio_compra, alquiler_mes, entrada, tin, hipoteca_anos):
    """Validate financial inputs and return error messages if any."""
    errors = []
    warnings = []
    
    # Critical validations (errors)
    if entrada > precio_compra:
        errors.append("⚠️ La entrada no puede ser mayor al precio de compra")
    
    if alquiler_mes * 12 < precio_compra * 0.03:
        errors.append("⚠️ El alquiler anual parece muy bajo comparado con el precio (< 3% anual)")
    
    if alquiler_mes * 12 > precio_compra * 0.20:
        errors.append("⚠️ El alquiler anual parece muy alto comparado con el precio (> 20% anual)")
    
    if tin < 0.5 or tin > 15:
        errors.append("⚠️ El tipo de interés parece fuera del rango normal (0.5% - 15%)")
    
    if hipoteca_anos < 5 or hipoteca_anos > 40:
        errors.append("⚠️ Los años de hipoteca están fuera del rango típico (5-40 años)")
    
    # Advisory validations (warnings)
    if entrada < precio_compra * 0.15:
        warnings.append("💡 Entrada menor al 15% puede requerir condiciones especiales del banco")
    
    if alquiler_mes * 12 < precio_compra * 0.05:
        warnings.append("💡 Rentabilidad bruta muy baja (< 5% anual)")
    
    if tin > 5:
        warnings.append("💡 Tipo de interés alto, considera negociar con otros bancos")
    
    return errors, warnings

def safe_calculate_mortgage(capital_prestamo, tin, hipoteca_anos):
    """Safely calculate mortgage payment with error handling."""
    try:
        if tin <= 0:
            return capital_prestamo / (hipoteca_anos * 12) if hipoteca_anos > 0 else 0
        
        tipo_interes_mensual = tin / 100 / 12
        total_cuotas = hipoteca_anos * 12
        
        if total_cuotas <= 0:
            return 0
            
        cuota_mensual = (
            capital_prestamo * tipo_interes_mensual / 
            (1 - (1 + tipo_interes_mensual) ** (-total_cuotas))
        )
        return cuota_mensual
    except (ZeroDivisionError, OverflowError, ValueError):
        return 0

def calcular_resultados(
    precio_compra, reformas, comision_agencia, alquiler_mes, entrada, tin,
    hipoteca_anos, irpf_marginal, valor_construccion_pct, gastos_compra, itp_iva,
    seguro_impago, impuesto_basuras, seguro_hogar, seguro_vida,
    comunidad, ibi, mantenimiento, vacio_pct, aplica_reduccion_60
):
    inversion_inicial = entrada + reformas + comision_agencia + gastos_compra + itp_iva

    capital_prestamo = precio_compra - entrada
    cuota_mensual = safe_calculate_mortgage(capital_prestamo, tin, hipoteca_anos)
    cuota_hipoteca_anual = cuota_mensual * 12

    ingresos_anuales = alquiler_mes * 12

    periodos_vacio = alquiler_mes * (vacio_pct / 100) * 12

    gastos_recurrentes = sum([
        seguro_impago, impuesto_basuras, seguro_hogar, seguro_vida,
        comunidad, ibi, mantenimiento, periodos_vacio
    ])

    gastos_anuales = gastos_recurrentes + cuota_hipoteca_anual

    valor_construccion = precio_compra * valor_construccion_pct / 100
    amortizacion_anual = valor_construccion * 0.03

    # Beneficio antes de impuestos y amortización
    beneficio_AI = ingresos_anuales - gastos_anuales
    beneficio_AI_amort = beneficio_AI - amortizacion_anual

    if aplica_reduccion_60:
    # Aplica reducción solo si corresponde (vivienda entera)
        deduccion_60residencia = beneficio_AI_amort * 0.6
        base_imponible = beneficio_AI_amort * 0.4
    else:
        deduccion_60residencia = 0
        base_imponible = beneficio_AI_amort

    irpf = max(base_imponible * (irpf_marginal / 100), 0)

    beneficio_DI = beneficio_AI - irpf

    rentabilidad_neta_real = beneficio_DI / inversion_inicial * 100 if inversion_inicial > 0 else 0


    # For visual breakdown
    gastos_dict = [
        ("Seguro impago", seguro_impago),
        ("Impuesto basuras", impuesto_basuras),
        ("Seguro hogar", seguro_hogar),
        ("Seguro vida", seguro_vida),
        ("Comunidad", comunidad),
        ("IBI", ibi),
        ("Mantenimiento", mantenimiento),
        ("Vacío (total)", periodos_vacio),
        ("Cuota hipoteca anual", cuota_hipoteca_anual)
    ]

    return {
        "inversion_inicial": inversion_inicial,
        "cuota_mensual": cuota_mensual,
        "cuota_hipoteca_anual": cuota_hipoteca_anual,
        "ingresos_anuales": ingresos_anuales,
        "gastos_recurrentes": gastos_recurrentes,
        "gastos_dict": gastos_dict,
        "gastos_anuales": gastos_anuales,
        "amortizacion_anual": amortizacion_anual,
        "beneficio_AI": beneficio_AI,
        "beneficio_AI_amort": beneficio_AI_amort,
        "base_imponible": base_imponible,
        "irpf": irpf,
        "beneficio_DI": beneficio_DI,
        "rentabilidad_neta_real": rentabilidad_neta_real
    }

# Chart creation functions
def create_profit_over_time_chart(data, results):
    """Create a chart showing annual profit over the mortgage period"""
    years = list(range(1, data['hipoteca_anos'] + 1))
    annual_profit = [results['beneficio_DI']] * len(years)
    cumulative_profit = np.cumsum(annual_profit)
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Beneficio Anual', 'Beneficio Acumulado'),
        vertical_spacing=0.1
    )
    
    # Annual profit
    fig.add_trace(
        go.Scatter(
            x=years, y=annual_profit,
            mode='lines+markers',
            name='Beneficio Anual',
            line=dict(color='#2E8B57', width=3),
            marker=dict(size=6)
        ),
        row=1, col=1
    )
    
    # Cumulative profit
    fig.add_trace(
        go.Scatter(
            x=years, y=cumulative_profit,
            mode='lines+markers',
            name='Beneficio Acumulado',
            line=dict(color='#1E90FF', width=3),
            marker=dict(size=6),
            fill='tonexty'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title="📈 Evolución de Beneficios a lo largo del tiempo",
        height=500,
        showlegend=False,
        template="plotly_white"
    )
    
    fig.update_yaxes(title_text="Euros (€)", tickformat=",")
    fig.update_xaxes(title_text="Años", row=2, col=1)
    
    return fig

def create_mortgage_breakdown_chart(data):
    """Create a chart showing mortgage payment breakdown over time"""
    capital_prestamo = data['precio_compra'] - data['entrada']
    monthly_rate = data['tin'] / 100 / 12
    total_payments = data['hipoteca_anos'] * 12
    monthly_payment = safe_calculate_mortgage(capital_prestamo, data['tin'], data['hipoteca_anos'])
    
    years = []
    principal_payments = []
    interest_payments = []
    remaining_balance = capital_prestamo
    
    for year in range(1, data['hipoteca_anos'] + 1):
        annual_principal = 0
        annual_interest = 0
        
        for month in range(12):
            if remaining_balance > 0:
                interest_payment = remaining_balance * monthly_rate
                principal_payment = monthly_payment - interest_payment
                
                annual_interest += interest_payment
                annual_principal += principal_payment
                remaining_balance -= principal_payment
        
        years.append(year)
        principal_payments.append(annual_principal)
        interest_payments.append(annual_interest)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=years,
        y=interest_payments,
        name='Intereses',
        marker_color='#FF6B6B'
    ))
    
    fig.add_trace(go.Bar(
        x=years,
        y=principal_payments,
        name='Capital',
        marker_color='#4ECDC4'
    ))
    
    fig.update_layout(
        title="🏦 Desglose de Pagos de Hipoteca (Capital vs Intereses)",
        xaxis_title="Años",
        yaxis_title="Euros (€)",
        barmode='stack',
        template="plotly_white",
        height=400
    )
    
    fig.update_yaxes(tickformat=",")
    
    return fig

def create_net_worth_chart(data, results):
    """Create a chart showing net worth evolution over time"""
    years = list(range(0, data['hipoteca_anos'] + 1))
    
    # Calculate property appreciation (assuming 2% annual)
    property_appreciation_rate = 0.02
    property_values = [data['precio_compra'] * (1 + property_appreciation_rate) ** year for year in years]
    
    # Calculate mortgage balance
    capital_prestamo = data['precio_compra'] - data['entrada']
    monthly_rate = data['tin'] / 100 / 12
    monthly_payment = safe_calculate_mortgage(capital_prestamo, data['tin'], data['hipoteca_anos'])
    
    mortgage_balances = [capital_prestamo]
    remaining_balance = capital_prestamo
    
    for year in range(1, data['hipoteca_anos'] + 1):
        for month in range(12):
            if remaining_balance > 0:
                interest_payment = remaining_balance * monthly_rate
                principal_payment = monthly_payment - interest_payment
                remaining_balance -= principal_payment
        mortgage_balances.append(max(0, remaining_balance))
    
    # Calculate net worth (property value - mortgage balance)
    net_worth = [prop_val - mortgage_bal for prop_val, mortgage_bal in zip(property_values, mortgage_balances)]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=years, y=property_values,
        mode='lines+markers',
        name='Valor Propiedad',
        line=dict(color='#32CD32', width=3),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=years, y=mortgage_balances,
        mode='lines+markers',
        name='Deuda Hipoteca',
        line=dict(color='#FF4500', width=3),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=years, y=net_worth,
        mode='lines+markers',
        name='Patrimonio Neto',
        line=dict(color='#1E90FF', width=4),
        marker=dict(size=8),
        fill='tonexty'
    ))
    
    fig.update_layout(
        title="💰 Evolución del Patrimonio Neto",
        xaxis_title="Años",
        yaxis_title="Euros (€)",
        template="plotly_white",
        height=500,
        hovermode='x unified'
    )
    
    fig.update_yaxes(tickformat=",")
    
    return fig

def create_expense_breakdown_chart(results):
    """Create a pie chart showing expense breakdown"""
    expenses = results['gastos_dict']
    
    # Filter out zero expenses and prepare data
    non_zero_expenses = [(name, value) for name, value in expenses if value > 0]
    
    if not non_zero_expenses:
        return None
    
    names, values = zip(*non_zero_expenses)
    
    # Custom colors for different expense types
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE']
    
    fig = go.Figure(data=[go.Pie(
        labels=names,
        values=values,
        hole=0.4,
        marker=dict(colors=colors[:len(names)]),
        textinfo='label+percent',
        textposition='outside'
    )])
    
    fig.update_layout(
        title="📊 Desglose de Gastos Anuales",
        template="plotly_white",
        height=500,
        showlegend=True
    )
    
    return fig

# Initialize session state
if "step" not in st.session_state:
    st.session_state.step = 1
if "saved_scenarios" not in st.session_state:
    # Load scenarios from file on first load
    st.session_state.saved_scenarios = load_scenarios_from_file()
if "current_scenario_name" not in st.session_state:
    st.session_state.current_scenario_name = ""

# Data persistence functions
def save_scenario(name, data):
    """Save current scenario to both session state and file."""
    scenario = {
        "data": data,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save to session state
    st.session_state.saved_scenarios[name] = scenario
    
    # Save all scenarios to file
    if save_scenarios_to_file(st.session_state.saved_scenarios):
        st.success(f"✅ Escenario '{name}' guardado correctamente")
    else:
        st.error(f"❌ Error guardando escenario '{name}'")

def load_scenario(name):
    """Load scenario from session state."""
    if name in st.session_state.saved_scenarios:
        return st.session_state.saved_scenarios[name]["data"]
    return None

def delete_scenario(name):
    """Delete scenario from both session state and file."""
    if name in st.session_state.saved_scenarios:
        del st.session_state.saved_scenarios[name]
        
        # Save updated scenarios to file
        if save_scenarios_to_file(st.session_state.saved_scenarios):
            st.success(f"🗑️ Escenario '{name}' eliminado")
        else:
            st.error(f"❌ Error eliminando escenario '{name}'")

def export_scenarios_json():
    """Export all scenarios as JSON."""
    return json.dumps(st.session_state.saved_scenarios, indent=2, ensure_ascii=False)

def format_number(val):
    # Formatea siempre con separador de miles y sin decimales
    return f"{val:,.0f} €".replace(",", ".")  # Si quieres punto como separador de miles

def cambiar_paso(paso):
    st.session_state.step = paso
    
    # If going back to step 2 from results (step 3), reset for new scenario
    if paso == 2 and st.session_state.get('step') == 3:
        reset_for_new_scenario()
    
    st.rerun()

def reset_for_new_scenario():
    """Reset form values and scenario name for a new analysis"""
    # Clear the current scenario name
    st.session_state.current_scenario_name = ""
    
    # Clear any loaded data
    if hasattr(st.session_state, 'loaded_data'):
        del st.session_state.loaded_data
    
    # Clear previous inputs
    if hasattr(st.session_state, 'inputs'):
        del st.session_state.inputs

total_steps = 3
step_labels = ["Inicio", "Datos inversión", "Resultados"]
progress_value = (st.session_state.step - 1) / (total_steps - 1)
st.markdown(f"""
<div style='width: 100%; display: flex; justify-content: space-between; margin-bottom:10px;'>
    {''.join([f"<div style='flex:1; text-align:center; font-weight:bold; {'color:#4CAF50;' if i+1 <= st.session_state.step else 'color:#ccc;'}'>{i+1}. {label}</div>" for i, label in enumerate(step_labels)])}
</div>
<div style='height: 15px; background: #ddd; border-radius: 7px; overflow: hidden;'>
  <div style='height: 100%; width: {progress_value*100}%; background: #4CAF50;'></div>
</div>
""", unsafe_allow_html=True)

if st.session_state.step == 1:
    st.markdown("<div class='big-title'>Calculadora de inversión inmobiliaria para alquiler</div>", unsafe_allow_html=True)
    st.markdown("""
Esta herramienta te ayuda a analizar la rentabilidad y el cashflow de invertir en un piso para alquilarlo en España, teniendo en cuenta todos los gastos, impuestos, hipoteca y supuestos realistas.

**¿Qué calcula esta herramienta?**  
- Capital real necesario (inversión inicial)
- Ingresos, gastos y beneficio anual antes y después de impuestos
- Rentabilidad neta real

> **Disclaimer:** Esta calculadora es educativa, no es asesoramiento financiero. Los resultados pueden variar según tu situación personal y la comunidad autónoma. Verifica siempre tus datos.
""")
    if st.button("🚀 Empezar análisis"):
        cambiar_paso(2)

elif st.session_state.step == 2:
    st.markdown("<div class='step-header'>Introduce los datos de tu inversión</div>", unsafe_allow_html=True)
    
    # Mandatory scenario naming section
    st.markdown("<div class='block-box'>", unsafe_allow_html=True)
    st.markdown("<span class='block-title'>📝 Nombre del escenario (Obligatorio)</span>", unsafe_allow_html=True)
    st.info("💾 Debes asignar un nombre a tu análisis antes de ver los resultados. Los escenarios se guardan automáticamente.")
    
    scenario_name = st.text_input(
        "Nombre del escenario*", 
        value=st.session_state.current_scenario_name, 
        placeholder="Ej: Piso Centro Madrid - 200k€",
        help="Este nombre te ayudará a identificar el análisis más tarde"
    )
    
    if scenario_name.strip():
        st.session_state.current_scenario_name = scenario_name.strip()
        st.success(f"✅ Escenario: '{scenario_name.strip()}'")
    else:
        st.warning("⚠️ Introduce un nombre para continuar")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Saved scenarios section
    if st.session_state.saved_scenarios:
        with st.expander("📁 Escenarios guardados", expanded=False):
            st.markdown("**Escenarios disponibles:**")
            for name, scenario in st.session_state.saved_scenarios.items():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.text(f"{name} ({scenario['timestamp']})")
                with col2:
                    if st.button("📂", key=f"load_{name}", help="Cargar escenario"):
                        loaded_data = load_scenario(name)
                        if loaded_data:
                            # Load data into session state for use below
                            st.session_state.loaded_data = loaded_data
                            st.session_state.current_scenario_name = name
                            st.rerun()
                with col3:
                    if st.button("🗑️", key=f"delete_{name}", help="Eliminar escenario"):
                        delete_scenario(name)
                        st.rerun()
            
            st.download_button(
                "📥 Exportar todos los escenarios (JSON)",
                data=export_scenarios_json(),
                file_name=f"escenarios_inmuebles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    # Load default values (either from loaded scenario or fresh defaults)
    loaded_data = getattr(st.session_state, 'loaded_data', {})
    
    # Default values for fresh scenario
    default_values = {
        'precio_compra': 200000,
        'reformas': 15000,
        'comision_agencia': 0,
        'alquiler_mes': 1100,
        'aplica_reduccion_60': True,
        'entrada': 40000,
        'tin': 2.8,
        'hipoteca_anos': 25,
        'irpf_marginal': 25.0,
        'valor_construccion_pct': 30,
        'seguro_impago': 230,
        'impuesto_basuras': 100,
        'seguro_hogar': 200,
        'seguro_vida': 100,
        'comunidad': 240,
        'ibi': 200,
        'mantenimiento': 480,
        'vacio': 5.0
    }
    
    # BLOQUE 1: DATOS DE COMPRA
    st.markdown("<div class='block-box'>", unsafe_allow_html=True)
    st.markdown("<span class='block-title'>1. Datos de compra</span>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        precio_compra = st.number_input(
            "Precio de compra (€)", min_value=50000, max_value=1000000, 
            value=loaded_data.get('precio_compra', default_values['precio_compra']),
            help="Precio total de compra del piso (sin reformas)."
        )
        reformas = st.number_input(
            "Reformas/arreglos (€)", min_value=0, max_value=500000, 
            value=loaded_data.get('reformas', default_values['reformas']),
            help="Coste estimado de reformas necesarias para alquilar."
        )

    with col2:
        comision_agencia = st.number_input(
            "Comisión agencia (€)", min_value=0, max_value=100000, 
            value=loaded_data.get('comision_agencia', default_values['comision_agencia']),
            help="Coste pagado a la agencia, si existe."
        )
        alquiler_mes = st.number_input(
            "Renta mensual (€)", min_value=200, max_value=5000, 
            value=loaded_data.get('alquiler_mes', default_values['alquiler_mes']),
            help="Alquiler mensual estimado tras la reforma."
        )
    
    default_alquiler_tipo = loaded_data.get('aplica_reduccion_60', default_values['aplica_reduccion_60'])
    alquiler_tipo = st.radio(
        "¿El alquiler será de la vivienda entera o solo habitaciones?",
        ["Vivienda entera de residencia habitual", "Habitaciones o no residencia habitual"],
        index=0 if default_alquiler_tipo else 1,
        help="Si alquilas solo habitaciones, la reducción del 60% en el IRPF no es aplicable por ley."
    )
    aplica_reduccion_60 = alquiler_tipo == "Vivienda entera de residencia habitual"
    st.markdown("</div>", unsafe_allow_html=True)

    # BLOQUE 2: DATOS HIPOTECA
    st.markdown("<div class='block-box'>", unsafe_allow_html=True)
    st.markdown("<span class='block-title'>2. Hipoteca</span>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        entrada = st.number_input(
            "Entrada pagada (€)", min_value=0, max_value=1000000, 
            value=loaded_data.get('entrada', default_values['entrada']),
            help="Dinero que pagas al principio (normalmente 20% del precio de compra)."
        )
        tin = st.number_input(
            "TIN hipotecario (%)", min_value=0.1, max_value=10.0, 
            value=loaded_data.get('tin', default_values['tin']), step=0.01,
            help="Tipo de interés nominal anual de la hipoteca. Según el BDE, en 2025 está alrededor del 2.8% pero puede variar según perfil y banco."
        )
    with col2:
        hipoteca_anos = st.number_input(
            "Años de hipoteca", min_value=5, max_value=40, 
            value=loaded_data.get('hipoteca_anos', default_values['hipoteca_anos']), step=1,
            help="Duración del préstamo hipotecario en años (lo habitual son entre 20 y 30)."
        )
        
        # Validation section
        errors, warnings = validate_inputs(precio_compra, alquiler_mes, entrada, tin, hipoteca_anos)
        
        if errors:
            for error in errors:
                st.error(error)
        if warnings:
            for warning in warnings:
                st.warning(warning)
        if precio_compra > 0 and tin > 0 and hipoteca_anos > 0 and entrada < precio_compra:
            capital_prestamo = precio_compra - entrada
            tipo_interes_mensual = tin / 100 / 12
            total_cuotas = hipoteca_anos * 12
            try:
                cuota_mensual = (
                    capital_prestamo * tipo_interes_mensual /
                    (1 - (1 + tipo_interes_mensual) ** (-total_cuotas))
                )
            except ZeroDivisionError:
                cuota_mensual = 0
        else:
            cuota_mensual = 0

        st.markdown(f"""
<div style='border-radius:10px; background:#f1f8ff; border:1.5px solid #dde4ee; padding:0.7em 1.1em; margin:0.6em 0 1.2em 0; color:#1762a6; font-size:1.07em;'>
    <b>Cuota mensual:</b> <span style='font-weight:900;font-size:1.16em;'>{cuota_mensual:,.0f} €</span>
</div>
""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # BLOQUE 3: IMPUESTOS Y GASTOS COMPRA
    st.markdown("<div class='block-box'>", unsafe_allow_html=True)
    st.markdown("<span class='block-title'>3. Impuestos y gastos de compra</span>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        # Calculate default percentage for gastos_compra
        if 'gastos_compra' in loaded_data and loaded_data['gastos_compra'] > 0:
            default_gastos_pct = loaded_data['gastos_compra'] / precio_compra * 100
        else:
            default_gastos_pct = 2.0
            
        gastos_compra_pct = st.number_input(
            "Gastos notario, registro, tasación, gestoría (% sobre compra)", min_value=0.5, max_value=4.0, 
            value=default_gastos_pct, step=0.1,
            help="Normalmente entre 1% y 2% del precio de compra total."
        )
        gastos_compra = precio_compra * gastos_compra_pct / 100
    with col2:
        # Calculate default percentage for ITP/IVA
        if 'itp_iva' in loaded_data and loaded_data['itp_iva'] > 0:
            default_itp_pct = loaded_data['itp_iva'] / precio_compra * 100
        else:
            default_itp_pct = 8.0
            
        itp_iva_pct = st.number_input(
            "ITP o IVA (% sobre compra)", min_value=4.0, max_value=15.0, 
            value=default_itp_pct, step=0.1,
            help="Porcentaje de impuesto aplicable (ITP en segunda mano o IVA en obra nueva)."
        )
        itp_iva = precio_compra * itp_iva_pct / 100
    st.markdown("</div>", unsafe_allow_html=True)

    # BLOQUE 4: DATOS FISCALES
    st.markdown("<div class='block-box'>", unsafe_allow_html=True)
    st.markdown("<span class='block-title'>4. Datos fiscales</span>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        irpf_marginal = st.number_input(
            "Tipo marginal IRPF (%)", min_value=0.0, max_value=55.0, 
            value=loaded_data.get('irpf_marginal', default_values['irpf_marginal']),
            help="Tu tipo marginal de IRPF. Consulta el tramo que te corresponde."
        )
    with col2:
        valor_construccion_pct = st.number_input(
            "Valor construcción (% sobre compra)", min_value=10, max_value=90, 
            value=loaded_data.get('valor_construccion_pct', default_values['valor_construccion_pct']),
            help="Por ley solo puedes deducir como amortización el 3% anual de la parte atribuida a construcción (habitual: 30%)."
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # BLOQUE 5: GASTOS ANUALES RECURRENTES
    st.markdown("<div class='block-box'>", unsafe_allow_html=True)
    st.markdown("<span class='block-title'>5. Gastos anuales recurrentes</span>", unsafe_allow_html=True)
    st.markdown("Ajusta los gastos anuales estimados de la vivienda. Si alguno no aplica a tu caso, déjalo en 0.")

    col1, col2 = st.columns(2)
    with col1:
        seguro_impago = st.number_input(
            "Seguro de impago (€)", min_value=0, max_value=5000, 
            value=loaded_data.get('seguro_impago', default_values['seguro_impago']),
            help="Seguro que cubre el impago de la renta por parte del inquilino."
        )
        impuesto_basuras = st.number_input(
            "Impuesto de basuras (€)", min_value=0, max_value=1000, 
            value=loaded_data.get('impuesto_basuras', default_values['impuesto_basuras']),
            help="Tasa municipal por la recogida de residuos urbanos."
        )
        seguro_hogar = st.number_input(
            "Seguro de hogar (€)", min_value=0, max_value=2000, 
            value=loaded_data.get('seguro_hogar', default_values['seguro_hogar']),
            help="Seguro de daños sobre la vivienda alquilada."
        )
        seguro_vida = st.number_input(
            "Seguro de vida (€)", min_value=0, max_value=2000, 
            value=loaded_data.get('seguro_vida', default_values['seguro_vida']),
            help="Seguro de vida vinculado a la hipoteca (opcional o según banco)."
        )
    with col2:
        comunidad = st.number_input(
            "Gastos de comunidad (€)", min_value=0, max_value=3000, 
            value=loaded_data.get('comunidad', default_values['comunidad']),
            help="Cuota anual de la comunidad de vecinos."
        )
        ibi = st.number_input(
            "IBI (€)", min_value=0, max_value=3000, 
            value=loaded_data.get('ibi', default_values['ibi']),
            help="Impuesto sobre Bienes Inmuebles municipal."
        )
        mantenimiento = st.number_input(
            "Mantenimiento y pequeñas reparaciones (€)", min_value=0, max_value=3000, 
            value=loaded_data.get('mantenimiento', default_values['mantenimiento']),
            help="Estimación de averías, fontanería, pintura, etc."
        )
        vacio = st.number_input(
            "Periodos vacíos (%)", min_value=0.0, max_value=100.0, 
            value=loaded_data.get('vacio', default_values['vacio']), step=0.5,
            help="Porcentaje estimado de meses que el piso estará vacío al año (por rotación de inquilino, reformas, etc)."
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Clear loaded data after use
    if hasattr(st.session_state, 'loaded_data'):
        del st.session_state.loaded_data
    
    # Single button that requires scenario name
    if st.button("📊 Calcular resultados ➡️", type="primary"):
        # Check if scenario name is provided
        if not st.session_state.current_scenario_name.strip():
            st.error("❌ Debes introducir un nombre para el escenario antes de continuar")
            st.stop()
        
        # Final validation before calculation
        errors, _ = validate_inputs(precio_compra, alquiler_mes, entrada, tin, hipoteca_anos)
        
        if errors:
            st.error("❌ Por favor, corrige los errores antes de continuar:")
            for error in errors:
                st.error(error)
        else:
            # Prepare data for storage
            current_inputs = {
                "aplica_reduccion_60": aplica_reduccion_60,
                "precio_compra": precio_compra,
                "reformas": reformas,
                "comision_agencia": comision_agencia,
                "alquiler_mes": alquiler_mes,
                "entrada": entrada,
                "tin": tin,
                "hipoteca_anos": hipoteca_anos,
                "gastos_compra": gastos_compra,
                "itp_iva": itp_iva,
                "irpf_marginal": irpf_marginal,
                "valor_construccion_pct": valor_construccion_pct,
                "seguro_impago": seguro_impago,
                "impuesto_basuras": impuesto_basuras,
                "seguro_hogar": seguro_hogar,
                "seguro_vida": seguro_vida,
                "comunidad": comunidad,
                "ibi": ibi,
                "mantenimiento": mantenimiento,
                "vacio": vacio
            }
            
            st.session_state.inputs = current_inputs
            
            # Always save scenario before proceeding
            save_scenario(st.session_state.current_scenario_name, current_inputs)
            
            cambiar_paso(3)

    if st.button("⬅️ Volver", key="input_back"):
        cambiar_paso(1)


elif st.session_state.step == 3:
    d = st.session_state.inputs
    aplica_reduccion_60 = d['aplica_reduccion_60']

    res = calcular_resultados(
        d['precio_compra'], d['reformas'], d['comision_agencia'], d['alquiler_mes'], d['entrada'],
        d['tin'], d['hipoteca_anos'], d['irpf_marginal'], d['valor_construccion_pct'], d['gastos_compra'], d['itp_iva'],
        d['seguro_impago'], d['impuesto_basuras'], d['seguro_hogar'], d['seguro_vida'],
        d['comunidad'], d['ibi'], d['mantenimiento'], d['vacio'], aplica_reduccion_60
    )

    # Variables para formato y desglose
    inv = res["inversion_inicial"]
    income = res["ingresos_anuales"]
    expenses_list = res["gastos_dict"]
    expenses_total = res["gastos_anuales"]
    amort = res["amortizacion_anual"]
    net_before_tax = res["beneficio_AI"]
    net_before_tax_amort = net_before_tax - amort

    if aplica_reduccion_60:
        reduc_60 = net_before_tax_amort * 0.6
        base_sujeta = net_before_tax_amort * 0.4
    else:
        reduc_60 = 0
        base_sujeta = net_before_tax_amort

    tax = res["irpf"]
    net_after_tax = res["beneficio_DI"]
    rentabilidad_neta = res["rentabilidad_neta_real"]

    # --------- BLOQUE DETALLE HTML SIN SANGRÍA ---------
    calculo_detalle = f"""
<div style="border-radius:13px;background:#f8fbff;border:2.2px solid #dde4ee;padding:1.35em 1.3em 1.05em 1.3em; margin-bottom:1.25em; color:#1a2635; font-size:1.07em; box-shadow:0 4px 16px #dde4ee3c;">
<b style='color:#232323;font-size:1.11em;'>Cálculo del beneficio anual después de impuestos:</b>
<ul style="margin:0.4em 0 0.2em 1.3em;padding:0;">
<li>= Beneficio antes de impuestos: <b>{format_number(net_before_tax)}</b></li>
<li>- Amortización anual deducible: <b>{format_number(amort)}</b></li>
<li>= Base imponible fiscal: <b>{format_number(net_before_tax_amort)}</b></li>"""

    if aplica_reduccion_60:
        calculo_detalle += f"""
<li>- Reducción del 60% vivienda habitual: <b>{format_number(net_before_tax_amort)} x 60% = {format_number(reduc_60)}</b></li>
<li>= Base sujeta a IRPF: <b>{format_number(base_sujeta)}</b></li>
"""
    else:
        calculo_detalle += f"""
<li><span style='color:#a90000; font-weight:600;'>No se aplica reducción del 60% porque el alquiler es de habitaciones o no es vivienda habitual.</span></li>
<li>= Base sujeta a IRPF: <b>{format_number(base_sujeta)}</b></li>
"""

    calculo_detalle += f"""
<li>x Tipo marginal IRPF: <b>{d['irpf_marginal']:.1f} %</b></li>
<li>= IRPF estimado: <b>{format_number(tax)}</b></li>
<li>= Beneficio anual después de impuestos: <b>{format_number(net_after_tax)}</b></li>
</ul>
</div>
"""

    # --- RESULTADOS PRINCIPALES ---
    resultado_html = f"""
<div style="border-radius:14px;background:#f9faff;border:2px solid #dde4ee;padding:1.5em 1.5em 0.6em 1.5em;margin-bottom:1.2em;">
<div style="font-size:1.15em;font-weight:700;color:#15539c;">
💼 <b>Total inversión inicial:</b> <span style='float:right;font-size:1.17em;color:#205520;'>{format_number(inv)}</span>
</div>
</div>
<div style="border-radius:14px;background:#e8f9f2;border:2px solid #c2e3d6;padding:1.1em 1.4em 0.7em 1.4em;margin-bottom:0.9em;">
<div style="font-weight:600;color:#1762a6;">
📈 <b>Ingresos anuales por alquiler:</b> <span style='float:right;font-size:1.13em;color:#1762a6;'>{format_number(income)}</span>
</div>
</div>
<div style="border-radius:14px;background:#fff6ee;border:2px solid #ffe2c2;padding:1.1em 1.4em 0.8em 1.4em;margin-bottom:0.7em;">
<div style="font-weight:650;color:#232323;font-size:1.11em;margin-bottom:0.13em;">Gastos anuales desglosados:</div>
<ul style="margin:0.3em 0 0.2em 0.7em;padding:0; color:#b35a18;">
{''.join([f"<li>{name}: <b>{format_number(val)}</b></li>" for name, val in expenses_list])}
</ul>
<div style="font-weight:650;color:#b35a18;margin-top:0.6em;">Total gastos anuales: <span style="float:right;color:#b35a18;font-size:1.07em;font-weight:800;">{format_number(expenses_total)}</span></div>
</div>
<div style="border-radius:12px;background:#fffef4;border:2px solid #ffeabf;padding:1.1em 1.2em 0.8em 1.2em; margin-bottom:1.1em;">
<b style='color:#9a7700;font-size:1.09em;'>Rentabilidad anual antes de impuestos:</b>
<span style='float:right;color:#ad860a;font-weight:700;font-size:1.14em;'>{format_number(net_before_tax)}</span>
<div style='color:#333; font-size:0.98em; margin-top:0.18em;'>Es el beneficio anual antes de impuestos y amortización.</div>
</div>
"""

    st.markdown(resultado_html, unsafe_allow_html=True)
    st.markdown(calculo_detalle, unsafe_allow_html=True)

    st.markdown(f"""
<div style="border-radius:12px;background:#f1ffec;border:2px solid #d8f8cc;padding:1.1em 1.2em 0.8em 1.2em;">
<b style='color:#237319;font-size:1.12em;'>Beneficio anual neto:</b>
<span style='float:right;color:#167c2d;font-weight:900;font-size:1.20em;'>{format_number(net_after_tax)}</span>
</div>
<div style="margin:1.1em 0 0.7em 0; color:#2c566e; font-weight:500;">
<b>Rentabilidad neta sobre la inversión inicial:</b> {rentabilidad_neta:.2f} %
</div>
""", unsafe_allow_html=True)

    # Charts section
    st.markdown("---")
    st.markdown("### 📊 Análisis Visual")
    
    # Create tabs for different charts
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Patrimonio Neto", "📈 Beneficios", "🏦 Hipoteca", "📊 Gastos"])
    
    with tab1:
        st.markdown("**Evolución del patrimonio neto a lo largo del tiempo**")
        st.info("💡 Asume una revalorización del inmueble del 2% anual")
        try:
            net_worth_chart = create_net_worth_chart(d, res)
            st.plotly_chart(net_worth_chart, use_container_width=True)
        except Exception as e:
            st.error(f"Error creando gráfico de patrimonio: {e}")
    
    with tab2:
        st.markdown("**Beneficios anuales y acumulados durante el período de hipoteca**")
        try:
            profit_chart = create_profit_over_time_chart(d, res)
            st.plotly_chart(profit_chart, use_container_width=True)
            
            # Show key metrics
            total_years = d['hipoteca_anos']
            total_profit = res['beneficio_DI'] * total_years
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Beneficio Total", f"{total_profit:,.0f} €")
            with col2:
                st.metric("Promedio Anual", f"{res['beneficio_DI']:,.0f} €")
            with col3:
                roi_total = (total_profit / res['inversion_inicial']) * 100
                st.metric("ROI Total", f"{roi_total:.1f}%")
        except Exception as e:
            st.error(f"Error creando gráfico de beneficios: {e}")
    
    with tab3:
        st.markdown("**Desglose de pagos de hipoteca: capital vs intereses**")
        try:
            mortgage_chart = create_mortgage_breakdown_chart(d)
            st.plotly_chart(mortgage_chart, use_container_width=True)
            
            # Show mortgage totals
            monthly_payment = safe_calculate_mortgage(d['precio_compra'] - d['entrada'], d['tin'], d['hipoteca_anos'])
            total_payments = monthly_payment * 12 * d['hipoteca_anos']
            total_interest = total_payments - (d['precio_compra'] - d['entrada'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Pagado", f"{total_payments:,.0f} €")
            with col2:
                st.metric("Total Intereses", f"{total_interest:,.0f} €")
        except Exception as e:
            st.error(f"Error creando gráfico de hipoteca: {e}")
    
    with tab4:
        st.markdown("**Distribución de gastos anuales**")
        try:
            expense_chart = create_expense_breakdown_chart(res)
            if expense_chart:
                st.plotly_chart(expense_chart, use_container_width=True)
            else:
                st.info("No hay gastos para mostrar en el gráfico")
        except Exception as e:
            st.error(f"Error creando gráfico de gastos: {e}")

    # Comparison tool
    st.markdown("---")
    st.markdown("### 📊 Herramientas adicionales")
    
    with st.expander("🔍 Comparar con otros escenarios", expanded=False):
        if len(st.session_state.saved_scenarios) > 1:
            scenario_names = list(st.session_state.saved_scenarios.keys())
            selected_scenarios = st.multiselect(
                "Selecciona escenarios para comparar:",
                scenario_names,
                default=scenario_names[:min(3, len(scenario_names))]
            )
            
            if len(selected_scenarios) > 1:
                comparison_data = []
                for scenario_name in selected_scenarios:
                    scenario_data = st.session_state.saved_scenarios[scenario_name]["data"]
                    scenario_results = calcular_resultados(
                        scenario_data['precio_compra'], scenario_data['reformas'], 
                        scenario_data['comision_agencia'], scenario_data['alquiler_mes'], 
                        scenario_data['entrada'], scenario_data['tin'], scenario_data['hipoteca_anos'], 
                        scenario_data['irpf_marginal'], scenario_data['valor_construccion_pct'], 
                        scenario_data['gastos_compra'], scenario_data['itp_iva'],
                        scenario_data['seguro_impago'], scenario_data['impuesto_basuras'], 
                        scenario_data['seguro_hogar'], scenario_data['seguro_vida'],
                        scenario_data['comunidad'], scenario_data['ibi'], scenario_data['mantenimiento'], 
                        scenario_data['vacio'], scenario_data['aplica_reduccion_60']
                    )
                    
                    comparison_data.append({
                        "Escenario": scenario_name,
                        "Precio compra": f"{scenario_data['precio_compra']:,.0f} €",
                        "Alquiler mensual": f"{scenario_data['alquiler_mes']:,.0f} €",
                        "Inversión inicial": f"{scenario_results['inversion_inicial']:,.0f} €",
                        "Beneficio anual": f"{scenario_results['beneficio_DI']:,.0f} €",
                        "Rentabilidad (%)": f"{scenario_results['rentabilidad_neta_real']:.2f}%",
                        "Cuota hipoteca": f"{scenario_results['cuota_mensual']:,.0f} €/mes"
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, use_container_width=True)
                
                # Download comparison as CSV
                csv = comparison_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Descargar comparación (CSV)",
                    csv,
                    f"comparacion_escenarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
        else:
            st.info("Guarda más escenarios para poder compararlos")
    

    st.markdown("---")
    st.info("Puedes volver atrás y ajustar cualquier dato para analizar otros escenarios.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 Nuevo análisis", key="restart"):
            cambiar_paso(2)
    with col2:
        if st.button("🏠 Volver al inicio", key="home"):
            cambiar_paso(1)
