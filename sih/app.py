import os
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Indian Food Packaging Optimizer (v1)",
    page_icon="📦",
    layout="wide",
)


@st.cache_data
def load_datasets():
    materials_path = os.path.join("data", "materials.csv")
    commodities_path = os.path.join("data", "commodities.csv")

    if not os.path.exists(materials_path) or not os.path.exists(
        commodities_path
    ):
        return None, None

    materials_df = pd.read_csv(materials_path)
    commodities_df = pd.read_csv(commodities_path)

    materials_db = materials_df.to_dict(orient="records")
    commodities_db = commodities_df.set_index("commodity_name").to_dict(
        orient="index"
    )

    return materials_db, commodities_db


MATERIALS_DB, COMMODITIES_DB = load_datasets()

if MATERIALS_DB is None or COMMODITIES_DB is None:
    st.error(
        "❌ CSV files not found! Please ensure `data/materials.csv` and `data/commodities.csv` exist."
    )
    st.stop()

st.sidebar.header("📂 Dataset Operations")
materials_csv_bytes = (
    pd.DataFrame(MATERIALS_DB).to_csv(index=False).encode("utf-8")
)
commodities_csv_bytes = (
    pd.DataFrame.from_dict(COMMODITIES_DB, orient="index")
    .reset_index()
    .rename(columns={"index": "commodity_name"})
    .to_csv(index=False)
    .encode("utf-8")
)

st.sidebar.download_button(
    "📥 Export Materials CSV",
    data=materials_csv_bytes,
    file_name="materials.csv",
    mime="text/csv",
)
st.sidebar.download_button(
    "📥 Export Commodities CSV",
    data=commodities_csv_bytes,
    file_name="commodities.csv",
    mime="text/csv",
)

st.sidebar.divider()

st.sidebar.header("⚙️ Product & Environmental Inputs")

preset_choice = st.sidebar.selectbox(
    "Select FSSAI Commodity Preset:", ["Custom"] + list(COMMODITIES_DB.keys())
)

if preset_choice != "Custom":
    preset = COMMODITIES_DB[preset_choice]
    default_moisture = preset["moisture_limit"]
    default_fat = preset["fat_content"]
    default_ph = preset["ph"]
    default_ro2 = preset["ro2"]
    default_shelf = preset["shelf_days"]
else:
    default_moisture, default_fat, default_ph, default_ro2, default_shelf = (
        10.0,
        5.0,
        6.0,
        0.0,
        90,
    )

col_in1, col_in2 = st.sidebar.columns(2)
with col_in1:
    pack_mass = st.number_input(
        "Pack Mass (g):", min_value=10, max_value=5000, value=500, step=50
    )
    moisture_crit = st.number_input(
        "Max Moisture Limit (%):",
        min_value=0.1,
        max_value=95.0,
        value=float(default_moisture),
    )
    fat_content = st.number_input(
        "Fat Content (%):",
        min_value=0.0,
        max_value=100.0,
        value=float(default_fat),
    )
    ph_level = st.number_input(
        "pH Level:", min_value=1.0, max_value=14.0, value=float(default_ph)
    )

with col_in2:
    pouch_area = st.number_input(
        "Pouch Area (m²):",
        min_value=0.01,
        max_value=2.0,
        value=0.08,
        step=0.01,
    )
    target_shelf = st.number_input(
        "Target Shelf Life (days):",
        min_value=1,
        max_value=730,
        value=int(default_shelf),
    )
    ro2_rate = st.number_input(
        "Respiration R_O2:",
        min_value=0.0,
        max_value=500.0,
        value=float(default_ro2),
    )
    rh_ambient = st.number_input(
        "Ambient RH (%):", min_value=10, max_value=100, value=85
    )

st.title("📦 Indian Food Packaging Decision Engine")
st.caption(
    "FSSAI Regulatory Compliant • Dynamic CSV Engine • Real-time Math Solver"
)

tabs = st.tabs(
    [
        "🚀 Recommendation Engine",
        "📐 Mathematical Formulation",
        "📊 Benchmark Material DB",
    ]
)

with tabs[0]:
    initial_moisture = moisture_crit * 0.5
    delta_m_max = (
        abs(moisture_crit - initial_moisture) / 100.0
    ) * pack_mass
    rh_factor = (rh_ambient - 50.0) / 100.0
    if rh_factor <= 0:
        rh_factor = 0.1

    wvtr_req = delta_m_max / (pouch_area * target_shelf * rh_factor)

    is_living = ro2_rate > 0
    if is_living:
        otr_req = (ro2_rate * (pack_mass / 1000.0)) / (
            pouch_area * (0.21 - 0.05)
        )
    else:
        otr_req = 100.0 / (pouch_area * target_shelf * 0.21)

    st.subheader("Calculated Barrier Thresholds")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Allowable Moisture Flux (ΔM)", f"{delta_m_max:.2f} g")
    m_col2.metric("Max Required WVTR", f"{wvtr_req:.3f} g/m²/day")
    m_col3.metric("Target OTR Limit", f"{otr_req:.2f} cm³/m²/day")
    m_col4.metric(
        "Biological Classification", "Living (MAP)" if is_living else "Processed"
    )

    st.divider()
    st.subheader("Material Evaluation & Scoring")

    results = []
    min_cost = min(m["cost_inr_per_kg"] for m in MATERIALS_DB)
    max_cost = max(m["cost_inr_per_kg"] for m in MATERIALS_DB)

    for mat in MATERIALS_DB:
        reject_reasons = []

        if is_living and not mat["breathable"]:
            reject_reasons.append(
                "Non-breathable structure (Causes decay in living produce)"
            )
        if not is_living and mat["breathable"] and wvtr_req < 10.0:
            reject_reasons.append(
                "Excessive permeability for non-living commodity"
            )

        if mat["wvtr"] > wvtr_req and not is_living:
            reject_reasons.append(
                f"WVTR exceeds threshold ({mat['wvtr']} > {wvtr_req:.2f})"
            )

        if fat_content > 10.0 and not mat["fat_safe"]:
            reject_reasons.append(
                "Inadequate grease barrier (Oil seepage risk)"
            )
        if ph_level < 4.0 and not mat["acid_resistant"]:
            reject_reasons.append(
                "Acid corrosion risk for pouch liner"
            )

        valid = len(reject_reasons) == 0

        if valid:
            barrier_score = max(
                0.0,
                100.0 * (1.0 - (mat["wvtr"] / max(wvtr_req, 0.001))),
            )
            cost_score = 100.0 * (
                1.0
                - (mat["cost_inr_per_kg"] - min_cost)
                / max((max_cost - min_cost), 0.001)
            )
            sustain_score = 100.0 if mat["biodegradable"] else 0.0
            total_score = round(
                0.50 * barrier_score + 0.35 * cost_score + 0.15 * sustain_score,
                1,
            )
            status = "✅ Suitable"
        else:
            total_score = 0.0
            status = "❌ Rejected"

        results.append(
            {
                "Material Structure": mat["material"],
                "Status": status,
                "Match Score": total_score,
                "Cost (₹/kg)": mat["cost_inr_per_kg"],
                "Material WVTR": mat["wvtr"],
                "Material OTR": mat["otr"],
                "Decision Audit Trail": (
                    "; ".join(reject_reasons)
                    if reject_reasons
                    else "Passes all barrier & safety limits"
                ),
            }
        )

    df_results = pd.DataFrame(results).sort_values(
        by="Match Score", ascending=False
    )
    st.dataframe(df_results, use_container_width=True, hide_index=True)

with tabs[1]:
    st.markdown("### Decision Engine Governing Equations")

    st.markdown("#### 1. Permissible Moisture Flux ($WVTR_{\\text{req}}$)")
    st.latex(
        r"\Delta M_{\text{max}} = \left(\frac{|M_{\text{critical}} - M_{\text{initial}}|}{100}\right) \cdot m_{\text{product}}"
    )
    st.latex(
        r"WVTR_{\text{required}} = \frac{\Delta M_{\text{max}}}{A_{\text{pouch}} \cdot t_{\text{shelf}} \cdot \left(\frac{RH_{\text{ambient}} - RH_{\text{internal}}}{100}\right)}"
    )

    st.markdown("#### 2. Respiration Rate Equilibrium ($OTR_{\\text{MAP}}$)")
    st.latex(
        r"OTR_{\text{MAP}} = \frac{R_{\text{O}_2} \cdot m_{\text{product}}}{1000 \cdot A_{\text{pouch}} \cdot (y_{\text{O}_2,\text{ext}} - y_{\text{O}_2,\text{int}})}"
    )

    st.markdown("#### 3. Multi-Criteria Ranking Algorithm")
    st.latex(
        r"\text{Score} = 0.50 \cdot S_{\text{barrier}} + 0.35 \cdot S_{\text{cost}} + 0.15 \cdot S_{\text{sustainability}}"
    )

with tabs[2]:
    st.markdown("### Loaded Materials Database (`materials.csv`)")
    st.dataframe(pd.DataFrame(MATERIALS_DB), use_container_width=True)

    st.markdown("### Loaded Commodities Database (`commodities.csv`)")
    commodities_display = (
        pd.DataFrame.from_dict(COMMODITIES_DB, orient="index")
        .reset_index()
        .rename(columns={"index": "commodity_name"})
    )
    st.dataframe(commodities_display, use_container_width=True)
