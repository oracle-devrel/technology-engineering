
BUCKET_NAME = "anomaly-detection-regression"
FOLDER_NAME = "daily_files"

# Must match the model training / deployment input features
FEATURE_COLS = [
    "Dept",
    "Temperature",
    "Fuel_Price",
    "CPI",
    "Unemployment",
    "Type",
    "Size",
]

DATE_COL = "Date"
TARGET_COL = "Weekly_Sales"

MONITORING_NAMESPACE = "walmart_sales_forecast"
MONITORING_METRIC_NAME = "weekly_sales"
COMPARTMENT='<your_compartment_ocid>'

ENDPOINT= "<your_endpoint>"

