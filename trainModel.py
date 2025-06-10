import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, roc_auc_score
from catboost import CatBoostClassifier, Pool

# Load the dataset and split it into features and target
df = pd.read_csv("training_dataset.csv", parse_dates=['earnings_date'])
X = df.drop(columns=['ticker', 'earnings_date', 'target'])
y = df['beat']
category_features = ["quarter", "day_of_week"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.3,
    random_state=42
)

# Create CatBoost Pool objects for training and testing
train_pool = Pool(data=X_train, label=y_train, cat_features=category_features) 
test_pool  = Pool(data=X_test,  label=y_test,  cat_features=category_features)

# Define the CatBoost model with initial parameters
model = CatBoostClassifier(
    iterations=1000,
    learning_rate=0.05,
    depth=6,
    eval_metric="AUC",
    random_seed=42,
    verbose=100,
    early_stopping_rounds=50
)