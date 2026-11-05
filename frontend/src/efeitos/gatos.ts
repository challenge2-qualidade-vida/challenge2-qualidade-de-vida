// Gatos vivos (tópico 25): cada gato é uma imagem só, deformada na placa de vídeo em tempo real.
// A cabeça gira como uma esfera, o focinho avança, as orelhas recuam, os olhos seguem o
// cursor, o peito respira e as pálpebras piscam. Nenhum quadro é misturado, então o rosto
// nunca duplica. Todos dividem um só contexto de WebGL, porque o navegador limita quantos
// podem existir, e só os gatos visíveis são desenhados. Sem WebGL 2 ou com menos movimento
// pedido, ficam as imagens paradas.
//
// Portado de src/web/gatos.js. Lá o script trocava cada <img> por um <canvas>; aqui quem troca
// é o componente GatoVivo, e este módulo só desenha nos canvas registrados.

export type NomeDoGato = "mia" | "cifrao" | "miauricio" | "recibaldo";
type Par = [number, number];

interface Medidas {
  semOlhos?: boolean;
  corPelo: [number, number, number];
  origem: Par; tamanho: Par;
  cabeca: Par; raio: Par;
  area: Par; areaRaio: Par;
  focinho: Par; focinhoRaio: Par;
  orelhaE: Par; orelhaD: Par; orelhaRaio: Par;
  olhoE: Par; olhoD: Par; olhoRaio: Par;
  peito: Par; peitoRaio: Par;
}

// Medidas em pixels da imagem de cada gato.
const GATOS: Record<NomeDoGato, Medidas> = {
  mia: {
    corPelo: [0.13, 0.135, 0.16],
    origem: [60, 0], tamanho: [790, 990],
    cabeca: [447, 320], raio: [340, 290],
    area: [450, 270], areaRaio: [450, 330],
    focinho: [443, 470], focinhoRaio: [140, 90],
    orelhaE: [165, 150], orelhaD: [735, 170], orelhaRaio: [100, 120],
    olhoE: [309, 361], olhoD: [581, 373], olhoRaio: [71, 59],
    peito: [430, 730], peitoRaio: [270, 210],
  },
  cifrao: {
    corPelo: [0.1, 0.1, 0.12],
    origem: [40, 0], tamanho: [816, 985],
    cabeca: [450, 340], raio: [310, 280],
    area: [450, 270], areaRaio: [440, 320],
    focinho: [470, 450], focinhoRaio: [130, 85],
    orelhaE: [195, 190], orelhaD: [665, 160], orelhaRaio: [95, 130],
    olhoE: [344, 368], olhoD: [576, 347], olhoRaio: [58, 47],
    peito: [450, 760], peitoRaio: [300, 190],
  },
  // De óculos escuros: só a cabeça acompanha o cursor.
  miauricio: {
    semOlhos: true,
    corPelo: [0.07, 0.07, 0.08],
    origem: [55, 0], tamanho: [825, 985],
    cabeca: [445, 340], raio: [320, 270],
    area: [445, 280], areaRaio: [430, 310],
    focinho: [440, 470], focinhoRaio: [140, 80],
    orelhaE: [190, 190], orelhaD: [720, 170], orelhaRaio: [100, 130],
    olhoE: [305, 385], olhoD: [555, 380], olhoRaio: [80, 75],
    peito: [470, 740], peitoRaio: [240, 170],
  },
  recibaldo: {
    corPelo: [0.07, 0.07, 0.08],
    origem: [80, 40], tamanho: [816, 945],
    cabeca: [430, 370], raio: [310, 270],
    area: [430, 320], areaRaio: [430, 300],
    focinho: [428, 510], focinhoRaio: [130, 85],
    orelhaE: [215, 190], orelhaD: [715, 230], orelhaRaio: [100, 120],
    olhoE: [318, 408], olhoD: [562, 423], olhoRaio: [61, 51],
    peito: [440, 760], peitoRaio: [230, 160],
  },
};

const VERTICES = `#version 300 es
  in vec2 pos;
  out vec2 uv;
  void main() {
    uv = vec2(pos.x + 1.0, 1.0 - pos.y) / 2.0;
    gl_Position = vec4(pos, 0.0, 1.0);
  }`;

const FRAGMENTOS = `#version 300 es
  precision highp float;
  uniform sampler2D imagem;
  uniform vec2 tamanho, origem, olhar, cabeca, raio, area, areaRaio, focinho, focinhoRaio;
  uniform vec2 orelhaE, orelhaD, orelhaRaio, olhoE, olhoD, olhoRaio, peito, peitoRaio;
  uniform vec3 corPelo;
  uniform float respiro, piscada, forcaOlho;
  in vec2 uv;
  out vec4 cor;

  float sino(vec2 p, vec2 c, vec2 r) { vec2 d = (p - c) / r; return exp(-dot(d, d)); }

  // Empurra o miolo do olho e deixa a borda parada, como um globo girando na órbita.
  vec2 globo(vec2 p, vec2 c) {
    vec2 e = (p - c) / olhoRaio;
    return p - forcaOlho * olhar * olhoRaio * vec2(0.24, 0.18) * max(0.0, 1.0 - dot(e, e));
  }

  // A pálpebra desce na cor do pelo e termina em um vinco escuro.
  vec4 palpebra(vec2 p, vec2 c, vec4 base) {
    vec2 e = (p - c) / (olhoRaio * 1.06);
    float dentro = 1.0 - smoothstep(0.86, 1.0, dot(e, e));
    if (dentro <= 0.0 || piscada <= 0.0) return base;
    float linha = -1.0 + 2.1 * piscada;
    vec4 pelo = vec4(corPelo * (1.0 + 0.25 * e.y) * (1.0 - 0.75 * exp(-pow((e.y - linha) / 0.1, 2.0))), 1.0);
    return mix(base, pelo, dentro * (1.0 - smoothstep(linha - 0.03, linha + 0.03, e.y)));
  }

  void main() {
    vec2 p = uv * tamanho + origem;
    p -= (p - peito) * 0.022 * respiro * sino(p, peito, peitoRaio);

    vec2 q = (p - cabeca) / raio;
    float z = pow(max(0.0, 1.0 - dot(q, q)), 1.5);
    z += 0.45 * sino(p, focinho, focinhoRaio);
    z -= 0.5 * (sino(p, orelhaE, orelhaRaio) + sino(p, orelhaD, orelhaRaio));
    float peso = 1.0 - smoothstep(1.0, 1.3, length((p - area) / areaRaio));
    p -= (olhar * vec2(1.0, 0.65) * (50.0 * z + 14.0) + vec2(0.0, -3.5 * respiro)) * peso;

    vec2 olho = globo(globo(p, olhoE), olhoD);
    vec4 base = texture(imagem, (olho - origem) / tamanho);
    cor = palpebra(p, olhoD, palpebra(p, olhoE, base));
  }`;

const NOMES_PONTOS = ["origem", "tamanho", "cabeca", "raio", "area", "areaRaio", "focinho", "focinhoRaio",
  "orelhaE", "orelhaD", "orelhaRaio", "olhoE", "olhoD", "olhoRaio", "peito", "peitoRaio"] as const;

interface GatoDesenhado {
  medidas: Medidas;
  textura: WebGLTexture;
  canvas: HTMLCanvasElement;
  ctx: CanvasRenderingContext2D;
  proporcao: number;
  larguraMaxima: number;
  x: number; y: number; fase: number;
  proximaPiscada: number; inicioPiscada: number;
}

interface Palco {
  canvas: HTMLCanvasElement;
  gl: WebGL2RenderingContext;
  uniformes: {
    olhar: WebGLUniformLocation | null; respiro: WebGLUniformLocation | null; piscada: WebGLUniformLocation | null;
    corPelo: WebGLUniformLocation | null; forcaOlho: WebGLUniformLocation | null;
    pontos: [typeof NOMES_PONTOS[number], WebGLUniformLocation | null][];
  };
}

const limite = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));
let mouseX: number | null = null, mouseY: number | null = null, ultimoMouse = 0;
const gatos: GatoDesenhado[] = [];
let palco: Palco | null | undefined;

function programa(gl: WebGL2RenderingContext) {
  const p = gl.createProgram();
  for (const [tipo, fonte] of [[gl.VERTEX_SHADER, VERTICES], [gl.FRAGMENT_SHADER, FRAGMENTOS]] as const) {
    const s = gl.createShader(tipo);
    if (!s) return null;
    gl.shaderSource(s, fonte);
    gl.compileShader(s);
    gl.attachShader(p, s);
  }
  gl.linkProgram(p);
  return gl.getProgramParameter(p, gl.LINK_STATUS) ? p : null;
}

/** Cria o contexto compartilhado na primeira vez. Devolve null sem WebGL 2 ou com menos movimento pedido. */
function obterPalco(): Palco | null {
  if (palco !== undefined) return palco;
  palco = null;
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return null;
  const canvas = document.createElement("canvas");
  const gl = canvas.getContext("webgl2", { alpha: true, premultipliedAlpha: true, antialias: false });
  const prog = gl && programa(gl);
  if (!gl || !prog) return null;

  gl.useProgram(prog);
  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(gl.getAttribLocation(prog, "pos"));
  gl.vertexAttribPointer(gl.getAttribLocation(prog, "pos"), 2, gl.FLOAT, false, 0, 0);
  gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
  gl.clearColor(0, 0, 0, 0);

  const local = (nome: string) => gl.getUniformLocation(prog, nome);
  palco = {
    canvas, gl,
    uniformes: {
      olhar: local("olhar"), respiro: local("respiro"), piscada: local("piscada"),
      corPelo: local("corPelo"), forcaOlho: local("forcaOlho"),
      pontos: NOMES_PONTOS.map((nome) => [nome, local(nome)]),
    },
  };

  addEventListener("pointermove", (e) => {
    if (e.pointerType === "touch") return;
    mouseX = e.clientX;
    mouseY = e.clientY;
    ultimoMouse = performance.now();
  }, { passive: true });
  // Na abertura, a Mia pisca quando um alimento cai na cesta.
  document.addEventListener("economia:comida-caiu", () => {
    const mia = gatos.find((g) => g.canvas.classList.contains("hero-gato"));
    if (mia) mia.inicioPiscada = performance.now();
  });
  requestAnimationFrame(quadro);
  return palco;
}

/** O componente GatoVivo usa isto para decidir entre canvas e imagem parada. */
export function gatoVivoDisponivel() {
  return obterPalco() !== null;
}

/** Passa a desenhar o gato no canvas. Devolve a função que para de desenhar. */
export function registrarGato(canvas: HTMLCanvasElement, imagem: HTMLImageElement, nome: NomeDoGato): () => void {
  const p = obterPalco();
  const ctx = canvas.getContext("2d");
  if (!p || !ctx) return () => {};
  const { gl } = p;
  const textura = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, textura);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, imagem);
  gl.generateMipmap(gl.TEXTURE_2D);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

  const gato: GatoDesenhado = {
    medidas: GATOS[nome], textura, canvas, ctx,
    proporcao: imagem.naturalHeight / imagem.naturalWidth, larguraMaxima: imagem.naturalWidth,
    x: 0, y: 0, fase: Math.random() * 6,
    proximaPiscada: performance.now() + 1000 + Math.random() * 4000, inicioPiscada: -1e9,
  };
  gatos.push(gato);
  return () => {
    gatos.splice(gatos.indexOf(gato), 1);
    gl.deleteTexture(textura);
  };
}

function desenhar(p: Palco, g: GatoDesenhado, agora: number, caixa: DOMRect) {
  const { gl, uniformes: u } = p;
  let alvoX, alvoY;
  if (mouseX !== null && mouseY !== null && agora - ultimoMouse < 6000) {
    // A cabeça fica acima do meio da imagem: é daí que o gato "olha".
    const olhoX = caixa.left + caixa.width / 2, olhoY = caixa.top + caixa.height * 0.35;
    alvoX = limite((mouseX - olhoX) / (innerWidth * 0.42), -1, 1);
    alvoY = limite((mouseY - olhoY) / (innerHeight * 0.5), -1, 1);
  } else {
    // Sem mouse, o gato olha em volta devagar.
    alvoX = Math.sin(agora / 3100 + g.fase) * 0.45;
    alvoY = Math.sin(agora / 4300 + g.fase) * 0.25;
  }
  g.x += (alvoX - g.x) * 0.09;
  g.y += (alvoY - g.y) * 0.09;

  if (agora > g.proximaPiscada) {
    g.inicioPiscada = agora;
    g.proximaPiscada = agora + 2200 + Math.random() * 4200;
  }
  const t = (agora - g.inicioPiscada) / 170;

  // Desenha só no tamanho em que o gato aparece: os pequenos custam pouco.
  const css = Math.max(g.canvas.offsetWidth, g.canvas.offsetHeight / g.proporcao);
  const largura = Math.round(Math.min(g.larguraMaxima, css * Math.min(devicePixelRatio, 2)));
  const altura = Math.round(largura * g.proporcao);
  if (g.canvas.width !== largura || g.canvas.height !== altura) {
    g.canvas.width = largura;
    g.canvas.height = altura;
  }
  if (p.canvas.width < largura) p.canvas.width = largura;
  if (p.canvas.height < altura) p.canvas.height = altura;

  gl.viewport(0, p.canvas.height - altura, largura, altura);
  gl.clear(gl.COLOR_BUFFER_BIT);
  gl.bindTexture(gl.TEXTURE_2D, g.textura);
  for (const [nome, local] of u.pontos) gl.uniform2f(local, ...g.medidas[nome]);
  gl.uniform3f(u.corPelo, ...g.medidas.corPelo);
  gl.uniform1f(u.forcaOlho, g.medidas.semOlhos ? 0 : 1);
  gl.uniform1f(u.piscada, !g.medidas.semOlhos && t < 1 ? Math.sin(t * Math.PI) : 0);
  gl.uniform1f(u.respiro, Math.sin(agora / 780 + g.fase));
  gl.uniform2f(u.olhar, g.x, g.y);
  gl.drawArrays(gl.TRIANGLES, 0, 3);

  g.ctx.clearRect(0, 0, largura, altura);
  g.ctx.drawImage(p.canvas, 0, 0, largura, altura, 0, 0, largura, altura);
}

function quadro(agora: number) {
  requestAnimationFrame(quadro);
  if (document.hidden || !palco) return;
  for (const g of gatos) {
    if (!g.canvas.isConnected) continue;
    const caixa = g.canvas.getBoundingClientRect();
    if (!caixa.width || caixa.bottom < 0 || caixa.top > innerHeight) continue;
    desenhar(palco, g, agora, caixa);
  }
}
