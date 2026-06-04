FEATURE_SET = [
    'category','amt','gender','street','city','state',
    'city_pop','job','age','hour','geo_dist' #,'iso_score'
]

LOW_CARD_THRESHOLD = 15

PARAM_DIST = {
    "model__n_estimators": [100,200,400],
    "model__max_depth": [4,6,8],
    "model__learning_rate": [0.01,0.05,0.1],
    "model__subsample": [0.6,0.75,0.9],
    "model__colsample_bytree": [0.6,0.75,0.9],
    "model__min_child_weight": [2,3,5]
}