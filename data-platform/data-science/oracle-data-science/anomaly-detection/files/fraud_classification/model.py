from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline
import xgboost as xgb
from config import PARAM_DIST


def build_model(scale_pos_weight_value):

    model = xgb.XGBClassifier(

        objective="binary:logistic",
        tree_method="hist",
        scale_pos_weight=scale_pos_weight_value,
        random_state=42
    )

    return model


def build_pipeline(preprocessor, model):

    pipeline = Pipeline([
        ("preprocess", preprocessor),
        ("model", model)
    ])

    return pipeline


def find_hyper_params(pipeline, X_train, y_train):

    search = RandomizedSearchCV(

        pipeline,
        PARAM_DIST,
        n_iter=50,
        scoring="roc_auc",
        cv=3,
        n_jobs=-1,
        verbose=2,
        random_state=42
    )

    search.fit(X_train, y_train)

    best_params = {
        k.replace("model__", ""): v
        for k, v in search.best_params_.items()
    }

    return best_params

def train_final_model(X_train, y_train, best_params, preprocessor,scale_pos_weight_value):
    model = xgb.XGBClassifier(

        objective="binary:logistic",
        tree_method="hist",
        scale_pos_weight=scale_pos_weight_value,
        random_state=42,
        **best_params
    )

    pipeline = build_pipeline(preprocessor, model)

    pipeline.fit(X_train, y_train)

    return pipeline