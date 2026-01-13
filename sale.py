import streamlit as st
import pandas as pd
import re
from difflib import SequenceMatcher
import time

st.set_page_config(
    page_title="VOLF Communications - VoIP Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .kpi-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        margin: 0.5rem 0;
    }
    .kpi-label {
        color: #666;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .filter-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    .section-title {
        color: #333;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    .loading-banner {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        animation: pulse 1.5s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
</style>
""", unsafe_allow_html=True)

# =========================
# STATE MANAGEMENT
# =========================
def init_session_state():
    """Initialize session state variables"""
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'filter_countries' not in st.session_state:
        st.session_state.filter_countries = []
    if 'filter_destinations' not in st.session_state:
        st.session_state.filter_destinations = []
    if 'filter_suppliers' not in st.session_state:
        st.session_state.filter_suppliers = []
    if 'filter_trunks' not in st.session_state:
        st.session_state.filter_trunks = []

init_session_state()

# =========================
# INTELLIGENT NAME MATCHING
# =========================
def normalize_supplier_name(name):
    """Normalize supplier names for intelligent matching"""
    replacements = {
        'communications': 'comm',
        'telecom': 'tel',
        'limited': 'ltd',
        'incorporated': 'inc',
        'corporation': 'corp',
        '&': 'and',
    }
    
    name = str(name).lower().strip()
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

def normalize_destination(name):
    """Keep original destination names - minimal normalization only for display"""
    if pd.isna(name):
        return "Unknown"
    
    # Just clean up extra whitespace and return as-is
    name = str(name).strip()
    name = re.sub(r"\s+", " ", name)
    
    return name

# =========================
# OPTIMIZED DATA LOADING
# =========================
@st.cache_data(show_spinner=False)
def load_and_process_data():
    """Load and process data with optimization"""
    try:
        # Read Excel file
        df = pd.read_excel("International Vendors.xlsx", engine='openpyxl')
        
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        # Rename columns
        df = df.rename(columns={"Customer": "Supplier"})
        
        # Keep destination names as-is from the Name column
        df["Destination"] = df["Name"].apply(normalize_destination)
        
        # Normalize supplier names for intelligent matching
        df["Supplier_Normalized"] = df["Supplier"].apply(normalize_supplier_name)
        
        # Extract country from destination (first word before space or dash)
        def extract_country(dest):
            if pd.isna(dest):
                return "Unknown"
            parts = str(dest).replace("-", " ").split()
            return parts[0] if parts else "Unknown"
        
        df["Country"] = df["Destination"].apply(extract_country)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# =========================
# HEADER
# =========================
st.markdown(
    """
    <div class="main-header">
        <h1>VOLF Communications</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# LAZY LOADING WITH PROGRESS
# =========================
if not st.session_state.data_loaded:
    with st.spinner(""):
        st.markdown('<div class="loading-banner">🔄 Loading VoIP data... Please wait</div>', unsafe_allow_html=True)
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulate progress stages
        status_text.text("Reading Excel file...")
        progress_bar.progress(30)
        
        df = load_and_process_data()
        
        if df is not None:
            status_text.text("Processing destinations...")
            progress_bar.progress(60)
            time.sleep(0.2)
            
            status_text.text("Normalizing supplier names...")
            progress_bar.progress(80)
            time.sleep(0.2)
            
            status_text.text("Finalizing...")
            progress_bar.progress(100)
            
            st.session_state.df = df
            st.session_state.data_loaded = True
            
            time.sleep(0.3)
            status_text.empty()
            progress_bar.empty()
            st.rerun()
        else:
            st.error("Failed to load data. Please check the file path.")
            st.stop()
else:
    df = st.session_state.df

# =========================
# KPI CARDS
# =========================
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Countries</div>
        <div class="kpi-value">{df['Country'].nunique()}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Destinations</div>
        <div class="kpi-value">{df['Destination'].nunique()}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Suppliers</div>
        <div class="kpi-value">{df['Supplier'].nunique()}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Active Trunks</div>
        <div class="kpi-value">{df['Trunk'].nunique()}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    avg_rate = df['Rate (inter)'].mean()
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Avg Rate</div>
        <div class="kpi-value">${avg_rate:.4f}</div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# FILTERS WITH STATE PERSISTENCE
# =========================
st.markdown('<div class="filter-container">', unsafe_allow_html=True)
col_filter, col_reset = st.columns([6, 1])

with col_filter:
    st.markdown("### 🔍 Filter Options")

with col_reset:
    if st.button("🔄 Reset Filters", use_container_width=True):
        st.session_state.filter_countries = []
        st.session_state.filter_destinations = []
        st.session_state.filter_suppliers = []
        st.session_state.filter_trunks = []
        st.rerun()

f1, f2, f3, f4 = st.columns(4)

with f1:
    selected_countries = st.multiselect(
        "🌍 Country",
        sorted(df["Country"].unique()),
        default=st.session_state.filter_countries,
        key="countries_select",
        help="Filter by country"
    )
    st.session_state.filter_countries = selected_countries

with f2:
    # Filter destinations based on selected countries
    available_destinations = df["Destination"].unique() if not selected_countries else \
        df[df["Country"].isin(selected_countries)]["Destination"].unique()
    
    selected_destinations = st.multiselect(
        "📍 Destination",
        sorted(available_destinations),
        default=[d for d in st.session_state.filter_destinations if d in available_destinations],
        key="destinations_select",
        help="Filter by destination type"
    )
    st.session_state.filter_destinations = selected_destinations

with f3:
    # Filter suppliers based on previous selections
    temp_df = df.copy()
    if selected_countries:
        temp_df = temp_df[temp_df["Country"].isin(selected_countries)]
    if selected_destinations:
        temp_df = temp_df[temp_df["Destination"].isin(selected_destinations)]
    
    available_suppliers = temp_df["Supplier"].unique()
    
    selected_suppliers = st.multiselect(
        "🏢 Supplier",
        sorted(available_suppliers),
        default=[s for s in st.session_state.filter_suppliers if s in available_suppliers],
        key="suppliers_select",
        help="Filter by supplier name"
    )
    st.session_state.filter_suppliers = selected_suppliers

with f4:
    # Filter trunks based on all previous selections
    if selected_suppliers:
        temp_df = temp_df[temp_df["Supplier"].isin(selected_suppliers)]
    
    available_trunks = temp_df["Trunk"].unique()
    
    selected_trunks = st.multiselect(
        "📡 Trunk",
        sorted(available_trunks),
        default=[t for t in st.session_state.filter_trunks if t in available_trunks],
        key="trunks_select",
        help="Filter by trunk"
    )
    st.session_state.filter_trunks = selected_trunks

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# OPTIMIZED FILTERING
# =========================
def filter_dataframe(df_input, countries, destinations, suppliers, trunks):
    """Optimized filtering without aggressive caching"""
    filtered = df_input.copy()
    
    if countries:
        filtered = filtered[filtered["Country"].isin(countries)]
    if destinations:
        filtered = filtered[filtered["Destination"].isin(destinations)]
    if suppliers:
        filtered = filtered[filtered["Supplier"].isin(suppliers)]
    if trunks:
        filtered = filtered[filtered["Trunk"].isin(trunks)]
    
    return filtered

filtered_df = filter_dataframe(
    df, 
    selected_countries, 
    selected_destinations, 
    selected_suppliers, 
    selected_trunks
)

if filtered_df.empty:
    st.warning("⚠️ No data available for selected filters.")
    st.stop()

# =========================
# FILTERED KPIs
# =========================
st.markdown("---")
st.markdown("### 📊 Filtered Results")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    min_rate = filtered_df["Rate (inter)"].min()
    st.metric("Lowest Rate", f"${min_rate:.4f}", help="Best rate available")

with kpi2:
    max_rate = filtered_df["Rate (inter)"].max()
    st.metric("Highest Rate", f"${max_rate:.4f}", help="Maximum rate")

with kpi3:
    avg_filtered = filtered_df["Rate (inter)"].mean()
    st.metric("Average Rate", f"${avg_filtered:.4f}", help="Mean rate")

with kpi4:
    total_routes = len(filtered_df)
    st.metric("Total Routes", f"{total_routes}", help="Number of routes")

# =========================
# MAIN TABLE
# =========================
def generate_main_table(filtered_df_input):
    """Generate main table"""
    main_table = (
        filtered_df_input
        .groupby(["Country", "Destination", "Supplier", "Trunk"])
        .agg(
            Rate=("Rate (inter)", "mean"),
            Min_Dur=("Min Dur", "min"),
            Inc_Dur=("Inc Dur", "min")
        )
        .reset_index()
        .sort_values(["Country", "Destination", "Rate"])
    )
    main_table["Rate"] = main_table["Rate"].apply(lambda x: f"${x:.4f}")
    return main_table

st.markdown('<div class="section-title">📊 Destination & Supplier Overview</div>', unsafe_allow_html=True)

main_table = generate_main_table(filtered_df)

st.dataframe(
    main_table[[
        "Country",
        "Destination",
        "Supplier",
        "Trunk",
        "Rate",
        "Min_Dur",
        "Inc_Dur"
    ]],
    use_container_width=True,
    hide_index=True,
    height=400,
    column_config={
        "Destination": st.column_config.TextColumn(
            "Destination",
            width="large"
        )
    }
)

# =========================
# BILLING INCREMENT
# =========================
def generate_billing_table(filtered_df_input):
    """Generate billing table"""
    billing_table = (
        filtered_df_input
        .groupby(["Supplier", "Trunk"])
        .agg(
            Min_Duration=("Min Dur", "min"),
            Increment_Duration=("Inc Dur", "min"),
            Avg_Rate=("Rate (inter)", "mean")
        )
        .reset_index()
    )
    billing_table["Avg_Rate"] = billing_table["Avg_Rate"].apply(lambda x: f"${x:.4f}")
    return billing_table

st.markdown('<div class="section-title">📦 Billing Increment Comparison</div>', unsafe_allow_html=True)

billing_table = generate_billing_table(filtered_df)

st.dataframe(
    billing_table,
    use_container_width=True,
    hide_index=True,
    height=300
)

# =========================
# ALL RATES BY DESTINATION (GROUPED BY SUPPLIER)
# =========================
def generate_all_rates_by_destination(filtered_df_input, sort_ascending):
    """Generate all rates sorted by destination and grouped by supplier"""
    all_rates = (
        filtered_df_input
        [["Country", "Destination", "Supplier", "Trunk", "Rate (inter)", "Min Dur", "Inc Dur"]]
        .copy()
    )
    
    # Sort by Destination first, then Supplier (to keep suppliers together), then Rate
    all_rates = all_rates.sort_values(
        ["Destination", "Supplier", "Rate (inter)"], 
        ascending=[True, True, sort_ascending]
    )
    
    # Format rate for display
    all_rates["Rate_Display"] = all_rates["Rate (inter)"].apply(lambda x: f"${x:.4f}")
    
    return all_rates

st.markdown('<div class="section-title">💰 All Rates by Destination (Grouped by Supplier)</div>', unsafe_allow_html=True)

# Add sorting options
sort_col1, sort_col2, sort_col3 = st.columns([1, 1, 4])
with sort_col1:
    sort_order = st.selectbox(
        "Sort Order",
        ["Lowest to Highest", "Highest to Lowest"],
        key="rate_sort_order"
    )

with sort_col2:
    group_view = st.selectbox(
        "Group By",
        ["Supplier", "Destination Only"],
        key="group_view"
    )

# Determine sort direction
sort_ascending = True if sort_order == "Lowest to Highest" else False

# Generate table based on grouping preference
if group_view == "Supplier":
    all_rates = generate_all_rates_by_destination(filtered_df, sort_ascending)
    
    # Add visual separator for better readability
    all_rates_display = all_rates[["Country", "Destination", "Supplier", "Trunk", "Rate_Display", "Min Dur", "Inc Dur"]].copy()
    all_rates_display.columns = ["Country", "Destination", "Supplier", "Trunk", "Rate", "Min Dur", "Inc Dur"]
    
    st.dataframe(
        all_rates_display,
        use_container_width=True,
        hide_index=True,
        height=400,
        column_config={
            "Supplier": st.column_config.TextColumn(
                "Supplier",
                width="medium",
            ),
            "Destination": st.column_config.TextColumn(
                "Destination",
                width="large",
            )
        }
    )
    
    # Show supplier summary
    st.markdown("---")
    supplier_summary = (
        filtered_df.groupby("Supplier")
        .agg(
            Routes=("Destination", "count"),
            Avg_Rate=("Rate (inter)", "mean"),
            Min_Rate=("Rate (inter)", "min"),
            Max_Rate=("Rate (inter)", "max")
        )
        .reset_index()
        .sort_values("Avg_Rate")
    )
    
    supplier_summary["Avg_Rate"] = supplier_summary["Avg_Rate"].apply(lambda x: f"${x:.4f}")
    supplier_summary["Min_Rate"] = supplier_summary["Min_Rate"].apply(lambda x: f"${x:.4f}")
    supplier_summary["Max_Rate"] = supplier_summary["Max_Rate"].apply(lambda x: f"${x:.4f}")
    
    with st.expander("📊 Supplier Summary"):
        st.dataframe(
            supplier_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Supplier": "Supplier",
                "Routes": "Total Routes",
                "Avg_Rate": "Average Rate",
                "Min_Rate": "Lowest Rate",
                "Max_Rate": "Highest Rate"
            }
        )
else:
    # Original view - sorted by destination and rate only
    all_rates = filtered_df[["Country", "Destination", "Supplier", "Trunk", "Rate (inter)", "Min Dur", "Inc Dur"]].copy()
    all_rates = all_rates.sort_values(["Destination", "Rate (inter)"], ascending=[True, sort_ascending])
    all_rates["Rate (inter)"] = all_rates["Rate (inter)"].apply(lambda x: f"${x:.4f}")
    
    st.dataframe(
        all_rates,
        use_container_width=True,
        hide_index=True,
        height=400
    )

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#999;font-size:0.9rem;'>VOLF Communications © 2026 | VoIP Sales Intelligence Dashboard</p>",
    unsafe_allow_html=True
)