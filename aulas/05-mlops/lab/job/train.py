"""
Aula 5 / Atividade 3 — Versão job-friendly do treino.

Recebe inputs como argumentos CLI (em vez de env vars do shell). É a versão
executada pelo Compute Cluster quando o job é submetido via `job.yml`.

MLflow tracking é automático em jobs do Azure ML — o tracking URI já vem
configurado pelo runtime do Workspace, não precisamos chamar
`set_tracking_uri()`.

Argumentos:
    --input-data       — caminho local do produtos.csv (montado pelo job)
    --n-neighbors      — número de vizinhos (default: 5)
    --embedding-model  — modelo de embedding (default: all-MiniLM-L6-v2)
"""
import argparse
import os
import pickle

import mlflow
import mlflow.pyfunc
import pandas as pd
from sklearn.neighbors import NearestNeighbors


class RecomendadorPyfunc(mlflow.pyfunc.PythonModel):
    """Wrapper pyfunc: empacota nn + embeddings + df para servir via endpoint."""

    def load_context(self, context):
        import pickle
        with open(context.artifacts["modelo_pkl"], "rb") as f:
            obj = pickle.load(f)
        self.nn = obj["nn"]
        self.embeddings = obj["embeddings"]
        self.df = obj["df"]

    def predict(self, context, model_input):
        produto_id = int(model_input["produto_id"].iloc[0])
        n = int(model_input["n_recomendacoes"].iloc[0]) if "n_recomendacoes" in model_input.columns else 5
        query = self.embeddings[produto_id].reshape(1, -1)
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-data",
        type=str,
        required=True,
        help="Caminho do produtos.csv (montado pelo job a partir do Data Asset)",
    )
    parser.add_argument("--n-neighbors", type=int, default=5)
    parser.add_argument(
        "--embedding-model", type=str, default="all-MiniLM-L6-v2"
    )
    args = parser.parse_args()

    # Log de params
    mlflow.log_param("n_neighbors", args.n_neighbors)
    mlflow.log_param("embedding_model", args.embedding_model)
    mlflow.log_param("metric", "cosine")

    # Carregar dataset
    print(f"→ Carregando dataset de {args.input_data}")
    df = pd.read_csv(args.input_data)
    mlflow.log_metric("num_produtos", len(df))

    # Embeddings
    print(f"→ Gerando embeddings com {args.embedding_model}")
    from sentence_transformers import SentenceTransformer
    model_emb = SentenceTransformer(args.embedding_model)
    textos = (df["nome"] + ". " + df["descricao"]).tolist()
    embeddings = model_emb.encode(textos, show_progress_bar=False)
    mlflow.log_metric("embedding_dim", embeddings.shape[1])

    # Treino
    print(f"→ Treinando NearestNeighbors n={args.n_neighbors}")
    nn = NearestNeighbors(n_neighbors=args.n_neighbors + 1, metric="cosine")
    nn.fit(embeddings)

    # Precision proxy
    _, indices = nn.kneighbors(embeddings)
    same_cat = sum(
        1
        for i, viz in enumerate(indices)
        for j in viz[1:]
        if df.iloc[j]["categoria"] == df.iloc[i]["categoria"]
    )
    total = len(df) * args.n_neighbors
    precision = same_cat / total
    mlflow.log_metric("precision_at_k_proxy", precision)
    print(f"✓ Precision proxy: {precision:.3f}")

    # Salvar artefato no output do job
    os.makedirs("./outputs", exist_ok=True)
    with open("./outputs/nn_model.pkl", "wb") as f:
        pickle.dump({"nn": nn, "embeddings": embeddings, "df": df}, f)

    # Registrar no Model Registry como pyfunc (nn + embeddings + df empacotados)
    # NearestNeighbors não tem predict() — pyfunc empacota o pkl completo para o endpoint.
    # pip_requirements declara apenas o que o endpoint precisa em runtime.
    # sentence-transformers/torch são usados só no treino; o predict usa embeddings pré-computados.
    mlflow.pyfunc.log_model(
        artifact_path="pyfunc_model",
        python_model=RecomendadorPyfunc(),
        artifacts={"modelo_pkl": "./outputs/nn_model.pkl"},
        registered_model_name="recomendador-qc",
        pip_requirements=["scikit-learn", "pandas", "numpy", "azureml-ai-monitoring"],
    )
    print("✓ Modelo registrado no Registry")


if __name__ == "__main__":
    main()
