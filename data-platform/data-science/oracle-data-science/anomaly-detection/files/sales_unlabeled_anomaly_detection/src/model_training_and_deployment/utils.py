import pandas as pd

def create_aggregated_df(df):
    agg_df = (
        df.groupby('Date', as_index=False)
          .agg({
              'Store': 'nunique',
              'Dept': 'count',
              'IsHoliday': 'sum',
              'Weekly_Sales': 'sum',
              'Temperature': 'mean',
              'Fuel_Price': 'mean',
              'MarkDown1': 'mean',
              'MarkDown2': 'mean',
              'MarkDown3': 'mean',
              'MarkDown4': 'mean',
              'MarkDown5': 'mean',
              'CPI': 'mean',
              'Unemployment': 'mean',
              'Type': 'mean',
              'Size': 'mean'
          })
          .sort_values('Date')
          .reset_index(drop=True)
    )

    return agg_df



def walk_forward_forecast(results, test_df, trend_cols, sales_col):
    predictions = []
    lower_bounds = []
    upper_bounds = []

    current_results = results

    for i in range(len(test_df)):

        next_row = test_df.iloc[[i]]

        X_next = next_row[trend_cols] if trend_cols else None

        # Forecast next step
        forecast_obj = current_results.get_forecast(
            steps=1,
            exog=X_next
        )

        forecast = forecast_obj.predicted_mean.iloc[0]

        conf_int = forecast_obj.conf_int()

        lower = conf_int.iloc[0, 0]
        upper = conf_int.iloc[0, 1]

        predictions.append(forecast)
        lower_bounds.append(lower)
        upper_bounds.append(upper)

        # Update model state with actual observation
        current_results = current_results.append(
            endog=next_row[sales_col],
            exog=X_next,
            refit=False
        )

    forecast_series = pd.Series(
        predictions,
        index=test_df.index
    )

    conf_int_df = pd.DataFrame({
        'lower': lower_bounds,
        'upper': upper_bounds
    }, index=test_df.index)

    return forecast_series, conf_int_df