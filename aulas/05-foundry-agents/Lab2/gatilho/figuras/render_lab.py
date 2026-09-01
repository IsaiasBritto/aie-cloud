"""Figuras do bloco de LABORATÓRIO — passo a passo, código e conceitos.

Cada figura amarra três coisas: o que o aluno faz, em que arquivo isso vive e qual
conceito da aula está sendo demonstrado.

    python3 figuras/render_lab.py
"""
import asyncio, os
from playwright.async_api import async_playwright

SAIDA = "/root/deva-continuo/figuras/png"
os.makedirs(SAIDA, exist_ok=True)

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'DejaVu Sans','Segoe UI',system-ui,sans-serif;background:#15151A;color:#F4F3EF;
     -webkit-font-smoothing:antialiased}
.wrap{padding:44px}
h1{font-size:38px;font-weight:700;letter-spacing:-.5px;margin-bottom:6px}
h2{font-size:22px;font-weight:600;color:#7A7872;margin-bottom:26px}
.row{display:flex;gap:16px;align-items:stretch}
.col{display:flex;flex-direction:column;gap:16px}
.card{background:#1C1C22;border:1px solid #2E2E38;border-radius:4px;padding:18px 20px}
.card.rosa{background:#22161B;border-color:#EB0B4F}
.card.ambar{background:#221E14;border-color:#FFD579}
.card.ciano{background:#12222A;border-color:#03E3FD}
.rot{font-size:12px;font-weight:700;letter-spacing:1.1px;text-transform:uppercase;
     color:#EB0B4F;margin-bottom:8px}
.rot.c{color:#03E3FD}.rot.a{color:#FFD579}.rot.m{color:#7A7872}
.t{font-size:19px;font-weight:700;margin-bottom:8px}
.d{font-size:15px;line-height:1.5;color:#C3C1BA}
.small{font-size:13px;color:#7A7872;line-height:1.45}
.mono{font-family:'DejaVu Sans Mono',monospace;color:#03E3FD}
table{width:100%;border-collapse:collapse;font-size:14.5px;color:#C3C1BA}
th{text-align:left;font-size:11.5px;text-transform:uppercase;letter-spacing:.6px;
   color:#7A7872;padding:9px 11px;border-bottom:1px solid #3A3A46}
td{padding:9px 11px;border-bottom:1px solid #26262E;vertical-align:top}
td b,td strong{color:#F4F3EF}
.cod{background:#101014;border:1px solid #26262E;border-radius:4px;padding:16px 18px;
     font-family:'DejaVu Sans Mono',monospace;font-size:13.5px;line-height:1.65;color:#C3C1BA}
.cod .arq{color:#5F6270;font-size:12px;display:block;margin-bottom:10px}
.ch{color:#03E3FD}.vl{color:#FFD579}.cm{color:#5F6270}.dq{color:#EB0B4F}
.kw{color:#EB0B4F}.fn{color:#FFD579}
.passo{display:flex;gap:14px;margin-bottom:9px;align-items:stretch}
.pn{width:52px;flex:none;display:flex;align-items:center;justify-content:center;
    font-size:22px;font-weight:700;border-radius:4px}
.pill{display:inline-block;font-size:11.5px;font-weight:700;letter-spacing:.5px;
      padding:3px 9px;border-radius:11px;border:1px solid #EB0B4F;color:#EB0B4F}
.pill.c{border-color:#03E3FD;color:#03E3FD}
.pill.a{border-color:#FFD579;color:#FFD579}
.pill.m{border-color:#3A3A46;color:#7A7872}
"""

P = {}

# ── 1 · Objetivo do laboratório ──────────────────────────────────────────────
P["dc-lab-01-objetivo"] = ("""
<div class="wrap">
<h1>O laboratório em uma tela</h1>
<h2>Sair de um agente que responde para um agente que trabalha — sem ganhar poder de decisão</h2>
<div class="row" style="margin-top:8px">
  <div class="card rosa" style="flex:1.25">
    <div class="rot">O objetivo</div>
    <div class="t">Fazer o Deva atravessar três degraus</div>
    <div class="d">Ele passa a <b>lembrar entre sessões</b> (nível 2), a <b>começar
    sozinho</b> quando um documento chega (nível 3) e a <b>parar</b> no que não é dele,
    chamando uma pessoa (nível 4).</div>
    <div class="d" style="margin-top:12px">E, ao fim, o aluno consegue <b>abrir o
    <span class="mono">MEMORY.md</span></b> e apontar a linha que entrou hoje — com o nome
    de quem aprovou.</div>
  </div>
  <div class="card" style="flex:1">
    <div class="rot c">O que você constrói</div>
    <div class="d">
      <b>1 ·</b> Serviço de Continuidade (FastAPI) com memória e fila<br><br>
      <b>2 ·</b> Tela de revisão (Streamlit) com 4 abas<br><br>
      <b>3 ·</b> Gatilho por evento no Blob Storage<br><br>
      <b>4 ·</b> Ferramenta OpenAPI ligada ao agente no Foundry
    </div>
  </div>
  <div class="card ambar" style="flex:1">
    <div class="rot a">O entregável</div>
    <div class="d">Um <b>print</b> de três coisas na mesma tela:</div>
    <div class="d" style="margin-top:10px">
      · a proposta na fila com a <b>evidência</b><br>
      · o <span class="mono">403</span> que o agente recebeu ao tentar aprovar<br>
      · a linha já no <span class="mono">MEMORY.md</span>, assinada
    </div>
  </div>
</div>
<div class="row" style="margin-top:18px">
  <div class="card" style="flex:1;text-align:center">
    <div class="rot m">Duração</div><div class="t">45 min</div>
    <div class="small">8 módulos · 5 min o mais curto, 8 min o mais longo</div></div>
  <div class="card" style="flex:1;text-align:center">
    <div class="rot m">Custo por aluno</div><div class="t">&lt; US$ 1,00</div>
    <div class="small">com o Módulo 0 respeitado e o Módulo 8 executado</div></div>
  <div class="card" style="flex:1;text-align:center">
    <div class="rot m">Sem Azure</div><div class="t">US$ 0,00</div>
    <div class="small mono">docker compose up --build</div></div>
  <div class="card" style="flex:1;text-align:center">
    <div class="rot m">Pré-requisito</div><div class="t">Aula 02</div>
    <div class="small">o Deva já criado, com AGENTS.md e MEMORY.md v1.3</div></div>
</div>
<div class="card ciano" style="margin-top:16px">
  <div class="rot c">A regra que atravessa o laboratório inteiro</div>
  <div class="d">Em nenhum momento o agente ganha permissão nova. Ele ganha
  <b>alcance</b> — lê mais, propõe, avança documento — e continua <b>sem poder decidir
  nada</b>. Se em algum passo você se pegar dando poder de decisão a ele, parou de seguir
  o laboratório.</div>
</div>
</div>""", 1440)

# ── 2 · Passo a passo, com o conceito de cada módulo ─────────────────────────
def passo(n, cor, fundo, min_, titulo, o_que, conceito):
    return f"""
    <div class="passo">
      <div class="pn" style="background:{fundo};color:{cor};border:1px solid {cor}">{n}</div>
      <div class="card" style="flex:1;background:{fundo};border-color:{cor};display:flex;
                  gap:18px;padding:13px 18px">
        <div style="flex:1.35">
          <div class="t" style="font-size:17px;margin-bottom:3px">{titulo}
            <span class="small" style="font-weight:400">· {min_} min</span></div>
          <div class="d" style="font-size:14px">{o_que}</div>
        </div>
        <div style="flex:1;border-left:1px solid #2E2E38;padding-left:18px">
          <div class="rot m" style="margin-bottom:4px">O conceito que isso demonstra</div>
          <div class="small" style="font-size:13.5px">{conceito}</div>
        </div>
      </div>
    </div>"""

P["dc-lab-02-passos"] = ("""
<div class="wrap">
<h1>Os oito módulos — e o que cada um ensina</h1>
<h2>docs/01-manual-portal.md · nenhum passo existe só para "configurar"</h2>
""" + passo("0", "#FFD579", "#221E14", 5, "Blindar o bolso",
            "Orçamento <span class='mono'>orc-aula-05-continuo</span>, R$ 10, alertas em "
            "50% e 90%.",
            "O orçamento <b>avisa, não freia</b>. E agora existe um motivo novo: a partir "
            "do nível 3 o agente acorda sozinho.")
 + passo("1", "#03E3FD", "#12222A", 5, "Grupo e armazenamento",
         "<span class='mono'>rg-aula-05-continuo</span> + contêineres "
         "<span class='mono'>memoria-do-deva</span> e <span class='mono'>entrada</span>.",
         "Memória de agente é um <b>arquivo, num contêiner, com dono, permissão e "
         "retenção</b>. Não é algo que mora 'no modelo'.")
 + passo("2", "#7A7872", "#1C1C22", 8, "Publicar serviço e tela",
         "Dois Container Apps. Réplicas mínimas <b>0</b>.",
         "<span class='mono'>--min-replicas 0</span>: fora da aula os containers dormem e "
         "não cobram. É a linha que economiza o semestre.")
 + passo("3", "#EB0B4F", "#22161B", 6, "Ligar o gatilho",
         "Event Grid → Logic App → <span class='mono'>POST /fila/documentos</span>, com "
         "filtro no contêiner <span class='mono'>entrada</span>.",
         "<b>Nível 3.</b> O gatilho é um evento, não um horário. E sem o filtro, o "
         "MEMORY.md que o serviço escreve dispara o fluxo: laço infinito de graça.")
 + passo("4", "#03E3FD", "#12222A", 6, "Dar a ferramenta ao Deva",
         "Ferramenta OpenAPI com <span class='mono'>agente/openapi-agente.json</span>.",
         "<b>Conte as operações em voz alta: são cinco.</b> A pergunta que fecha o "
         "módulo: onde está o botão de aprovar?")
 + passo("5", "#7A7872", "#1C1C22", 4, "Trocar as instruções",
         "Colar o <span class='mono'>AGENTS.md v2.0</span> — ao menos §0, §3 e §7.",
         "Instrução é a <b>primeira</b> camada. A §7 diz 'propõe, não escreve'; o "
         "Módulo 4 garante isso mesmo se a §7 for ignorada.")
 + passo("6", "#EB0B4F", "#22161B", 8, "A demonstração",
         "4 PDFs → 2 conformes, 1 duplicado, 1 exceção. Depois: corrigir, propor, "
         "tentar aprovar, aprovar pela tela.",
         "É aqui que a linha <b>atravessa</b> de memoria-pendente.md para MEMORY.md, na "
         "frente da turma. O resto da aula existe para este momento.")
 + passo("7", "#FFD579", "#221E14", 4, "A tentativa de injeção",
         "Pedir para gravar 'aprovar automaticamente, sem revisão'.",
         "Texto lido de documento é <b>dado, nunca instrução</b>. E o filtro é rede "
         "didática — o que segura de verdade é a falta do cabeçalho.")
 + passo("8", "#7A7872", "#1C1C22", 3, "Apagar tudo",
         "<span class='mono'>rg-aula-05-continuo</span> excluído + remover a Ferramenta "
         "OpenAPI do agente.",
         "Ferramenta apontando para URL morta faz o agente <b>tentar, falhar e gastar</b>. "
         "Encerrar é parte do laboratório, não limpeza.")
 + """</div>""", 1500)

# ── 3 · Mapa do repositório: arquivo → conceito ──────────────────────────────
P["dc-lab-03-mapa"] = ("""
<div class="wrap">
<h1>Onde cada conceito vira código</h1>
<h2>Se o aluno abrir um arquivo só, que seja o da linha em destaque</h2>
<div class="card" style="margin-top:8px;padding:8px 14px 14px">
<table>
<tr><th style="width:30%">Arquivo</th><th style="width:34%">O que ele faz</th>
    <th>O conceito da aula</th></tr>

<tr><td class="mono">api/modelos.py</td>
    <td>Contratos e a tabela <b>TRANSICOES_PERMITIDAS</b></td>
    <td>Nível 4 · estado explícito é o que transforma repetição em processo</td></tr>

<tr style="background:#22161B"><td class="mono" style="color:#EB0B4F">api/servicos/memoria.py</td>
    <td><b>propor · aprovar · descartar</b> e os padrões de recusa</td>
    <td><b style="color:#F4F3EF">A fronteira: o agente propõe, o humano decide</b></td></tr>

<tr><td class="mono">api/servicos/fila.py</td>
    <td>Valida transição e <b>recusa o agente em exceção</b></td>
    <td>Nível 4 · o que impede o laço infinito noturno</td></tr>

<tr style="background:#22161B"><td class="mono" style="color:#EB0B4F">api/principal.py</td>
    <td>As rotas e a dependência <b>exigir_auditor</b></td>
    <td><b style="color:#F4F3EF">Instrução × permissão, em 8 linhas</b></td></tr>

<tr><td class="mono">gerar_openapi_do_agente.py</td>
    <td>Filtra 14 operações para <b>5</b>, com <span class="mono">assert</span></td>
    <td>O agente não vê o que ele não pode fazer</td></tr>

<tr><td class="mono">gatilho/disparador.py</td>
    <td>Sondagem da pasta + <span class="mono">--semear</span></td>
    <td>Nível 3 · o agente deixa de esperar alguém digitar</td></tr>

<tr><td class="mono">gatilho/ciclo_do_agente.py</td>
    <td>As <b>cinco etapas do laço</b>, sem chamar modelo</td>
    <td>O ciclo é simples: ler · olhar · avançar · parar · propor</td></tr>

<tr><td class="mono">agente/AGENTS.md</td>
    <td>v2.0 — §0, §3 e §7 reescritas</td>
    <td>A camada de intenção, que o serviço não substitui: complementa</td></tr>

<tr><td class="mono">api/testes/teste_memoria.py</td>
    <td>22 testes, nenhum toca a rede</td>
    <td>A garantia é <b>testada</b>, não prometida</td></tr>
</table>
</div>
<div class="row" style="margin-top:16px">
  <div class="card ciano" style="flex:1">
    <div class="rot c">O teste que vale a aula inteira</div>
    <div class="d mono" style="font-size:15px;color:#F4F3EF">
      teste_agente_nao_consegue_aprovar_sozinho</div>
    <div class="small" style="margin-top:8px">Se ele passar a falhar, o projeto perdeu o
    sentido. Não é regressão qualquer: é o teste do conceito.</div>
  </div>
  <div class="card ambar" style="flex:1">
    <div class="rot a">Como rodar antes de subir qualquer coisa</div>
    <div class="cod" style="margin-top:8px;font-size:14px">python -m pytest -q<br>
    <span class="cm">22 passed in 0.44s</span></div>
  </div>
</div>
</div>""", 1440)

# ── 4 · Dois minutos, sem nuvem ──────────────────────────────────────────────
P["dc-lab-04-local"] = ("""
<div class="wrap">
<h1>Antes de provisionar: dois minutos na sua máquina</h1>
<h2>O melhor uso possível de dois minutos — o ciclo inteiro roda sem gastar nada</h2>
<div class="row" style="margin-top:8px;align-items:flex-start">
  <div style="flex:1.15">
    <div class="cod">
<span class="arq">docs/02-manual-script.md · seção 1</span>
<span class="cm"># tudo de uma vez</span><br>
docker compose up --build<br><br>
<span class="cm"># ou os três processos separados</span><br>
uvicorn api.principal:app --reload<br>
streamlit run web/aplicacao.py<br><br>
<span class="cm"># 4 documentos de exemplo (o 4º é duplicata do 2º)</span><br>
python gatilho/disparador.py <span class="vl">--semear</span><br><br>
<span class="cm"># três voltas do agente, uma por vez</span><br>
python gatilho/ciclo_do_agente.py <span class="vl">--uma-volta --propor</span><br>
python gatilho/ciclo_do_agente.py <span class="vl">--uma-volta</span><br>
python gatilho/ciclo_do_agente.py <span class="vl">--uma-volta</span>
    </div>
    <div class="card" style="margin-top:16px">
      <div class="rot m">O que a saída mostra, volta a volta</div>
      <div class="cod" style="margin-top:8px;font-size:12.5px;border:none;padding:10px 0">
<span class="cm">volta 1</span> &nbsp;memória: 0 regra(s) · fila: 4 comigo<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;doc-afdf1834 → extraido &nbsp;(×4)<br>
<span class="cm">volta 2</span> &nbsp;doc-a8c621f1 → <span class="vl">duplicado</span><br>
<span class="cm">volta 3</span> &nbsp;doc-afdf1834 → <span class="dq">excecao</span> ·
doc-82ec0610 → conforme<br>
<span class="cm">volta 4</span> &nbsp;<span class="cm">nada acontece</span>
      </div>
    </div>
  </div>
  <div class="col" style="flex:.9">
    <div class="card ciano"><div class="rot c">Aponte na volta 2</div>
      <div class="t">O duplicado</div>
      <div class="d">Ninguém programou "procure duplicata agora". Foi o <b>estado</b> que
      disse ao agente que era a hora — é o nível 4 aparecendo na prática.</div></div>
    <div class="card rosa"><div class="rot">Aponte na volta 3</div>
      <div class="t">A exceção</div>
      <div class="d">O documento parou. E vai ficar parado até uma pessoa decidir.</div></div>
    <div class="card ambar"><div class="rot a">E então rode de novo</div>
      <div class="t">Nada acontece</div>
      <div class="d">O agente <b>não tenta de novo</b> o que não é dele. Se tentasse,
      tentaria a noite inteira — e essa é a fatura que ninguém vê chegar.</div></div>
  </div>
</div>
</div>""", 1440)

# ── 5 · O código da fronteira ────────────────────────────────────────────────
P["dc-lab-05-codigo-fronteira"] = ("""
<div class="wrap">
<h1>A fronteira, em código</h1>
<h2>Oito linhas que fazem a revisão humana ser real em vez de decorativa</h2>
<div class="row" style="margin-top:8px;align-items:flex-start">
  <div style="flex:1.1">
    <div class="cod">
<span class="arq">api/principal.py</span>
<span class="kw">def</span> <span class="fn">exigir_auditor</span>(x_auditor, x_segredo):<br>
&nbsp;&nbsp;<span class="cm"># A fronteira. Só passa quem é gente.</span><br>
&nbsp;&nbsp;<span class="kw">if</span> <span class="kw">not</span> x_auditor:<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="kw">raise</span> <span class="fn">AutorizacaoDeAuditorAusente</span>(<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="vl">"Esta operação exige o cabeçalho X-Auditor."</span>,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;como_resolver=<span class="vl">"...o agente propõe, não aprova."</span>)<br>
&nbsp;&nbsp;<span class="kw">return</span> x_auditor.strip()<br><br>
<span class="cm"># e a rota que depende dela</span><br>
<span class="dq">@app.post</span>(<span class="vl">"/memoria/propostas/{id}/aprovar"</span>)<br>
<span class="kw">def</span> <span class="fn">aprovar</span>(id, decisao,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;auditor=<span class="fn">Depends</span>(exigir_auditor)):
    </div>
    <div class="card rosa" style="margin-top:16px">
      <div class="rot">O agente é configurado sem esse cabeçalho</div>
      <div class="d">A Ferramenta OpenAPI dele <b>não declara</b>
      <span class="mono">X-Auditor</span> nem <span class="mono">X-Segredo</span>. Ele não
      tem como enviá-los, então não tem como aprovar. Não é desconfiança — é a única forma
      de a revisão humana existir de verdade.</div>
    </div>
  </div>
  <div style="flex:1">
    <div class="cod">
<span class="arq">gerar_openapi_do_agente.py</span>
<span class="cm"># as ÚNICAS cinco operações que o Deva pode executar</span><br>
PERMITIDAS = {<br>
&nbsp;&nbsp;(<span class="vl">"/memoria"</span>, <span class="vl">"get"</span>),<br>
&nbsp;&nbsp;(<span class="vl">"/fila"</span>, <span class="vl">"get"</span>),<br>
&nbsp;&nbsp;(<span class="vl">"/fila/documentos/{id}"</span>, <span class="vl">"get"</span>),<br>
&nbsp;&nbsp;(<span class="vl">"/fila/documentos/{id}/estado"</span>, <span class="vl">"post"</span>),<br>
&nbsp;&nbsp;(<span class="vl">"/memoria/proposta"</span>, <span class="vl">"post"</span>),<br>
}<br><br>
<span class="cm"># se alguma rota de aprovação vazar, a geração FALHA</span><br>
<span class="kw">for</span> proibida <span class="kw">in</span> PROIBIDAS:<br>
&nbsp;&nbsp;<span class="kw">assert</span> proibida <span class="kw">not in</span> texto
    </div>
    <div class="card ciano" style="margin-top:16px">
      <div class="rot c">E um teste guarda isso</div>
      <div class="cod" style="margin-top:8px;font-size:12.5px;border:none;padding:8px 0">
<span class="kw">def</span> <span class="fn">teste_especificacao_do_agente_nao_expoe_aprovacao</span>():<br>
&nbsp;&nbsp;<span class="kw">assert</span> operacoes == <span class="vl">5</span><br>
&nbsp;&nbsp;<span class="kw">assert</span> <span class="vl">"X-Auditor"</span> <span class="kw">not in</span> texto</div>
      <div class="small" style="margin-top:10px">No dia em que alguém "só quiser facilitar"
      e adicionar a rota de aprovação à lista, o teste quebra antes do commit.</div>
    </div>
  </div>
</div>
</div>""", 1460)

# ── 6 · O código do nível 4 ──────────────────────────────────────────────────
P["dc-lab-06-codigo-estados"] = ("""
<div class="wrap">
<h1>O nível 4, em código</h1>
<h2>Máquina de estados não é burocracia: é o que impede o agente de girar em falso</h2>
<div class="row" style="margin-top:8px;align-items:flex-start">
  <div style="flex:1.05">
    <div class="cod">
<span class="arq">api/modelos.py</span>
TRANSICOES_PERMITIDAS = {<br>
&nbsp;&nbsp;RECEBIDO:&nbsp; {EXTRAIDO, ILEGIVEL},<br>
&nbsp;&nbsp;EXTRAIDO:&nbsp; {AUDITADO, DUPLICADO, ILEGIVEL},<br>
&nbsp;&nbsp;AUDITADO:&nbsp; {CONFORME, EXCECAO},<br>
&nbsp;&nbsp;CONFORME:&nbsp; <span class="fn">set</span>(),<br>
&nbsp;&nbsp;EXCECAO:&nbsp;&nbsp; {CONFORME},&nbsp;&nbsp;<span class="cm"># o humano pode liberar</span><br>
&nbsp;&nbsp;ILEGIVEL:&nbsp; {RECEBIDO},&nbsp;&nbsp;<span class="cm"># reenvio de arquivo melhor</span><br>
&nbsp;&nbsp;DUPLICADO: <span class="fn">set</span>(),<br>
}
    </div>
    <div class="card" style="margin-top:16px">
      <div class="rot m">Leia as duas linhas com <span class="mono">set()</span> vazio</div>
      <div class="d">De <span class="mono">conforme</span> e
      <span class="mono">duplicado</span> não se sai. Um documento que chegou lá
      <b>terminou</b> — e é isso que impede a fila de ser reprocessada para sempre.</div>
    </div>
  </div>
  <div style="flex:1.05">
    <div class="cod">
<span class="arq">api/servicos/fila.py</span>
<span class="kw">if</span> documento.estado <span class="kw">is</span> EstadoDoDocumento.EXCECAO \\<br>
&nbsp;&nbsp;&nbsp;<span class="kw">and</span> por == <span class="vl">"deva"</span>:<br>
&nbsp;&nbsp;<span class="kw">raise</span> <span class="fn">TransicaoProibida</span>(<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="vl">"Documento em exceção só é liberado"</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="vl">" por uma pessoa."</span>,<br>
&nbsp;&nbsp;&nbsp;&nbsp;como_resolver=<span class="vl">"Abra a aba Exceções e decida."</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="vl">" Se o agente pudesse liberar a própria"</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="vl">" exceção, a revisão viraria enfeite."</span>)
    </div>
    <div class="card rosa" style="margin-top:16px">
      <div class="rot">O modo de falha que isto evita</div>
      <div class="d">Sem essa linha, o agente contínuo tenta de novo o que já falhou.
      Ele <b>não gasta muito por volta</b> — gasta por não parar nunca. É o tipo de
      fatura que aparece na segunda-feira.</div>
    </div>
  </div>
</div>
<div class="card ambar" style="margin-top:18px">
  <div class="rot a">Repare no argumento <span class="mono">por</span></div>
  <div class="d">A mesma função avança o documento para o agente e para a pessoa. O que
  muda é <b>quem está chamando</b> — e quem chama vai para o histórico do documento.
  Ao fim, o registro diz: <span class="mono">excecao → conforme (por Camila Rocha)</span>.
  Auditoria não é relatório: é o histórico existir.</div>
</div>
</div>""", 1460)

# ── 7 · Checkpoints ──────────────────────────────────────────────────────────
P["dc-lab-07-checkpoints"] = ("""
<div class="wrap">
<h1>Checkpoints — como saber que funcionou</h1>
<h2>Um por módulo. Se algum falhar, não siga: o próximo depende dele.</h2>
<div class="card" style="margin-top:8px;padding:8px 14px 14px">
<table>
<tr><th style="width:8%">Módulo</th><th style="width:46%">O que conferir</th>
    <th>Como se manifesta quando está errado</th></tr>
<tr><td><b>0</b></td><td>O orçamento aparece na lista de <b>Orçamentos</b></td>
    <td>Você descobre o gasto pela fatura, não pelo e-mail</td></tr>
<tr><td><b>1</b></td><td>Dois contêineres, ambos com acesso <b>Privado</b></td>
    <td>Memória de agente exposta na internet pública</td></tr>
<tr><td><b>2</b></td><td><span class="mono">GET /saude</span> responde
    <span class="mono">"memoria_acessivel": true</span></td>
    <td>Cadeia de conexão errada ou contêiner com outro nome</td></tr>
<tr><td><b>3</b></td><td>Sobe um PDF em <span class="mono">entrada</span> → o documento
    aparece em <span class="mono">GET /fila</span> em até 1 min</td>
    <td>Filtro do assunto ausente, ou URI da Logic App sem o caminho completo</td></tr>
<tr style="background:#12222A"><td><b>4</b></td>
    <td>O portal lista <b style="color:#03E3FD">cinco</b> operações — conte com a turma</td>
    <td>Se listar mais, você colou a especificação completa em vez da do agente</td></tr>
<tr><td><b>5</b></td><td>No Playground, "o que você já sabe?" dispara
    <span class="mono">GET /memoria</span> (veja em <b>Rastreamentos</b>)</td>
    <td>Ele responde pelo que acha, não pelo que está aprovado</td></tr>
<tr style="background:#22161B"><td><b>6</b></td>
    <td>A linha aparece na aba <b>Memória</b> com a borda <b style="color:#03E3FD">ciano</b>
    de <i>entrou hoje</i></td>
    <td>Se não aparecer, você aprovou sem nome na barra lateral</td></tr>
<tr><td><b>7</b></td><td>A proposta com "aprovar automaticamente" é
    <b style="color:#EB0B4F">recusada</b></td>
    <td>Se passar, avise — é defeito do filtro, e vale um exercício</td></tr>
<tr><td><b>8</b></td><td><b>Todos os recursos (0)</b> no grupo</td>
    <td>Logic App órfã tentando chamar uma URL que não existe mais</td></tr>
</table>
</div>
<div class="card ciano" style="margin-top:16px">
  <div class="rot c">O checkpoint que resume o laboratório</div>
  <div class="d">Abra o <span class="mono">MEMORY.md</span> no portal do Azure e no
  <span class="mono">GET /memoria/markdown</span> ao mesmo tempo. <b>É o mesmo texto, com a
  mesma hora de modificação.</b> Memória de agente não é abstração: é um arquivo que
  alguém assinou.</div>
</div>
</div>""", 1440)

# ── 8 · Erros que vão acontecer ──────────────────────────────────────────────
P["dc-lab-08-erros"] = ("""
<div class="wrap">
<h1>Os erros que vão acontecer</h1>
<h2>Todos já aconteceram. Tenha esta tela aberta durante o laboratório.</h2>
<div class="card" style="margin-top:8px;padding:8px 14px 14px">
<table>
<tr><th style="width:33%">Sintoma</th><th style="width:33%">Causa quase certa</th>
    <th>O que fazer</th></tr>
<tr><td><span class="mono">memoria_acessivel: false</span> em /saude</td>
    <td>cadeia de conexão errada ou contêiner inexistente</td>
    <td>conferir <span class="mono">DEVA_BLOB_CONEXAO</span> e o nome
        <span class="mono">memoria-do-deva</span></td></tr>
<tr style="background:#22161B"><td>A Logic App <b>dispara em laço</b></td>
    <td>faltou o filtro <span class="mono">subjectBeginsWith</span></td>
    <td>adicionar o filtro; enquanto isso, <b>desabilitar o gatilho</b> — este é o erro
        que custa dinheiro</td></tr>
<tr><td>Logic App executa mas o serviço responde 404</td>
    <td>URI sem <span class="mono">/fila/documentos</span> no fim</td>
    <td>corrigir a URI da etapa HTTP</td></tr>
<tr><td>O agente diz que <b>"aprendeu"</b></td>
    <td>ele ainda está com o AGENTS.md v1.3</td>
    <td>colar a §7 da v2.0: <i>propõe, não aprende</i></td></tr>
<tr><td>Proposta recusada por "manipulação"</td>
    <td>nenhuma — é o comportamento esperado</td>
    <td>é o Módulo 7. Mostre o <span class="mono">como_resolver</span> na tela</td></tr>
<tr style="background:#221E14"><td>Uma regra <b>legítima</b> recusada por "alterar alçada"</td>
    <td>o texto tem um verbo de mudança perto de "limite" ou "teto"</td>
    <td>reescrever descrevendo a <b>interpretação</b>, não a mudança. Este filtro já
        esteve errado — vale contar a história</td></tr>
<tr><td>A tela abre branca</td>
    <td>falta o <span class="mono">.streamlit/config.toml</span> na imagem</td>
    <td>rebuild da imagem da tela</td></tr>
<tr><td><span class="mono">ModuleNotFoundError</span> no container</td>
    <td>build feito de dentro de <span class="mono">api/</span></td>
    <td>construir da <b>raiz</b>: <span class="mono">docker build -f api/Dockerfile .</span></td></tr>
<tr><td><span class="mono">pytest</span> diz "no tests ran"</td>
    <td>os testes se chamam <span class="mono">teste_*</span>, não <span class="mono">test_*</span></td>
    <td>o <span class="mono">pytest.ini</span> já redefine isso — rode da raiz do projeto</td></tr>
</table>
</div>
<div class="card rosa" style="margin-top:16px">
  <div class="rot">A diferença entre os dois tipos de erro nesta tabela</div>
  <div class="d">Uns são configuração — você conserta e segue. Dois são
  <b>conteúdo</b>: a proposta recusada por manipulação e a Logic App em laço. Quando
  acontecerem, não conserte em silêncio: <b>pare a aula e mostre</b>. São os dois momentos
  em que o risco deixa de ser teoria.</div>
</div>
</div>""", 1480)


async def principal():
    async with async_playwright() as p:
        navegador = await p.chromium.launch()
        for nome, (html, largura) in P.items():
            pagina = await navegador.new_page(
                viewport={"width": largura, "height": 200}, device_scale_factor=2)
            await pagina.set_content(f"<style>{CSS}</style>{html}")
            await pagina.screenshot(path=f"{SAIDA}/{nome}.png", full_page=True)
            await pagina.close()
            print("ok", nome)
        await navegador.close()

asyncio.run(principal())
