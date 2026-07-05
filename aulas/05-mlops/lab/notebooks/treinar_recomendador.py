"""
Aula 5 / Atividade 2 — Treino LOCAL (no Cloud Shell) com tracking no MLflow do Workspace.

Treina um recomendador content-based de produtos QC usando TF-IDF (scikit-learn)
+ NearestNeighbors. Rastreia o experimento no MLflow integrado ao Azure ML Workspace
e registra o modelo no Model Registry.

NOTA pedagógica: versão leve (TF-IDF) para rodar no Cloud Shell sem instalar torch.
A Atividade 3 usa embeddings semânticos (sentence-transformers) rodando no Compute
Cluster — compare os valores de precision_at_k_proxy entre as duas abordagens.

Variáveis de ambiente necessárias:
    SUBSCRIPTION_ID   — id da subscription
    RESOURCE_GROUP    — nome do RG da Aula 5
    WORKSPACE_NAME    — nome do Workspace
    DATA_PATH         — caminho local do produtos.csv (default: ~/qc-aula05/produtos.csv)

Hiperparâmetros opcionais:
    N_NEIGHBORS       — número de vizinhos (default: 5)

Dependências:
    pip install --user mlflow azureml-mlflow azure-ai-ml azure-identity pandas scikit-learn
"""
import os
import pickle

import mlflow
import mlflow.pyfunc
import numpy as np
import pandas as pd
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors


class RecomendadorPyfunc(mlflow.pyfunc.PythonModel):
    """Wrapper pyfunc: empacota nn + matriz TF-IDF + df para servir via endpoint."""

    def load_context(self, context):
        with open(context.artifacts["modelo_pkl"], "rb") as f:
            obj = pickle.load(f)
        self.nn = obj["nn"]
        self.tfidf_matrix = obj["tfidf_matrix"]
        self.df = obj["df"]

    def predict(self, context, model_input):
        produto_id = int(model_input["produto_id"].iloc[0])
        n = int(model_input["n_recomendacoes"].iloc[0]) if "n_recomendacoes" in model_input.columns else 5
        query = self.tfidf_matrix[produto_id].reshape(1, -1)
        dists, idxs = self.nn.kneighbors(query, n_neighbors=min(n + 1, len(self.df)))
        vizinhos = [i for i in idxs[0] if i != produto_id][:n]
        scores = [float(1 - d) for i, d in zip(idxs[0], dists[0]) if i != produto_id][:n]
        rows = [
            {
                "produto_id": int(idx),
                "nome": str(self.df.iloc[idx]["nome"]),
                "categoria": str(self.df.iloc[idx]["categoria"]),
                "preco": float(self.df.iloc[idx]["preco"]),
                "score_similaridade": round(s, 4),
            }
            for idx, s in zip(vizinhos, scores)
        ]
        return pd.DataFrame(rows)


# === 1. Conectar no Azure ML Workspace ===
SUBSCRIPTION_ID = os.environ["SUBSCRIPTION_ID"]
RESOURCE_GROUP  = os.environ["RESOURCE_GROUP"]
WORKSPACE       = os.environ["WORKSPACE_NAME"]

credential = DefaultAzureCredential()
ml_client = MLClient(credential, SUBSCRIPTION_ID, RESOURCE_GROUP, WORKSPACE)

mlflow.set_tracking_uri(ml_client.workspaces.get(WORKSPACE).mlflow_tracking_uri)
mlflow.set_experiment("recomendacao-qc")


# === 2. Hiperparâmetros ===
N_NEIGHBORS = int(os.environ.get("N_NEIGHBORS", 5))
DATA_PATH = os.path.expanduser(
    os.environ.get("DATA_PATH", "~/qc-aula05/produtos.csv")
)


def main():
    with mlflow.start_run() as run:
        print(f"Run ID: {run.info.run_id}")

        # === 3. Log de params ===
        mlflow.log_param("n_neighbors", N_NEIGHBORS)
        mlflow.log_param("vectorizer", "tfidf")
        mlflow.log_param("metric", "cosine")

        # === 4. Carregar dataset ===
        print(f"→ Carregando produtos de {DATA_PATH}...")
        df = pd.read_csv(DATA_PATH)
        mlflow.log_metric("num_produtos", len(df))
        print(f"✓ {len(df)} produtos carregados")

        # === 5. Vetorizar textos com TF-IDF ===
        print("→ Vetorizando com TF-IDF...")
        textos = (df["nome"] + ". " + df["descricao"] + ". " + df["categoria"]).tolist()
        vectorizer = TfidfVectorizer(max_features=500)
        tfidf_matrix = vectorizer.fit_transform(textos).toarray()
        mlflow.log_metric("vocab_size", len(vectorizer.vocabulary_))
        print(f"✓ Matriz TF-IDF: {tfidf_matrix.shape}")

        # === 6. Treinar NearestNeighbors ===
        print(f"→ Treinando NearestNeighbors com n={N_NEIGHBORS}...")
        nn = NearestNeighbors(n_neighbors=N_NEIGHBORS + 1, metric="cosine")
        nn.fit(tfidf_matrix)

        # === 7. Avaliação simplificada (precision proxy) ===
        _, indices = nn.kneighbors(tfidf_matrix)
        same_cat = sum(
            df.iloc[j]["categoria"] == df.iloc[i]["categoria"]
            for i, vizinhos in enumerate(indices)
            for j in vizinhos[1:]
        )
        precision_proxy = same_cat / (len(df) * N_NEIGHBORS)
        mlflow.log_metric("precision_at_k_proxy", precision_proxy)
        print(f"✓ Precision proxy (mesma categoria): {precision_proxy:.3f}")
        print("  → Compare com o valor da Atividade 3 (embeddings semânticos no cluster)")

        # === 8. Serializar modelo ===
        os.makedirs("./model_artifacts", exist_ok=True)
        with open("./model_artifacts/nn_model.pkl", "wb") as f:
            pickle.dump({"nn": nn, "tfidf_matrix": tfidf_matrix, "df": df}, f)

        # === 9. Registrar no Model Registry ===
        mlflow.pyfunc.log_model(
            artifact_path="pyfunc_model",
            python_model=RecomendadorPyfunc(),
            artifacts={"modelo_pkl": "./model_artifacts/nn_model.pkl"},
            registered_model_name="recomendador-qc",
        )

        print("✓ Modelo registrado no Registry como 'recomendador-qc'")
        print(f"  Veja no Studio: experimento 'recomendacao-qc' → run {run.info.run_id}")


if __name__ == "__main__":
    main()
