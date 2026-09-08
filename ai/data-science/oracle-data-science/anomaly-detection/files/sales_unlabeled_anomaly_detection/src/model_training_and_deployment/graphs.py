import matplotlib.pyplot as plt

def plot_store_vs_overall_sales(df, agg_df, store_id=1, sales_col='Weekly_Sales', date_col='Date'):
    store_df = df[df['Store'] == store_id][[date_col, sales_col]].copy()
    store_sales = (
        store_df.groupby(date_col, as_index=False)[sales_col]
        .sum()
        .sort_values(date_col)
    )

    overall_sales = agg_df[[date_col, sales_col]].copy().sort_values(date_col)

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    axes[0].plot(store_sales[date_col], store_sales[sales_col], linewidth=1.8)
    axes[0].set_title(f'Store {store_id} Weekly Sales')
    axes[0].set_ylabel('Weekly Sales')

    axes[1].plot(overall_sales[date_col], overall_sales[sales_col], linewidth=1.8)
    axes[1].set_title('Overall Weekly Sales')
    axes[1].set_xlabel('Date')
    axes[1].set_ylabel('Weekly Sales')

    plt.tight_layout()
    plt.show()


def plot_forecast(train_df, test_df, sales_col, forecast, title, conf_int=None):
    plt.figure(figsize=(14, 6))

    plt.plot(train_df.index, train_df[sales_col], label='Train')
    plt.plot(test_df.index, test_df[sales_col], label='Actual')
    plt.plot(test_df.index, forecast, linestyle='--', label='Forecast')

    if conf_int is not None:
        plt.fill_between(
            test_df.index,
            conf_int.iloc[:, 0],
            conf_int.iloc[:, 1],
            alpha=0.2
        )

    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel(sales_col)
    plt.legend()
    plt.show()

    