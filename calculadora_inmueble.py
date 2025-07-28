import streamlit as st
import math

st.set_page_config(page_title="Calculadora de inversión inmobiliaria", layout="centered")

st.markdown("""
<style>
.big-title { font-size: 2.2em; font-weight: 800; text-align: center; margin-bottom: 0.15em; margin-top: 0.4em;}
.step-header {font-size: 1.5em; font-weight: bold; color: #4CAF50;}
.block-title { font-size: 1.13em; font-weight: bold; color: #207ca5; margin-bottom: 0.3em; margin-top:0.2em;}
.block-box { border: 2px solid #e7e8fa; border-radius: 10px; background: #f8fafb; padding: 1.1em 1.2em 0.8em 1.2em; margin-bottom: 1.2em;}
</style>
""", unsafe_allow_html=True)

def calcular_resultados(
    precio_compra, reformas, comision_agencia, alquiler_mes, entrada, tin,
    hipoteca_anos, irpf_marginal, valor_construccion_pct, gastos_compra, itp_iva,
    seguro_impago, impuesto_basuras, seguro_hogar, seguro_vida,
    comunidad, ibi, mantenimiento, vacio_pct, aplica_reduccion_60
):
    inversion_inicial = entrada + reformas + comision_agencia + gastos_compra + itp_iva

    capital_prestamo = precio_compra - entrada
    tipo_interes_mensual = tin / 100 / 12
    total_cuotas = hipoteca_anos * 12
    cuota_mensual = (
        capital_prestamo * tipo_interes_mensual / (1 - (1 + tipo_interes_mensual) ** (-total_cuotas))
        if tin > 0 else capital_prestamo / total_cuotas
    )
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

if "step" not in st.session_state:
    st.session_state.step = 1

def format_number(val):
    # Formatea siempre con separador de miles y sin decimales
    return f"{val:,.0f} €".replace(",", ".")  # Si quieres punto como separador de miles

def cambiar_paso(paso):
    st.session_state.step = paso
    st.rerun()

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

    # BLOQUE 1: DATOS DE COMPRA
    st.markdown("<div class='block-box'>", unsafe_allow_html=True)
    st.markdown("<span class='block-title'>1. Datos de compra</span>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        precio_compra = st.number_input(
            "Precio de compra (€)", min_value=50000, max_value=1000000, value=200000,
            help="Precio total de compra del piso (sin reformas)."
        )
        reformas = st.number_input(
            "Reformas/arreglos (€)", min_value=0, max_value=500000, value=15000,
            help="Coste estimado de reformas necesarias para alquilar."
        )

    with col2:
        comision_agencia = st.number_input(
            "Comisión agencia (€)", min_value=0, max_value=100000, value=0,
            help="Coste pagado a la agencia, si existe."
        )
        alquiler_mes = st.number_input(
            "Renta mensual (€)", min_value=200, max_value=5000, value=1100,
            help="Alquiler mensual estimado tras la reforma."
        )
    
    alquiler_tipo = st.radio(
    "¿El alquiler será de la vivienda entera o solo habitaciones?",
    ["Vivienda entera de residencia habitual", "Habitaciones o no residencia habitual"],
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
            "Entrada pagada (€)", min_value=0, max_value=1000000, value=40000,
            help="Dinero que pagas al principio (normalmente 20% del precio de compra)."
        )
        tin = st.number_input(
            "TIN hipotecario (%)", min_value=0.1, max_value=10.0, value=2.8, step=0.01,
            help="Tipo de interés nominal anual de la hipoteca. Según el BDE, en 2025 está alrededor del 2.8% pero puede variar según perfil y banco."
        )
    with col2:
        hipoteca_anos = st.number_input(
            "Años de hipoteca", min_value=5, max_value=40, value=25, step=1,
            help="Duración del préstamo hipotecario en años (lo habitual son entre 20 y 30)."
        )
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
        gastos_compra_pct = st.number_input(
            "Gastos notario, registro, tasación, gestoría (% sobre compra)", min_value=0.5, max_value=4.0, value=2.0, step=0.1,
            help="Normalmente entre 1% y 2% del precio de compra total."
        )
        gastos_compra = precio_compra * gastos_compra_pct / 100
    with col2:
        itp_iva_pct = st.number_input(
            "ITP o IVA (% sobre compra)", min_value=4.0, max_value=15.0, value=8.0, step=0.1,
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
            "Tipo marginal IRPF (%)", min_value=0.0, max_value=55.0, value=25.0,
            help="Tu tipo marginal de IRPF. Consulta el tramo que te corresponde."
        )
    with col2:
        valor_construccion_pct = st.number_input(
            "Valor construcción (% sobre compra)", min_value=10, max_value=90, value=30,
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
            "Seguro de impago (€)", min_value=0, max_value=5000, value=230,
            help="Seguro que cubre el impago de la renta por parte del inquilino."
        )
        impuesto_basuras = st.number_input(
            "Impuesto de basuras (€)", min_value=0, max_value=1000, value=100,
            help="Tasa municipal por la recogida de residuos urbanos."
        )
        seguro_hogar = st.number_input(
            "Seguro de hogar (€)", min_value=0, max_value=2000, value=200,
            help="Seguro de daños sobre la vivienda alquilada."
        )
        seguro_vida = st.number_input(
            "Seguro de vida (€)", min_value=0, max_value=2000, value=100,
            help="Seguro de vida vinculado a la hipoteca (opcional o según banco)."
        )
    with col2:
        comunidad = st.number_input(
            "Gastos de comunidad (€)", min_value=0, max_value=3000, value=240,
            help="Cuota anual de la comunidad de vecinos."
        )
        ibi = st.number_input(
            "IBI (€)", min_value=0, max_value=3000, value=200,
            help="Impuesto sobre Bienes Inmuebles municipal."
        )
        mantenimiento = st.number_input(
            "Mantenimiento y pequeñas reparaciones (€)", min_value=0, max_value=3000, value=480,
            help="Estimación de averías, fontanería, pintura, etc."
        )
        vacio = st.number_input(
            "Periodos vacíos (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.5,
            help="Porcentaje estimado de meses que el piso estará vacío al año (por rotación de inquilino, reformas, etc)."
        )
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Calcular resultados ➡️"):
        st.session_state.inputs = {
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

    st.markdown("---")
    st.info("Puedes volver atrás y ajustar cualquier dato para analizar otros escenarios.")

    if st.button("⬅️ Analizar otro escenario", key="restart"):
        cambiar_paso(2)
