"""Erros que ensinam.

Regra da casa: todo erro carrega `como_resolver`. Mensagem de erro sem instrução é aula
perdida — e, num laboratório com 40 pessoas, é o professor atendendo 40 vezes a mesma
dúvida.
"""
from __future__ import annotations


class ErroDoServico(Exception):
    codigo = "erro_interno"
    situacao_http = 500

    def __init__(self, mensagem: str, detalhe: str | None = None,
                 como_resolver: str | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.detalhe = detalhe
        self.como_resolver = como_resolver

    def para_payload(self) -> dict:
        return {
            "erro": self.codigo,
            "mensagem": self.mensagem,
            "detalhe": self.detalhe,
            "como_resolver": self.como_resolver,
        }


class PropostaInvalida(ErroDoServico):
    codigo = "proposta_invalida"
    situacao_http = 422


class PropostaNaoEncontrada(ErroDoServico):
    codigo = "proposta_nao_encontrada"
    situacao_http = 404


class PropostaJaDecidida(ErroDoServico):
    codigo = "proposta_ja_decidida"
    situacao_http = 409


class DocumentoNaoEncontrado(ErroDoServico):
    codigo = "documento_nao_encontrado"
    situacao_http = 404


class TransicaoProibida(ErroDoServico):
    codigo = "transicao_proibida"
    situacao_http = 409


class AutorizacaoDeAuditorAusente(ErroDoServico):
    """O erro mais importante do serviço.

    É ele que impede o agente de aprovar a própria memória. Se algum dia esta exceção
    parar de ser lançada, o laboratório inteiro perde o sentido.
    """

    codigo = "autorizacao_de_auditor_ausente"
    situacao_http = 403


class ArmazenamentoIndisponivel(ErroDoServico):
    codigo = "armazenamento_indisponivel"
    situacao_http = 503
