import numpy as np
import matplotlib.pyplot as plt
import shap
from sklearn.metrics import roc_curve, roc_auc_score

def compute_roc_metrics(y_true, y_probs):
    """
    Compute ROC curve metrics.
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_probs)
    auc = roc_auc_score(y_true, y_probs)

    return fpr, tpr, thresholds, auc


def plot_roc_curve(fpr, tpr, auc):
    plt.figure(figsize=(7,5))

    plt.plot(fpr, tpr, label=f"AUC = {auc:.3f}")
    plt.plot([0,1], [0,1], linestyle="--")

    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend()

    plt.show()


def get_feature_names(preprocessor, low_cardinality, high_cardinality, numeric_cols):

    feature_names = []

    if "onehot" in preprocessor.named_transformers_:
        onehot_cols = preprocessor.named_transformers_["onehot"].get_feature_names_out(low_cardinality)
        feature_names.extend(onehot_cols)

    if "target" in preprocessor.named_transformers_:
        feature_names.extend(high_cardinality)

    feature_names.extend(numeric_cols)

    return feature_names


def plot_feature_importance(pipeline, feature_names, top_n=20):

    model = pipeline.named_steps["model"]

    importance = model.feature_importances_

    indices = np.argsort(importance)[::-1]

    sorted_features = [feature_names[i] for i in indices]
    sorted_importance = importance[indices]

    plt.figure(figsize=(10,6))

    plt.barh(range(min(top_n, len(sorted_importance))), sorted_importance[:top_n])
    plt.yticks(range(min(top_n, len(sorted_importance))), sorted_features[:top_n])

    plt.gca().invert_yaxis()

    plt.xlabel("Feature Importance")
    plt.title(f"Top {top_n} Feature Importances")

    plt.show()



def compute_shap_values(pipeline, X_train):

    model = pipeline.named_steps["model"]
    preprocessor = pipeline.named_steps["preprocess"]

    X_transformed = preprocessor.transform(X_train)

    explainer = shap.TreeExplainer(model)

    shap_values = explainer.shap_values(X_transformed)

    return shap_values, X_transformed


def plot_shap_summary(shap_values, X_transformed, feature_names):

    shap.summary_plot(
        shap_values,
        X_transformed,
        feature_names=feature_names
    )


def plot_prop(df,var_x):
    plt.figure(figsize=(8, 6))
    fraud_counts = df[var_x].value_counts()
    plt.pie(fraud_counts.values, labels=fraud_counts.index, autopct='%1.1f%%', startangle=90)
    plt.title('Proportion of Fraud Categories')
    plt.axis('equal')
    plt.show()

    print(f"Class distribution:")
    print(fraud_counts)


def plot_fraud_rate_by_category(df, top_n=5):
    fraud_rate_by_cat = (df.groupby('category')['is_fraud']
                           .mean()
                           .sort_values(ascending=False))
    top_n_cats = fraud_rate_by_cat.head(top_n) * 100
    avg_fraud_rate = fraud_rate_by_cat.iloc[top_n:].mean() * 100

    plot_data = top_n_cats.copy()
    plot_data['Other avg'] = avg_fraud_rate

    colors = ['steelblue'] * len(top_n_cats) + ['tomato']

    fig, ax = plt.subplots(figsize=(8, 5))
    plot_data.plot(kind='bar', ax=ax, color=colors, alpha=0.8, edgecolor='none')
    ax.set_title(f'Fraud Rate (%) — Top {top_n} Categories vs Other Categories Average')
    ax.set_xlabel('')
    ax.set_ylabel('Fraud Rate (%)')
    ax.tick_params(axis='x', rotation=30)
    plt.tight_layout()
    plt.show()


def plot_fraud_by_hour(df):
    fraud_by_hour = (df[df['is_fraud'] == 1]
                     .groupby('hour')
                     .size()
                     .reindex(range(24), fill_value=0))

    hours = fraud_by_hour.index.values
    counts = fraud_by_hour.values
    angles = np.deg2rad((hours / 24) * 360 - 90)
    max_count = counts.max()
    bar_heights = counts / max_count * 0.4

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.add_patch(plt.Circle((0, 0), 0.5, color='lightgray', alpha=0.15))
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)

    for angle, height, count in zip(angles, bar_heights, counts):
        x_start = 0.1 * np.cos(angle)
        y_start = 0.1 * np.sin(angle)
        x_end = (0.1 + height) * np.cos(angle)
        y_end = (0.1 + height) * np.sin(angle)
        color = plt.cm.Reds(0.4 + 0.6 * (count / max_count))
        ax.plot([x_start, x_end], [y_start, y_end],
                color=color, linewidth=6, solid_capstyle='round')

    for h, label in zip([0, 6, 12, 18], ['12am', '6am', '12pm', '6pm']):
        angle = np.deg2rad((h / 24) * 360 - 90)
        ax.text(0.7 * np.cos(angle), 0.7 * np.sin(angle),
                label, ha='center', va='center', fontsize=9, color='gray')

    plt.title('Fraud by Hour of Day')
    plt.tight_layout()
    plt.show()


def plot_boxplot_by_fraud(df, column):
    data = [df[df['is_fraud'] == 0][column].dropna(),
            df[df['is_fraud'] == 1][column].dropna()]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(data, labels=['Not Fraud', 'Fraud'], patch_artist=True,
               boxprops=dict(facecolor='steelblue', alpha=0.6),
               medianprops=dict(color='red', linewidth=2))
    ax.set_title(f'{column} Distribution by Fraud Label')
    ax.set_ylabel(column)
    ax.set_xlabel('is_fraud')
    plt.tight_layout()
    plt.show()