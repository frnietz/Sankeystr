import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- Page Configuration ---
st.set_page_config(page_title="Sankey Generator", layout="wide")

# --- Language Dictionary ---
TRANS = {
    "English": {
        "title": "Financial Sankey Generator",
        "upload_header": "Upload Income Statement (Excel)",
        "manual_header": "Or Enter Data Manually",
        "rev_label": "Revenue Sources (e.g., iPhone, Services)",
        "cogs_label": "Cost of Revenue (COGS)",
        "exp_label": "Operating Expenses & Tax",
        "calculate": "Generate Diagram",
        "error_neg": "Error: Expenses exceed Gross Profit!",
        "net_income": "Net Income",
        "gross_profit": "Gross Profit",
        "total_revenue": "Total Revenue",
        "download_template": "Download Excel Template",
        "source_col": "Name",
        "value_col": "Value",
        "type_col": "Type (Revenue/COGS/Expense)",
        "instr": "Upload an Excel file with columns: **Name**, **Value**, **Type**."
    },
    "Türkçe": {
        "title": "Finansal Sankey Oluşturucu",
        "upload_header": "Gelir Tablosu Yükle (Excel)",
        "manual_header": "Veya Verileri Manuel Girin",
        "rev_label": "Gelir Kaynakları (örn. Ürün Satışı, Hizmetler)",
        "cogs_label": "Satışların Maliyeti (COGS)",
        "exp_label": "Faaliyet Giderleri ve Vergi",
        "calculate": "Diyagramı Oluştur",
        "error_neg": "Hata: Giderler Brüt Kârı aşıyor!",
        "net_income": "Net Kâr",
        "gross_profit": "Brüt Kâr",
        "total_revenue": "Toplam Gelir",
        "download_template": "Excel Şablonunu İndir",
        "source_col": "İsim",
        "value_col": "Değer",
        "type_col": "Tür (Gelir/Maliyet/Gider)",
        "instr": "Şu sütunlara sahip bir Excel yükleyin: **İsim**, **Değer**, **Tür**."
    }
}

# --- Sidebar: Language & Inputs ---
lang = st.sidebar.radio("Language / Dil", ["English", "Türkçe"])
t = TRANS[lang]

st.title(t["title"])

# Data Holders
revenue_items = {}
cogs_value = 0.0
expense_items = {}

# --- Tab Selection: Upload vs Manual ---
tab1, tab2 = st.tabs(["📂 Upload Excel", "✍️ Manual Input"])

with tab1:
    st.markdown(t["instr"])
    
    # Template Creator for User Convenience
    data = {
        'Name': ['iPhone', 'Services', 'Cost of Sales', 'R&D', 'Tax'],
        'Value': [46.2, 25.0, 51.0, 8.3, 13.8],
        'Type': ['Revenue', 'Revenue', 'COGS', 'Expense', 'Expense']
    }
    df_template = pd.DataFrame(data)
    
    # Allow user to download template
    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df(df_template)
    st.download_button(label=t["download_template"], data=csv, file_name='template.csv', mime='text/csv')

    uploaded_file = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx"])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Normalize column names for processing
            df.columns = [c.lower() for c in df.columns]
            
            # Extract Data based on 'type' column (flexible matching)
            for index, row in df.iterrows():
                name = str(row[0]) # First column is Name
                val = float(row[1]) # Second column is Value
                row_type = str(row[2]).lower() # Third column is Type
                
                if 'rev' in row_type or 'gelir' in row_type:
                    revenue_items[name] = val
                elif 'cog' in row_type or 'cost' in row_type or 'maliyet' in row_type:
                    cogs_value += val
                elif 'exp' in row_type or 'gider' in row_type or 'tax' in row_type or 'vergi' in row_type:
                    expense_items[name] = val
            
            st.success(f"Loaded {len(df)} rows successfully!")
            
        except Exception as e:
            st.error(f"Error reading file: {e}")

with tab2:
    st.subheader(t["rev_label"])
    col1, col2 = st.columns(2)
    with col1:
        r1_name = st.text_input("Source 1 Name", "Product A")
        r1_val = st.number_input("Source 1 Value", min_value=0.0, value=100.0)
    with col2:
        r2_name = st.text_input("Source 2 Name", "Services")
        r2_val = st.number_input("Source 2 Value", min_value=0.0, value=50.0)
    
    # Add manual inputs to dictionary
    revenue_items[r1_name] = r1_val
    revenue_items[r2_name] = r2_val
    
    st.divider()
    
    cogs_value = st.number_input(t["cogs_label"], min_value=0.0, value=60.0)
    
    st.divider()
    
    st.subheader(t["exp_label"])
    e1_name = st.text_input("Expense 1 Name", "R&D")
    e1_val = st.number_input("Expense 1 Value", min_value=0.0, value=20.0)
    
    expense_items[e1_name] = e1_val


# --- Logic: Build the Sankey ---

# 1. Calculate Totals
total_revenue = sum(revenue_items.values())
gross_profit = total_revenue - cogs_value
total_expenses = sum(expense_items.values())
net_income = gross_profit - total_expenses

if net_income < 0:
    st.warning("⚠️ Warning: Net Income is negative. The diagram handles losses differently, but for this demo, ensure Revenue > Expenses.")

# 2. Define Lists for Plotly
labels = []
source_indices = []
target_indices = []
values = []

# Helper to get index of a label (adding it if new)
def get_idx(name):
    if name not in labels:
        labels.append(name)
    return labels.index(name)

# 3. Build Flows

# Flow: Revenue Sources -> Total Revenue
total_rev_idx = get_idx(t["total_revenue"])

for name, val in revenue_items.items():
    if val > 0:
        idx = get_idx(name)
        source_indices.append(idx)
        target_indices.append(total_rev_idx)
        values.append(val)

# Flow: Total Revenue -> COGS & Gross Profit
cogs_idx = get_idx(t["cogs_label"])
gp_idx = get_idx(t["gross_profit"])

# Link to COGS
if cogs_value > 0:
    source_indices.append(total_rev_idx)
    target_indices.append(cogs_idx)
    values.append(cogs_value)

# Link to Gross Profit
if gross_profit > 0:
    source_indices.append(total_rev_idx)
    target_indices.append(gp_idx)
    values.append(gross_profit)

# Flow: Gross Profit -> Expenses & Net Income
for name, val in expense_items.items():
    if val > 0:
        exp_idx = get_idx(name)
        source_indices.append(gp_idx)
        target_indices.append(exp_idx)
        values.append(val)

# Flow: Gross Profit -> Net Income (Remaining)
if net_income > 0:
    ni_idx = get_idx(t["net_income"])
    source_indices.append(gp_idx)
    target_indices.append(ni_idx)
    values.append(net_income)

# --- Render Chart ---
st.divider()

if total_revenue > 0:
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color="blue"
        ),
        link=dict(
            source=source_indices,
            target=target_indices,
            value=values,
            color='rgba(200, 200, 200, 0.5)'  # Transparent Grey
        )
    )])

    fig.update_layout(title_text=f"{t['title']} ({lang})", font_size=14, height=600)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Enter data or upload a file to see the diagram.")

