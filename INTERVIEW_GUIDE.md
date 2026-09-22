# Interview Guide

## 60-second explanation
I built SmartERP Insights, a small SAP-oriented retail analytics project. I used the public UCI Online Retail dataset, which contains invoice, product, quantity, price, date, customer and country fields. I cleaned dates, IDs, duplicates, missing keys and invalid quantities, then calculated revenue and created customer, material and sales views. Because the source had no inventory or supplier ledger, I built a transparent derived inventory model and labeled it as simulated. I mapped customers and materials to SAP master-data concepts, sales to SD, inventory and replenishment to MM, and revenue to a billing/FI integration discussion. The Streamlit dashboard shows KPIs, sales trends, stock-risk flags, a replenishment review queue, and simplified O2C/P2P workflows. It models SAP concepts; it does not claim SAP access or transaction execution.

## Two-minute explanation
The business problem was that a retailer needs to connect demand with availability and procurement decisions. I selected UCI Online Retail because it is public, understandable and has transaction-level fields for customers, materials, invoices, quantities, prices, dates and countries. The pipeline downloads the workbook, standardizes column names, parses dates and numeric fields, removes rows missing required analytical keys, removes exact duplicates, excludes returns for demand analysis, normalizes text and calculates revenue as quantity multiplied by unit price. I then created customer, material and sales tables and exported them to SQLite.

The main SAP learning was the mapping layer. Customer records represent Customer Master or Business Partner concepts, products represent Material Master, sales analysis is related to SAP SD, and inventory, goods movement and purchasing are related to SAP MM. Billing and payment are explained as SD/FI integration concepts. The app presents Order-to-Cash from sales order through delivery, goods issue, billing and payment, and Procure-to-Pay from low stock through purchase requisition, purchase order, goods receipt, supplier invoice and payment.

The source did not contain actual inventory, supplier, delivery or payment data. Instead of hiding that limitation, I created a derived inventory model: opening stock is two months of average demand, safety stock is 0.5 months, reorder level is demand plus safety stock, goods issued is one modeled month of demand, and goods received follows a simple order-line cadence assumption. The dashboard identifies products for replenishment review and shows revenue/customer/category patterns. The most important limitation is that stock findings are hypotheses until validated against real SAP material-plant-storage-location and movement data.

## Project questions

### What problem were you solving?
**Short answer:** I connected retail sales demand to inventory and procurement review.  
**Understand it:** Management needs more than revenue totals: it needs to know what sells, who buys it and which materials may need replenishment.

### Why this problem?
**Short answer:** It links analytics to common ERP decisions in sales, inventory and procurement.  
**Understand it:** It creates a natural bridge to SD, MM and basic FI integration without pretending to implement a full ERP.

### Why this dataset and where from?
**Short answer:** UCI Online Retail is a legitimate public transaction dataset with product, customer, invoice, quantity, price, date and country fields.  
**Understand it:** Those fields support sales and master-data analysis; inventory and supplier fields are not present and are explicitly derived.

### How did you clean it?
**Short answer:** I corrected types, standardized dates and text, removed missing analytical keys and exact duplicates, excluded non-positive sales quantities, and calculated revenue.  
**Understand it:** Each action is recorded in the in-app data-quality report with a reason.

### What assumptions and limitations did you make?
**Short answer:** Inventory is simulated from average demand; there are no actual stock, supplier, delivery, payment or SAP document records.  
**Understand it:** The model demonstrates the business rule only. In real SAP, I would replace it with material, plant, storage-location and movement data.

## SAP questions

### What is ERP?
**Short answer:** ERP integrates core business functions around shared data and processes.  
**Understand it:** Sales, procurement, inventory and finance can use connected master and transaction data.

### What is SAP?
**Short answer:** SAP is an enterprise software platform used to run and integrate business processes.  
**Understand it:** Its value is process integration, controls and a common data model, not just individual screens.

### What is S/4HANA?
**Short answer:** SAP S/4HANA is SAP's modern ERP suite built around the HANA database and a simplified data model.  
**Understand it:** It supports real-time operational processing and analytics in an integrated system.

### What are SD, MM and FI?
**Short answer:** SD supports sales, MM supports materials and procurement, and FI supports financial accounting.  
**Understand it:** O2C crosses SD and FI; P2P crosses MM and FI; inventory movements affect both stock and accounting in appropriate scenarios.

### What is master data versus transactional data?
**Short answer:** Master data describes stable business objects; transactional data records business events.  
**Understand it:** A material and customer are master-data examples; a sales order, goods receipt and billing document are transactions referencing them.

### What are Material, Customer and Vendor Master?
**Short answer:** They hold reusable attributes for products, customers and suppliers.  
**Understand it:** The project has material and customer views from source fields and a simulated supplier; it does not claim complete SAP master records.

### What are Plant, Storage Location and Sales Organization?
**Short answer:** Plant and storage location structure inventory responsibility; sales organization structures selling responsibility.  
**Understand it:** The project includes simulated plant/storage fields to show the organizational idea, but no source values existed.

### Explain O2C and P2P.
**Short answer:** O2C runs from customer order to cash collection; P2P runs from purchasing need to supplier payment.  
**Understand it:** O2C includes sales order, delivery, goods issue and billing. P2P includes requisition, purchase order, goods receipt and invoice/payment.

### Goods issue, goods receipt, sales order, purchase order and billing?
**Short answer:** Goods issue reduces stock when goods leave; goods receipt increases stock when goods arrive; sales and purchase orders record commitments; billing records the customer charge.  
**Understand it:** The app models these relationships, but only sales and derived stock evidence are populated from data.

### What is document flow?
**Short answer:** Document flow links related business documents across a process.  
**Understand it:** In O2C, a sales order can lead to delivery, goods issue and billing; the app shows this as a conceptual chain, not real document numbers.

## Project plus SAP

### How did you map the dataset to SAP?
**Short answer:** I mapped customer IDs to Customer/Business Partner, stock codes to Material Master candidates, invoices to sales-analysis transactions, and derived movements to MM concepts.  
**Understand it:** I distinguished source fields, proxies and simulated fields so the mapping stays honest.

### Why SD, MM and FI?
**Short answer:** SD explains selling and billing, MM explains stock and procurement, and FI explains the financial effect of billing and supplier invoices.  
**Understand it:** The project demonstrates integration points rather than claiming accounting postings.

### How would this work in real S/4HANA?
**Short answer:** I would extract authorized SAP data or use approved interfaces, map real document keys, and reconcile KPIs with operational reports.  
**Understand it:** Inventory would come from material/plant/storage-location stock and movement records; billing and payment would come from actual documents.

### What would you change with SAP access?
**Short answer:** Replace proxies with real master data, document flow, stock movements, lead times and financial postings, then validate every KPI with business owners.  
**Understand it:** The current app is an analytical prototype, not an ERP implementation.

## Technical questions

### Why Python, Pandas, Streamlit and SQL?
**Short answer:** Python and Pandas make cleaning and grouping readable, Streamlit quickly communicates results, and SQLite gives a simple relational output.  
**Understand it:** The stack is intentionally small so each transformation can be explained and reproduced.

### How did you calculate and validate KPIs?
**Short answer:** Revenue is quantity times unit price; orders are distinct invoice IDs; inventory follows a documented stock equation; focused tests check these contracts.  
**Understand it:** I would additionally reconcile against SAP totals in a real project.

### How did you create inventory?
**Short answer:** I used average monthly demand to derive opening stock, receipts, goods issue, current stock and reorder level.  
**Understand it:** These are simulation inputs, not source facts.

## Challenge questions

### What was hardest?
**Short answer:** Making the SAP mapping useful without overstating what the dataset contained.  
**Understand it:** The solution was to label source, derived and simulated fields and document boundaries.

### Which assumption are you least confident about?
**Short answer:** The two-month opening-stock assumption, because no actual stock ledger or lead times were available.  
**Understand it:** It is suitable for learning the calculation, not for purchasing decisions.

### What would you improve?
**Short answer:** Add real stock movements, supplier lead times, delivery dates, currencies, returns treatment and actual document keys.  
**Understand it:** Those additions would turn hypotheses into operational analysis.
