from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from src.config import MODEL_VERSION
from src.data_pipeline import kpis, load_or_build_model

st.set_page_config(page_title="SmartERP Insights", page_icon="SAP", layout="wide")
st.title("SmartERP Insights")
st.caption("SAP-oriented sales, inventory and process analytics | Modeled using SAP concepts, not executed in SAP")


def compact_number(value: float) -> str:
    for divisor, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if abs(value) >= divisor:
            return f"{value / divisor:.2f}{suffix}"
    return f"{value:,.0f}"


def currency(value: float) -> str:
    return f"GBP {compact_number(value)}"


def data_lineage_box() -> None:
    st.info("SOURCE: UCI Online Retail transactions  |  DERIVED: revenue, demand metrics and inventory calculations  |  SIMULATED: supplier, plant, storage location and inventory assumptions")

@st.cache_resource(show_spinner="Downloading and preparing the public UCI dataset...")
def get_model(model_version: int):
    return load_or_build_model()

model = get_model(MODEL_VERSION)
sales, inventory, customers, materials, quality = (model[key] for key in ("sales", "inventory", "customers", "materials", "quality"))
metrics = kpis(model)

pages = ["Executive Dashboard", "Data Overview", "Sales Analytics", "Inventory Analytics", "Procurement Analysis", "SAP Business Mapping", "O2C Workflow", "P2P Workflow", "Business Insights", "Data Quality", "Methodology", "About the Dataset"]
page = st.sidebar.radio("Navigate", pages)
st.sidebar.info("Source: UCI Online Retail dataset\n\nDerived fields are marked in the methodology and README.")

if page == "Executive Dashboard":
    st.header("Executive Dashboard")
    st.caption("Currency: GBP (£) | All monetary values are represented in GBP because the source dataset is UK-based.")
    data_lineage_box()
    cols = st.columns(5)
    for col, label in zip(cols, ["Total Revenue", "Total Orders", "Total Quantity Sold", "Unique Customers", "Low Stock Products"]):
        value = metrics[label]
        col.metric(label, currency(value) if "Revenue" in label else compact_number(value))
    monthly = sales.assign(month=sales["invoice_date"].dt.to_period("M").astype(str)).groupby("month", as_index=False)["revenue"].sum()
    monthly = monthly.rename(columns={"revenue": "Revenue (GBP)"})
    left, right = st.columns(2)
    left.plotly_chart(px.line(monthly, x="month", y="Revenue (GBP)", markers=True, title="Revenue by Month (GBP)", labels={"month": "Month", "Revenue (GBP)": "Revenue (GBP)"}), use_container_width=True)
    status_counts = inventory["status"].value_counts().rename_axis("Status").reset_index(name="Number of Materials")
    right.plotly_chart(px.bar(status_counts, x="Status", y="Number of Materials", title="Inventory Status (Number of Materials)"), use_container_width=True)
    st.subheader("Decision summary")
    st.write("Use high-revenue products and low-stock products as the first review queue. This dashboard estimates inventory because the source dataset has no stock ledger.")

elif page == "Data Overview":
    st.header("Data Overview")
    st.write(f"The cleaned analytical sales table contains **{len(sales):,} rows**, {sales['invoice_id'].nunique():,} invoices, and {sales['material_id'].nunique():,} materials.")
    st.dataframe(sales.head(100), use_container_width=True)
    st.subheader("Conceptual entities")
    st.dataframe(pd.DataFrame({"Entity": ["Customer", "Material", "Sales Order / Item", "Inventory", "Supplier"], "Source": ["customer_id, country", "material_id, description", "invoice_id, invoice_date, quantity", "Derived from demand assumptions", "Simulated default supplier"], "SAP concept": ["Customer / Business Partner", "Material Master", "SD Sales Order", "MM Inventory Management", "Vendor / Business Partner"]}), use_container_width=True)

elif page == "Sales Analytics":
    st.header("Sales Analytics")
    st.caption("Currency: GBP (£) | Historical sales analysis from cleaned UCI transactions.")
    left, right = st.columns(2)
    top_products = sales.groupby("material_description", as_index=False)["revenue"].sum().nlargest(10, "revenue")
    top_customers = customers.nlargest(10, "total_revenue")
    left.plotly_chart(px.bar(top_products.sort_values("revenue"), x="revenue", y="material_description", orientation="h", title="Top 10 Products by Revenue (GBP)", labels={"revenue": "Revenue (GBP)", "material_description": "Material"}), use_container_width=True)
    right.plotly_chart(px.bar(top_customers.sort_values("total_revenue"), x="total_revenue", y="customer_id", orientation="h", title="Top 10 Customers by Revenue (GBP)", labels={"total_revenue": "Revenue (GBP)", "customer_id": "Customer ID"}), use_container_width=True)
    st.plotly_chart(px.bar(sales.groupby("region", as_index=False)["revenue"].sum(), x="region", y="revenue", title="Revenue by Region (GBP)", labels={"revenue": "Revenue (GBP)", "region": "Region"}), use_container_width=True)

elif page == "Inventory Analytics":
    st.header("Inventory Analytics")
    st.warning("DERIVED / MODELED INVENTORY: Inventory is not present in the UCI source. The model uses a defined one-month issue period and documented replenishment assumptions.")
    st.caption("DERIVED / MODELED FIELDS: average demand, safety stock, opening stock, goods received, goods issued, current stock, reorder level and target stock.")
    st.plotly_chart(px.scatter(inventory, x="avg_monthly_demand", y="current_stock", color="status", hover_data=["material_description"], title="Average Monthly Demand vs Current Stock (units)", labels={"avg_monthly_demand": "Average Monthly Demand (units)", "current_stock": "Current Stock (units)", "status": "Status"}), use_container_width=True)
    st.dataframe(inventory.sort_values(["status", "current_stock"])[["material_id", "material_description", "avg_monthly_demand", "safety_stock", "opening_stock", "goods_received", "goods_issued", "current_stock", "reorder_level", "target_stock", "status", "plant", "storage_location"]].head(100), use_container_width=True)

elif page == "Procurement Analysis":
    st.header("Procurement Analysis")
    purchase = inventory[inventory["status"].isin(["Low Stock", "Out of Stock"])].copy()
    purchase["suggested_purchase_qty"] = (purchase["target_stock"] - purchase["current_stock"]).clip(lower=0)
    st.metric("Materials requiring review", f"{len(purchase):,}")
    st.caption("Suggested purchase quantity = max(0, target stock - current stock). Target stock is reorder level plus one month of average demand.")
    st.dataframe(purchase[["material_id", "material_description", "current_stock", "reorder_level", "target_stock", "suggested_purchase_qty", "supplier_id"]].sort_values("suggested_purchase_qty", ascending=False), use_container_width=True)
    st.info("This is a derived purchase requirement suggestion, not an actual SAP purchase requisition or purchase order.")

elif page == "SAP Business Mapping":
    st.header("SAP Business Mapping")
    st.table(pd.DataFrame({"Business Area": ["Sales", "Inventory", "Procurement", "Billing", "Master Data", "Analytics"], "SAP Module / Concept": ["SAP SD", "SAP MM", "SAP MM Purchasing", "SAP SD + FI integration", "Customer / Material / Vendor Master", "SAP-oriented reporting"], "Project Representation": ["Invoice and customer sales analysis", "Derived stock, goods issue and plant fields", "Replenishment analysis", "Revenue and billing proxy", "Normalized customer/material plus simulated supplier", "Streamlit KPI dashboard"], "What I Learned": ["Order-to-Cash concepts", "Material and inventory management", "Purchase process concepts", "Revenue and receivables concept", "Master-data concepts", "Business-process analysis"]}))
    st.subheader("Important boundary")
    st.write("The project models SAP concepts and document relationships. It does not connect to SAP, execute transactions, create master records, or post financial documents.")

elif page == "O2C Workflow":
    st.header("Order-to-Cash (O2C)")
    st.markdown("1. Customer -> 2. Sales Order -> 3. Availability Check -> 4. Delivery -> 5. Goods Issue -> 6. Billing -> 7. Payment")
    st.table(pd.DataFrame({"Stage": ["2. Sales Order", "3. Availability Check", "4. Delivery", "5. Goods Issue", "6. Billing", "7. Payment"], "Evidence Type": ["ACTUAL DATA EVIDENCE", "DERIVED DATA EVIDENCE", "CONCEPTUAL / MODELED", "DERIVED DATA EVIDENCE", "ANALYTICAL PROXY", "NOT AVAILABLE"], "Project evidence": ["invoice_id, customer_id, material_id", "current_stock and reorder_level", "Shipment step is not in source", "goods_issued in inventory model", "invoice revenue by transaction", "Payment data is not in source"]}))
    st.info("Document flow is represented conceptually: one retail invoice is treated as an analytical proxy for a sales transaction, not as a real SAP billing document.")

elif page == "P2P Workflow":
    st.header("Procure-to-Pay (P2P)")
    st.markdown("1. Low Stock -> 2. Purchase Requisition -> 3. Purchase Order -> 4. Goods Receipt -> 5. Supplier Invoice -> 6. Payment")
    st.table(pd.DataFrame({"Stage": ["1. Low Stock", "2. Purchase Requisition", "3. Purchase Order", "4. Goods Receipt", "5. Supplier Invoice", "6. Payment"], "Evidence Type": ["DERIVED", "DERIVED", "MODELED", "SIMULATED", "NOT AVAILABLE", "NOT AVAILABLE"], "Project implementation": ["Derived inventory status", "Suggested purchase quantity", "No document created", "Simulated receipt assumption", "No supplier invoice in source", "No payment data in source"], "SAP relevance": ["MM inventory planning", "MM purchasing demand", "MM purchasing document", "MM inventory posting", "FI invoice verification", "FI accounts payable"]}))

elif page == "Business Insights":
    st.header("SAP-Oriented Business Insights")
    top = sales.groupby("material_description", as_index=False).agg(revenue=("revenue", "sum"), quantity=("quantity", "sum")).merge(inventory[["material_description", "status", "current_stock"]], on="material_description", how="left")
    finding = top.sort_values(["quantity", "revenue"], ascending=False).iloc[0]
    st.subheader("Finding 1: Demand Concentration")
    st.write(f"**FACT:** {finding['material_description']} has the highest historical demand in this analytical view. **EVIDENCE:** {finding['quantity']:,.0f} units and GBP {finding['revenue']:,.0f} revenue. **BUSINESS IMPACT:** availability may be important for a high-demand material. **SAP RELEVANCE:** Material Master and MM inventory planning. **ACTION:** review replenishment parameters and lead-time assumptions.")
    low = inventory[inventory["status"].isin(["Low Stock", "Out of Stock"])].shape[0]
    st.subheader("Finding 2: Replenishment Review Queue")
    st.write(f"**FACT:** {low:,} materials are flagged for replenishment review by the simulation. **EVIDENCE:** current stock is at or below the modeled reorder level. **BUSINESS IMPACT:** if the estimate reflects operational reality, availability could require review. **SAP RELEVANCE:** MM purchasing and inventory management. **ACTION:** validate stock and lead-time data before creating a purchase requisition.")
    st.subheader("Finding 3: Process Bottlenecks")
    st.table(pd.DataFrame({"Issue": ["Stock-out risk", "Overstock risk", "Low-performing materials"], "Evidence": ["Derived status", "Derived status", "Low revenue ranking"], "Type": ["FACT + hypothesis", "FACT + hypothesis", "FACT"], "Potential improvement": ["Validate safety stock and replenishment timing", "Review demand and holding cost", "Review assortment and pricing"]}))

elif page == "Data Quality":
    st.header("Data Quality Report")
    quality_display = quality.copy()
    quality_display["step"] = [
        "1. Type and Date Correction",
        "2. Missing-Value Handling",
        "3. Duplicate Detection",
        "4. Invalid-Value Handling",
        "5. Normalization and Revenue",
    ]
    st.dataframe(quality_display, use_container_width=True)
    st.metric("Final cleaned rows retained", f"{len(sales):,}")
    st.write("The report distinguishes rows inspected, rows removed, rows retained and rows standardized. Revenue is calculated as quantity multiplied by unit price after invalid quantities and prices are excluded.")

elif page == "Methodology":
    st.header("Methodology and Assumptions")
    st.markdown("""### Project at a glance
**Problem:** Connect sales demand with inventory and procurement decisions.  
**Dataset:** UCI Online Retail.  
**SAP areas:** SAP SD, SAP MM and basic FI integration concepts.  
**Business processes:** Order-to-Cash and Procure-to-Pay.  
**Core analysis:** Sales, inventory, procurement and data quality.  
**Output:** SAP-oriented business analytics dashboard.

### Method steps
1. **Problem Identification:** Connect sales demand with stock and purchasing decisions.
2. **Dataset Selection:** Use UCI Online Retail because it contains customer, material, invoice, quantity, price, date and country fields.
3. **Data Cleaning:** Parse dates and measures, remove missing keys, duplicates, returns and invalid prices, then normalize identifiers.
4. **Data Modeling:** Create customer, material, sales, inventory and simulated supplier views.
5. **SAP Mapping:** Map customers to Business Partner, products to Material Master, selling to SD, stock/procurement to MM and revenue to an FI integration discussion.
6. **Inventory Modeling:** DERIVED / MODELED: Opening stock = 2 x average monthly demand; safety stock = 0.5 x demand; reorder level = demand + safety stock; target stock = reorder level + demand; goods received uses a documented simulated cadence; current stock = opening stock + goods received - goods issued.
7. **KPI Creation:** Calculate revenue, orders, units, average order value, customers, products and status counts from the same model.
8. **Business Insight Generation:** Separate FACT, EVIDENCE, BUSINESS IMPACT, SAP RELEVANCE and ACTION.
9. **Validation:** Check revenue, stock arithmetic, status rules, purchase quantities and the real-data pipeline.
10. **Limitations:** The source has no stock ledger, suppliers, deliveries, payments, tax, currency conversion or SAP document numbers.

### My contribution
I defined the problem, selected and cleaned the dataset, mapped business processes to SAP concepts, designed the inventory methodology, created KPIs and insights, built the dashboard, exported SQLite tables and validated the calculations. I did not configure SAP or execute SAP transactions.""")
    st.stop()

elif page == "About the Dataset":
    st.header("About the Dataset")
    st.subheader("Project at a glance")
    st.write("Problem: connect sales demand with inventory and procurement decisions. | Dataset: UCI Online Retail | SAP areas: SD, MM and basic FI integration | Processes: O2C and P2P | Output: SAP-oriented business analytics dashboard.")
    data_lineage_box()
    st.write("The source is the UCI Machine Learning Repository Online Retail dataset, collected from a UK-based online retailer and published for public research. It contains invoice number, product code, description, quantity, invoice date, unit price, customer ID and country.")
    st.link_button("Open UCI dataset page", "https://archive.ics.uci.edu/dataset/352/online+retail")
    st.write("All monetary values are represented in GBP because the source dataset is UK-based. No private or personal data was added. Customer IDs are source identifiers, not names. Inventory, supplier, plant and storage-location fields are derived or simulated and are labeled accordingly.")
