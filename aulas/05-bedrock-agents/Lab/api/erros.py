"""Erros da aplicação.

Regra do projeto: todo erro que chega ao aluno traz **como resolver**.
Mensagem de erro sem instrução é aula perdida.
"""

from __future__ import annotations


class ErroDoDeva(Exception):
    """Erro base. Tudo que a API lança conscientemente herda daqui."""

    codigo = "erro_interno"
    situacao_http = 500

    def __init__(self, mensagem: str, detalhe: str | None = None,
                 como_resolver: str | None = None) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.detalhe = detalhe
        self.como_resolver = como_resolver

    def como_dicionario(self) -> dict:
        return {
            "erro": self.codigo,
            "mensagem": self.mensagem,
            "detalhe": self.detalhe,
            "como_resolver": self.como_resolver,
        }


class ImagemInvalida(ErroDoDeva):
    codigo = "imagem_invalida"
    situacao_http = 400


class ImagemGrandeDemais(ErroDoDeva):
    codigo = "imagem_grande_demais"
    situacao_http = 413


class ServicoNaoConfigurado(ErroDoDeva):
    codigo = "servico_nao_configurado"
    situacao_http = 503

    def __init__(self, servico: str, como_resolver: str | None = None) -> None:
        super().__init__(
            mensagem=f"O serviço {servico} não está configurado nesta instância.",
            detalhe=None,
            como_resolver=como_resolver,
        )
        self.servico = servico


class FalhaDeIntegracao(ErroDoDeva):
    codigo = "falha_de_integracao"
    situacao_http = 502

    def __init__(self, servico: str, mensagem: str, detalhe: str | None = None,
                 como_resolver: str | None = None) -> None:
        super().__init__(mensagem=mensagem, detalhe=detalhe, como_resolver=como_resolver)
        self.servico = servico


class FalhaDeArmazenamento(ErroDoDeva):
    codigo = "falha_de_armazenamento"
    situacao_http = 502
