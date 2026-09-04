from statsmodels.tsa.statespace.sarimax import SARIMAX

def fit_model(train_df,order_value, seasonal_order_value, trend_cols,sales_col):

    y_series = train_df[sales_col]

    X = train_df[trend_cols] if trend_cols else None

    model = SARIMAX(
        y_series,
        exog=X,
        order=order_value,
        seasonal_order=seasonal_order_value,
        enforce_stationarity=False,
        enforce_invertibility=False
    )

    results = model.fit(disp=False)

    print(results.summary())

    return results