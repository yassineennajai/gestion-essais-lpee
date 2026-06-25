import pandas as pd

orders = pd.read_csv("data/olist_orders_dataset.csv")
orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])
print("Min date:", orders["order_purchase_timestamp"].min())
print("Max date:", orders["order_purchase_timestamp"].max())