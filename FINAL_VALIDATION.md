# Final Validation Report

- [x] Dataset source verified: UCI Online Retail, official public archive.
- [x] Data cleaning verified: types, missing keys, duplicates, invalid values and normalization are implemented.
- [x] KPI calculations verified: revenue, orders, units, average order value, customers and materials use the cleaned model.
- [x] Inventory formulas verified: opening stock + goods received - goods issued = current stock.
- [x] Inventory bounds verified: corrected real-data model produces no negative current stock.
- [x] Procurement formulas verified: suggested quantity is `max(0, target_stock - current_stock)`.
- [x] SAP mappings reviewed: SD, MM, master data and basic FI integration are described as concepts.
- [x] O2C reviewed: actual, derived, modeled, proxy and unavailable evidence are distinguished.
- [x] P2P reviewed: derived, modeled, simulated and unavailable steps are distinguished.
- [x] Business insights reviewed: findings use FACT, EVIDENCE, BUSINESS IMPACT, SAP RELEVANCE and ACTION.
- [x] SAP claims checked for accuracy: no SAP connection, execution, configuration or posting is claimed.
- [x] UI reviewed: compact KPIs, GBP labels, readable chart labels and source/derived/simulated disclosures added.
- [x] Resume description generated using actual project results.

## Verified real-data snapshot

- Cleaned sales rows: 392,732
- Revenue: GBP 8,887,208.89
- Orders: 18,536
- Quantity sold: 5,165,886 units
- Customers: 4,339
- Materials: 3,665
- Low-stock review materials: 2,278
- Out-of-stock materials: 0
- Overstocked materials: 1,459

The inventory figures are derived educational estimates. They must be reconciled to real SAP material, plant, storage-location and movement data before operational use.

## Validation result

Python source compilation, the real-data pipeline, monthly revenue aggregation, inventory arithmetic smoke checks and the focused test suite passed. The project virtual environment reports `3 passed` for `tests/test_pipeline.py`.
