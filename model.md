"""
CICIDS2017 — XGBoost Training Pipeline  (with Regularization)
--------------------------------------------------------------
Regularization techniques applied:
  L1  (reg_alpha)       — sparsifies feature weights; drops irrelevant flow stats
  L2  (reg_lambda)      — shrinks leaf weights; reduces variance
  gamma                 — minimum loss reduction to make a split (pruning)
  max_depth             — limits tree complexity
  min_child_weight      — requires minimum sample mass per leaf
  subsample             — row-level bagging (prevents memorisation)
  colsample_bytree      — column-level bagging (feature dropout per tree)
  colsample_bylevel     — column dropout per tree depth level
  learning_rate         — shrinks each tree's contribution (slow + steady)
  early_stopping_rounds — halts training when val loss stops improving

Steps:
  1. Load & clean the dataset
  2. Encode labels
  3. Handle class imbalance with sample_weight
  4. Train XGBoost with full regularization stack + early stopping
  5. Plot: training curve, confusion matrix, feature importance
  6. Save model + label encoder
"""