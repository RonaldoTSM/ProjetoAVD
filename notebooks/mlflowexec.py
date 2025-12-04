import os

# 🔧 Força MLflow/boto3 a usar MinIO como S3
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://minio:9000"

import mlflow
import mlflow.sklearn
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
import pandas as pd
from sqlalchemy import create_engine

mlflow.set_tracking_uri("http://mlflow:5000")

# 1) Definir experimento no MLflow
mlflow.set_experiment("modelo_conforto_termico_v2")
# 2) Conectar ao Postgres
engine = create_engine("postgresql://postgres:postgres@postgres:5432/weather_db")

# 3) Carregar a tabela
df = pd.read_sql("SELECT * FROM weather_hourly", engine)

print("Colunas disponíveis em weather_hourly:")
print(df.columns.tolist())

# -----------------------------
# 4) CRIAR A COLUNA comfort_class
# -----------------------------
# Regras simples de conforto (você pode depois ajustar melhor):
# 1 = confortável, 0 = desconforto
# confortável se: 22°C <= temperatura <= 27°C e 40% <= umidade <= 70%

# Garante que as colunas existem antes
required_cols = ["temperatura", "umidade_relativa", "velocidade_vento"]
for c in required_cols:
    if c not in df.columns:
        raise ValueError(f"Coluna obrigatória '{c}' não existe em weather_hourly.")

df = df.dropna(subset=["temperatura", "umidade_relativa", "velocidade_vento"]).copy()

df["comfort_class"] = 0  # default = desconforto
cond_conforto = (
    (df["temperatura"] >= 22) & (df["temperatura"] <= 27) &
    (df["umidade_relativa"] >= 40) & (df["umidade_relativa"] <= 70)
)
df.loc[cond_conforto, "comfort_class"] = 1

print("Distribuição da comfort_class:")
print(df["comfort_class"].value_counts())

# -----------------------------
# 5) Preparar X e y
# -----------------------------
feature_cols = ["temperatura", "umidade_relativa", "velocidade_vento"]
target_col = "comfort_class"

df_model = df[feature_cols + [target_col]].dropna()

X = df_model[feature_cols]
y = df_model[target_col]

# Se por acaso só tiver uma classe, o modelo não treina
if y.nunique() < 2:
    raise ValueError("Só existe uma classe em comfort_class. Ajuste as regras de conforto para gerar 0 e 1.")

# -----------------------------
# 6) Train/test split
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# -----------------------------
# 7) Definir modelo
# -----------------------------
model = DecisionTreeClassifier(max_depth=5, random_state=42)

with mlflow.start_run(run_name="modelo_conforto_termico_decision_tree"):

    # Treinar
    model.fit(X_train, y_train)

    # Prever
    preds = model.predict(X_test)

    # Métricas
    acc = accuracy_score(y_test, preds)
    f1 = f1_score(y_test, preds, average="weighted")

    # Logar métricas
    mlflow.log_metric("accuracy", acc)
    mlflow.log_metric("f1_score", f1)

    # Logar parâmetros
    mlflow.log_param("max_depth", 5)
    mlflow.log_param("test_size", 0.2)
    mlflow.log_param("model_type", "DecisionTreeClassifier")

    # Logar o modelo
    mlflow.sklearn.log_model(model, "modelo_conforto")

print("✅ Modelo registrado no MLflow!")
print("Accuracy:", acc, "F1:", f1)
