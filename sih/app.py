import streamlit as st
import pandas as pd
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="Indian Food Packaging Optimizer (v1)",
    page_icon="📦",
    layout="wide"
)

# ---------------------------------------------------------
# DATASETS (FSSAI COMMODITIES & INDIAN MATERIALS)
# ---------------------------------------------------------

MATERIALS_DB = [
    {
        "material": "LDPE (Low-Density Polyethylene)",
        "thickness_um": 70,
        "wvtr": 11.0,
        "otr": 2700.0,
        "acid_resistant": True,
        "fat_safe": False,
        "breathable": False,
        "biodegradable": False,
        "cost_inr_per_kg": 125.0
    },
    {
        "material": "HDPE (High-Density Polyethylene)",
        "thickness_um": 60,
        "wvtr": 3.8,
        "otr": 2000.0,
        "acid_resistant": True,
        "fat_safe": True,
        "breathable": False,
        "biodegradable": False,
        "cost_inr_per_kg": 132.0
    },
    {
        "material": "PET / LLDPE Laminate",
        "thickness_um": 50,
        "wvtr": 1.2,
        "otr": 75.0,
        "acid_resistant": True,
        "fat_safe": True,
        "breathable": False,
        "biodegradable": False,
        "cost_inr_per_kg": 155.0
    },
    {
        "material": "PET / VMPET / LLDPE (Metalized)",
        "thickness_um": 45,
        "wvtr": 0.8,
        "otr": 1.5,
        "acid_resistant": False,
        "fat_safe": True,
        "breathable": False,
        "biodegradable": False,
        "cost_inr_per_kg": 195.0
    },
    {
        "material": "PET / ALU / LLDPE (Aluminum Foil Laminate)",
        "thickness_um": 90,
        "wvtr": 0.005,
        "otr": 0.005,
        "acid_resistant": True,
        "fat_safe": True,
        "breathable": False,
        "biodegradable": False,
        "cost_inr_per_kg": 340.0
    },
    {
        "material": "Biodegradable Film (PLA / PBAT)",
        "thickness_um": 35,
        "wvtr": 180.0,
        "otr": 950.0,
        "acid_resistant": False,
        "fat_safe": False,
        "breathable": True,
        "biodegradable": True,
        "cost_inr_per_kg": 280.0
    },
    {
        "material": "Micro-Perforated LDPE / PP",
        "thickness_um": 30,
        "wvtr": 14.0,
        "otr": 12000.0,
        "acid_resistant": True,
        "fat_safe": False,
        "breathable": True,
        "biodegradable": False,
        "cost_inr_per_kg": 150.0
    }
]

COMMODITIES_DB = {
    "Whole Wheat Atta": {"moisture_limit": 14.0, "fat_content": 1.8, "ph": 6.2, "ro2": 0.0, "shelf_days": 120},
    "Fresh Paneer": {"moisture_limit": 60.0, "fat_content": 22.0, "ph": 5.6, "ro2": 0.0, "shelf_days": 15},
    "Pure Desi Ghee": {"moisture_limit": 0.3, "fat_content": 99.7, "ph": 5.0, "ro2": 0.0, "shelf_days": 365},
    "Garam Masala": {"moisture_limit": 10.0, "fat_content": 10.0, "ph": 5.5, "ro2": 0.0, "shelf_days": 270},
    "Potato Chips / Namkeen": {"moisture_limit": 2.0, "fat_content": 32.0, "ph": 6.0, "ro2": 0.0, "shelf_days": 150},
    "Fresh Mangoes (Alphonso)": {"moisture_limit": 82.0, "fat_content": 0.4, "ph": 4.0, "ro2": 25.0, "shelf_days": 21},
    "Button Mushrooms": {"moisture_limit": 91.0, "fat_content": 0.3, "ph": 6.2, "ro2": 150.0, "shelf_days": 7},
    "Mango Pickle (in Oil)": {"moisture_limit": 48.0, "fat_content": 25.0, "ph": 3.4, "ro2": 0.0, "shelf_days": 365}
}

# ---------------------------------------------------------
# UI HEADER
# ---------------------------------------------------------
st.title("📦 Indian Food Packaging Decision Engine")
st.caption("FSSAI Regulatory Compliant • IIP Testing Standards • Real-time Math Solver")

tabs = st.tabs(["🚀 Recommendation Engine", "📐 Mathematical Formulation", "📊 Benchmark Material DB"])

# ---------------------------------------------------------
# TAB 1: RECOMMENDATION ENGINE
# ---------------------------------------------------------
with tabs[0]:
    st.sidebar.header("1. User Input Parameters")
    
    preset_choice = st.sidebar.selectbox("Select FSSAI Commodity Preset:", ["Custom"] + list(COMMODITIES_DB.keys()))
    
    if preset_choice != "Custom":
        preset = COMMODITIES_DB[preset_choice]
        default_moisture = preset["moisture_limit"]
        default_fat = preset["fat_content"]
        default_ph = preset["ph"]
        default_ro2 = preset["ro2"]
        default_shelf = preset["shelf_days"]
    else:
        default_moisture, default_fat, default_ph, default_ro2, default_shelf = 10.0, 5.0, 6.0, 0.0, 90

    col_in1, col_in2 = st.sidebar.columns(2)
    with col_in1:
        pack_mass = st.number_input("Pack Mass (g):", min_value=10, max_value=5000, value=500, step=50)
        moisture_crit = st.number_input("Max Moisture Limit (%):", min_value=0.1, max_value=95.0, value=float(default_moisture))
        fat_content = st.number_input("Fat Content (%):", min_value=0.0, max_value=100.0, value=float(default_fat))
        ph_level = st.number_input("pH Level:", min_value=1.0, max_value=14.0, value=float(default_ph))
    
    with col_in2:
        pouch_area = st.number_input("Pouch Surface Area (m²):", min_value=0.01, max_value=2.0, value=0.08, step=0.01)
        target_shelf = st.number_input("Target Shelf Life (days):", min_value=1, max_value=730, value=int(default_shelf))
        ro2_rate = st.number_input("Respiration Rate R_O2:", min_value=0.0, max_value=500.0, value=float(default_ro2))
        rh_ambient = st.number_input("Ambient RH (%):", min_value=10, max_value=100, value=85)

    # ---------------------------------------------------------
    # MATH ENGINE COMPUTATIONS
    # ---------------------------------------------------------
    initial_moisture = moisture_crit * 0.5  # Assumed starting point
    delta_m_max = (abs(moisture_crit - initial_moisture) / 100.0) * pack_mass
    rh_factor = (rh_ambient - 50.0) / 100.0  # Assumed internal RH = 50%
    if rh_factor <= 0:
        rh_factor = 0.1

    wvtr_req = delta_m_max / (pouch_area * target_shelf * rh_factor)
    
    is_living = ro2_rate > 0
    if is_living:
        otr_req = (ro2_rate * (pack_mass / 1000.0)) / (pouch_area * (0.21 - 0.05))
    else:
        otr_req = 100.0 / (pouch_area * target_shelf * 0.21)

    st.subheader("Calculated Barrier Constraints")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Allowable Water Flux (ΔM)", f"{delta_m_max:.2f} g")
    m_col2.metric("Target WVTR (Max)", f"{wvtr_req:.3f} g/m²/day")
    m_col3.metric("Target OTR", f"{otr_req:.2f} cm³/m²/day")
    m_col4.metric("Biological State", "Living (MAP)" if is_living else "Non-living")

    st.divider()
    st.subheader("Candidate Materials Evaluation")

    # Evaluate Materials
    results = []
    min_cost = min(m["cost_inr_per_kg"] for m in MATERIALS_DB)
    max_cost = max(m["cost_inr_per_kg"] for m in MATERIALS_DB)

    for mat in MATERIALS_DB:
        reject_reasons = []
        
        # Hard Rule 1: Respiration / MAP compatibility
        if is_living and not mat["breathable"]:
            reject_reasons.append("Non-breathable (Suffocation risk for living produce)")
        if not is_living and mat["breathable"] and wvtr_req < 10.0:
            reject_reasons.append("Excessive permeability for non-living food")

        # Hard Rule 2: WVTR constraint
        if mat["wvtr"] > wvtr_req and not is_living:
            reject_reasons.append(f"WVTR too high ({mat['wvtr']} > {wvtr_req:.2f})")

        # Hard Rule 3: Fat / Acid Compatibility
        if fat_content > 10.0 and not mat["fat_safe"]:
            reject_reasons.append("Poor oil resistance (Grease bleed risk)")
        if ph_level < 4.0 and not mat["acid_resistant"]:
            reject_reasons.append("Acid corrosion risk")

        # Calculate Scores
        valid = len(reject_reasons) == 0
        
        if valid:
            barrier_score = max(0.0, 100.0 * (1.0 - (mat["wvtr"] / max(wvtr_req, 0.001))))
            cost_score = 100.0 * (1.0 - (mat["cost_inr_per_kg"] - min_cost) / (max_cost - min_cost))
            sustain_score = 100.0 if mat["biodegradable"] else 0.0
            total_score = round(0.50 * barrier_score + 0.35 * cost_score + 0.15 * sustain_score, 1)
            status = "✅ Suitable"
        else:
            total_score = 0.0
            status = "❌ Rejected"

        results.append({
            "Material Structure": mat["material"],
            "Status": status,
            "Overall Score": total_score,
            "Cost (₹/kg)": mat["cost_inr_per_kg"],
            "Mat WVTR": mat["wvtr"],
            "Mat OTR": mat["otr"],
            "Rejection Reason / Notes": "; ".join(reject_reasons) if reject_reasons else "Meets all FSSAI/Physical constraints"
        })

    df_results = pd.DataFrame(results).sort_values(by="Overall Score", ascending=False)
    st.dataframe(df_results, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 2: MATHEMATICAL FORMULATION
# ---------------------------------------------------------
with tabs[1]:
    st.markdown("### Step-by-Step Mathematical Engine")

    st.markdown("#### 1. Allowable Moisture Transfer Equation")
    st.latex(r"\Delta M_{\text{max}} = \left(\frac{|M_{\text{critical}} - M_{\text{initial}}|}{100}\right) \cdot m_{\text{product}}")
    st.latex(r"WVTR_{\text{required}} = \frac{\Delta M_{\text{max}}}{A_{\text{pouch}} \cdot t_{\text{shelf}} \cdot \left(\frac{RH_{\text{ambient}} - RH_{\text{internal}}}{100}\right)}")

    st.markdown("#### 2. Respiration Rate Balance for MAP (Living Produce)")
    st.latex(r"OTR_{\text{MAP}} = \frac{R_{\text{O}_2} \cdot m_{\text{product}}}{1000 \cdot A_{\text{pouch}} \cdot (y_{\text{O}_2,\text{ext}} - y_{\text{O}_2,\text{int}})}")

    st.markdown("#### 3. Composite Ranking Function")
    st.latex(r"\text{Score} = w_1 \cdot S_{\text{barrier}} + w_2 \cdot S_{\text{cost}} + w_3 \cdot S_{\text{sustainability}}")
    st.markdown("""
    * $w_1 = 0.50$ (Barrier Safety Weight)
    * $w_2 = 0.35$ (Cost Efficiency Weight)
    * $w_3 = 0.15$ (Eco/Sustainability Weight)
    """)

# ---------------------------------------------------------
# TAB 3: BENCHMARK MATERIAL DATABASE
# ---------------------------------------------------------
with tabs[2]:
    st.markdown("### FSSAI / IIP Standard Packaging Material Specification Database")
    st.dataframe(pd.DataFrame(MATERIALS_DB), use_container_width=True)