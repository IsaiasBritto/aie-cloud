const pptxgen = require("pptxgenjs");
const path = require("path");
const IMG = "/root/deva3/figuras/png";

/* ── Identidade visual FIAP · MBA AI Engineering e Multi-Agents ───────── */
const C = {
  bg: "15151A", panel: "1C1C22", panel2: "22161B", panelY: "221E14", panelC: "12222A",
  line: "2E2E38", rule: "3A3A46",
  text: "F4F3EF", text2: "C3C1BA", mute: "7A7872",
  pink: "EB0B4F", cyan: "03E3FD", amber: "FFD579", teal: "01678B",
  code: "101014",
};
const F = { h: "Calibri", b: "Calibri", m: "Consolas" };

const pres = new pptxgen();
pres.defineLayout({ name: "FIAP16x9", width: 20, height: 11.25 });
pres.layout = "FIAP16x9";
pres.author = "Isaias S. Britto";
pres.company = "FIAP · MBA AI Engineering e Multi-Agents";
pres.title = "Deva3 — API de Validação Biométrica Básica";

const W = 20, H = 11.25, M = 1.15, CW = W - 2 * M;
let n = 0;

function novo() { const s = pres.addSlide(); s.background = { color: C.bg }; return s; }

function marca(s) {
  s.addText([
    { text: "FIAP ", options: { color: C.pink, bold: true } },
    { text: "MBA", options: { color: C.mute, bold: true } },
    { text: "+", options: { color: C.pink, bold: true, superscript: true } },
  ], { x: W - 2.6, y: 0.28, w: 2.1, h: 0.32, isTextBox: true, margin: 0, align: "right",
       fontFace: F.b, fontSize: 12, charSpacing: 1 });
}

function rodape(s) {
  n++;
  s.addText("Deva3 · API de Validação Biométrica Básica · Aula 05 · Uso exclusivo para fins acadêmicos", {
    x: M, y: H - 0.62, w: 14, h: 0.3, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 10, color: "4A4A54" });
  s.addText(String(n), {
    x: W - M - 1.2, y: H - 0.62, w: 1.2, h: 0.3, isTextBox: true, margin: 0, align: "right",
    fontFace: F.b, fontSize: 10, color: "4A4A54" });
}

function sobrancelha(s, esq, dir) {
  s.addText("▶ " + esq.toUpperCase(), {
    x: M, y: 0.62, w: 11, h: 0.34, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 13, color: C.mute, charSpacing: 1.2 });
  if (dir) s.addText(dir, {
    x: W - M - 7, y: 0.62, w: 7, h: 0.34, isTextBox: true, margin: 0, align: "right",
    fontFace: F.b, fontSize: 13, color: C.mute });
  s.addShape(pres.ShapeType.rect, { x: M, y: 1.08, w: CW, h: 0.012, fill: { color: C.rule } });
}

function conteudo(kicker, dir, titulo, sub) {
  const s = novo(); marca(s); sobrancelha(s, kicker, dir);
  s.addText(titulo, { x: M, y: 1.5, w: CW, h: 0.95, isTextBox: true, margin: 0,
    fontFace: F.h, fontSize: 46, bold: true, color: C.text });
  if (sub) s.addText(sub, { x: M, y: 2.5, w: CW, h: 0.5, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 19, color: C.mute });
  return s;
}

function cartao(s, o) {
  s.addShape(pres.ShapeType.rect, { x: o.x, y: o.y, w: o.w, h: o.h,
    fill: { color: o.fundo || C.panel },
    line: { color: o.cor || C.line, width: o.cor ? 1.25 : 1 } });
  let ty = o.y + 0.34;
  if (o.rotulo) {
    s.addText(o.rotulo.toUpperCase(), { x: o.x + 0.4, y: ty, w: o.w - 0.8, h: 0.3,
      isTextBox: true, margin: 0, fontFace: F.b, fontSize: 13, bold: true,
      color: o.cor || C.pink, charSpacing: 1.1 });
    ty += 0.44;
  }
  if (o.titulo) {
    s.addText(o.titulo, { x: o.x + 0.4, y: ty, w: o.w - 0.8, h: o.tituloH || 0.6,
      isTextBox: true, margin: 0, fontFace: F.h, fontSize: o.tituloTam || 22,
      bold: true, color: C.text });
    ty += (o.tituloH || 0.6) + 0.12;
  }
  if (o.corpo) s.addText(o.corpo, { x: o.x + 0.4, y: ty, w: o.w - 0.8,
    h: o.y + o.h - ty - 0.34 - (o.pilula ? 0.78 : 0), isTextBox: true, margin: 0,
    fontFace: o.mono ? F.m : F.b, fontSize: o.corpoTam || 16,
    color: C.text2, lineSpacingMultiple: 1.22 });
  if (o.pilula) {
    s.addShape(pres.ShapeType.roundRect, { x: o.x + 0.4, y: o.y + o.h - 0.92,
      w: o.w - 0.8, h: 0.52, rectRadius: 0.26,
      fill: { color: o.fundo || C.panel }, line: { color: o.cor || C.pink, width: 1 } });
    s.addText(o.pilula, { x: o.x + 0.4, y: o.y + o.h - 0.92, w: o.w - 0.8, h: 0.52,
      isTextBox: true, margin: 0, align: "center", valign: "middle",
      fontFace: F.b, fontSize: 14, color: o.cor || C.pink });
  }
}

function figura(arquivo, ar, kicker, dir, legenda) {
  const s = novo(); marca(s); sobrancelha(s, kicker, dir);
  const maxL = CW, maxA = H - 1.45 - 0.95;
  let l = maxL, a = l / ar;
  if (a > maxA) { a = maxA; l = a * ar; }
  s.addImage({ path: path.join(IMG, arquivo), x: (W - l) / 2, y: 1.45, w: l, h: a });
  if (legenda) s.addText(legenda, { x: M, y: 1.45 + a + 0.1, w: CW, h: 0.34,
    isTextBox: true, margin: 0, fontFace: F.b, fontSize: 12, italic: true, color: C.mute });
  rodape(s);
  return s;
}

function bloco(num, kicker, titulo, sub) {
  const s = novo(); marca(s);
  s.addText("▶ " + kicker.toUpperCase(), { x: M, y: 0.62, w: 12, h: 0.34,
    isTextBox: true, margin: 0, fontFace: F.b, fontSize: 13, color: C.mute, charSpacing: 1.2 });
  s.addText(num, { x: M, y: 3.0, w: 4.2, h: 2.3, isTextBox: true, margin: 0,
    fontFace: F.h, fontSize: 130, bold: true, color: C.pink });
  s.addShape(pres.ShapeType.rect, { x: M, y: 6.05, w: 1.5, h: 0.06, fill: { color: C.pink } });
  s.addText(titulo, { x: M, y: 6.35, w: 14, h: 1.1, isTextBox: true, margin: 0,
    fontFace: F.h, fontSize: 54, bold: true, color: C.text });
  s.addText(sub, { x: M, y: 7.55, w: 13, h: 1.2, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 20, color: C.text2, lineSpacingMultiple: 1.2 });
  rodape(s);
  return s;
}


const DIAG = "/root/deva3/docs/imagens";

/* diagrama Mermaid: imagem + cartões de leitura */
function diagrama(o) {
  const s = novo(); marca(s); sobrancelha(s, o.kicker, o.dir);
  s.addText(o.titulo, { x: M, y: 1.5, w: CW, h: 0.9, isTextBox: true, margin: 0,
    fontFace: F.h, fontSize: 42, bold: true, color: C.text });
  s.addText(o.sub, { x: M, y: 2.42, w: CW, h: 0.45, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 18, color: C.mute });

  if (o.banner) {
    // imagem larga em cima, cartões embaixo
    let l = CW, a = l / o.ar;
    const maxA = 4.7;
    if (a > maxA) { a = maxA; l = a * o.ar; }
    s.addShape(pres.ShapeType.rect, { x: (W - l) / 2 - 0.12, y: 3.05 - 0.12,
      w: l + 0.24, h: a + 0.24, fill: { color: C.bg }, line: { color: C.line, width: 1 } });
    s.addImage({ path: path.join(DIAG, o.arquivo), x: (W - l) / 2, y: 3.05, w: l, h: a });
    const larg = (CW - 0.7) / o.cartoes.length;
    o.cartoes.forEach((c, i) => cartao(s, {
      x: M + i * (larg + 0.35), y: 3.05 + a + 0.5, w: larg, h: 10.15 - (3.05 + a + 0.5),
      cor: c[0], rotulo: c[1], corpo: c[2], corpoTam: 15 }));
  } else {
    // imagem à esquerda, cartões à direita
    const largImg = o.largImg || 10.6;
    const maxA = 6.9;
    let l = largImg, a = l / o.ar;
    if (a > maxA) { a = maxA; l = a * o.ar; }
    const x0 = M + (largImg - l) / 2;
    s.addShape(pres.ShapeType.rect, { x: x0 - 0.12, y: 3.05 - 0.12, w: l + 0.24, h: a + 0.24,
      fill: { color: C.bg }, line: { color: C.line, width: 1 } });
    s.addImage({ path: path.join(DIAG, o.arquivo), x: x0, y: 3.05, w: l, h: a });
    const xc = M + largImg + 0.5;
    const wc = W - M - xc;
    const alt = (10.15 - 3.05 - 0.35 * (o.cartoes.length - 1)) / o.cartoes.length;
    o.cartoes.forEach((c, i) => cartao(s, {
      x: xc, y: 3.05 + i * (alt + 0.35), w: wc, h: alt,
      cor: c[0], rotulo: c[1], corpo: c[2], corpoTam: 15 }));
  }
  if (o.fonte) s.addText(o.fonte, { x: M, y: 10.25, w: CW, h: 0.35, isTextBox: true,
    margin: 0, fontFace: F.b, fontSize: 12, italic: true, color: C.mute });
  rodape(s);
  return s;
}

/* ═══════════════ CAPA ═══════════════ */
{
  const s = novo();
  s.addShape(pres.ShapeType.ellipse, { x: -1.9, y: -2.6, w: 9.2, h: 8.0, fill: { color: C.teal } });
  s.addShape(pres.ShapeType.ellipse, { x: 12.6, y: 5.0, w: 9.6, h: 8.4, fill: { color: C.pink } });
  marca(s);
  s.addText("FIAP · MBA AI ENGINEERING & MULTI-AGENTS", { x: 7.7, y: 1.15, w: 11.5, h: 0.5,
    isTextBox: true, margin: 0, fontFace: F.b, fontSize: 22, color: C.mute, charSpacing: 0.5 });
  s.addText("CLOUD & COGNITIVE ENVIRONMENTS", { x: 7.7, y: 1.95, w: 11.5, h: 0.5,
    isTextBox: true, margin: 0, fontFace: F.b, fontSize: 22, color: C.mute, charSpacing: 0.5 });
  s.addShape(pres.ShapeType.rect, { x: M, y: 5.9, w: 1.35, h: 0.07, fill: { color: C.pink } });
  s.addText("Deva3 · Validação Biométrica", { x: M, y: 6.25, w: 16, h: 1.15, isTextBox: true,
    margin: 0, fontFace: F.h, fontSize: 58, bold: true, color: C.text });
  s.addText("Uma API, um serviço cognitivo e a pergunta que fica", { x: M, y: 7.45, w: 15,
    h: 0.65, isTextBox: true, margin: 0, fontFace: F.h, fontSize: 30, color: C.text2 });
  s.addText("Aula 05 — Do container ao rosto: FastAPI, Streamlit, Azure AI Vision e Blob Storage,\npublicados em Azure Container Apps a partir do grupo rg-aula-05", {
    x: M, y: 8.25, w: 13, h: 1.0, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 18, color: C.text2, lineSpacingMultiple: 1.2 });
  s.addText("PROF. ISAIAS S. BRITTO   ·   30 DE AGOSTO DE 2026", { x: M, y: 9.75, w: 13, h: 0.4,
    isTextBox: true, margin: 0, fontFace: F.b, fontSize: 13, color: C.mute, charSpacing: 1 });
  n++;
  s.addNotes("Deva3 é a terceira geração do agente do curso. Deva1/2 eram sobre despesas; o Deva3 é sobre um caso extremamente visual: o aluno sobe a própria foto e vê a caixa e o número na hora.");
}

/* ═══════════════ ABERTURA ═══════════════ */
{
  const s = conteudo("Abertura", "O que o Deva3 faz", "O que vamos construir hoje",
    "Um backend simples e isolado — e uma tela onde a IA deixa de ser abstrata");
  const itens = [
    ["Receber", "Um endpoint que aceita o upload de uma imagem: JPEG, PNG, BMP ou WEBP, até 4 MB", C.pink],
    ["Perguntar", "Uma requisição direta ao Azure AI Vision, sem SDK escondendo o contrato", C.amber],
    ["Devolver", "JSON com as coordenadas da caixa e a pontuação de confiança de cada detecção", C.cyan],
    ["Mostrar", "Interface em Streamlit que desenha a caixa sobre a foto do próprio aluno", C.pink],
    ["Guardar", "Imagem e resultado no Blob Storage — só com consentimento explícito", C.amber],
    ["Publicar", "Duas imagens no ACR e dois Container Apps, tudo dentro de rg-aula-05", C.cyan],
  ];
  itens.forEach((it, i) => {
    const col = i % 3, lin = Math.floor(i / 3);
    const l = (CW - 0.7) / 3;
    cartao(s, { x: M + col * (l + 0.35), y: 3.35 + lin * 3.5, w: l, h: 3.05, cor: it[2],
      rotulo: (i + 1) + " · " + it[0], corpo: it[1], corpoTam: 16 });
  });
  rodape(s);
  s.addNotes("Pergunta de abertura: quem aqui já usou desbloqueio facial hoje? E quem sabe dizer qual número o celular usou para decidir que era você? É esse número que a aula persegue.");
}

/* ═══════════════ BLOCO 1 · O CASO ═══════════════ */
bloco("01", "Bloco 1 · O caso", "O que o Deva3 é",
  "Um backend isolado que recebe uma foto e devolve coordenadas com confiança. Nada além disso — e isso é uma decisão.");
diagrama({
  arquivo: "01-contexto.png", ar: 0.948, largImg: 9.2,
  kicker: "Bloco 1 · O caso", dir: "Diagrama de contexto",
  titulo: "Com quem o Deva3 conversa",
  sub: "Diagrama de contexto · nível 1 do modelo C4 · docs/00-diagramas.md",
  cartoes: [
    [C.pink, "Pessoas", "O aluno envia a foto e lê o JSON. O professor provisiona, publica, define o limiar e apaga o ambiente no fim da aula."],
    [C.cyan, "O limite do sistema", "Tudo dentro da moldura é responsabilidade nossa. É pequeno de propósito: receber, perguntar, devolver. Nada de treinar modelo ou guardar template biométrico."],
    [C.amber, "Três dependências externas", "Vision (sem gating) · Face (Acesso Limitado, tracejado porque é opcional) · Blob. Cada uma falha de um jeito e tem o seu próprio como_resolver."],
    [null, "A regra está no desenho", "A seta para o Blob diz \"SOMENTE com consentimento\". Se a regra é importante, ela aparece no diagrama — não numa nota de rodapé."],
  ],
  fonte: "Fonte editável: docs/diagramas/01-contexto.mmd · regere com mmdc",
});

figura("d3-01-arquitetura.png", 2.162, "Bloco 1 · O caso", "Arquitetura");
figura("d3-03-dois-modos.png", 2.119, "Bloco 1 · O caso", "pessoas × rostos",
  "Contratos conferidos na documentação da Azure em 30/08/2026.");

/* ═══════════════ BLOCO 2 · O CÓDIGO ═══════════════ */
bloco("02", "Bloco 2 · O código", "O projeto",
  "Python, tudo nomeado em português, com o agente lendo a própria memória antes de começar.");
figura("d3-04-repositorio.png", 1.818, "Bloco 2 · O código", "Estrutura do repositório");

{
  const s = conteudo("Bloco 2 · O código", "Os dois arquivos do agente",
    "AGENTS.md e MEMORY.md", "A alma e o aprendizado — escritos em português, para serem lidos por gente");
  cartao(s, { x: M, y: 3.35, w: CW / 2 - 0.35, h: 6.3, fundo: C.panel2, cor: C.pink,
    rotulo: "A alma", titulo: "AGENTS.md · 12 seções", tituloTam: 24,
    corpo: "0 · Ler o MEMORY.md antes de qualquer ação\n1 · Identidade e escopo\n2 · O que faz — e o que não faz\n3 · Definição de pronto\n4 · Fontes de verdade, com precedência\n5 · Convenção de nomes (regra dura)\n6 · O que nunca faz sem humano\n7 · Regras de memória\n8 · Ferramentas autorizadas\n9 · Orçamento e parada\n10 · Formato das respostas\n11 · Mapa do repositório",
    corpoTam: 16, pilula: "revisada antes da aula" });
  cartao(s, { x: M + CW / 2 + 0.35, y: 3.35, w: CW / 2 - 0.35, h: 6.3, cor: C.cyan,
    rotulo: "O aprendizado", titulo: "MEMORY.md · o que já custou tempo", tituloTam: 24,
    corpo: "Formato:  [origem · AAAA-MM-DD] regra\n\n• Por que o modo padrão é 'pessoas'\n• O contrato exato das duas APIs, com a data\n• Que o Face NÃO devolve confiança\n• Endpoint com barra no fim → HTTP 404\n• Docker construído da pasta errada → ModuleNotFoundError\n• F0 = 20 chamadas/minuto → 429 com a turma toda\n• Dentro do compose, a interface fala com http://api:8000",
    corpoTam: 16, pilula: "só o professor escreve aqui" });
  rodape(s);
  s.addNotes("A seção 0 do AGENTS.md é a linha mais importante do projeto: 'leia o MEMORY.md antes de qualquer outra ação'. Sem ela escrita, o arquivo de memória é decoração.");
}

figura("d3-02-payload.png", 1.704, "Bloco 2 · O código", "O contrato de resposta");

{
  const s = conteudo("Bloco 2 · O código", "Um endpoint só", "POST /detectar",
    "Uma responsabilidade: receber a imagem, perguntar à Azure, devolver as coordenadas");
  cartao(s, { x: M, y: 3.3, w: CW / 2 - 0.35, h: 3.1, cor: C.cyan, rotulo: "Chamada",
    corpo: "curl -X POST \\\n  \"$URL/detectar?modo=pessoas&consentimento=true\" \\\n  -F \"imagem=@foto.jpg\"",
    mono: true, corpoTam: 15 });
  cartao(s, { x: M + CW / 2 + 0.35, y: 3.3, w: CW / 2 - 0.35, h: 3.1, cor: C.amber,
    rotulo: "Erro — sempre no mesmo formato",
    corpo: "{\n  \"erro\": \"servico_nao_configurado\",\n  \"mensagem\": \"...\",\n  \"como_resolver\": \"Use ?modo=pessoas\"\n}",
    mono: true, corpoTam: 15 });
  const tres = [
    ["GET /", "Diz o que a API é e onde está a documentação", C.mute],
    ["GET /saude", "Situação, modos disponíveis, limiar e se o blob está configurado. O primeiro lugar onde se olha quando trava", C.cyan],
    ["POST /detectar", "Valida a imagem · escolhe o serviço · chama · monta o resultado · decide sobre persistência · devolve", C.pink],
  ];
  tres.forEach((t, i) => {
    const l = (CW - 0.7) / 3;
    cartao(s, { x: M + i * (l + 0.35), y: 6.75, w: l, h: 2.9, cor: t[2] === C.mute ? null : t[2],
      rotulo: "Rota", titulo: t[0], tituloTam: 20, corpo: t[1], corpoTam: 15 });
  });
  s.addText("Todo erro carrega o campo como_resolver. Mensagem de erro sem instrução é aula perdida — e professor atendendo 40 vezes a mesma dúvida.", {
    x: M, y: 9.85, w: CW, h: 0.45, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 16, italic: true, color: C.pink });
  rodape(s);
}

/* ── sequência: o diagrama ocupa o slide inteiro; a leitura vem no slide seguinte ── */
{
  const s = novo(); marca(s); sobrancelha(s, "Bloco 2 · O código", "Diagrama de sequência");
  s.addText("O que acontece quando o aluno clica em Analisar", {
    x: M, y: 1.32, w: CW - 4.2, h: 0.6, isTextBox: true, margin: 0,
    fontFace: F.h, fontSize: 32, bold: true, color: C.text });
  s.addText("POST /detectar · 23 passos, do clique à caixa desenhada", {
    x: W - M - 8.4, y: 1.42, w: 8.4, h: 0.42, isTextBox: true, margin: 0, align: "right",
    fontFace: F.b, fontSize: 16, color: C.mute });
  const ar = 1.422, maxA = 8.05;
  let a = maxA, l = a * ar;
  if (l > CW) { l = CW; a = l / ar; }
  s.addShape(pres.ShapeType.rect, { x: (W - l) / 2 - 0.12, y: 2.02 - 0.12,
    w: l + 0.24, h: a + 0.24, fill: { color: C.bg }, line: { color: C.line, width: 1 } });
  s.addImage({ path: path.join(DIAG, "03-sequencia.png"), x: (W - l) / 2, y: 2.02, w: l, h: a });
  s.addText("Fonte editável: docs/diagramas/03-sequencia.mmd · o PNG em alta resolução está em docs/imagens/ — projete a partir do arquivo para dar zoom em sala", {
    x: M, y: 10.25, w: CW, h: 0.35, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 12, italic: true, color: C.mute });
  rodape(s);
  s.addNotes("Não tente ler o diagrama inteiro projetado. Percorra os quatro momentos do slide seguinte e volte aqui apontando os números.");
}

{
  const s = conteudo("Bloco 2 · O código", "Como ler o diagrama de sequência",
    "Os quatro momentos do POST /detectar",
    "Percorra por número — o diagrama do slide anterior está numerado de 1 a 23");
  const momentos = [
    ["3 a 7", "Validar antes de pagar", C.cyan,
     "Tamanho, tipo e integridade são checados antes de qualquer chamada à Azure. Arquivo ruim nunca vira custo — e o erro já sai com o campo como_resolver preenchido."],
    ["9 a 12", "O caminho de erro também é desenhado", C.pink,
     "401, 404, 429 e 5xx viram FalhaDeIntegracao e chegam ao aluno como HTTP 502 com instrução. Diagrama que só mostra o caminho feliz esconde metade do sistema."],
    ["14 e 16", "Tradução e limiar", C.amber,
     "_interpretar converte boundingBox para CaixaDelimitadora num lugar só. O limiar é aplicado na API, não na tela: a interface apenas pinta ciano acima e âmbar abaixo."],
    ["17 a 20", "O consentimento decide", C.cyan,
     "A imagem só sobe para o Blob se PERSISTIR_IMAGENS=true E o consentimento estiver marcado. Sem consentimento, vai só o JSON. A regra está desenhada, não escondida no código."],
  ];
  momentos.forEach((m, i) => {
    const y = 3.4 + i * 1.72;
    s.addText(m[0], { x: M, y, w: 2.0, h: 0.55, isTextBox: true, margin: 0,
      fontFace: F.h, fontSize: 27, bold: true, color: m[2] });
    s.addText(m[1], { x: M + 2.2, y: y + 0.03, w: 6.4, h: 0.5, isTextBox: true, margin: 0,
      fontFace: F.h, fontSize: 22, bold: true, color: C.text });
    s.addText(m[3], { x: M + 8.9, y: y + 0.02, w: CW - 8.9, h: 1.3, isTextBox: true,
      margin: 0, fontFace: F.b, fontSize: 16, color: C.text2, lineSpacingMultiple: 1.18 });
    s.addShape(pres.ShapeType.rect, { x: M, y: y + 1.42, w: CW, h: 0.008,
      fill: { color: "23232B" } });
  });
  s.addText("Quando algo quebrar em sala, pergunte primeiro: em qual número do diagrama isso acontece? É mais rápido que abrir log.", {
    x: M, y: 10.3, w: CW, h: 0.45, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 16, italic: true, color: C.pink });
  rodape(s);
}

figura("d3-08-interface.png", 1.643, "Bloco 2 · O código", "A interface em Streamlit");

/* ═══════════════ BLOCO 3 · A NUVEM ═══════════════ */
bloco("03", "Bloco 3 · A nuvem", "Provisionar e publicar",
  "Sete recursos, um grupo, duas trilhas — e um comando que apaga tudo no fim.");
diagrama({
  arquivo: "02-arquitetura.png", ar: 4.43, banner: true,
  kicker: "Bloco 3 · A nuvem", dir: "Diagrama de arquitetura",
  titulo: "Onde cada pedaço roda",
  sub: "Diagrama de arquitetura e implantação · as setas numeradas são a ordem do laboratório",
  cartoes: [
    [C.pink, "1 e 2 · do código ao ar", "az acr build constrói NA NUVEM — o aluno não precisa de Docker. Depois, az containerapp create/update leva a imagem para o ambiente."],
    [C.cyan, "3 a 6 · o caminho da requisição", "Navegador → ca-deva3-web → ca-deva3-api → Vision, e o blob só quando há consentimento. Cada seta é um ponto onde a aula pode quebrar."],
    [C.amber, "A moldura magenta é o rg-aula-05", "Tudo dentro dela some com um az group delete. A chave nunca aparece numa seta: ela vive como segredo dentro do ca-deva3-api."],
  ],
  fonte: "Fonte editável: docs/diagramas/02-arquitetura.mmd · regere com mmdc",
});

figura("d3-05-recursos.png", 1.936, "Bloco 3 · A nuvem", "rg-aula-05");
figura("d3-06-duas-trilhas.png", 1.678, "Bloco 3 · A nuvem", "Portal × Script");

{
  const s = conteudo("Bloco 3 · A nuvem", "Do código ao ar", "Como a aplicação sobe",
    "Três comandos entre o seu editor e a URL pública");
  const passos = [
    ["Construir", "az acr build --registry $ACR --image deva3-api:v1 --file api/Dockerfile .", "Constrói dentro da Azure. O aluno não precisa de Docker na máquina.", C.cyan],
    ["Publicar", "az containerapp create --target-port 8000 --ingress external --min-replicas 0", "Escala a zero: fora da aula, os containers dormem e não cobram.", C.pink],
    ["Proteger", "--secrets visao-chave=... --env-vars VISAO_CHAVE=secretref:visao-chave", "Chave e cadeia de conexão entram como segredo, nunca em texto puro.", C.amber],
  ];
  passos.forEach((p, i) => {
    const y = 3.35 + i * 2.2;
    s.addText("0" + (i + 1), { x: M, y, w: 1.1, h: 0.6, isTextBox: true, margin: 0,
      fontFace: F.h, fontSize: 30, bold: true, color: p[3] });
    s.addText(p[0], { x: M + 1.3, y, w: 3.2, h: 0.5, isTextBox: true, margin: 0,
      fontFace: F.h, fontSize: 23, bold: true, color: C.text });
    s.addShape(pres.ShapeType.rect, { x: M + 4.7, y: y - 0.02, w: CW - 4.7, h: 0.82,
      fill: { color: C.code }, line: { color: C.line, width: 1 } });
    s.addText(p[1], { x: M + 4.95, y: y + 0.12, w: CW - 5.2, h: 0.6, isTextBox: true,
      margin: 0, fontFace: F.m, fontSize: 14, color: C.cyan });
    s.addText(p[2], { x: M + 4.7, y: y + 0.92, w: CW - 4.7, h: 0.5, isTextBox: true,
      margin: 0, fontFace: F.b, fontSize: 15, color: C.text2 });
  });
  cartao(s, { x: M, y: 9.95, w: CW, h: 0.001 });
  s.addText("A etiqueta é v1, v2, v3 — nunca latest. Com versão numerada você sabe o que está no ar e consegue voltar atrás com az containerapp revision activate.", {
    x: M, y: 10.0, w: CW, h: 0.45, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 16, italic: true, color: C.pink });
  rodape(s);
}

/* ═══════════════ BLOCO 4 · A CONVERSA ═══════════════ */
bloco("04", "Bloco 4 · A conversa", "Responsabilidade",
  "A parte da aula em que a tela para de ser bonita e passa a ser um problema jurídico.");
figura("d3-07-ia-responsavel.png", 1.565, "Bloco 4 · A conversa", "Dados biométricos",
  "Texto reproduzido da tela de criação do recurso, conferida no portal em 30/08/2026.");
figura("d3-09-limiar.png", 2.055, "Bloco 4 · A conversa", "Confiança × acurácia");

/* ═══════════════ ROTEIRO DA AULA ═══════════════ */
{
  const s = conteudo("Condução", "100 minutos", "Roteiro da aula",
    "O laboratório inteiro cabe em uma aula — se o Módulo 0 vier primeiro");
  const linhas = [
    ["10 min", "Abertura + o caso", "Pergunta de entrada, arquitetura, os dois modos", C.pink],
    ["10 min", "Módulo 0 · Orçamento", "Todos criam orçamento com alerta. Ninguém avança sem isso", C.amber],
    ["20 min", "Provisionar", "Portal (trilha 1) ou script (trilha 2). Grupo rg-aula-05", C.cyan],
    ["15 min", "Publicar", "az acr build + dois Container Apps. As duas URLs no quadro", C.cyan],
    ["20 min", "Testar com foto própria", "Uma pessoa · um grupo · alguém de costas · uma paisagem", C.pink],
    ["15 min", "A conversa", "IA Responsável, LGPD e onde colocar o limiar", C.amber],
    ["10 min", "Módulo 8 · Apagar tudo", "az group delete e conferência do custo no dia seguinte", C.pink],
  ];
  linhas.forEach((l, i) => {
    const y = 3.3 + i * 0.95;
    s.addText(l[0], { x: M, y, w: 1.6, h: 0.45, isTextBox: true, margin: 0,
      fontFace: F.h, fontSize: 19, bold: true, color: l[3] });
    s.addText(l[1], { x: M + 1.9, y, w: 5.0, h: 0.45, isTextBox: true, margin: 0,
      fontFace: F.h, fontSize: 19, bold: true, color: C.text });
    s.addText(l[2], { x: M + 7.2, y: y + 0.02, w: CW - 7.2, h: 0.5, isTextBox: true,
      margin: 0, fontFace: F.b, fontSize: 16, color: C.text2 });
    s.addShape(pres.ShapeType.rect, { x: M, y: y + 0.78, w: CW, h: 0.008,
      fill: { color: "23232B" } });
  });
  s.addText("Se o tempo apertar, corte nesta ordem: trilha do portal (fica como leitura), depois o modo rostos. Nunca corte o Módulo 0.", {
    x: M, y: 10.05, w: CW, h: 0.45, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 16, italic: true, color: C.pink });
  rodape(s);
}

/* ═══════════════ ERROS COMUNS ═══════════════ */
{
  const s = conteudo("Condução", "Avise antes de acontecer", "Os erros que vão acontecer",
    "Anunciar o erro antes evita 40 pessoas depurando a mesma coisa");
  const erros = [
    ["\"O nome já está em uso\"", "Storage e ACR têm nome global", "Troque o sufixo"],
    ["Não consigo criar o F0", "Já existe um F0 na assinatura/região", "Use S1 ou outra região"],
    ["HTTP 404 na chamada", "Endpoint com barra no final", "Remova a barra do VISAO_ENDPOINT"],
    ["HTTP 401", "Chave copiada de outro recurso", "Recopie em Chaves e Ponto de Extremidade"],
    ["HTTP 429", "Cota do F0: 20 chamadas por minuto", "Espere 1 min · combine rodadas"],
    ["HTTP 403 no modo rostos", "Acesso Limitado do Face", "Use ?modo=pessoas"],
    ["Container sobe e cai", "Porta de destino errada", "API 8000 · interface 8501"],
    ["ModuleNotFoundError: api", "Imagem construída da pasta errada", "Construa a partir da raiz"],
    ["Zero detecção", "Não é erro", "Peça outra foto antes de mexer no código"],
  ];
  const th = ["Sintoma", "Causa provável", "Correção"];
  const cols = [0, 6.6, 12.2], larg = [6.3, 5.4, CW - 12.2];
  th.forEach((t, i) => s.addText(t.toUpperCase(), { x: M + cols[i], y: 3.2, w: larg[i], h: 0.32,
    isTextBox: true, margin: 0, fontFace: F.b, fontSize: 12, bold: true,
    color: C.mute, charSpacing: 1 }));
  s.addShape(pres.ShapeType.rect, { x: M, y: 3.58, w: CW, h: 0.012, fill: { color: C.rule } });
  erros.forEach((e, i) => {
    const y = 3.75 + i * 0.72;
    s.addText(e[0], { x: M, y, w: larg[0], h: 0.44, isTextBox: true, margin: 0,
      fontFace: F.b, fontSize: 16, bold: true, color: C.text });
    s.addText(e[1], { x: M + cols[1], y, w: larg[1], h: 0.44, isTextBox: true, margin: 0,
      fontFace: F.b, fontSize: 15, color: C.text2 });
    s.addText(e[2], { x: M + cols[2], y, w: larg[2], h: 0.44, isTextBox: true, margin: 0,
      fontFace: F.b, fontSize: 15, color: C.cyan });
    s.addShape(pres.ShapeType.rect, { x: M, y: y + 0.56, w: CW, h: 0.008,
      fill: { color: "23232B" } });
  });
  rodape(s);
}

/* ═══════════════ REFAZER DO ZERO ═══════════════ */
{
  const s = conteudo("Encerramento", "Se você começasse hoje", "Como refazer do zero",
    "Catorze passos em três fases — e a ordem importa");
  const fases = [
    ["A · O agente", C.pink, "1 · git init, estrutura de pastas e .gitignore\n2 · AGENTS.md, com a regra de ler a memória\n3 · MEMORY.md, mesmo quase vazio"],
    ["B · O código", C.cyan, "4 · modelos.py — o contrato antes da lógica\n5 · configuracao.py — nada de getenv espalhado\n6 · erros.py — todo erro com como_resolver\n7 · servicos/ — uma classe por integração\n8 · principal.py — a rota orquestra, não integra\n9 · web/aplicacao.py — a interface\n10 · testes, antes de containerizar\n11 · Dockerfiles + docker compose"],
    ["C · A nuvem", C.amber, "12 · infra/ — scripts numerados + Bicep\n13 · publicar com az acr build + containerapp\n14 · skills/ e docs/ — para a próxima turma"],
  ];
  fases.forEach((f, i) => {
    const l = (CW - 0.7) / 3;
    cartao(s, { x: M + i * (l + 0.35), y: 3.35, w: l, h: 5.4, cor: f[1],
      rotulo: f[0], corpo: f[2], corpoTam: 15.5 });
  });
  cartao(s, { x: M, y: 9.05, w: CW, h: 1.35, fundo: C.panel2, cor: C.pink,
    corpo: "A ordem importa: escrever o AGENTS.md antes do código é o que faz o agente trabalhar do seu jeito desde a primeira linha, em vez de você corrigir depois.",
    corpoTam: 17 });
  rodape(s);
}

/* ═══════════════ REFERÊNCIAS ═══════════════ */
{
  const s = conteudo("Encerramento", "Verificadas em 30/08/2026", "Referências", null);
  const refs = [
    ["Image Analysis 4.0 — detecção de pessoas", "learn.microsoft.com/azure/ai-services/computer-vision/concept-people-detection"],
    ["Chamar a API Analyze Image 4.0", "learn.microsoft.com/azure/ai-services/computer-vision/how-to/call-analyze-image-40"],
    ["Face — operação Detect (v1.2)", "learn.microsoft.com/rest/api/face/face-detection-operations/detect"],
    ["Face — nota de transparência e Acesso Limitado", "learn.microsoft.com/azure/ai-foundry/responsible-ai/face/transparency-note"],
    ["Azure Container Apps — implantar do ACR", "learn.microsoft.com/azure/container-apps/quickstart-code-to-cloud"],
    ["az acr build", "learn.microsoft.com/cli/azure/acr#az-acr-build"],
    ["Blob Storage — SDK Python", "learn.microsoft.com/azure/storage/blobs/storage-quickstart-blobs-python"],
    ["Gerenciamento de Custos — orçamentos", "learn.microsoft.com/azure/cost-management-billing/costs/tutorial-acm-create-budgets"],
    ["FastAPI", "fastapi.tiangolo.com"],
    ["Streamlit", "docs.streamlit.io"],
    ["LGPD — Lei 13.709/2018, art. 5º, II", "planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm"],
  ];
  refs.forEach((r, i) => {
    const col = i < 6 ? 0 : 1;
    const y = 3.2 + (i % 6) * 1.12;
    const x = M + col * (CW / 2 + 0.3);
    s.addShape(pres.ShapeType.rect, { x, y: y + 0.14, w: 0.16, h: 0.16, fill: { color: C.pink } });
    s.addText(r[0], { x: x + 0.42, y, w: CW / 2 - 0.7, h: 0.42, isTextBox: true, margin: 0,
      fontFace: F.h, fontSize: 17, bold: true, color: C.text });
    s.addText(r[1], { x: x + 0.42, y: y + 0.42, w: CW / 2 - 0.5, h: 0.38, isTextBox: true,
      margin: 0, fontFace: F.b, fontSize: 12, color: C.cyan });
  });
  rodape(s);
}

/* ═══════════════ FECHAMENTO ═══════════════ */
{
  const s = novo();
  s.addShape(pres.ShapeType.ellipse, { x: 14.2, y: -3.4, w: 9.4, h: 8.2, fill: { color: C.pink } });
  s.addShape(pres.ShapeType.rect, { x: M, y: 2.9, w: 1.35, h: 0.07, fill: { color: C.pink } });
  s.addText("O QUE FICA", { x: M, y: 3.25, w: 12, h: 0.5, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 17, bold: true, color: C.pink, charSpacing: 2.5 });
  s.addText("O serviço devolve uma probabilidade.\nQuem decide o que fazer com ela é gente.", {
    x: M, y: 3.9, w: 15, h: 2.2, isTextBox: true, margin: 0,
    fontFace: F.h, fontSize: 44, bold: true, color: C.text, lineSpacingMultiple: 1.14 });
  s.addText("O Deva3 detecta presença e devolve caixa. Não identifica ninguém, não compara rostos e não guarda template biométrico. O limiar é configurável, aparece no payload e aparece na tela — porque onde colocar a régua é decisão de risco, não verdade técnica.", {
    x: M, y: 6.3, w: 13.2, h: 1.4, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 19, color: C.text2, lineSpacingMultiple: 1.22 });
  const tri = [["AGENTS.md", "a alma", C.pink], ["MEMORY.md", "o aprendizado", C.amber],
               ["rg-aula-05", "e um comando que apaga tudo", C.cyan]];
  tri.forEach((t, i) => {
    const l = 4.4, x = M + i * (l + 0.4);
    s.addShape(pres.ShapeType.rect, { x, y: 8.0, w: l, h: 1.5,
      fill: { color: C.panel }, line: { color: t[2], width: 1.25 } });
    s.addText(t[0], { x: x + 0.35, y: 8.22, w: l - 0.7, h: 0.46, isTextBox: true, margin: 0,
      fontFace: F.h, fontSize: 20, bold: true, color: C.text });
    s.addText(t[1], { x: x + 0.35, y: 8.72, w: l - 0.7, h: 0.42, isTextBox: true, margin: 0,
      fontFace: F.b, fontSize: 15, color: t[2] });
  });
  s.addText("PROF. ISAIAS S. BRITTO   ·   FIAP · MBA AI ENGINEERING & MULTI-AGENTS", {
    x: M, y: 9.9, w: 15, h: 0.4, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 13, color: C.mute, charSpacing: 1 });
  rodape(s);
}

pres.writeFile({ fileName: "/root/deva3/deva3-validacao-biometrica.pptx" })
  .then(f => console.log("gerado:", f));
