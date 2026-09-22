from __future__ import annotations

import sqlite3
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

import numpy as np
import pandas as pd

from .config import DATASET_URL, MODEL_VERSION, RAW_FILE, SQLITE_FILE

REQUIRED_INVENTORY_COLUMNS = {
    "material_id",
    "material_description",
    "avg_monthly_demand",
    "safety_stock",
    "opening_stock",
    "goods_received",
    "goods_issued",
    "current_stock",
    "reorder_level",
    "target_stock",
    "status",
}


def download_dataset(force: bool = False) -> Path:
    """Download the public UCI workbook once and return its local path."""
    if force or not RAW_FILE.exists():
        with urlopen(DATASET_URL, timeout=60) as response:
            archive = BytesIO(response.read())
        with ZipFile(archive) as zip_file:
            workbook_name = next(name for name in zip_file.namelist() if name.lower().endswith(".xlsx"))
            RAW_FILE.write_bytes(zip_file.read(workbook_name))
    return RAW_FILE


def load_raw(path: str | Path | None = None) -> pd.DataFrame:
    source = Path(path) if path else download_dataset()
    frame = pd.read_excel(source)
    return frame.rename(
        columns={
            "InvoiceNo": "invoice_id",
            "StockCode": "material_id",
            "Description": "material_description",
            "Quantity": "quantity",
            "InvoiceDate": "invoice_date",
            "UnitPrice": "unit_price",
            "CustomerID": "customer_id",
            "Country": "country",
        }
    )


def clean_sales(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = raw.rename(
        columns={
            "InvoiceNo": "invoice_id",
            "StockCode": "material_id",
            "Description": "material_description",
            "Quantity": "quantity",
            "InvoiceDate": "invoice_date",
            "UnitPrice": "unit_price",
            "CustomerID": "customer_id",
            "Country": "country",
        }
    ).copy()
    initial_rows = len(frame)
    report: list[dict[str, object]] = []

    frame["invoice_date"] = pd.to_datetime(frame["invoice_date"], errors="coerce")
    frame["quantity"] = pd.to_numeric(frame["quantity"], errors="coerce")
    frame["unit_price"] = pd.to_numeric(frame["unit_price"], errors="coerce")
    report.append({"step": "Type and date correction", "action": "Parsed dates and numeric measures", "rows_inspected": initial_rows, "rows_removed": 0, "rows_retained": initial_rows, "rows_standardized": initial_rows, "reason": "Makes filtering and aggregation reliable"})

    missing_before = int(frame.isna().any(axis=1).sum())
    frame = frame.dropna(subset=["invoice_id", "material_id", "invoice_date", "quantity", "unit_price", "customer_id"])
    report.append({"step": "Missing-value handling", "action": "Removed rows missing keys, quantity, price, or customer", "rows_inspected": initial_rows, "rows_removed": missing_before, "rows_retained": len(frame), "rows_standardized": 0, "reason": "Required for customer, product, and revenue analysis"})

    duplicate_count = int(frame.duplicated().sum())
    frame = frame.drop_duplicates()
    report.append({"step": "Duplicate detection", "action": "Removed exact duplicate transactions", "rows_inspected": len(frame) + duplicate_count, "rows_removed": duplicate_count, "rows_retained": len(frame), "rows_standardized": 0, "reason": "Prevents double-counting revenue and quantity"})

    invalid_count = int(((frame["quantity"] <= 0) | (frame["unit_price"] < 0)).sum())
    frame = frame[(frame["quantity"] > 0) & (frame["unit_price"] >= 0)].copy()
    report.append({"step": "Invalid-value handling", "action": "Excluded returns and non-positive sales measures", "rows_inspected": len(frame), "rows_removed": invalid_count, "rows_retained": len(frame), "rows_standardized": 0, "reason": "This dashboard analyzes fulfilled sales demand"})

    frame["invoice_id"] = frame["invoice_id"].astype(str).str.strip()
    frame["material_id"] = frame["material_id"].astype(str).str.strip().str.upper()
    frame["material_description"] = frame["material_description"].astype(str).str.strip().str.title()
    frame["country"] = frame["country"].astype(str).str.strip().str.title()
    frame["customer_id"] = frame["customer_id"].astype(int).astype(str)
    frame["revenue"] = (frame["quantity"] * frame["unit_price"]).round(2)
    frame["category"] = frame["material_description"].str.split().str[0].replace("Nan", "Other")
    frame["region"] = np.where(frame["country"].eq("United Kingdom"), "United Kingdom", "International")
    report.append({"step": "Normalization and revenue", "action": "Standardized identifiers/text and calculated quantity x price", "rows_inspected": len(frame), "rows_removed": 0, "rows_retained": len(frame), "rows_standardized": len(frame), "reason": "Creates consistent analytical master-data fields"})

    quality = pd.DataFrame(report)
    return frame.reset_index(drop=True), quality


def build_inventory(sales: pd.DataFrame) -> pd.DataFrame:
    """Create a transparent one-month inventory simulation by material."""
    summary = sales.groupby(["material_id", "material_description", "category"], as_index=False).agg(
        total_quantity_sold=("quantity", "sum"), order_lines=("invoice_id", "nunique"),
    )
    months = max(1, sales["invoice_date"].dt.to_period("M").nunique())
    summary["avg_monthly_demand"] = (summary["total_quantity_sold"] / months).round(1)
    summary["safety_stock"] = np.ceil(summary["avg_monthly_demand"] * 0.5).astype(int)
    summary["reorder_level"] = np.ceil(summary["avg_monthly_demand"] + summary["safety_stock"]).astype(int)
    summary["target_stock"] = np.ceil(summary["reorder_level"] + summary["avg_monthly_demand"]).astype(int)
    summary["opening_stock"] = np.ceil(summary["avg_monthly_demand"] * 2).astype(int)
    median_lines = summary["order_lines"].median()
    receipt_months = np.where(summary["order_lines"] >= median_lines, 0.5, 2.0)
    summary["goods_received"] = np.ceil(summary["avg_monthly_demand"] * receipt_months).astype(int)
    summary["goods_issued"] = np.ceil(summary["avg_monthly_demand"]).astype(int)
    summary["current_stock"] = summary["opening_stock"] + summary["goods_received"] - summary["goods_issued"]
    summary["upper_stock_threshold"] = np.ceil(summary["avg_monthly_demand"] * 2.5).astype(int)
    summary["status"] = np.select(
        [summary["current_stock"] <= 0, summary["current_stock"] <= summary["reorder_level"], summary["current_stock"] > summary["upper_stock_threshold"]],
        ["Out of Stock", "Low Stock", "Overstocked"], default="Healthy",
    )
    summary["plant"] = "UK01"
    summary["storage_location"] = "0001"
    summary["supplier_id"] = "SIM-DEFAULT"
    return summary


def build_model(path: str | Path | None = None, write_sql: bool = True) -> dict[str, pd.DataFrame]:
    sales, quality = clean_sales(load_raw(path))
    inventory = build_inventory(sales)
    customers = sales.groupby(["customer_id", "country", "region"], as_index=False).agg(total_revenue=("revenue", "sum"), order_count=("invoice_id", "nunique"))
    materials = sales[["material_id", "material_description", "category"]].drop_duplicates().merge(inventory, on=["material_id", "material_description", "category"], how="left")
    if write_sql:
        with sqlite3.connect(SQLITE_FILE) as connection:
            for name, frame in {"sales": sales, "inventory": inventory, "customers": customers, "materials": materials, "quality_report": quality}.items():
                frame.to_sql(name, connection, if_exists="replace", index=False)
            pd.DataFrame([{"model_version": MODEL_VERSION}]).to_sql("model_metadata", connection, if_exists="replace", index=False)
    return {"sales": sales, "inventory": inventory, "customers": customers, "materials": materials, "quality": quality}


def load_or_build_model(path: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Reuse the processed SQLite model until the source workbook changes."""
    source = Path(path) if path else download_dataset()
    rebuild = False
    if SQLITE_FILE.exists() and SQLITE_FILE.stat().st_mtime >= source.stat().st_mtime:
        with sqlite3.connect(SQLITE_FILE) as connection:
            try:
                version = int(pd.read_sql_query("SELECT model_version FROM model_metadata LIMIT 1", connection).iloc[0, 0])
            except (pd.errors.DatabaseError, IndexError, KeyError):
                version = 0
            try:
                inventory_columns = set(pd.read_sql_query("SELECT * FROM inventory LIMIT 0", connection).columns) if version == MODEL_VERSION else set()
            except pd.errors.DatabaseError:
                inventory_columns = set()
            rebuild = version != MODEL_VERSION or not REQUIRED_INVENTORY_COLUMNS.issubset(inventory_columns)
            if not rebuild:
                model = {
                    name: pd.read_sql_query(f"SELECT * FROM {name}", connection)
                    for name in ("sales", "inventory", "customers", "materials")
                }
                model["quality"] = pd.read_sql_query("SELECT * FROM quality_report", connection)
        if not rebuild:
            model["sales"]["invoice_date"] = pd.to_datetime(model["sales"]["invoice_date"], errors="coerce")
            return model
    return build_model(source)


def kpis(model: dict[str, pd.DataFrame]) -> dict[str, int | float]:
    sales, inventory, customers, materials = (model[key] for key in ("sales", "inventory", "customers", "materials"))
    return {
        "Total Revenue": float(sales["revenue"].sum()),
        "Total Orders": int(sales["invoice_id"].nunique()),
        "Total Quantity Sold": int(sales["quantity"].sum()),
        "Average Order Value": float(sales.groupby("invoice_id")["revenue"].sum().mean()),
        "Unique Customers": int(customers["customer_id"].nunique()),
        "Unique Products": int(materials["material_id"].nunique()),
        "Low Stock Products": int((inventory["status"] == "Low Stock").sum()),
        "Out-of-Stock Products": int((inventory["status"] == "Out of Stock").sum()),
        "Overstocked Products": int((inventory["status"] == "Overstocked").sum()),
    }
