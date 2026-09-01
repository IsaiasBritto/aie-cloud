const pptxgen = require("pptxgenjs");
const path = require("path");
const IMG = "/root/deva-continuo/figuras/png";

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
pres.title = "Deva contínuo — memória revisável e fila de documentos";

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
  s.addText("Aula 02 · Deva contínuo: memória revisável e fila · Uso exclusivo para fins acadêmicos", {
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
  const y0 = 1.45 + Math.max(0, (maxA - a - 0.45) / 2);
  s.addImage({ path: path.join(IMG, arquivo), x: (W - l) / 2, y: y0, w: l, h: a });
  if (legenda) s.addText(legenda, { x: M, y: y0 + a + 0.12, w: CW, h: 0.34,
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


const DIAG = "/root/deva-continuo/docs/imagens";

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
  s.addText("Deva contínuo", { x: M, y: 6.25, w: 16, h: 1.15, isTextBox: true,
    margin: 0, fontFace: F.h, fontSize: 58, bold: true, color: C.text });
  s.addText("O agente entre uma conversa e outra", { x: M, y: 7.45, w: 15,
    h: 0.65, isTextBox: true, margin: 0, fontFace: F.h, fontSize: 30, color: C.text2 });
  s.addText("Aula 02 · módulo complementar — memória revisável, fila de documentos e o gatilho\nque faz o agente começar sozinho. E a tela onde o aluno VÊ o MEMORY.md mudar.", {
    x: M, y: 8.25, w: 13, h: 1.0, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 18, color: C.text2, lineSpacingMultiple: 1.2 });
  s.addText("PROF. ISAIAS S. BRITTO   ·   45 MINUTOS", { x: M, y: 9.75, w: 13, h: 0.4,
    isTextBox: true, margin: 0, fontFace: F.b, fontSize: 13, color: C.mute, charSpacing: 1 });
  n++;
  s.addNotes("Este módulo nasceu de duas perguntas feitas em sala: como o Deva vira um agente contínuo, e como o aluno consegue ver que ele está aprendendo.");
}

/* ═══════════════ AS DUAS PERGUNTAS ═══════════════ */
{
  const s = conteudo("Abertura", "De onde veio este módulo", "As duas perguntas da turma",
    "Nenhuma delas se responde com um slide. As duas se respondem com um projeto.");
  cartao(s, { x: M, y: 3.35, w: (CW - 0.5) / 2, h: 3.3, cor: C.pink,
    rotulo: "Pergunta 1",
    titulo: "\"Ele lê nota fiscal, mas não parece um agente contínuo.\"", tituloTam: 22,
    tituloH: 1.0,
    corpo: "Como incrementá-lo para ter esse comportamento?", corpoTam: 17 });
  cartao(s, { x: M + (CW - 0.5) / 2 + 0.5, y: 3.35, w: (CW - 0.5) / 2, h: 3.3, cor: C.cyan,
    rotulo: "Pergunta 2",
    titulo: "\"Como o aluno abre o MEMORY.md para saber que ele está aprendendo?\"",
    tituloTam: 22, tituloH: 1.0,
    corpo: "Se não dá para ver, não dá para ensinar — nem para auditar.", corpoTam: 17 });
  cartao(s, { x: M, y: 7.0, w: CW, h: 2.85, cor: C.amber,
    rotulo: "A resposta curta da pergunta 1",
    titulo: "O problema não é o agente", tituloTam: 26,
    corpo: "É que ninguém deu a ele um motivo para existir entre duas perguntas. Continuidade não é uma configuração que se liga: é uma escada de cinco degraus, e cada um exige alguma coisa construída.",
    corpoTam: 18 });
  rodape(s);
}

figura("dc-04-abertura.png", 2800 / 1054, "Abertura", "Faça isto antes de explicar",
  "Trinta segundos que valem mais que dez minutos de slide");

/* ═══════════════ BLOCO 1 · OS CINCO NÍVEIS ═══════════════ */
bloco("1", "Bloco 1 · 6 minutos", "Os cinco níveis",
  "Cada degrau depende do anterior.\nPular para o 3 dá um agente que acorda e não sabe o que já fez.");

figura("dc-01-cinco-niveis.png", 2840 / 1560, "Bloco 1", "A escada",
  "Nível 3 é o que muda a percepção da turma · Nível 4 é o que separa automação de brinquedo");

{
  const s = conteudo("Bloco 1", "Nível 3", "Ele começa sozinho",
    "O gatilho é um EVENTO, não um horário");
  const it = [
    [C.cyan, "Event Grid → Logic App", "BlobCreated no contêiner 'entrada' chama POST /fila/documentos. Sem sondagem, custo por evento. É o caminho de produção."],
    [C.amber, "Sondagem (gatilho/disparador.py)", "Um laço olha a pasta a cada N segundos. Pior em produção, MELHOR em sala: roda na máquina do aluno e deixa ver o mecanismo."],
    [C.pink, "O filtro que ninguém lembra", "subjectBeginsWith no contêiner 'entrada'. Sem ele, o MEMORY.md que o próprio serviço escreve dispara o fluxo: o agente acorda, escreve e acorda de novo."],
    [C.cyan, "E o freio novo do AGENTS.md", "Duas voltas seguidas sem avançar nada = parar e avisar. Laço que não progride não gasta muito por volta; gasta por não parar nunca."],
  ];
  const l = (CW - 1.05) / 4;
  it.forEach((c, i) => cartao(s, { x: M + i * (l + 0.35), y: 3.35, w: l, h: 5.4,
    cor: c[0], rotulo: c[1], corpo: c[2], corpoTam: 16 }));
  rodape(s);
  s.addNotes("Pergunte depois da demonstração: quem disparou esse processo? Ninguém. Um arquivo chegou.");
}

/* ═══════════════ BLOCO 2 · MEMÓRIA REVISÁVEL ═══════════════ */
bloco("2", "Bloco 2 · 8 minutos", "Memória revisável",
  "O agente propõe; ele não decide.\nE o motivo veio do laboratório de vocês.");

figura("dc-02-instrucao-permissao.png", 2800 / 1690, "Bloco 2", "A lição de arquitetura",
  "A mesma regra, escrita de duas formas — e só uma delas segura");

{
  const s = conteudo("Bloco 2", "A evidência", "O que teria acontecido se ele errasse uma vez",
    "Isto aconteceu de verdade no laboratório do Deva, na versão 1.3");
  cartao(s, { x: M, y: 3.35, w: CW, h: 2.5, cor: C.amber,
    rotulo: "O que aconteceu",
    corpo: "Uma nota fiscal chegou com uma instrução escondida no rodapé mandando aprovar sem revisão. O Deva RECUSOU e registrou como incidente de segurança — exatamente como o AGENTS.md mandava.",
    corpoTam: 19 });
  cartao(s, { x: M, y: 6.2, w: (CW - 0.5) / 2, h: 3.6, cor: C.pink,
    rotulo: "O que teria acontecido se ele errasse",
    titulo: "A frase viraria regra permanente", tituloTam: 22,
    corpo: "Aprovada por ele mesmo. Aplicada a todos os documentos seguintes. Ninguém perceberia até a auditoria externa.",
    corpoTam: 17 });
  cartao(s, { x: M + (CW - 0.5) / 2 + 0.5, y: 6.2, w: (CW - 0.5) / 2, h: 3.6, cor: C.cyan,
    rotulo: "A conclusão",
    titulo: "Aprendizado automático sem revisão não é funcionalidade", tituloTam: 22,
    tituloH: 1.0,
    corpo: "É superfície de ataque. E a defesa não é escrever \"não faça isso\" — é não expor a operação.",
    corpoTam: 17 });
  rodape(s);
}

diagrama({
  kicker: "Bloco 2", dir: "O fluxo completo",
  titulo: "Da correção do auditor até a regra valer",
  sub: "Dois arquivos, e uma linha atravessando de um para o outro",
  arquivo: "01-fluxo-da-memoria.png", ar: 4368 / 1126, banner: true,
  cartoes: [
    [C.amber, "memoria-pendente.md", "O que o agente QUER aprender. Não influencia uma única decisão dele."],
    [C.cyan, "MEMORY.md", "O que ele PODE usar. A origem da linha é o nome do auditor que aprovou — nunca 'deva'."],
    [C.pink, "Os dois caminhos de recusa", "Padrão de manipulação vira incidente de segurança. Tentativa de alterar alçada vai para a Controladoria."],
  ],
  fonte: "Fonte: docs/diagramas/01-fluxo-da-memoria.mmd",
});

figura("dc-03-cinco-de-catorze.png", 2720 / 1300, "Bloco 2", "A fronteira, em números",
  "A API tem 14 operações · o agente recebe 5 · e a garantia é testada, não prometida");

/* ═══════════════ BLOCO 3 · A TELA ═══════════════ */
bloco("3", "Bloco 3 · 8 minutos", "Onde o aluno vê",
  "A resposta da pergunta 2.\nQuatro abas, e a linha mudando de arquivo na frente da turma.");

figura("dc-tela-2-memoria.png", 3000 / 1861, "Bloco 3 · aba Memória", "O que ele já sabe",
  "A borda ciano marca o que ENTROU HOJE · à direita, o texto exato que está no MEMORY.md do Blob");

figura("dc-tela-3-propostas.png", 3000 / 1489, "Bloco 3 · aba Propostas", "O que ele quer aprender e ainda não pode",
  "Cada proposta traz a EVIDÊNCIA: qual documento e qual correção a motivaram");

figura("dc-tela-1-painel.png", 3000 / 1802, "Bloco 3 · aba Painel", "Ele está trabalhando agora?",
  "Com o agente · esperando gente · propostas pendentes — os três números que importam");

{
  const s = conteudo("Bloco 3", "Quatro formas", "Como o aluno abre o MEMORY.md",
    "Da mais didática para a mais barata. Todas funcionam; escolha pelo tempo de aula.");
  const it = [
    [C.cyan, "A · A tela", "GET /memoria, markdown renderizado, linhas de hoje em ciano. O aluno pergunta, o agente propõe, ele aprova e VÊ a linha aparecer. Custa uma tela de Streamlit."],
    [C.amber, "B · O arquivo no Blob", "Portal do Azure → contêiner memoria-do-deva → MEMORY.md → Editar. Menos bonito, zero código extra, e mostra que memória é um ARQUIVO com dono, permissão e retenção."],
    [C.pink, "C · Repositório Git", "O agente abre um PR com a linha; o aluno revisa e faz merge. O mais próximo do mundo real, o melhor para governança — e o que mais gasta tempo de aula."],
    [C.mute, "D · Sem construir nada", "O agente termina a resposta com um bloco PROPOSTA DE MEMÓRIA pronto para colar. Parece pobre e é o oposto: coloca o humano no meio do aprendizado."],
  ];
  const l = (CW - 1.05) / 4;
  it.forEach((c, i) => cartao(s, { x: M + i * (l + 0.35), y: 3.35, w: l, h: 5.6,
    cor: c[0], rotulo: c[1], corpo: c[2], corpoTam: 15 }));
  rodape(s);
}

/* ═══════════════ BLOCO 4 · A FILA ═══════════════ */
bloco("4", "Bloco 4 · 10 minutos", "A fila e as exceções",
  "O que transforma repetição em processo —\ne a regra que impede o agente de girar em falso.");

diagrama({
  kicker: "Bloco 4", dir: "Máquina de estados",
  titulo: "Sete estados, e um do qual ele não sai",
  sub: "Estado explícito é o que faz o agente saber o que já fez sem ninguém dizer",
  arquivo: "02-maquina-de-estados.png", ar: 4368 / 1112, banner: true,
  cartoes: [
    [C.pink, "Exceção não volta para ele", "Mesmo que ele ache que sabe resolver. Sem essa regra ele tenta de novo, falha de novo e gasta de novo — a noite inteira."],
    [C.cyan, "E é código, não recomendação", "if estado is EXCECAO and por == 'deva': raise TransicaoProibida"],
    [C.amber, "O número do nível 4", "Não é quantos ele processou. É quantos ele DEVOLVEU. Se mais de 30% param em exceção, o problema é a regra, não o modelo."],
  ],
  fonte: "Fonte: docs/diagramas/02-maquina-de-estados.mmd",
});

figura("dc-tela-4-excecoes.png", 3000 / 1115, "Bloco 4 · aba Exceções", "O que ele não resolveu sozinho",
  "Cada documento com o histórico de quem fez o quê — inclusive quem liberou, e quando");

/* ═══════════════ BLOCO 5 · O CICLO INTEIRO ═══════════════ */
diagrama({
  kicker: "Bloco 5", dir: "Ponta a ponta",
  titulo: "Uma volta completa do ciclo",
  sub: "Do PDF caindo na pasta até a regra nova valendo na próxima sessão",
  arquivo: "03-ciclo-continuo.png", ar: 3416 / 3080, banner: false, largImg: 10.2,
  cartoes: [
    [C.cyan, "Nível 3 · ele começa sozinho", "Ninguém digitou nada. Um arquivo chegou no contêiner e o Event Grid acordou o processo."],
    [C.pink, "Duas recusas de propósito", "409 ao tentar liberar a exceção. 403 ao tentar aprovar a própria proposta. As duas são a arquitetura funcionando."],
    [C.amber, "E a decisão fica assinada", "A linha do MEMORY.md leva o nome do auditor. Um agente que aprende sem alguém assinar é um agente indefensável numa auditoria."],
  ],
  fonte: "Fonte: docs/diagramas/03-ciclo-continuo.mmd",
});

/* ═══════════════ FECHAMENTO ═══════════════ */
{
  const s = novo();
  s.addShape(pres.ShapeType.ellipse, { x: 14.4, y: -3.2, w: 8.6, h: 7.6, fill: { color: C.pink } });
  s.addText("Instrução é intenção.\nPermissão é controle.", {
    x: M, y: 3.3, w: 13.0, h: 2.6, isTextBox: true, margin: 0,
    fontFace: F.h, fontSize: 46, bold: true, color: C.text, lineSpacingMultiple: 1.14 });
  s.addText("O que impede o Deva de aprovar a própria memória não é a frase no AGENTS.md. É o fato de a operação não existir na especificação que ele carrega. Em agentes, o que você não quer que aconteça, você não expõe.", {
    x: M, y: 6.2, w: 13.2, h: 1.5, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 19, color: C.text2, lineSpacingMultiple: 1.22 });
  const tri = [["propõe, não escreve", "a memória", C.cyan],
               ["para, não insiste", "a exceção", C.amber],
               ["5 de 14 operações", "a fronteira", C.pink]];
  tri.forEach((t, i) => {
    const l = 4.4, x = M + i * (l + 0.4);
    s.addShape(pres.ShapeType.rect, { x, y: 8.1, w: l, h: 1.5,
      fill: { color: C.panel }, line: { color: t[2], width: 1.25 } });
    s.addText(t[0], { x: x + 0.35, y: 8.32, w: l - 0.7, h: 0.46, isTextBox: true, margin: 0,
      fontFace: F.h, fontSize: 20, bold: true, color: C.text });
    s.addText(t[1], { x: x + 0.35, y: 8.82, w: l - 0.7, h: 0.42, isTextBox: true, margin: 0,
      fontFace: F.b, fontSize: 15, color: t[2] });
  });
  s.addText("PROF. ISAIAS S. BRITTO   ·   FIAP · MBA AI ENGINEERING & MULTI-AGENTS", {
    x: M, y: 9.95, w: 15, h: 0.4, isTextBox: true, margin: 0,
    fontFace: F.b, fontSize: 13, color: C.mute, charSpacing: 1 });
  rodape(s);
}

{
  const s = conteudo("Depois da aula", "Quatro exercícios", "O que fica para vocês",
    "Nenhum deles é sobre modelo. Todos são sobre governança.");
  const it = [
    [C.pink, "1 · Esquecimento", "Implemente POST /memoria/{id}/arquivar, com X-Auditor. Uma regra de 12 meses sem uso deve continuar valendo? Quem decide?"],
    [C.amber, "2 · Rastreabilidade", "Faça cada decisão registrar QUAL regra da memória foi aplicada. Quando uma regra for arquivada, liste os documentos que dependeram dela."],
    [C.cyan, "3 · Taxa de devolução", "Meça quantos por cento param em exceção. Se passar de 30%, o problema é a regra, não o modelo. Prove."],
    [C.mute, "4 · Segunda opinião", "Um segundo agente critica a proposta antes da aprovação. Isso ajuda ou vira teatro? Defenda a resposta."],
  ];
  const l = (CW - 1.05) / 4;
  it.forEach((c, i) => cartao(s, { x: M + i * (l + 0.35), y: 3.35, w: l, h: 4.6,
    cor: c[0], rotulo: c[1], corpo: c[2], corpoTam: 16 }));
  cartao(s, { x: M, y: 8.25, w: CW, h: 1.6, cor: C.cyan,
    rotulo: "E o gancho para a Aula 03",
    corpo: "O Deva2 vive numa plataforma que já sabe quem ele é e quanto ele custou. O que vocês construíram hoje à mão, o Foundry oferece pronto — e agora vocês sabem o que ele está fazendo por baixo.",
    corpoTam: 17 });
  rodape(s);
}

pres.writeFile({ fileName: "/root/deva-continuo/deva-continuo-memoria-e-fila.pptx" })
  .then(f => console.log("gerado:", f));
