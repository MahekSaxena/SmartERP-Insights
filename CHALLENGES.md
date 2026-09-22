# Challenges

## Source data did not contain inventory
The UCI dataset records sales transactions, not opening stock, goods receipts or goods issues. The solution is a clearly labeled demand-based inventory simulation with visible assumptions.

## Source fields did not equal SAP entities
An invoice number is not automatically an SAP billing document, and a stock code is not a complete Material Master. The solution uses an explicit mapping layer and states which fields are proxies.

## Returns and incomplete rows affect demand analysis
The source contains non-positive quantities and missing customer values. The sales view removes those records for this specific demand analysis and reports the action in the data-quality table.

## SAP process scope is larger than the dataset
The source cannot prove delivery, payment, supplier invoice, or document-flow timing. The solution models those workflow stages conceptually and avoids claiming actual SAP execution.

## Inventory statuses depend on assumptions
The derived stock status is useful for demonstrating the business rule, but it is not an operational inventory position. A real implementation would replace assumptions with material-plant-storage-location stock, movement and lead-time data.
