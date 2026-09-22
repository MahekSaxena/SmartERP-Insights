import pandas as pd

from src.data_pipeline import build_inventory, clean_sales, kpis


def sample_frame():
    return pd.DataFrame({
        "InvoiceNo": ["1", "1", "2", "2"],
        "StockCode": ["a", "b", "a", "a"],
        "Description": ["Red mug", "Blue pen", "Red mug", "Red mug"],
        "Quantity": [2, 3, -1, 2],
        "InvoiceDate": ["2011-01-01"] * 4,
        "UnitPrice": [5, 2, 5, 5],
        "CustomerID": [10, 10, 11, 11],
        "Country": ["United Kingdom"] * 4,
    })


def test_clean_sales_removes_returns_and_calculates_revenue():
    sales, quality = clean_sales(sample_frame())
    assert len(sales) == 3
    assert sales["revenue"].sum() == 26
    assert "Invalid-value handling" in quality["step"].tolist()


def test_inventory_rule_is_reproducible():
    sales, _ = clean_sales(sample_frame())
    inventory = build_inventory(sales)
    assert (inventory["current_stock"] == inventory["opening_stock"] + inventory["goods_received"] - inventory["goods_issued"]).all()
    assert (inventory["current_stock"] >= 0).all()
    assert ((inventory["target_stock"] - inventory["current_stock"]).clip(lower=0) >= 0).all()
    assert set(inventory["status"]).issubset({"Healthy", "Low Stock", "Out of Stock", "Overstocked"})


def test_kpis_have_expected_contract():
    sales, _ = clean_sales(sample_frame())
    inventory = build_inventory(sales)
    model = {"sales": sales, "inventory": inventory, "customers": sales[["customer_id"]].drop_duplicates(), "materials": inventory}
    assert kpis(model)["Total Orders"] == 2
