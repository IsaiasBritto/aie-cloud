"""
Aula 5 / Atividades 2 e 3 — Treino do recomendador da Quantum Commerce.

O MESMO arquivo roda em dois lugares, e esse é o ponto da aula:

  - no CloudShell (Atividade 2):  python codigo/train.py --vetorizador tfidf
  - num SageMaker Training Job (Atividade 3): o container de scikit-learn da AWS
    baixa este código do S3, monta o dataset em /opt/ml/input/data/treino e chama
    `python train.py --n_neighbors 5 --vetorizador tfidf`.

Como o mesmo código sabe onde está? Pelas variáveis de ambiente que o SageMaker
define dentro do container (e que têm padrão local quando não existem):

    SM_CHANNEL_TREINO  → pasta do dataset   (local: ~/qc-aula05)
    SM_MODEL_DIR       → onde salvar o modelo (local: ./modelo-local)
    SM_OUTPUT_DATA_DIR → artefatos extras     (local: ./modelo-local/saida)

Tracking:
  - as MÉTRICAS saem no log no formato `metrica=valor`. No Training Job, as
    `MetricDefinitions` (regex) as capturam e elas aparecem no console do
    SageMaker e no CloudWatch — sem SDK nenhum.
  - se o MLflow estiver instalado (só no CloudShell, Atividade 2), o mesmo run
    também vai para um MLflow local (./mlruns).

Hiperparâmetros (o SageMaker passa como --nome valor):
    --n_neighbors   número de vizinhos (padrão 5)
    --vetorizador   tfidf (leve, padrão) | embeddings (sentence-transformers)
"""
import argparse
import json
import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.neighbors import NearestNeighbors

PASTA_DADOS = Path(os.environ.get("SM_CHANNEL_TREINO", os.path.expanduser("~/qc-aula05")))
PASTA_MODELO = Path(os.environ.get("SM_MODEL_DIR", "./modelo-local"))
PASTA_SAIDA = Path(os.environ.get("SM_OUTPUT_DATA_DIR", str(PASTA_MODELO / "saida")))


def vetorizar(textos: list[str], vetorizador: str):
    """Transforma texto em vetores. Devolve (matriz, descrição do vetorizador)."""
    if vetorizador == "embeddings":
        from sentence_transformers import SentenceTransformer

        nome = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        return SentenceTransformer(nome).encode(textos, show_progress_bar=False), nome

    from sklearn.feature_extraction.text import TfidfVectorizer

    matriz = TfidfVectorizer(max_features=500).fit_transform(textos).toarray()
    return matriz, "tfidf-500"


def precisao_proxy(df: pd.DataFrame, indices, k: int) -> float:
    """Fração dos k vizinhos que são da mesma categoria do produto.

    Não é acurácia de recomendação de verdade (não há clique de usuário aqui). É um
    proxy barato, suficiente para COMPARAR execuções — que é o que o tracking mostra.
    """
    mesma = sum(
        df.iloc[j]["categoria"] == df.iloc[i]["categoria"]
        for i, vizinhos in enumerate(indices)
        for j in vizinhos[1:]
    )
    return mesma / (len(df) * k)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_neighbors", type=int, default=5)
    parser.add_argument("--vetorizador", choices=["tfidf", "embeddings"], default="tfidf")
    parser.add_argument("--arquivo", default="produtos.csv")
    args = parser.parse_args()

    PASTA_MODELO.mkdir(parents=True, exist_ok=True)
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    print(f"→ Dados: {PASTA_DADOS / args.arquivo}")
    df = pd.read_csv(PASTA_DADOS / args.arquivo)
    textos = (df["nome"] + ". " + df["descricao"] + ". " + df["categoria"]).tolist()

    print(f"→ Vetorizando com {args.vetorizador}...")
    matriz, descricao = vetorizar(textos, args.vetorizador)

    print(f"→ Treinando NearestNeighbors (k={args.n_neighbors}, cosseno)...")
    nn = NearestNeighbors(n_neighbors=args.n_neighbors + 1, metric="cosine").fit(matriz)
    _, indices = nn.kneighbors(matriz)
    precisao = precisao_proxy(df, indices, args.n_neighbors)

    metricas = {
        "num_produtos": len(df),
        "dimensao_vetor": int(matriz.shape[1]),
        "precision_at_k_proxy": round(float(precisao), 4),
    }
    # Formato `nome=valor`: é o que as MetricDefinitions do Training Job leem.
    for nome, valor in metricas.items():
        print(f"{nome}={valor}")

    # O modelo: tudo que a inferência precisa, num arquivo só.
    joblib.dump({"nn": nn, "matriz": matriz, "df": df}, PASTA_MODELO / "modelo.joblib")
    parametros = {"n_neighbors": args.n_neighbors, "vetorizador": descricao}
    (PASTA_MODELO / "metadados.json").write_text(
        json.dumps({"parametros": parametros, "metricas": metricas}, ensure_ascii=False, indent=2)
    )
    print(f"✓ Modelo salvo em {PASTA_MODELO}")

    _registrar_no_mlflow_local(parametros, metricas)


def _registrar_no_mlflow_local(parametros: dict, metricas: dict) -> None:
    """Tracking opcional: só se o MLflow existir (CloudShell). No job, não existe."""
    try:
        import mlflow
    except ImportError:
        return
    mlflow.set_experiment("recomendacao-qc")
    with mlflow.start_run() as run:
        mlflow.log_params(parametros)
        mlflow.log_metrics({k: float(v) for k, v in metricas.items()})
        mlflow.log_artifact(str(PASTA_MODELO / "metadados.json"))
        print(f"✓ MLflow local: experimento recomendacao-qc · run {run.info.run_id}")


if __name__ == "__main__":
    main()
