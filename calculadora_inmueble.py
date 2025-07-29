import streamlit as st
import math

st.set_page_config(page_title="Calculadora de inversión inmobiliaria", layout="centered")

st.markdown("""
<style>
.big-title { font-size: 2.2em; font-weight: 800; text-align: center; margin-bottom: 0.15em; margin-top: 0.4em;}
.block-title { font-size: 1.13em; font-weight: bold; color: #207ca5; margin-bottom: 0.3em; margin-top:0.2em;}
.block-box { border: 2px solid #e7e8fa; border-radius: 10px; background: #f8fafb; padding: 1.1em 1.2em 0.8em 1.2em; margin-bottom: 1.2em;}
</style>
""", unsafe_allow_html=True)

def calcular_resultados(
    precio_compra, reformas, comision_agencia, alquiler_mes, entrada, tin,
    hipoteca_anos, irpf_marginal, valor_construccion_pct, gastos_compra, itp_iva,
    seguro_impago, impuesto_basuras, seguro_hogar, seguro_vida,
    comunidad, ibi, mantenimiento, vacio_pct, aplica_reduccion_60,
    revalorizacion_pct, anos_reval
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
        deduccion_60residencia = beneficio_AI_amort * 0.6
        base_imponible = beneficio_AI_amort * 0.4
    else:
        deduccion_60residencia = 0
        base_imponible = beneficio_AI_amort

    irpf = max(base_imponible * (irpf_marginal / 100), 0)

    beneficio_DI = beneficio_AI - irpf

    rentabilidad_neta_real = beneficio_DI / inversion_inicial * 100 if inversion_inicial > 0 else 0
    rentabilidad_bruta = beneficio_AI / inversion_inicial * 100 if inversion_inicial > 0 else 0

    # Revalorización
    valor_futuro = precio_compra * ((1 + revalorizacion_pct / 100) ** anos_reval)
    plusvalia_bruta = valor_futuro - precio_compra

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
        "rentabilidad_neta_real": rentabilidad_neta_real,
        "rentabilidad_bruta": rentabilidad_bruta,
        "valor_futuro": valor_futuro,
        "plusvalia_bruta": plusvalia_bruta
    }

def format_number(val):
    return f"{val:,.0f} €".replace(",", ".")

st.markdown("<div class='big-title'>Calculadora de inversión inmobiliaria para alquiler</div>", unsafe_allow_html=True)
st.markdown("""
Esta herramienta te ayuda a analizar la rentabilidad y el cashflow de invertir en un piso para alquilarlo en España, teniendo en cuenta todos los gastos, impuestos, hipoteca y supuestos realistas.

> **Disclaimer:** Esta calculadora es educativa, no es asesoramiento financiero. Los resultados pueden variar según tu situación personal y la comunidad autónoma. Verifica siempre tus datos.
""")

with st.form("input_form"):
    # 1. Datos de compra
    st.markdown("<div class='block-box'><span class='block-title'>1. Datos de compra</span>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        precio_compra = st.number_input("Precio de compra (€)", min_value=50000, max_value=1000000, value=250000)
        reformas = st.number_input("Reformas/arreglos (€)", min_value=0, max_value=500000, value=15000)
        alquiler_tipo = st.radio("¿El alquiler será de la vivienda entera o solo habitaciones?", ["Vivienda entera", "Habitaciones"])
        aplica_reduccion_60 = alquiler_tipo == "Vivienda entera"
    with col2:
        comision_agencia = st.number_input("Comisión agencia (€)", min_value=0, max_value=100000, value=0)
        alquiler_mes = st.number_input("Renta mensual (€)", min_value=200, max_value=5000, value=1200)
    st.markdown("</div>", unsafe_allow_html=True)

    # 2. Hipoteca
    st.markdown("<div class='block-box'><span class='block-title'>2. Hipoteca</span>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        entrada = st.number_input("Entrada pagada (€)", min_value=0, max_value=1000000, value=50000)
        tin = st.number_input("TIN hipotecario (%)", min_value=0.1, max_value=10.0, value=2.8, step=0.01)
    with col2:
        hipoteca_anos = st.number_input("Años de hipoteca", min_value=5, max_value=40, value=25, step=1)
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

    # 3. Impuestos y gastos de compra
    st.markdown("<div class='block-box'><span class='block-title'>3. Impuestos y gastos de compra</span>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        gastos_compra_pct = st.number_input("Gastos notario, registro, tasación, gestoría (% sobre compra)", min_value=0.5, max_value=4.0, value=2.0, step=0.1)
        gastos_compra = precio_compra * gastos_compra_pct / 100
    with col2:
        itp_iva_pct = st.number_input("ITP o IVA (% sobre compra)", min_value=4.0, max_value=15.0, value=8.0, step=0.1)
        itp_iva = precio_compra * itp_iva_pct / 100
    st.markdown("</div>", unsafe_allow_html=True)

    # 4. Datos fiscales
    st.markdown("<div class='block-box'><span class='block-title'>4. Datos fiscales</span>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        irpf_marginal = st.number_input("Tipo marginal IRPF (%)", min_value=0.0, max_value=55.0, value=30.0)
    with col2:
        valor_construccion_pct = st.number_input("Valor construcción (% sobre compra)", min_value=10, max_value=90, value=30)
    st.markdown("</div>", unsafe_allow_html=True)

    # 5. Gastos anuales recurrentes
    st.markdown("<div class='block-box'><span class='block-title'>5. Gastos anuales recurrentes</span>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        seguro_impago = st.number_input("Seguro de impago (€)", min_value=0, max_value=5000, value=230)
        impuesto_basuras = st.number_input("Impuesto de basuras (€)", min_value=0, max_value=1000, value=98)
        seguro_hogar = st.number_input("Seguro de hogar (€)", min_value=0, max_value=2000, value=200)
        seguro_vida = st.number_input("Seguro de vida (€)", min_value=0, max_value=2000, value=93)
    with col2:
        comunidad = st.number_input("Gastos de comunidad (€)", min_value=0, max_value=3000, value=240)
        ibi = st.number_input("IBI (€)", min_value=0, max_value=3000, value=175)
        mantenimiento = st.number_input("Mantenimiento y pequeñas reparaciones (€)", min_value=0, max_value=3000, value=480)
        vacio = st.number_input("Periodos vacíos (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.5)
    st.markdown("</div>", unsafe_allow_html=True)

    # 6. Supuesto de revalorización
    st.markdown("<div class='block-box'><span class='block-title'>6. Supuesto de revalorización</span>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        revalorizacion_pct = st.number_input("Revalorización anual estimada (%)", min_value=-10.0, max_value=15.0, value=2.0, step=0.1)
    with col2:
        anos_reval = st.number_input("Años de inversión (para simular revalorización)", min_value=1, max_value=40, value=25)
    st.markdown("</div>", unsafe_allow_html=True)

    submitted = st.form_submit_button("Calcular resultados")

if submitted:
    res = calcular_resultados(
        precio_compra, reformas, comision_agencia, alquiler_mes, entrada, tin, hipoteca_anos, irpf_marginal, valor_construccion_pct,
        gastos_compra, itp_iva, seguro_impago, impuesto_basuras, seguro_hogar, seguro_vida, comunidad, ibi, mantenimiento,
        vacio, aplica_reduccion_60, revalorizacion_pct, anos_reval
    )

    inv = res["inversion_inicial"]
    income = res["ingresos_anuales"]
    expenses_list = res["gastos_dict"]
    expenses_total = res["gastos_anuales"]
    amort = res["amortizacion_anual"]
    net_before_tax = res["beneficio_AI"]
    net_before_tax_amort = res["beneficio_AI_amort"]
    reduc_60 = net_before_tax_amort * 0.6 if aplica_reduccion_60 else 0
    base_sujeta = net_before_tax_amort * 0.4 if aplica_reduccion_60 else net_before_tax_amort
    tax = res["irpf"]
    net_after_tax = res["beneficio_DI"]
    rentabilidad_neta = res["rentabilidad_neta_real"]
    rentabilidad_bruta = res["rentabilidad_bruta"]
    valor_futuro = res["valor_futuro"]
    plusvalia_bruta = res["plusvalia_bruta"]

    st.markdown("""
<div style="border-radius:14px;background:#f9faff;border:2px solid #dde4ee;padding:1.5em 1.5em 0.6em 1.5em;margin-bottom:1.2em;">
  <div style="font-size:1.15em;font-weight:700;color:#15539c;">
    💼 <b>Total inversión inicial necesaria:</b> <span style='float:right;font-size:1.17em;color:#205520;'>{inv}</span>
  </div>
</div>
<div style="border-radius:14px;background:#e8f9f2;border:2px solid #c2e3d6;padding:1.1em 1.4em 0.7em 1.4em;margin-bottom:0.9em;">
  <div style="font-weight:600;color:#1762a6;">
    📈 <b>Ingresos anuales por alquiler:</b> <span style='float:right;font-size:1.13em;color:#1762a6;'>{income}</span>
  </div>
</div>
<div style="border-radius:14px;background:#fff6ee;border:2px solid #ffe2c2;padding:1.1em 1.4em 0.8em 1.4em;margin-bottom:0.7em;">
  <div style="font-weight:650;color:#232323;font-size:1.11em;margin-bottom:0.13em;">Gastos anuales desglosados:</div>
  <ul style="margin:0.3em 0 0.2em 0.7em;padding:0; color:#b35a18;">
    {expenses_html}
  </ul>
  <div style="font-weight:650;color:#b35a18;margin-top:0.6em;">Total gastos anuales: <span style="float:right;color:#b35a18;font-size:1.07em;font-weight:800;">{expenses_total}</span></div>
</div>
<div style="border-radius:12px;background:#fffef4;border:2px solid #ffeabf;padding:1.1em 1.2em 0.8em 1.2em; margin-bottom:1.1em;">
  <b style='color:#9a7700;font-size:1.09em;'>Rentabilidad anual antes de impuestos:</b>
  <span style='float:right;color:#ad860a;font-weight:700;font-size:1.14em;'>{net_before_tax}</span>
  <div style='color:#333; font-size:0.98em; margin-top:0.18em;'>Es el beneficio anual antes de impuestos y amortización. No descuenta ni amortización ni IRPF.</div>
</div>
<div style="border-radius:12px;background:#f1ffec;border:2px solid #d8f8cc;padding:1.1em 1.2em 0.8em 1.2em; margin-bottom:1.1em;">
  <b style='color:#237319;font-size:1.12em;'>Rentabilidad neta después de impuestos:</b>
  <span style='float:right;color:#167c2d;font-weight:900;font-size:1.20em;'>{net_after_tax}</span>
  <div style='color:#2c566e; font-size:0.99em;'>Rentabilidad neta sobre la inversión inicial: <b>{rentabilidad_neta:.2f} %</b></div>
</div>
<div style="border-radius:12px;background:#e0f7ff;border:2px solid #99daef;padding:1.1em 1.2em 0.8em 1.2em; margin-bottom:1.1em;">
  <b style='color:#0969da;font-size:1.08em;'>Rentabilidad bruta anual:</b>
  <span style='float:right;color:#2a74bb;font-weight:700;font-size:1.13em;'>{rentabilidad_bruta:.2f} %</span>
  <div style='color:#365f8a; font-size:0.98em;'>Beneficio antes de impuestos, sobre la inversión inicial, sin deducir amortización ni IRPF.</div>
</div>
<div style="border-radius:13px;background:#eef8fa;border:2px solid #b2d8e8;padding:1.25em 1.2em 1.1em 1.2em; margin-bottom:1.0em; color:#1a2635; font-size:1.06em;">
  <b style='color:#232323;font-size:1.09em;'>Escenario de revalorización:</b>
  <ul style="margin:0.4em 0 0.2em 1.3em;padding:0;">
    <li>Valor futuro estimado de la vivienda tras {anos_reval} años: <b>{valor_futuro}</b></li>
    <li>Plusvalía bruta potencial: <b>{plusvalia_bruta}</b></li>
  </ul>
</div>
""".format(
    inv=format_number(inv),
    income=format_number(income),
    expenses_html="".join([f"<li>{name}: <b>{format_number(val)}</b></li>" for name, val in expenses_list]),
    expenses_total=format_number(expenses_total),
    net_before_tax=format_number(net_before_tax),
    net_after_tax=format_number(net_after_tax),
    rentabilidad_neta=rentabilidad_neta,
    rentabilidad_bruta=rentabilidad_bruta,
    valor_futuro=format_number(valor_futuro),
    plusvalia_bruta=format_number(plusvalia_bruta),
    anos_reval=anos_reval
), unsafe_allow_html=True)

    # Detalle de cálculo fiscal
    st.markdown("<div style='font-size:1.08em; margin-bottom:0.2em; margin-top:1.2em; color:#2c5676;'><b>Detalle del cálculo fiscal anual:</b></div>", unsafe_allow_html=True)
    st.markdown("<ul>", unsafe_allow_html=True)
    st.markdown(f"<li>Beneficio antes de amortización: <b>{format_number(net_before_tax)}</b></li>", unsafe_allow_html=True)
    st.markdown(f"<li>- Amortización anual deducible: <b>{format_number(amort)}</b></li>", unsafe_allow_html=True)
    st.markdown(f"<li>= Base imponible fiscal: <b>{format_number(net_before_tax_amort)}</b></li>", unsafe_allow_html=True)
    if aplica_reduccion_60:
        st.markdown(f"<li>- Reducción del 60% arrendamiento vivienda habitual: <b>{format_number(reduc_60)}</b></li>", unsafe_allow_html=True)
        st.markdown(f"<li>= Base sujeta a IRPF: <b>{format_number(base_sujeta)}</b></li>", unsafe_allow_html=True)
    else:
        st.markdown(f"<li><span style='color:#a90000; font-weight:600;'>No se aplica reducción del 60% porque el alquiler es de habitaciones o no es vivienda habitual.</span></li>", unsafe_allow_html=True)
        st.markdown(f"<li>= Base sujeta a IRPF: <b>{format_number(base_sujeta)}</b></li>", unsafe_allow_html=True)
    st.markdown(f"<li>x Tipo marginal IRPF: <b>{format_number(tax)}</b></li>", unsafe_allow_html=True)
    st.markdown(f"<li>= IRPF estimado: <b>{format_number(tax)}</b></li>", unsafe_allow_html=True)
    st.markdown(f"<li>= Beneficio anual después de impuestos: <b>{format_number(net_after_tax)}</b></li>", unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True)

    st.info("Puedes modificar cualquier dato y recalcular para analizar diferentes escenarios.")
