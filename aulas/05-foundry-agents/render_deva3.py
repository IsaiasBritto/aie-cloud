"""Figuras do deck do Deva3, na identidade visual FIAP.

    python3 figuras/render_deva3.py
"""
import asyncio, os
from pathlib import Path

from playwright.async_api import async_playwright

# Saída relativa ao próprio script — funciona em qualquer máquina.
SAIDA = str(Path(__file__).resolve().parent / "png")
os.makedirs(SAIDA, exist_ok=True)

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'DejaVu Sans','Segoe UI',system-ui,sans-serif;background:#15151A;color:#F4F3EF;
     -webkit-font-smoothing:antialiased}
.wrap{padding:44px}
h1{font-size:38px;font-weight:700;letter-spacing:-.5px;margin-bottom:6px;color:#F4F3EF}
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
.t{font-size:19px;font-weight:700;margin-bottom:8px;color:#F4F3EF}
.d{font-size:15px;line-height:1.5;color:#C3C1BA}
.small{font-size:13px;color:#7A7872;line-height:1.45}
.mono{font-family:'DejaVu Sans Mono',monospace}
table{width:100%;border-collapse:collapse;font-size:15px;color:#C3C1BA}
th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.6px;
   color:#7A7872;padding:9px 11px;border-bottom:1px solid #3A3A46}
td{padding:10px 11px;border-bottom:1px solid #26262E;vertical-align:top}
td b,td strong{color:#F4F3EF}
.seta{display:flex;align-items:center;justify-content:center;font-size:26px;
      color:#EB0B4F;font-weight:700;min-width:26px}
.cod{background:#101014;border:1px solid #26262E;border-radius:4px;padding:16px 18px;
     font-family:'DejaVu Sans Mono',monospace;font-size:13.5px;line-height:1.65;color:#C3C1BA}
.ch{color:#03E3FD}.vl{color:#FFD579}.cm{color:#5F6270}.dq{color:#EB0B4F}
"""

def janela(titulo, corpo, clara=True):
    fundo = "#fff" if clara else "#101014"
    barra = "#f2f3f5" if clara else "#1C1C22"
    borda = "#3A3A46"
    cor_t = "#5b6270" if clara else "#7A7872"
    return f"""
    <div style="border:1px solid {borda};border-radius:8px;overflow:hidden;
                box-shadow:0 10px 34px rgba(0,0,0,.55);background:{fundo}">
      <div style="background:{barra};border-bottom:1px solid {borda};padding:10px 15px;
                  display:flex;align-items:center;gap:8px">
        <span style="width:10px;height:10px;border-radius:50%;background:#ff5f57"></span>
        <span style="width:10px;height:10px;border-radius:50%;background:#febc2e"></span>
        <span style="width:10px;height:10px;border-radius:50%;background:#28c840"></span>
        <span style="margin-left:12px;font-size:13px;color:{cor_t};font-weight:600">{titulo}</span>
      </div>
      <div>{corpo}</div>
    </div>"""

P = {}

# ── 1 · Arquitetura ──────────────────────────────────────────────────────
P["d3-01-arquitetura"] = ("""
<div class="wrap">
<h1>Arquitetura do Deva3</h1>
<h2>Dois containers, um serviço cognitivo, um blob — e nada mais</h2>
<div class="row" style="align-items:center;margin-top:6px">
  <div class="card" style="flex:.95;text-align:center">
    <div class="rot m">Aluno</div><div class="t">📷 Foto</div>
    <div class="small">JPEG · PNG · BMP<br>até 4 MB</div></div>
  <div class="seta">→</div>
  <div class="card ciano" style="flex:1.1;text-align:center">
    <div class="rot c">Container 1</div><div class="t">Streamlit</div>
    <div class="small mono">ca-deva3-web<br>porta 8501</div></div>
  <div class="seta">→</div>
  <div class="card rosa" style="flex:1.15;text-align:center">
    <div class="rot">Container 2</div><div class="t">FastAPI</div>
    <div class="small mono">ca-deva3-api<br>porta 8000</div></div>
  <div class="seta">→</div>
  <div class="card ambar" style="flex:1.25;text-align:center">
    <div class="rot a">Serviço cognitivo</div><div class="t">Azure AI Vision</div>
    <div class="small mono">imageanalysis:analyze<br>features=people</div></div>
</div>
<div class="row" style="margin-top:18px">
  <div class="card" style="flex:1.6">
    <div class="rot">O que volta</div>
    <div class="d"><span class="mono">boundingBox {x, y, w, h}</span> + <span class="mono">confidence</span>
    por detecção. A API traduz para o nosso contrato em português e devolve o JSON.</div></div>
  <div class="card ciano" style="flex:1">
    <div class="rot c">Com consentimento</div>
    <div class="d">Blob Storage guarda <span class="mono">original.jpg</span> e
    <span class="mono">resultado.json</span> em <span class="mono">deteccoes/AAAA/MM/DD/&lt;id&gt;/</span></div></div>
  <div class="card" style="flex:1">
    <div class="rot m">Sem consentimento</div>
    <div class="d">Grava <b>só o JSON</b>. A foto não é persistida em lugar nenhum.</div></div>
</div>
<div class="card rosa" style="margin-top:16px">
  <div class="t">O que o Deva3 deliberadamente não faz</div>
  <div class="d">Não identifica ninguém · não compara rostos · não guarda template biométrico ·
  não infere idade, gênero ou emoção. Ele detecta presença e devolve caixa.</div>
</div>
</div>""", 1280)

# ── 2 · Payload anotado ──────────────────────────────────────────────────
P["d3-02-payload"] = ("""
<div class="wrap">
<h1>O payload é o material didático</h1>
<h2>Todo campo em português, porque o aluno vai abrir o JSON e ler</h2>
<div class="row" style="margin-top:6px">
  <div style="flex:1.35">
""" + janela("POST /detectar?modo=pessoas — 200 OK", """
<div class="cod">
{<br>
&nbsp;&nbsp;<span class="ch">"identificador"</span>: <span class="vl">"9f2c41ab77de"</span>,<br>
&nbsp;&nbsp;<span class="ch">"modo"</span>: <span class="vl">"pessoas"</span>,<br>
&nbsp;&nbsp;<span class="ch">"servico"</span>: <span class="vl">"Azure AI Vision · Image Analysis 4.0"</span>,<br>
&nbsp;&nbsp;<span class="ch">"dimensoes"</span>: { <span class="ch">"largura"</span>: <span class="vl">1280</span>, <span class="ch">"altura"</span>: <span class="vl">960</span> },<br>
&nbsp;&nbsp;<span class="ch">"limiar_confianca"</span>: <span class="dq">0.60</span>,<br>
&nbsp;&nbsp;<span class="ch">"total_detectado"</span>: <span class="vl">2</span>,<br>
&nbsp;&nbsp;<span class="ch">"total_acima_do_limiar"</span>: <span class="vl">1</span>,<br>
&nbsp;&nbsp;<span class="ch">"deteccoes"</span>: [<br>
&nbsp;&nbsp;&nbsp;&nbsp;{<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="ch">"indice"</span>: <span class="vl">1</span>,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="ch">"caixa"</span>: { <span class="ch">"x"</span>: <span class="vl">412</span>, <span class="ch">"y"</span>: <span class="vl">96</span>,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="ch">"largura"</span>: <span class="vl">288</span>, <span class="ch">"altura"</span>: <span class="vl">640</span> },<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="ch">"confianca"</span>: <span class="dq">0.947</span>,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="ch">"acima_do_limiar"</span>: <span class="vl">true</span>,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="ch">"proporcao_da_imagem"</span>: <span class="vl">0.15</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;}<br>
&nbsp;&nbsp;],<br>
&nbsp;&nbsp;<span class="ch">"duracao_ms"</span>: <span class="vl">412</span>,<br>
&nbsp;&nbsp;<span class="ch">"imagem_persistida"</span>: <span class="vl">true</span>,<br>
&nbsp;&nbsp;<span class="ch">"caminho_blob"</span>: <span class="vl">"deteccoes/2026/08/30/9f2c…"</span><br>
}
</div>""", clara=False) + """
  </div>
  <div class="col" style="flex:1">
    <div class="card rosa"><div class="rot">limiar_confianca</div>
      <div class="d">A régua vai <b>no payload</b>. Quem lê o JSON sabe com qual critério
      aquele resultado foi julgado — sem precisar perguntar.</div></div>
    <div class="card ciano"><div class="rot c">acima_do_limiar</div>
      <div class="d">A API já aplica a regra. A interface só pinta: ciano acima, âmbar abaixo.</div></div>
    <div class="card ambar"><div class="rot a">confianca pode ser nula</div>
      <div class="d">No modo <span class="mono">rostos</span> a Azure não devolve confiança.
      Modelar a ausência é mais honesto que inventar um <span class="mono">0.0</span>.</div></div>
    <div class="card"><div class="rot m">duracao_ms · proporcao_da_imagem</div>
      <div class="d">Custo e tamanho relativo da caixa. É o que transforma
      demonstração em medição.</div></div>
  </div>
</div>
</div>""", 1280)

# ── 3 · Os dois modos ────────────────────────────────────────────────────
P["d3-03-dois-modos"] = ("""
<div class="wrap">
<h1>Por que o modo padrão não é "rostos"</h1>
<h2>A decisão de arquitetura que evita a aula travar</h2>
<table style="margin-top:6px">
<tr><th style="width:270px"></th>
    <th style="width:420px">modo=pessoas &nbsp;<span style="color:#03E3FD">(padrão)</span></th>
    <th>modo=rostos &nbsp;<span style="color:#FFD579">(opcional)</span></th></tr>
<tr><td><b>Serviço</b></td>
    <td>Azure AI Vision · Image Analysis 4.0</td>
    <td>Azure AI Face · <span class="mono">/face/v1.2/detect</span></td></tr>
<tr><td><b>Precisa de aprovação?</b></td>
    <td style="color:#03E3FD"><b>Não.</b> Qualquer chave de Vision serve</td>
    <td style="color:#EB0B4F"><b>Sim.</b> Acesso Limitado, com formulário</td></tr>
<tr><td><b>Devolve confiança?</b></td>
    <td style="color:#03E3FD"><b>Sim</b> — <span class="mono">confidence</span> de 0 a 1</td>
    <td style="color:#EB0B4F"><b>Não.</b> Só o retângulo</td></tr>
<tr><td><b>Campos da resposta</b></td>
    <td class="mono">boundingBox {x, y, w, h}</td>
    <td class="mono">faceRectangle {top, left, width, height}</td></tr>
<tr><td><b>O que a caixa cerca</b></td><td>a pessoa inteira</td><td>o rosto</td></tr>
<tr><td><b>Risco em sala</b></td>
    <td>baixo</td>
    <td>alto — a turma pode não conseguir criar o recurso</td></tr>
</table>
<div class="row" style="margin-top:20px">
  <div class="card ambar" style="flex:1.3">
    <div class="rot a">A nota derivada</div>
    <div class="d">Como o Face não dá confiança, o Deva3 pede
    <span class="mono">qualityForRecognition</span> e converte
    <span class="mono">high/medium/low</span> em <span class="mono">0,95 / 0,70 / 0,35</span> —
    e diz no payload, num aviso, que a nota é <b>derivada</b>. Nunca invente um número
    e chame de confiança.</div></div>
  <div class="card ciano" style="flex:1">
    <div class="rot c">A conversão fica num lugar só</div>
    <div class="d">O Face usa <span class="mono">left/top</span>; nosso contrato usa
    <span class="mono">x/y</span>. A tradução acontece dentro de
    <span class="mono">ServicoFaceAzure._interpretar</span> — e só ali.</div></div>
</div>
</div>""", 1280)

# ── 4 · Estrutura do repositório ─────────────────────────────────────────
P["d3-04-repositorio"] = ("""
<div class="wrap">
<h1>A estrutura do repositório</h1>
<h2>Cada pasta responde a uma pergunta</h2>
<div class="row" style="margin-top:6px">
  <div style="flex:1.15">
""" + janela("05-foundry-agents/Lab/", """
<div class="cod" style="border:0;border-radius:0">
<span class="dq">AGENTS.md</span>              <span class="cm">a alma do agente</span><br>
<span class="dq">MEMORY.md</span>              <span class="cm">lido no início de TODA sessão</span><br>
README.md<br>
.env.exemplo           <span class="cm">o .env real nunca é versionado</span><br>
docker-compose.yml<br>
Makefile · pytest.ini<br>
<span class="ch">api/</span><br>
&nbsp;&nbsp;principal.py         <span class="cm">/ · /saude · /detectar</span><br>
&nbsp;&nbsp;configuracao.py      <span class="cm">variáveis de ambiente</span><br>
&nbsp;&nbsp;modelos.py           <span class="cm">o contrato de dados</span><br>
&nbsp;&nbsp;erros.py             <span class="cm">erros com "como_resolver"</span><br>
&nbsp;&nbsp;<span class="ch">servicos/</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;detector_visao.py<br>
&nbsp;&nbsp;&nbsp;&nbsp;detector_rostos.py<br>
&nbsp;&nbsp;&nbsp;&nbsp;armazenamento.py<br>
&nbsp;&nbsp;<span class="ch">testes/</span>              <span class="cm">15 testes, sem rede</span><br>
<span class="ch">web/</span>aplicacao.py       <span class="cm">interface Streamlit</span><br>
<span class="ch">infra/</span>                 <span class="cm">az CLI + Bicep</span><br>
<span class="ch">skills/</span>                <span class="cm">3 procedimentos salvos</span><br>
<span class="ch">docs/</span>                  <span class="cm">os três manuais</span>
</div>""", clara=False) + """
  </div>
  <div class="col" style="flex:1">
    <div class="card rosa"><div class="rot">AGENTS.md · seção 0</div>
      <div class="d">"<b>Leia o MEMORY.md antes de qualquer outra ação.</b>"<br><br>
      Sem essa linha escrita, o arquivo de memória existe e nunca é lido — o erro
      silencioso mais comum de quem monta agente.</div></div>
    <div class="card ciano"><div class="rot c">Tudo em português</div>
      <div class="d"><span class="mono">ServicoVisaoAzure</span> ·
      <span class="mono">CaixaDelimitadora</span> · <span class="mono">detectar</span> ·
      <span class="mono">teste_regra_do_limiar</span><br><br>
      Em inglês só o que não é nosso: bibliotecas, campos que a Azure devolve e termos
      de infra consagrados.</div></div>
    <div class="card"><div class="rot m">pytest.ini existe por quê?</div>
      <div class="d">Os testes se chamam <span class="mono">teste_*</span>, não
      <span class="mono">test_*</span>. Sem redefinir isso, o pytest diz
      "no tests ran" e o aluno acha que quebrou.</div></div>
  </div>
</div>
</div>""", 1280)

# ── 5 · Recursos do rg-aula-05 ───────────────────────────────────────────
P["d3-05-recursos"] = ("""
<div class="wrap">
<h1>O que existe dentro do <span class="mono">rg-aula-05</span></h1>
<h2>Sete recursos, um grupo — e um comando que apaga tudo</h2>
<table style="margin-top:6px">
<tr><th style="width:56px">#</th><th style="width:290px">Recurso</th><th style="width:280px">Nome</th>
    <th style="width:250px">Para quê</th><th>Cobra parado?</th></tr>
<tr><td class="mono" style="color:#EB0B4F"><b>1</b></td><td><b>Grupo de recursos</b></td>
    <td class="mono">rg-aula-05</td><td>A pasta que apaga tudo de uma vez</td>
    <td style="color:#03E3FD">não</td></tr>
<tr><td class="mono" style="color:#EB0B4F"><b>2</b></td><td><b>Conta de armazenamento</b></td>
    <td class="mono">stdeva3&lt;sufixo&gt;</td><td>Container privado <span class="mono">deteccoes</span></td>
    <td>só o que estiver guardado</td></tr>
<tr><td class="mono" style="color:#EB0B4F"><b>3</b></td><td><b>Pesquisa Visual Computacional</b></td>
    <td class="mono">cv-deva3-&lt;sufixo&gt;</td><td>O cérebro · nível F0</td>
    <td style="color:#03E3FD">não</td></tr>
<tr><td class="mono" style="color:#EB0B4F"><b>4</b></td><td><b>Registro de contêiner</b></td>
    <td class="mono">acrdeva3&lt;sufixo&gt;</td><td>Guarda as duas imagens</td>
    <td style="color:#EB0B4F"><b>sim — custo fixo</b></td></tr>
<tr><td class="mono" style="color:#EB0B4F"><b>5</b></td><td><b>Ambiente de Container Apps</b></td>
    <td class="mono">cae-aula-05</td><td>Onde os apps rodam</td>
    <td style="color:#03E3FD">não</td></tr>
<tr><td class="mono" style="color:#EB0B4F"><b>6</b></td><td><b>Container App · API</b></td>
    <td class="mono">ca-deva3-api</td><td>FastAPI · porta 8000</td>
    <td style="color:#03E3FD">não · escala a zero</td></tr>
<tr><td class="mono" style="color:#EB0B4F"><b>7</b></td><td><b>Container App · interface</b></td>
    <td class="mono">ca-deva3-web</td><td>Streamlit · porta 8501</td>
    <td style="color:#03E3FD">não · escala a zero</td></tr>
</table>
<div class="row" style="margin-top:20px">
  <div class="card ambar" style="flex:1.2"><div class="rot a">Nome global</div>
    <div class="d">Conta de armazenamento e registro de contêiner têm nome único
    <b>no mundo inteiro</b>. Sem sufixo próprio, o script falha com "já está em uso".</div></div>
  <div class="card ciano" style="flex:1"><div class="rot c">F0 tem limite</div>
    <div class="d">20 chamadas por minuto e <b>um por assinatura por região</b>.
    Turma de 40 clicando junto = HTTP 429 garantido.</div></div>
  <div class="card rosa" style="flex:1"><div class="rot">O módulo que ninguém faz</div>
    <div class="d"><span class="mono">bash infra/99-remover-tudo.sh</span><br>
    O registro Basic continua cobrando enquanto existir.</div></div>
</div>
</div>""", 1280)

# ── 6 · Duas trilhas ─────────────────────────────────────────────────────
P["d3-06-duas-trilhas"] = ("""
<div class="wrap">
<h1>Duas trilhas, o mesmo laboratório</h1>
<h2>Primeiro pelo portal, para entender. Depois por script, para repetir.</h2>
<div class="row" style="margin-top:6px">
  <div class="card ciano" style="flex:1">
    <div class="rot c">Trilha 1 · Portal</div>
    <div class="t">35 a 45 minutos, sem um comando</div>
    <div class="d small" style="margin-top:12px;line-height:1.9">
    <b>0</b> · Orçamento com alerta em 50% e 90%<br>
    <b>1</b> · Grupo de recursos <span class="mono">rg-aula-05</span><br>
    <b>2</b> · Conta de armazenamento + contêiner <span class="mono">deteccoes</span><br>
    <b>3</b> · Pesquisa Visual Computacional · <b>Free F0</b><br>
    <b>4</b> · Registro de contêiner · SKU Basic<br>
    <b>5</b> · Enviar as imagens para o registro<br>
    <b>6</b> · Aplicativo de contêiner · API · porta 8000<br>
    <b>7</b> · Aplicativo de contêiner · interface · porta 8501<br>
    <b>8</b> · Excluir o grupo de recursos
    </div>
    <div class="small" style="margin-top:14px;color:#03E3FD">
    Ensina <b>o que</b> cada recurso é. É a trilha da primeira vez.</div>
  </div>
  <div class="card rosa" style="flex:1">
    <div class="rot">Trilha 2 · Script</div>
    <div class="t">10 a 15 minutos, três comandos</div>
    <div class="cod" style="margin-top:12px;font-size:12.5px;background:#101014">
<span class="cm"># uma vez por máquina</span><br>
az login<br>
az extension add --name containerapp<br>
az provider register -n Microsoft.App --wait<br><br>
<span class="cm"># o laboratório inteiro</span><br>
export SUFIXO=fiap01<br>
bash infra/<span class="ch">01-criar-recursos.sh</span><br>
bash infra/<span class="ch">02-publicar-imagens.sh</span><br>
bash infra/<span class="ch">03-implantar-apps.sh</span><br><br>
<span class="cm"># no fim da aula</span><br>
bash infra/<span class="dq">99-remover-tudo.sh</span>
    </div>
    <div class="small" style="margin-top:14px;color:#EB0B4F">
    Ensina <b>como</b> repetir. Só depois que a turma entendeu o quê.</div>
  </div>
</div>
<div class="card" style="margin-top:18px">
  <div class="rot m">O único passo sem equivalente clicável</div>
  <div class="d"><span class="mono">az acr build --registry $ACR --image deva3-api:v1 --file api/Dockerfile .</span><br>
  Ele envia a pasta e <b>constrói dentro da Azure</b> — o aluno não precisa de Docker na máquina.
  Vale dizer isso à turma em vez de fingir que dá para clicar.</div>
</div>
</div>""", 1280)

# ── 7 · IA Responsável (tela real) ───────────────────────────────────────
P["d3-07-ia-responsavel"] = ("""
<div class="wrap">
<h1>A tela que ninguém lê</h1>
<h2>Criar a Pesquisa Visual Computacional → Aviso de IA Responsável</h2>
""" + janela("Criar a Pesquisa Visual Computacional — Microsoft Azure", """
<div style="padding:24px 28px;color:#14161a;font-size:15px">
  <div style="display:flex;gap:24px;border-bottom:1px solid #e3e6ea;padding-bottom:11px;
              font-size:14px;color:#5b6270">
    <b style="color:#0a63c9;border-bottom:2px solid #0a63c9;padding-bottom:11px">Básico</b>
    <span>Rede</span><span>Identity</span><span>Tags</span><span>Examinar + criar</span>
  </div>
  <table style="font-size:15px;color:#14161a;margin-top:18px">
    <tr><td style="width:200px;border:0;padding:7px 0;color:#14161a"><b>Nome</b> <span style="color:#c2410c">*</span></td>
        <td style="border:0"><div style="border:1px solid #8a8f98;border-radius:3px;padding:7px 11px;background:#fff;font-family:monospace">cv-deva3-fiap01</div></td></tr>
    <tr><td style="border:0;padding:7px 0;color:#14161a"><b>Faixa de preços</b> <span style="color:#c2410c">*</span></td>
        <td style="border:0"><div style="border:1px solid #8a8f98;border-radius:3px;padding:7px 11px;background:#fff">Free F0 (20 Calls per minute, 5K Calls per month)</div></td></tr>
  </table>
  <div style="font-size:18px;font-weight:700;margin:22px 0 10px;color:#14161a">Aviso de IA Responsável</div>
  <div style="font-size:14px;line-height:1.6;color:#3a3f4a">
    A Microsoft fornece documentação técnica sobre a operação apropriada aplicável a este
    serviço de IA do Azure. Este Serviço de IA do Azure foi projetado para processar
    <b style="color:#b3003c">Dados do Cliente que incluem Dados Biométricos</b> que o Cliente pode
    incorporar aos seus próprios sistemas usados para identificação pessoal ou outras
    finalidades. <b style="color:#b3003c">O cliente reconhece e concorda que é responsável por cumprir
    as obrigações de dados biométricos</b> contidos no DPA de serviços online.
  </div>
  <div style="color:#0a63c9;font-size:14px;margin-top:12px">DPA de serviços online</div>
  <div style="display:flex;align-items:center;gap:12px;margin-top:18px;font-size:14px">
    <span style="width:17px;height:17px;border:1px solid #8a8f98;background:#fff;display:inline-block"></span>
    <span>Ao marcar esta caixa, declaro que li e aceito todos os termos acima. <span style="color:#c2410c">*</span></span>
  </div>
</div>""") + """
<div class="row" style="margin-top:20px">
  <div class="card rosa" style="flex:1.4"><div class="rot">Quem clica é você</div>
    <div class="d">A Microsoft está transferindo a responsabilidade legal para quem aceita.
    Em projeto real, esta tela é conversa com o jurídico e com o encarregado de dados —
    não é um "próximo".</div></div>
  <div class="card ciano" style="flex:1"><div class="rot c">LGPD, art. 5º, II</div>
    <div class="d">Imagem de rosto é <b>dado pessoal sensível</b>. Exige base legal,
    consentimento informado, prazo de retenção e um jeito de apagar.</div></div>
  <div class="card ambar" style="flex:1"><div class="rot a">O que o Deva3 faz</div>
    <div class="d">Consentimento explícito na tela · sem ele, grava só o JSON ·
    contêiner privado · retenção = o tempo da aula.</div></div>
</div>
</div>""", 1280)

# ── 8 · Tela do Streamlit ────────────────────────────────────────────────
P["d3-08-interface"] = ("""
<div class="wrap">
<h1>A interface que torna o abstrato palpável</h1>
<h2>O aluno sobe a própria foto e vê o número aparecer</h2>
""" + janela("Deva3 · Validação Biométrica Básica — ca-deva3-web", """
<div style="padding:20px 24px;background:#15151A">
  <div class="small" style="letter-spacing:1px">▶ FIAP · MBA AI ENGINEERING &amp; MULTI-AGENTS · AULA 05</div>
  <div style="font-size:24px;font-weight:700;margin:6px 0 4px">Deva3 · Validação Biométrica Básica</div>
  <div style="border-top:1px solid #3A3A46;margin:10px 0 18px"></div>
  <div style="display:flex;gap:18px">
    <div style="flex:.85">
      <div class="rot">1 · Envie uma foto</div>
      <div style="border:1px dashed #3A3A46;border-radius:4px;height:150px;display:flex;
                  align-items:center;justify-content:center;color:#7A7872;font-size:14px;margin-bottom:12px">
        Arraste ou selecione uma imagem</div>
      <div style="background:#EB0B4F;color:#fff;text-align:center;padding:9px;
                  border-radius:3px;font-size:14px;font-weight:600">Analisar imagem</div>
      <div class="rot m" style="margin-top:16px">Consentimento</div>
      <div style="display:flex;gap:9px;align-items:flex-start;font-size:12.5px;color:#C3C1BA">
        <span style="width:14px;height:14px;border:1px solid #EB0B4F;background:#EB0B4F;
                     display:inline-block;margin-top:2px"></span>
        <span>Autorizo guardar esta imagem no Blob Storage</span></div>
    </div>
    <div style="flex:1.35">
      <div class="rot c">2 · Resposta do serviço cognitivo</div>
      <div style="display:flex;gap:10px;margin-bottom:12px">
        <div style="flex:1;background:#1C1C22;border:1px solid #2E2E38;padding:9px 11px">
          <div style="font-size:11px;color:#7A7872">DETECÇÕES</div>
          <div style="font-size:24px;font-weight:700">2</div></div>
        <div style="flex:1;background:#1C1C22;border:1px solid #2E2E38;padding:9px 11px">
          <div style="font-size:11px;color:#7A7872">ACIMA DO LIMIAR</div>
          <div style="font-size:24px;font-weight:700;color:#03E3FD">1</div></div>
        <div style="flex:1;background:#1C1C22;border:1px solid #2E2E38;padding:9px 11px">
          <div style="font-size:11px;color:#7A7872">TEMPO</div>
          <div style="font-size:24px;font-weight:700">412 ms</div></div>
      </div>
      <div style="position:relative;height:190px;background:#23232B;border:1px solid #2E2E38;
                  border-radius:3px;overflow:hidden">
        <div style="position:absolute;left:24%;top:12%;width:26%;height:74%;
                    border:3px solid #03E3FD"></div>
        <div style="position:absolute;left:24%;top:2%;background:#03E3FD;color:#15151A;
                    font-size:11px;font-weight:700;padding:2px 7px">#1 · 95%</div>
        <div style="position:absolute;left:62%;top:26%;width:19%;height:52%;
                    border:3px solid #FFD579"></div>
        <div style="position:absolute;left:62%;top:16%;background:#FFD579;color:#15151A;
                    font-size:11px;font-weight:700;padding:2px 7px">#2 · 42%</div>
        <div style="position:absolute;right:9px;bottom:7px;font-size:11px;color:#7A7872">
          ciano = acima do limiar · âmbar = abaixo</div>
      </div>
    </div>
  </div>
</div>""", clara=False) + """
<div class="row" style="margin-top:18px">
  <div class="card ciano" style="flex:1"><div class="rot c">Duas cores, uma lição</div>
    <div class="d">O aluno <b>vê</b> o limiar operando. Mude
    <span class="mono">LIMIAR_CONFIANCA</span> de 0,60 para 0,40 e a caixa âmbar vira ciano.</div></div>
  <div class="card" style="flex:1"><div class="rot m">O JSON fica visível</div>
    <div class="d">A caixa desenhada encanta; o payload é o que ensina. Os dois aparecem
    na mesma tela, o tempo todo.</div></div>
  <div class="card rosa" style="flex:1"><div class="rot">Erro vira conteúdo</div>
    <div class="d">Toda falha mostra o campo <span class="mono">como_resolver</span> em destaque,
    não um stack trace.</div></div>
</div>
</div>""", 1280)

# ── 9 · Confiança x acurácia ─────────────────────────────────────────────
P["d3-09-limiar"] = ("""
<div class="wrap">
<h1>Confiança não é acurácia</h1>
<h2>A ideia central da aula — e a razão de o limiar ser configurável</h2>
<div class="row" style="margin-top:6px">
  <div class="card ciano" style="flex:1">
    <div class="rot c">Limiar 0,40</div>
    <div class="t">Quase tudo passa</div>
    <div class="d">Você automatiza mais e <b>deixa passar</b> detecção ruim.
    O erro caro aqui é o falso positivo: o sistema afirma que viu alguém e não viu.</div>
  </div>
  <div class="card ambar" style="flex:1">
    <div class="rot a">Limiar 0,60 &nbsp;<span style="color:#7A7872">(padrão)</span></div>
    <div class="t">O meio-termo escolhido</div>
    <div class="d">Não é uma verdade técnica. É uma <b>decisão de risco</b> que alguém
    tomou, e que está escrita no <span class="mono">.env</span> e no payload.</div>
  </div>
  <div class="card rosa" style="flex:1">
    <div class="rot">Limiar 0,90</div>
    <div class="t">Vira fila manual</div>
    <div class="d">Quase nada passa. A automação some e o trabalho volta para a pessoa —
    com a diferença de que agora existe um relatório dizendo que "a IA não funcionou".</div>
  </div>
</div>
<div class="card" style="margin-top:20px">
  <div class="rot m">O experimento de 3 minutos que fecha a aula</div>
  <div class="d">Peça à turma quatro fotos, nesta ordem: <b>uma pessoa de frente</b> ·
  <b>um grupo</b> · <b>alguém de costas ou de lado</b> · <b>uma paisagem sem gente</b>.
  Anote a confiança de cada uma. Depois pergunte: com qual limiar essa aplicação poderia
  liberar uma catraca? E quem, na sua empresa, assina essa escolha?</div>
</div>
<div class="card rosa" style="margin-top:16px">
  <div class="t">A frase para o quadro</div>
  <div class="d">O serviço pode <b>acertar com confiança baixa</b> e <b>errar com confiança alta</b>.
  Onde colocar a régua é decisão de quem responde pelo processo — não de quem escreve o código.</div>
</div>
</div>""", 1280)


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
