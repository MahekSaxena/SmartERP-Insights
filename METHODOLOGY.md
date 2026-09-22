# Methodology

## Project at a glance

- Problem: connect sales demand with inventory and procurement decisions.
- Dataset: UCI Online Retail.
- SAP areas: SAP SD, SAP MM and basic FI integration concepts.
- Business processes: Order-to-Cash and Procure-to-Pay.
- Core analysis: sales, inventory, procurement and data quality.
- Output: SAP-oriented business analytics dashboard.

## 1. Problem identification
Retail decisions improve when sales demand, availability and replenishment are reviewed together. The project asks which materials and customers matter most and which materials require stock review. The result is a focused set of management questions rather than a simulated ERP system.

## 2. Dataset selection
UCI Online Retail was selected because it is public, transaction-level, compact enough to understand, and includes order/invoice, material, quantity, price, date, customer and country fields.

## 3. Data understanding
The raw workbook is ingested with Pandas. The pipeline renames source columns to business-friendly names and creates sales, customer and material views.

## 4. Data cleaning
Dates and measures are parsed; missing analytical keys are removed; exact duplicates are removed; returns/non-positive quantities and invalid prices are excluded for the sales-demand view; IDs and descriptions are normalized; revenue is calculated as `quantity * unit_price`.

## 5. Data model
Customer: `customer_id`, `country`, `region`. Material: `material_id`, description, category. Sales Order/Item proxy: `invoice_id`, date, customer, material, quantity, price, revenue. Inventory: derived stock movements and status. Supplier: one simulated default supplier because the source has no supplier field.

## 6. SAP mapping
Customer is mapped to Customer Master/Business Partner, material to Material Master, invoice-level sales to SD sales analysis, plant/storage location to MM organizational context, goods issued/received to inventory movements, and revenue to a billing/FI integration concept.

## 7. Process modeling
O2C is modeled as customer request, sales order, availability check, delivery, goods issue, billing and payment. P2P is modeled as low stock, purchase requisition, purchase order, goods receipt, supplier invoice and payment. Only the analytical evidence available in the source is populated.

## 8. KPI development
The app calculates revenue, orders, quantity, average order value, unique customers/products, and inventory-status counts from the cleaned tables.

## 9. Inventory assumptions
The model uses a defined one-month issue period so historical sales are not incorrectly subtracted from a short modeled stock period:

- Average monthly demand = total cleaned quantity / number of calendar months.
- Opening stock = 2 x average monthly demand.
- Safety stock = 0.5 x average monthly demand.
- Reorder level = average monthly demand + safety stock.
- Target stock = reorder level + one month of average demand.
- Goods issued = one month of average monthly demand.
- Goods received = 0.5 demand-months for materials at/above median order-line frequency, otherwise 2 demand-months. This is a simple simulated replenishment cadence, not source data.
- Current stock = opening stock + goods received - goods issued.
- Upper stock threshold = 2.5 x average monthly demand.

Status rules are: Out of Stock when current stock <= 0; Low Stock when current stock is above 0 and at/below reorder level; Overstocked when current stock is above the upper threshold; otherwise Healthy. Suggested purchase quantity is `max(0, target stock - current stock)`.

## 10. Validation
`tests/test_pipeline.py` checks return removal, revenue calculation, stock arithmetic and KPI contracts. A production implementation should add reconciliation to real SAP stock and document data.

## 11. Limitations
The source has no stock ledger, supplier, delivery, payment, tax, currency conversion, plant, storage location or actual SAP document flow. Findings about inventory are hypotheses until validated against operational records.

## My contribution
I defined the business problem, selected and analyzed the UCI dataset, cleaned and normalized the data, mapped business entities and workflows to SAP concepts, designed the inventory methodology, created KPIs and business insights, built the Streamlit dashboard, exported the analytical model to SQLite, and validated the formulas and status rules. I did not configure SAP or execute SAP transactions.
