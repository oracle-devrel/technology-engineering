from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, make_scorer, f1_score
from sklearn.pipeline import Pipeline
from sklearn.model_selection import RandomizedSearchCV
import numpy as np


def build_model(random_state: int = 42):
    """Random Forest classifier - base estimator for HPO."""
    return RandomForestClassifier(
        random_state=random_state,
        n_jobs=-1
    )


def build_pipeline(preprocessor, model):
    """Attach preprocessing and model in one sklearn Pipeline."""
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", model),
        ]
    )


def optimize_hyperparameters(pipeline, X_train, y_train, random_state: int = 42):
    """
    Run RandomizedSearchCV optimizing for F1 on the minority class (label=1).
    Returns the best fitted pipeline.
    """
    param_dist = {
        "model__n_estimators": [100, 200, 300, 500],
        "model__max_depth": [10, 15, 20, 30, None],
        "model__min_samples_split": [2, 5, 10, 20],
        "model__min_samples_leaf": [1, 2, 4, 8],
        "model__max_features": ["sqrt", "log2", 0.3, 0.5],
        "model__class_weight": [
            "balanced",
            "balanced_subsample",
            {0: 1, 1: 2},   # penalize missing class 1 twice as much
            {0: 1, 1: 3},   # penalize missing class 1 three times as much
        ],
    }

    # Optimize for F1 on minority class specifically
    scorer = make_scorer(f1_score, pos_label=1)

    search = RandomizedSearchCV(
        estimator=pipeline,
        param_distributions=param_dist,
        n_iter=30,           # number of parameter combinations to try
        scoring=scorer,
        cv=5,                # 5-fold cross validation
        verbose=2,
        random_state=random_state,
        n_jobs=-1
    )

    search.fit(X_train, y_train)

    print(f"\nBest F1 (class 1): {search.best_score_:.4f}")
    print(f"Best params: {search.best_params_}")

    return search.best_estimator_


def evaluate_model(pipeline, X_test, y_test):
    """Return key evaluation artifacts for test data."""
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    report = classification_report(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    return {
        "classification_report": report,
        "confusion_matrix": cm,
        "roc_auc": auc,
    }