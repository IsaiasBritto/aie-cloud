"""Figuras conceituais do módulo do agente contínuo, na identidade FIAP.

    python3 figuras/render_figuras.py
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
.mono{font-family:'DejaVu Sans Mono',monospace}
table{width:100%;border-collapse:collapse;font-size:15px;color:#C3C1BA}
th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.6px;
   color:#7A7872;padding:9px 11px;border-bottom:1px solid #3A3A46}
td{padding:11px;border-bottom:1px solid #26262E;vertical-align:top}
td b,td strong{color:#F4F3EF}
.cod{background:#101014;border:1px solid #26262E;border-radius:4px;padding:16px 18px;
     font-family:'DejaVu Sans Mono',monospace;font-size:14px;line-height:1.7;color:#C3C1BA}
.ch{color:#03E3FD}.vl{color:#FFD579}.cm{color:#5F6270}.dq{color:#EB0B4F}
.degrau{display:flex;align-items:stretch;gap:14px;margin-bottom:10px}
.num{width:62px;flex:none;display:flex;align-items:center;justify-content:center;
     font-size:30px;font-weight:700;border-radius:4px}
.pill{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.6px;
      padding:4px 10px;border-radius:12px;border:1px solid #EB0B4F;color:#EB0B4F}
.pill.c{border-color:#03E3FD;color:#03E3FD}
.pill.a{border-color:#FFD579;color:#FFD579}
"""

P = {}

# ── 1 · A escada dos cinco níveis ────────────────────────────────────────────
def degrau(n, cor, fundo, titulo, o_que_muda, o_que_construir):
    return f"""
    <div class="degrau">
      <div class="num" style="background:{fundo};color:{cor};border:1px solid {cor}">{n}</div>
      <div class="card" style="flex:1;background:{fundo};border-color:{cor};display:flex;gap:20px">
        <div style="flex:1.05">
          <div class="t" style="margin-bottom:4px">{titulo}</div>
          <div class="d">{o_que_muda}</div>
        </div>
        <div style="flex:.95;border-left:1px solid #2E2E38;padding-left:20px">
          <div class="rot m">O que é preciso construir</div>
          <div class="small">{o_que_construir}</div>
        </div>
      </div>
    </div>"""

P["dc-01-cinco-niveis"] = ("""
<div class="wrap">
<h1>Os cinco níveis de continuidade</h1>
<h2>Cada degrau depende do anterior. Pular para o 3 dá um agente que acorda e não sabe o que já fez.</h2>
""" + degrau("0", "#7A7872", "#1C1C22", "Pergunta e resposta",
             "Nada persiste. Toda conversa começa do zero.",
             "Nada. É onde quase todo agente de curso para.")
 + degrau("1", "#7A7872", "#1C1C22", "Sessão com contexto",
          "Ele lembra <b>dentro</b> da conversa.",
          "Nada: o <b>thread</b> do Foundry já faz. Amanhã é outro thread.")
 + degrau("2", "#03E3FD", "#12222A", "Memória entre sessões",
          "Ele lembra <b>amanhã</b>.",
          "Serviço de memória + Ferramenta OpenAPI. E a decisão que define o projeto: "
          "ele <b>propõe</b>, não escreve.")
 + degrau("3", "#EB0B4F", "#22161B", "Iniciativa",
          "Ele <b>começa sozinho</b>. É o degrau que muda a percepção da turma.",
          "Gatilho por evento (Event Grid → Logic App) + fila de documentos. "
          "E freio de laço, senão ele gira em falso a noite inteira.")
 + degrau("4", "#FFD579", "#221E14", "Fila de exceções",
          "Ele trabalha e <b>chama gente só quando precisa</b>.",
          "Máquina de estados + tela de revisão. Documento em exceção NÃO volta para ele.")
 + """
<div class="card ciano" style="margin-top:14px">
  <div class="rot c">O número que interessa no nível 4</div>
  <div class="d">Não é "quantos ele processou". É <b>quantos ele devolveu</b>. Um agente
  que manda 40 itens para revisão não economizou nada; um que manda 3 economizou 37.</div>
</div>
</div>""", 1420)

# ── 2 · Instrução × permissão ────────────────────────────────────────────────
P["dc-02-instrucao-permissao"] = ("""
<div class="wrap">
<h1>Instrução não é controle</h1>
<h2>A mesma regra, escrita de duas formas — e só uma delas segura</h2>
<div class="row" style="margin-top:8px;align-items:stretch">
  <div class="card ambar" style="flex:1">
    <div class="rot a">AGENTS.md v1.3 · instrução</div>
    <div class="cod" style="margin:12px 0 16px">
<span class="cm"># §7 Regras de memória</span><br><br>
Escreva em <span class="vl">MEMORY.md</span> <b style="color:#F4F3EF">somente</b><br>
quando o auditor humano<br>
corrigir você.
    </div>
    <div class="d"><b>A pergunta que derruba:</b> quem verifica que essa condição foi
    satisfeita?</div>
    <div class="d" style="margin-top:10px;color:#FFD579"><b>O próprio agente.</b></div>
  </div>
  <div class="card ciano" style="flex:1">
    <div class="rot c">v2.0 · permissão</div>
    <div class="cod" style="margin:12px 0 16px">
<span class="cm"># api/principal.py</span><br><br>
<span class="dq">def</span> <span class="ch">exigir_auditor</span>(x_auditor, x_segredo):<br>
&nbsp;&nbsp;<span class="dq">if</span> <span class="dq">not</span> x_auditor:<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="dq">raise</span> <span class="ch">AutorizacaoDeAuditorAusente</span>(…)
    </div>
    <div class="d">O agente <b>não recebe</b> esse cabeçalho. Não é desconfiança:
    é a única forma de a revisão humana ser real.</div>
    <div class="d" style="margin-top:10px;color:#03E3FD"><b>Ele não consegue. Ponto.</b></div>
  </div>
</div>
<div class="card" style="margin-top:18px;padding:8px 14px 14px">
<table>
<tr><th style="width:26%"></th><th>Instrução</th><th>Permissão</th></tr>
<tr><td><b>Onde vive</b></td><td>AGENTS.md</td><td>o serviço e a especificação OpenAPI</td></tr>
<tr><td><b>Quem garante</b></td><td>o agente</td><td>a arquitetura</td></tr>
<tr><td><b>Se falhar</b></td><td>o agente faz o que não devia</td>
    <td style="color:#03E3FD">nada: ele não consegue</td></tr>
<tr><td><b>Custo de mudar</b></td><td>reescrever um parágrafo</td><td>reimplantar</td></tr>
</table>
</div>
<div class="card rosa" style="margin-top:16px">
  <div class="t">A frase para o quadro</div>
  <div class="d">Instrução é intenção; permissão é controle. Em agentes, <b>o que você não
  quer que aconteça, você não expõe</b>.</div>
</div>
</div>""", 1400)

# ── 3 · Cinco de catorze ─────────────────────────────────────────────────────
P["dc-03-cinco-de-catorze"] = ("""
<div class="wrap">
<h1>A API tem 14 operações. O agente recebe 5.</h1>
<h2>As outras nove não estão escondidas nem bloqueadas por mensagem — não estão no arquivo</h2>
<div class="row" style="margin-top:8px;align-items:flex-start">
  <div class="card ciano" style="flex:1">
    <div class="rot c">O que o Deva pode fazer</div>
    <div class="cod" style="margin-top:12px">
<span class="ch">GET</span>&nbsp;&nbsp; /memoria<br>
<span class="ch">GET</span>&nbsp;&nbsp; /fila<br>
<span class="ch">GET</span>&nbsp;&nbsp; /fila/documentos/{id}<br>
<span class="dq">POST</span>&nbsp; /fila/documentos/{id}/estado<br>
<span class="dq">POST</span>&nbsp; /memoria/proposta
    </div>
    <div class="small" style="margin-top:14px">Ler o que já sabe · descobrir o que fazer ·
    avançar um documento · propor uma regra.</div>
  </div>
  <div class="card rosa" style="flex:1">
    <div class="rot">O que só a pessoa faz</div>
    <div class="cod" style="margin-top:12px">
<span class="cm">POST /memoria/propostas/{id}/aprovar</span><br>
<span class="cm">POST /memoria/propostas/{id}/descartar</span><br>
<span class="cm">POST /fila/documentos/{id}/liberar</span><br><br>
<span class="cm">exigem o cabeçalho X-Auditor</span>
    </div>
    <div class="small" style="margin-top:14px">Existem, funcionam e são usadas — pela
    <b style="color:#F4F3EF">tela</b>, nunca pelo agente.</div>
  </div>
</div>
<div class="card ambar" style="margin-top:18px">
  <div class="rot a">E a garantia é testada, não prometida</div>
  <div class="cod" style="margin-top:10px;font-size:13px">
<span class="cm"># gerar_openapi_do_agente.py</span><br>
<span class="dq">for</span> proibida <span class="dq">in</span> PROIBIDAS:<br>
&nbsp;&nbsp;<span class="dq">assert</span> proibida <span class="dq">not in</span> texto,
<span class="vl">f"rota proibida vazou para a especificação: {proibida}"</span>
  </div>
  <div class="small" style="margin-top:12px">Se alguém, um dia, adicionar a rota de
  aprovação à lista de permitidas, a geração <b style="color:#F4F3EF">falha</b> — e o teste
  <span class="mono">teste_especificacao_do_agente_nao_expoe_aprovacao</span> quebra junto.</div>
</div>
</div>""", 1360)

# ── 4 · A pergunta de abertura ───────────────────────────────────────────────
P["dc-04-abertura"] = ("""
<div class="wrap">
<h1>A demonstração de 30 segundos</h1>
<h2>Não comece explicando. Comece mostrando o problema.</h2>
<div class="row" style="margin-top:8px">
  <div class="card" style="flex:1">
    <div class="rot m">1</div>
    <div class="t">Corrija o Deva</div>
    <div class="d">"Estacionamento em aeroporto é viagem aérea, não estacionamento
    e pedágio."</div>
  </div>
  <div class="card" style="flex:1">
    <div class="rot m">2</div>
    <div class="t">Ele concorda</div>
    <div class="d">Educadamente. Parece que entendeu — e entendeu mesmo, dentro
    daquela conversa.</div>
  </div>
  <div class="card ambar" style="flex:1">
    <div class="rot a">3</div>
    <div class="t">Abra uma conversa nova</div>
    <div class="d">Faça exatamente a mesma pergunta.</div>
  </div>
  <div class="card rosa" style="flex:1">
    <div class="rot">4</div>
    <div class="t">Ele erra igual</div>
    <div class="d">Nada do que aconteceu na conversa anterior sobreviveu.</div>
  </div>
</div>
<div class="card ciano" style="margin-top:20px;text-align:center;padding:30px">
  <div class="t" style="font-size:30px;margin-bottom:10px">
    "Vocês acabaram de ensinar uma coisa a ele.<br>Onde foi parar?"</div>
  <div class="small">Deixe o silêncio durar. É a pergunta que sustenta os 45 minutos.</div>
</div>
</div>""", 1400)


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
