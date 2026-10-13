"""
Inferência do recomendador — o contrato que o container de scikit-learn da AWS
espera num endpoint do SageMaker. Quatro funções, chamadas nesta ordem:

    model_fn(pasta)                  → carrega o modelo (uma vez, na subida)
    input_fn(corpo, content_type)    → JSON da requisição vira dicionário
    predict_fn(entrada, modelo)      → a recomendação
    output_fn(resultado, accept)     → dicionário vira JSON de resposta

Requisição:   {"produto_id": 5, "n_recomendacoes": 5}
Resposta:     {"produto_id": 5, "recomendacoes": [{"produto_id", "nome", ...}]}

Diferença em relação à versão Azure (pyfunc do MLflow): o produto é localizado
pelo campo `id` do catálogo, não pela posição da linha — `produto_id = 5` é o
produto 5 do CSV, como o aluno espera.
"""
import json
import os

import joblib


def model_fn(pasta_modelo):
    return joblib.load(os.path.join(pasta_modelo, "modelo.joblib"))


def input_fn(corpo, content_type="application/json"):
    if content_type != "application/json":
        raise ValueError(f"Content-Type não suportado: {content_type}. Use application/json.")
    if isinstance(corpo, (bytes, bytearray)):
        corpo = corpo.decode("utf-8")
    return json.loads(corpo)


def predict_fn(entrada, modelo):
    df, nn, matriz = modelo["df"], modelo["nn"], modelo["matriz"]
    produto_id = int(entrada["produto_id"])
    n = int(entrada.get("n_recomendacoes", 5))

    linhas = df.index[df["id"] == produto_id].tolist()
    if not linhas:
        return {"erro": f"produto_id {produto_id} não existe no catálogo",
                "ids_validos": df["id"].tolist()}
    linha = linhas[0]

    dists, idxs = nn.kneighbors(matriz[linha].reshape(1, -1), n_neighbors=min(n + 1, len(df)))
    recomendacoes = [
        {
            "produto_id": int(df.iloc[i]["id"]),
            "nome": str(df.iloc[i]["nome"]),
            "categoria": str(df.iloc[i]["categoria"]),
            "preco": float(df.iloc[i]["preco"]),
            "score_similaridade": round(float(1 - d), 4),
        }
        for i, d in zip(idxs[0], dists[0])
        if i != linha
    ][:n]
    return {"produto_id": produto_id, "recomendacoes": recomendacoes}


def output_fn(resultado, accept="application/json"):
    return json.dumps(resultado, ensure_ascii=False), "application/json"
