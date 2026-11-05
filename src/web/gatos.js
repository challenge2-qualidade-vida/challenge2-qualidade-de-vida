// Gatos vivos (tópico 25): cada gato é uma imagem só, deformada na placa de vídeo em tempo real.
// A cabeça gira como uma esfera, o focinho avança, as orelhas recuam, os olhos seguem o
// cursor, o peito respira e as pálpebras piscam. Nenhum quadro é misturado, então o rosto
// nunca duplica. Todos dividem um só contexto de WebGL, porque o navegador limita quantos
// podem existir, e só os gatos visíveis são desenhados. Sem WebGL 2 ou com menos movimento
// pedido, ficam as imagens paradas.
(() => {
  // Medidas em pixels da imagem de cada gato.
  const GATOS = {
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

  function programa(gl) {
    const p = gl.createProgram();
    for (const [tipo, fonte] of [[gl.VERTEX_SHADER, VERTICES], [gl.FRAGMENT_SHADER, FRAGMENTOS]]) {
      const s = gl.createShader(tipo);
      gl.shaderSource(s, fonte);
      gl.compileShader(s);
      gl.attachShader(p, s);
    }
    gl.linkProgram(p);
    return gl.getProgramParameter(p, gl.LINK_STATUS) ? p : null;
  }

  const limite = (v, a, b) => Math.min(b, Math.max(a, v));
  let mouseX = null, mouseY = null, ultimoMouse = 0;

  addEventListener("pointermove", (e) => {
    if (e.pointerType === "touch") return;
    mouseX = e.clientX;
    mouseY = e.clientY;
    ultimoMouse = performance.now();
  }, { passive: true });

  const palco = document.createElement("canvas");
  const gl = !matchMedia("(prefers-reduced-motion: reduce)").matches
    && palco.getContext("webgl2", { alpha: true, premultipliedAlpha: true, antialias: false });
  const prog = gl && programa(gl);
  if (!prog) return;

  gl.useProgram(prog);
  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(gl.getAttribLocation(prog, "pos"));
  gl.vertexAttribPointer(gl.getAttribLocation(prog, "pos"), 2, gl.FLOAT, false, 0, 0);
  gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
  gl.clearColor(0, 0, 0, 0);

  const local = (nome) => gl.getUniformLocation(prog, nome);
  const uOlhar = local("olhar"), uRespiro = local("respiro"), uPiscada = local("piscada");
  const uCorPelo = local("corPelo"), uForcaOlho = local("forcaOlho");
  const NOMES_PONTOS = ["origem", "tamanho", "cabeca", "raio", "area", "areaRaio", "focinho", "focinhoRaio",
    "orelhaE", "orelhaD", "orelhaRaio", "olhoE", "olhoD", "olhoRaio", "peito", "peitoRaio"];
  const pontos = NOMES_PONTOS.map((nome) => [nome, local(nome)]);
  const gatos = [];

  async function iniciar(img) {
    const medidas = GATOS[img.dataset.gato];
    if (!medidas) return;
    await img.decode().catch(() => {});
    if (!img.naturalWidth) return;

    const textura = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, textura);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

    const canvas = document.createElement("canvas");
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    canvas.className = img.className;
    if (img.alt) {
      canvas.setAttribute("role", "img");
      canvas.setAttribute("aria-label", img.alt);
    } else {
      canvas.setAttribute("aria-hidden", "true");
    }
    img.replaceWith(canvas);
    gatos.push({
      medidas, textura, canvas, ctx: canvas.getContext("2d"),
      proporcao: img.naturalHeight / img.naturalWidth, larguraMaxima: img.naturalWidth,
      x: 0, y: 0, fase: Math.random() * 6,
      proximaPiscada: performance.now() + 1000 + Math.random() * 4000, inicioPiscada: -1e9,
    });
  }

  function desenhar(g, agora, caixa) {
    let alvoX, alvoY;
    if (mouseX !== null && agora - ultimoMouse < 6000) {
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
    if (palco.width < largura) palco.width = largura;
    if (palco.height < altura) palco.height = altura;

    gl.viewport(0, palco.height - altura, largura, altura);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.bindTexture(gl.TEXTURE_2D, g.textura);
    for (const [nome, u] of pontos) gl.uniform2f(u, ...g.medidas[nome]);
    gl.uniform3f(uCorPelo, ...g.medidas.corPelo);
    gl.uniform1f(uForcaOlho, g.medidas.semOlhos ? 0 : 1);
    gl.uniform1f(uPiscada, !g.medidas.semOlhos && t < 1 ? Math.sin(t * Math.PI) : 0);
    gl.uniform1f(uRespiro, Math.sin(agora / 780 + g.fase));
    gl.uniform2f(uOlhar, g.x, g.y);
    gl.drawArrays(gl.TRIANGLES, 0, 3);

    g.ctx.clearRect(0, 0, largura, altura);
    g.ctx.drawImage(palco, 0, 0, largura, altura, 0, 0, largura, altura);
  }

  function quadro(agora) {
    requestAnimationFrame(quadro);
    if (document.hidden) return;
    for (const g of gatos) {
      if (!g.canvas.isConnected) continue;
      const caixa = g.canvas.getBoundingClientRect();
      if (!caixa.width || caixa.bottom < 0 || caixa.top > innerHeight) continue;
      desenhar(g, agora, caixa);
    }
  }

  // Na abertura, a Mia pisca quando um alimento cai na cesta.
  document.addEventListener("economia:comida-caiu", () => {
    const mia = gatos.find((g) => g.canvas.classList.contains("hero-gato"));
    if (mia) mia.inicioPiscada = performance.now();
  });

  document.querySelectorAll("img[data-gato]").forEach(iniciar);
  requestAnimationFrame(quadro);
})();
