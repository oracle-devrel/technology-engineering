MODEL_ID = "ocid1.generativeaimodel.oc1.eu-frankfurt-1.YOUR_MODEL_ID"
SERVICE_ENDPOINT = "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"
COMPARTMENT_ID = "ocid1.compartment.oc1..YOUR_COMPARTMENT_ID"
AGENT_ENDPOINT_ID = "ocid1.genaiagentendpoint.oc1.eu-frankfurt-1.YOUR_AGENT_ENDPOINT_ID"
SQL_AGENT_ID = "ocid1.genaiagentendpoint.oc1.eu-frankfurt-1.YOUR_AGENT_ENDPOINT_ID"
SQL_AGENT_ENDPOINT = "https://agent-runtime.generativeai.eu-frankfurt-1.oci.oraclecloud.com"

TEMPERATURE = 0.1
MAX_TOKENS = 1024
TOP_P = 0.9
MAX_ROWS_IN_CHART = 50
CHART_EXPORT_FORMAT = "json"
DEBUG = False
AUTH = "API_KEY"

# Database Schema - Customize for your database
DATABASE_SCHEMA = {
    "CUSTOMERS": [
        "CUSTOMER_ID", "CUSTOMER_NAME", "EMAIL", "SIGNUP_DATE", "SEGMENT",
        "COUNTRY", "LIFETIME_VALUE", "CREATION_DATE", "CREATED_BY",
        "LAST_UPDATED_DATE", "LAST_UPDATED_BY"
    ],
    "PRODUCTS": [
        "PRODUCT_ID", "PRODUCT_NAME", "CATEGORY", "PRICE", "COST",
        "STOCK_QUANTITY", "LAUNCH_DATE", "CREATION_DATE", "CREATED_BY",
        "LAST_UPDATED_DATE", "LAST_UPDATED_BY"
    ],
    "ORDERS": [
        "ORDER_ID", "CUSTOMER_ID", "ORDER_DATE", "TOTAL_AMOUNT", "STATUS",
        "REGION", "SALES_REP", "CREATION_DATE", "CREATED_BY",
        "LAST_UPDATED_DATE", "LAST_UPDATED_BY"
    ],
    "ORDER_ITEMS": [
        "ORDER_ITEM_ID", "ORDER_ID", "PRODUCT_ID", "QUANTITY", "UNIT_PRICE",
        "DISCOUNT_PERCENT", "CREATION_DATE", "CREATED_BY",
        "LAST_UPDATED_DATE", "LAST_UPDATED_BY"
    ]
}

ECOMMERCE_CORE_FIELDS = {
    "CUSTOMERS": ["CUSTOMER_ID", "CUSTOMER_NAME", "SEGMENT", "COUNTRY", "LIFETIME_VALUE"],
    "PRODUCTS": ["PRODUCT_ID", "PRODUCT_NAME", "CATEGORY", "PRICE"],
    "ORDERS": ["ORDER_ID", "CUSTOMER_ID", "ORDER_DATE", "TOTAL_AMOUNT", "STATUS", "REGION"],
    "ORDER_ITEMS": ["ORDER_ITEM_ID", "ORDER_ID", "PRODUCT_ID", "QUANTITY", "UNIT_PRICE"]
}
