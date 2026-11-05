// Cena 3D da EconoMIA (tópico 24): moedas que viram comida e caem na cesta.
// O canvas fica fixo atrás do site, e os objetos seguem "palcos" do HTML, então
// rolam junto com a página. Sem WebGL, o Three.js nem é baixado e o site continua
// igual, só sem o 3D. Em aparelho fraco, a cena só fica mais leve.

const reduzirMovimento = matchMedia("(prefers-reduced-motion: reduce)").matches;

// O 3D fica sempre ligado; só não roda em navegador sem WebGL.
function temWebGL() {
  const teste = document.createElement("canvas");
  return !!(teste.getContext("webgl2") || teste.getContext("webgl"));
}

// Cores da marca.
const COR = { ouro: 0xf5cf5f, mata: 0x6f8f4f, cesta: 0x2f6b3f, floresta: 0x463708 };

// Alimentos: posição em img/comida.webp e anel de nutrição de cada um, na ordem dos anéis do cartão.
const ATLAS = ["tomate", "banana", "ovo", "arroz", "cenoura", "laranja", "feijao_carioca", "repolho", "abobora", "leite", "frango_coxa", "macarrao", "maca", "batata", "mandioca", "cebola", "feijao_preto", "lentilha", "farinha_mandioca", "aveia", "acucar", "oleo_soja", "sardinha", "frango_peito", "patinho", "lombo_porco", "mucarela", "pao_frances"];
const COLUNAS_ATLAS = 7, LINHAS_ATLAS = 4;
const ANEIS = [
  { cor: "#f5cf5f", ids: ["arroz", "macarrao", "pao_frances", "batata", "mandioca", "farinha_mandioca", "acucar", "oleo_soja"] },
  { cor: "#d9603b", ids: ["ovo", "frango_coxa", "frango_peito", "patinho", "lombo_porco", "sardinha", "leite", "mucarela"] },
  { cor: "#9a6b3f", ids: ["feijao_carioca", "feijao_preto", "lentilha", "aveia", "cenoura"] },
  { cor: "#6fb34a", ids: ["banana", "laranja", "maca", "tomate", "repolho", "abobora", "cebola"] },
];
const anelDe = (id) => Math.max(0, ANEIS.findIndex((a) => a.ids.includes(id)));

// Moedas da EconoMIA: inspiradas nas do real, sem copiar o desenho oficial.
const MOEDAS = [
  { peso: 0.5, escala: 1, serrilha: true, aro: "#e2b13c", miolo: "#dfe3e6", desenho: "real" },
  { peso: 0.3, escala: 0.92, serrilha: true, aro: "#e6b23f", miolo: "#e6b23f", desenho: "real" },
  { peso: 0.2, escala: 0.8, serrilha: false, aro: "#cf8450", miolo: "#cf8450", desenho: "pata" },
];

// O relevo é pintado em cinza: quanto mais claro, mais alto.
function pintarRelevo(x, t, desenho, sombra) {
  const c = t / 2;
  x.fillStyle = sombra; x.fillRect(0, 0, t, t);
  x.strokeStyle = "#fff"; x.lineWidth = t * 0.025;
  x.beginPath(); x.arc(c, c, t * 0.345, 0, 7); x.stroke();
  x.fillStyle = "#fff";
  if (desenho === "real") {
    x.font = `800 ${t * 0.3}px Nunito, sans-serif`;
    x.textAlign = "center"; x.textBaseline = "middle";
    x.fillText("R$", c, c * 1.03);
  } else {
    [[0, 0.09, 0.15, 0.125], [-0.17, -0.07, 0.055, 0.075], [-0.06, -0.15, 0.055, 0.08], [0.06, -0.15, 0.055, 0.08], [0.17, -0.07, 0.055, 0.075]].forEach(([px, py, rx, ry]) => {
      x.beginPath(); x.ellipse(c + px * t, c + py * t, rx * t, ry * t, 0, 0, 7); x.fill();
    });
  }
}

async function iniciar() {
  if (!temWebGL()) return;
  const THREE = await import("./vendor/three.min.js");

  const fraco = innerWidth < 720 || (navigator.hardwareConcurrency ?? 8) <= 4;
  const canvas = document.createElement("canvas");
  canvas.id = "cena-3d";
  canvas.setAttribute("aria-hidden", "true");
  document.body.prepend(canvas);

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: !fraco, powerPreference: "low-power" });
  } catch {
    canvas.remove();
    return;
  }
  // Tela pequena não é aparelho fraco: só a resolução mínima fica para quem tem poucos núcleos.
  renderer.setPixelRatio((navigator.hardwareConcurrency ?? 8) <= 4 ? 1 : Math.min(devicePixelRatio, 1.5));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  document.documentElement.classList.add("com-3d");

  const cena = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 80);
  camera.position.z = 16;
  let alturaMundo = 1, larguraMundo = 1;

  function redimensionar() {
    renderer.setSize(innerWidth, innerHeight, false);
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    alturaMundo = 2 * Math.tan((camera.fov * Math.PI) / 360) * camera.position.z;
    larguraMundo = alturaMundo * camera.aspect;
  }
  addEventListener("resize", redimensionar);
  redimensionar();

  // Luz: um ambiente pintado em canvas dá brilho de metal às moedas sem baixar imagem.
  const ceu = document.createElement("canvas");
  ceu.width = 256; ceu.height = 128;
  const c = ceu.getContext("2d");
  const grad = c.createLinearGradient(0, 0, 0, 128);
  grad.addColorStop(0, "#fff4d6"); grad.addColorStop(0.5, "#d9b64f"); grad.addColorStop(1, "#6b5614");
  c.fillStyle = grad; c.fillRect(0, 0, 256, 128);
  // Faixas de luz forte, que fazem o reflexo deslizar quando a moeda gira.
  c.fillStyle = "#ffffff";
  c.fillRect(30, 18, 46, 30); c.fillRect(150, 30, 26, 56); c.fillRect(205, 12, 34, 20);
  const texturaCeu = new THREE.CanvasTexture(ceu);
  texturaCeu.mapping = THREE.EquirectangularReflectionMapping;
  texturaCeu.colorSpace = THREE.SRGBColorSpace;
  const pmrem = new THREE.PMREMGenerator(renderer);
  cena.environment = pmrem.fromEquirectangular(texturaCeu).texture;
  pmrem.dispose();
  cena.add(new THREE.HemisphereLight(0xfff4d6, 0x97791f, 2));
  const sol = new THREE.DirectionalLight(0xfff4d6, 2.6);
  sol.position.set(4, 8, 8);
  cena.add(sol);

  // ---------- Peças ----------
  const geo = { cone: new THREE.ConeGeometry(0.3, 0.95, 16) };
  // As cópias da textura só aparecem depois de avisadas de que a imagem carregou.
  const mapasEsperando = [];
  let comidaPronta = false;
  const texturaComida = new THREE.TextureLoader().load("img/comida.webp", () => {
    comidaPronta = true;
    mapasEsperando.splice(0).forEach((m) => { m.needsUpdate = true; });
  });
  texturaComida.colorSpace = THREE.SRGBColorSpace;

  // Cada alimento é uma imagem no estilo dos gatos, sempre de frente para a câmera.
  function criarAlimento(id) {
    const n = Math.max(0, ATLAS.indexOf(id));
    const mapa = texturaComida.clone();
    mapa.repeat.set(1 / COLUNAS_ATLAS, 1 / LINHAS_ATLAS);
    mapa.offset.set((n % COLUNAS_ATLAS) / COLUNAS_ATLAS, 1 - (Math.floor(n / COLUNAS_ATLAS) + 1) / LINHAS_ATLAS);
    if (comidaPronta) mapa.needsUpdate = true;
    else mapasEsperando.push(mapa);
    return new THREE.Sprite(new THREE.SpriteMaterial({ map: mapa, alphaTest: 0.15, toneMapped: false }));
  }

  // Estrelinha das faíscas e do brilho das moedas.
  const texturaFaisca = (() => {
    const t = document.createElement("canvas");
    t.width = t.height = 64;
    const x = t.getContext("2d");
    const g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, "#fff"); g.addColorStop(0.18, "rgba(255,255,255,.9)"); g.addColorStop(1, "rgba(255,255,255,0)");
    x.fillStyle = g;
    x.fillRect(0, 0, 64, 64);
    x.fillStyle = "#fff";
    x.beginPath();
    for (let i = 0; i < 8; i++) {
      const a = (i * Math.PI) / 4, r = i % 2 ? 4 : 31;
      x.lineTo(32 + Math.cos(a) * r, 32 + Math.sin(a) * r);
    }
    x.fill();
    return new THREE.CanvasTexture(t);
  })();

  // O perfil gira em torno do eixo Y; as duas faces usam a textura de frente, com o aro alto.
  function criarGeoMoeda(serrilha) {
    const voltas = fraco ? 24 : serrilha ? 96 : 48;
    const meio = [[0, 0.05], [0.37, 0.05], [0.39, 0.066], [0.46, 0.066], [0.49, 0.05], [0.5, 0.025]];
    const perfil = [...meio, ...meio.slice().reverse().map(([r, y]) => [r, -y])].map(([r, y]) => new THREE.Vector2(r, y));
    const g = new THREE.LatheGeometry(perfil, voltas);
    const pos = g.attributes.position, uv = g.attributes.uv;
    for (let i = 0; i < pos.count; i++) {
      let x = pos.getX(i), z = pos.getZ(i);
      const r = Math.hypot(x, z);
      if (serrilha && !fraco && r > 0.49 && Math.abs(pos.getY(i)) < 0.04) {
        const a = Math.atan2(z, x);
        const f = 1 + 0.014 * Math.sin(a * (voltas / 2));
        x *= f; z *= f;
        pos.setX(i, x); pos.setZ(i, z);
      }
      // A face de trás inverte o U, para o desenho não ficar espelhado.
      uv.setXY(i, 0.5 + (pos.getY(i) < 0 ? -x : x), 0.5 + z);
    }
    g.computeVertexNormals();
    return g;
  }

  function criarMatMoeda(tipo) {
    const t = fraco ? 128 : 256;
    const tela = () => {
      const m = document.createElement("canvas");
      m.width = m.height = t;
      return [m, m.getContext("2d", { willReadFrequently: true })];
    };
    const [telaCor, cor] = tela();
    cor.fillStyle = tipo.aro; cor.fillRect(0, 0, t, t);
    cor.fillStyle = tipo.miolo;
    cor.beginPath(); cor.arc(t / 2, t / 2, t * 0.345, 0, 7); cor.fill();
    const [telaAltura, altura] = tela();
    pintarRelevo(altura, t, tipo.desenho, "#000");
    const px = altura.getImageData(0, 0, t, t).data;
    const [telaNormal, normal] = tela();
    const saida = normal.createImageData(t, t);
    const alt = (i, j) => px[(((j + t) % t) * t + ((i + t) % t)) * 4];
    for (let j = 0; j < t; j++) for (let i = 0; i < t; i++) {
      const dx = (alt(i - 1, j) - alt(i + 1, j)) / 255, dy = (alt(i, j - 1) - alt(i, j + 1)) / 255;
      const k = (j * t + i) * 4, n = Math.hypot(dx * 2.4, dy * 2.4, 1);
      saida.data[k] = ((dx * 2.4) / n + 1) * 127.5;
      saida.data[k + 1] = ((dy * 2.4) / n + 1) * 127.5;
      saida.data[k + 2] = (1 / n + 1) * 127.5;
      saida.data[k + 3] = 255;
    }
    normal.putImageData(saida, 0, 0);
    // Campo mais fosco e relevo polido: é o que faz a moeda parecer moeda.
    const [telaBrilho, brilho] = tela();
    pintarRelevo(brilho, t, tipo.desenho, "#6b6b6b");
    brilho.globalCompositeOperation = "multiply";
    brilho.fillStyle = "#6b6b6b";
    brilho.fillRect(0, 0, t, t);
    const mapa = new THREE.CanvasTexture(telaCor);
    mapa.colorSpace = THREE.SRGBColorSpace;
    return new THREE.MeshPhysicalMaterial({
      map: mapa, normalMap: new THREE.CanvasTexture(telaNormal), roughnessMap: new THREE.CanvasTexture(telaBrilho),
      metalness: 1, roughness: 1, clearcoat: 0.3, clearcoatRoughness: 0.2,
      emissive: 0x4a3208, emissiveIntensity: 0.35,
    });
  }

  const tiposMoeda = MOEDAS.map((tipo) => ({ ...tipo, geo: criarGeoMoeda(tipo.serrilha), mat: criarMatMoeda(tipo) }));

  // Cestinha de mercado: parede vazada em duas camadas, para ter espessura, e borda dourada.
  const texturaTrama = (() => {
    const t = document.createElement("canvas");
    t.width = 1024; t.height = 256;
    const x = t.getContext("2d");
    x.fillStyle = "#fff"; x.fillRect(0, 0, 1024, 256);
    x.fillStyle = "#000";
    const colunas = 28, linhas = 4, l = 1024 / colunas, a = 180 / linhas;
    for (let i = 0; i < colunas; i++) for (let j = 0; j < linhas; j++) {
      x.beginPath();
      x.roundRect(i * l + l * 0.2, 34 + j * a + a * 0.14, l * 0.6, a * 0.72, 6);
      x.fill();
    }
    return new THREE.CanvasTexture(t);
  })();
  const matCesta = new THREE.MeshPhysicalMaterial({
    color: COR.cesta, roughness: 0.42, clearcoat: 0.5, clearcoatRoughness: 0.3,
    alphaMap: texturaTrama, alphaTest: 0.5, side: THREE.DoubleSide,
  });
  const matCestaSolida = new THREE.MeshPhysicalMaterial({ color: COR.cesta, roughness: 0.42, clearcoat: 0.5, clearcoatRoughness: 0.3 });
  const matBorda = new THREE.MeshPhysicalMaterial({ color: COR.ouro, metalness: 0.85, roughness: 0.28, clearcoat: 0.4 });
  const segmentos = fraco ? 32 : 64;

  function parede(folga) {
    const perfil = [[0.42, -0.28], [0.47, -0.24], [0.56, 0], [0.62, 0.28]].map(([r, y]) => new THREE.Vector2(r - folga, y));
    return new THREE.Mesh(new THREE.LatheGeometry(perfil, segmentos), matCesta);
  }

  function criarCesta() {
    const g = new THREE.Group();
    const fundo = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.025, segmentos), matCestaSolida);
    fundo.position.y = -0.28;
    const borda = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.032, 12, segmentos), matBorda);
    borda.rotation.x = Math.PI / 2;
    borda.position.y = 0.28;
    g.add(parede(0), parede(0.018), fundo, borda);
    // Duas alças, abertas para os lados, para não esconder o que cai na cesta.
    [1, -1].forEach((lado) => {
      const alca = new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.024, 10, 32, Math.PI), matCestaSolida);
      alca.position.set(0, 0.28, lado * 0.3);
      alca.rotation.x = lado * 0.5;
      g.add(alca);
    });
    return g;
  }

  // ---------- Chuva de moedas (e comida, conforme a pessoa rola a tela inicial) ----------
  const TOTAL = fraco ? 14 : 32;
  let usados = 0;
  tiposMoeda.forEach((tipo, n) => {
    tipo.quantos = n === tiposMoeda.length - 1 ? TOTAL - usados : Math.round(TOTAL * tipo.peso);
    usados += tipo.quantos;
    tipo.malha = new THREE.InstancedMesh(tipo.geo, tipo.mat, tipo.quantos);
    tipo.malha.frustumCulled = false;
    cena.add(tipo.malha);
  });
  const tipoDaPeca = tiposMoeda.flatMap((tipo) => Array.from({ length: tipo.quantos }, (_, indice) => ({ tipo, indice })));
  const auxiliar = new THREE.Object3D();
  // Sorteia para os tipos ficarem misturados na chuva; u é a posição dentro da coluna livre.
  const pecas = tipoDaPeca.sort(() => Math.random() - 0.5).map(({ tipo, indice }) => ({
    tipo, indice, u: Math.random(), y: Math.random(), z: -6 + Math.random() * 5,
    r: Math.random() * 6, rv: 0.6 + Math.random() * 1.6, oscila: Math.random() * 6, s: (0.72 + Math.random() * 0.5) * tipo.escala,
    v: 0, visivel: 1, encolhe: 1, ocupada: false, x: 0, py: 0,
  }));
  // As do fundo são menores na tela e caem mais devagar, o que dá profundidade.
  pecas.forEach((q) => { q.v = 0.05 + (q.z + 6) * 0.018; });

  const faiscas = Array.from({ length: fraco ? 12 : 28 }, () => {
    const obj = new THREE.Sprite(new THREE.SpriteMaterial({ map: texturaFaisca, blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false, transparent: true }));
    obj.visible = false;
    cena.add(obj);
    return { obj, vida: 0, total: 1, vx: 0, vy: 0, tamanho: 0.2 };
  });
  function faisca(x, y, z, cor, tamanho, vx, vy, vida) {
    const f = faiscas.find((item) => item.vida <= 0);
    if (!f) return;
    Object.assign(f, { vida, total: vida, vx, vy, tamanho });
    f.obj.material.color.set(cor);
    f.obj.position.set(x, y, z);
    f.obj.visible = true;
  }
  function atualizarFaiscas(dt) {
    for (const f of faiscas) {
      if (f.vida <= 0) continue;
      f.vida -= dt;
      f.vy -= 2.4 * dt;
      f.obj.position.x += f.vx * dt;
      f.obj.position.y += f.vy * dt;
      f.obj.scale.setScalar(Math.max(f.tamanho * Math.sin(Math.PI * Math.max(f.vida, 0) / f.total), 0.0001));
      if (f.vida <= 0) f.obj.visible = false;
    }
  }

  // ---------- Objetos presos aos palcos ----------
  const cestaHero = criarCesta();
  const cestaResultado = criarCesta();
  const moedaGrande = new THREE.Mesh(tiposMoeda[0].geo, tiposMoeda[0].mat);
  const radar = new THREE.Group();
  [0.45, 0.8, 1.15].forEach((r, i) => {
    const anel = new THREE.Mesh(new THREE.RingGeometry(r - 0.012, r + 0.012, 48), new THREE.MeshBasicMaterial({ color: i === 2 ? COR.ouro : COR.mata, side: THREE.DoubleSide, transparent: true, opacity: 0.8 }));
    radar.add(anel);
  });
  const varredura = new THREE.Mesh(new THREE.RingGeometry(0.02, 1.15, 32, 1, 0, 0.7), new THREE.MeshBasicMaterial({ color: COR.ouro, transparent: true, opacity: 0.28, side: THREE.DoubleSide, blending: THREE.AdditiveBlending, depthWrite: false }));
  radar.add(varredura);
  const pinos = new THREE.Group();
  radar.add(pinos);
  radar.rotation.x = -1.05;
  const matPino = new THREE.MeshStandardMaterial({ color: COR.ouro, metalness: 0.7, roughness: 0.3 });
  [[0.38, 1], [0.7, 2.6], [0.95, 4.1], [0.55, 5.3], [1.02, 0.5], [0.82, 3.4]].forEach(([r, a]) => {
    const pino = new THREE.Mesh(geo.cone, matPino);
    pino.scale.setScalar(0.22);
    pino.rotation.x = Math.PI + Math.PI / 2;
    pino.position.set(Math.cos(a) * r, Math.sin(a) * r, 0.11);
    pinos.add(pino);
  });
  // ---------- Cupom ----------
  // Papel térmico com a estrutura de um cupom brasileiro. É ilustração, e o papel diz isso.
  const cupom = new THREE.Group();
  const RECIBO_L = fraco ? 512 : 768, RECIBO_A = RECIBO_L * 2;
  const ITENS_RECIBO = [
    ["arroz", "Arroz 5 kg", "24,90"], ["feijao_carioca", "Feijão 1 kg", "7,99"], ["banana", "Banana 1 kg", "5,49"],
    ["ovo", "Ovos 12 un", "11,90"], ["leite", "Leite 1 L", "4,89"],
  ];
  const telaRecibo = document.createElement("canvas");
  telaRecibo.width = RECIBO_L; telaRecibo.height = RECIBO_A;
  const imagensRecibo = {};
  let reciboMarcados = 0, reciboCarimbo = false;

  // Só gera números repetíveis, para as fibras e o QR não mudarem a cada desenho.
  const repetivel = (semente) => () => { semente = (semente * 16807) % 2147483647; return semente / 2147483647; };

  function desenharRecibo() {
    const x = telaRecibo.getContext("2d");
    const k = RECIBO_L / 640;
    x.setTransform(k, 0, 0, k, 0, 0);
    const L = 640, A = 1280, TINTA = "#2d2a26", MONO = '"Courier New", ui-monospace, monospace';
    x.clearRect(0, 0, L, A);
    const papel = x.createLinearGradient(0, 0, L, A);
    papel.addColorStop(0, "#fffdf6"); papel.addColorStop(0.55, "#fbf7ec"); papel.addColorStop(1, "#f4eedf");
    x.fillStyle = papel;
    x.fillRect(0, 0, L, A);
    // Fibras do papel e a impressão levemente irregular da máquina térmica.
    const acaso = repetivel(4242);
    for (let i = 0; i < 900; i++) {
      x.fillStyle = `rgba(120,100,70,${0.015 + acaso() * 0.035})`;
      x.fillRect(acaso() * L, acaso() * A, 1 + acaso() * 9, 1);
    }
    x.fillStyle = TINTA;
    x.textBaseline = "alphabetic";
    const centro = (texto, y, fonte) => { x.font = fonte; x.textAlign = "center"; x.fillText(texto, L / 2, y); };
    const tracejado = (y) => {
      x.strokeStyle = "rgba(45,42,38,.55)"; x.lineWidth = 2; x.setLineDash([10, 8]);
      x.beginPath(); x.moveTo(44, y); x.lineTo(L - 44, y); x.stroke(); x.setLineDash([]);
    };
    if (imagensRecibo.gato && imagensRecibo.nome) {
      const g = imagensRecibo.gato, n = imagensRecibo.nome;
      const altG = 92, largG = (g.width / g.height) * altG, altN = 54, largN = (n.width / n.height) * altN;
      const ini = (L - largG - 12 - largN) / 2;
      x.drawImage(g, ini, 44, largG, altG);
      x.drawImage(n, ini + largG + 12, 64, largN, altN);
    } else centro("EconoMIA", 110, "800 58px Fredoka, Nunito, sans-serif");
    centro("CUPOM DE EXEMPLO", 182, `700 30px ${MONO}`);
    centro("SEM VALOR FISCAL", 216, `700 24px ${MONO}`);
    tracejado(240);
    x.font = `700 23px ${MONO}`;
    x.textAlign = "left"; x.fillText("ITEM", 44, 276);
    x.textAlign = "right"; x.fillText("R$", L - 44, 276);
    let y = 296;
    ITENS_RECIBO.forEach(([id, nome, valor], i) => {
      if (imagensRecibo.comida) {
        const n = ATLAS.indexOf(id), cel = imagensRecibo.comida.width / COLUNAS_ATLAS;
        x.drawImage(imagensRecibo.comida, (n % COLUNAS_ATLAS) * cel, Math.floor(n / COLUNAS_ATLAS) * cel, cel, cel, 44, y + 4, 62, 62);
      }
      x.fillStyle = TINTA;
      x.font = `700 31px ${MONO}`;
      x.textAlign = "left"; x.fillText(nome, 118, y + 46);
      x.textAlign = "right"; x.fillText(valor, L - 44, y + 46);
      if (i < reciboMarcados) {
        x.fillStyle = "#2f8a4c";
        x.font = "800 34px Nunito, sans-serif";
        x.textAlign = "right"; x.fillText("✓", L - 154, y + 47);
      }
      y += 74;
    });
    x.fillStyle = TINTA;
    tracejado(y + 12);
    x.font = `700 46px ${MONO}`;
    x.textAlign = "left"; x.fillText("TOTAL", 44, y + 72);
    x.textAlign = "right"; x.fillText("55,17", L - 44, y + 72);
    // Marca-texto, um pouco torto, como feito à mão.
    x.save();
    x.translate(L / 2, y + 112);
    x.rotate(-0.012);
    x.fillStyle = "rgba(245,207,95,.85)";
    x.beginPath(); x.roundRect(-274, -26, 548, 50, 10); x.fill();
    x.restore();
    x.fillStyle = TINTA;
    centro("Economia: R$ 8,40", y + 122, `700 31px ${MONO}`);
    tracejado(y + 158);
    // QR só de enfeite: tem cara de QR e não abre nada.
    const lado = 196, q = 21, m = lado / q, qx = (L - lado) / 2, qy = y + 178;
    const acasoQr = repetivel(977);
    const canto = (i, j) => (i < 8 && j < 8) || (i >= q - 8 && j < 8) || (i < 8 && j >= q - 8);
    for (let j = 0; j < q; j++) for (let i = 0; i < q; i++) if (acasoQr() > 0.5 && !canto(i, j)) x.fillRect(qx + i * m, qy + j * m, m + 0.3, m + 0.3);
    [[0, 0], [q - 7, 0], [0, q - 7]].forEach(([i, j]) => {
      x.fillRect(qx + i * m, qy + j * m, 7 * m, 7 * m);
      x.fillStyle = "#fbf7ec"; x.fillRect(qx + (i + 1) * m, qy + (j + 1) * m, 5 * m, 5 * m);
      x.fillStyle = TINTA; x.fillRect(qx + (i + 2) * m, qy + (j + 2) * m, 3 * m, 3 * m);
    });
    centro("0000 0000 0000 0000 0000", qy + lado + 36, `700 23px ${MONO}`);
    centro("Obrigado por economizar!", qy + lado + 72, "800 28px Nunito, sans-serif");
    if (reciboCarimbo) {
      x.save();
      x.translate(L / 2, 1190);
      x.rotate(-0.07);
      x.globalAlpha = 0.9;
      x.strokeStyle = x.fillStyle = "#2f8a4c";
      x.lineWidth = 7;
      x.beginPath(); x.roundRect(-150, -52, 300, 104, 16); x.stroke();
      x.lineWidth = 2.5;
      x.beginPath(); x.roundRect(-139, -41, 278, 82, 10); x.stroke();
      x.font = "800 40px Fredoka, Nunito, sans-serif";
      x.textAlign = "center";
      x.fillText("CONFERIDO", 0, 2);
      x.font = "700 21px Nunito, sans-serif";
      x.fillText("pelo Recibaldo", 0, 30);
      x.restore();
    }
    // Serrilha de papel destacado, em cima e embaixo.
    x.globalCompositeOperation = "destination-out";
    x.fillStyle = "#000";
    const dente = 22, altura = 15;
    for (let i = 0; i <= L / dente; i++) {
      x.beginPath(); x.moveTo(i * dente, -1); x.lineTo((i + 0.5) * dente, altura); x.lineTo((i + 1) * dente, -1); x.fill();
      x.beginPath(); x.moveTo(i * dente, A + 1); x.lineTo((i + 0.5) * dente, A - altura); x.lineTo((i + 1) * dente, A + 1); x.fill();
    }
    x.globalCompositeOperation = "source-over";
    texturaRecibo.needsUpdate = true;
  }

  const texturaRecibo = new THREE.CanvasTexture(telaRecibo);
  texturaRecibo.colorSpace = THREE.SRGBColorSpace;
  texturaRecibo.anisotropy = renderer.capabilities.getMaxAnisotropy();
  const RECIBO_LARG = 0.8, RECIBO_ALT = 1.6;
  const geoRecibo = new THREE.PlaneGeometry(RECIBO_LARG, RECIBO_ALT, 16, fraco ? 24 : 48);
  const baseRecibo = Float32Array.from(geoRecibo.attributes.position.array);
  const papelRecibo = new THREE.Mesh(geoRecibo, new THREE.MeshStandardMaterial({
    map: texturaRecibo, alphaTest: 0.5, side: THREE.DoubleSide, roughness: 0.82, envMapIntensity: 0.25,
    color: 0xa6a9b4, toneMapped: false,
  }));
  // Curvatura do papel: a ponta de baixo enrola um pouco, e o resto ondula devagar.
  const curvaRecibo = (px, py, t) => {
    const v = py / RECIBO_ALT + 0.5;
    const rolo = (1 - v) ** 3 * 0.42;
    const onda = Math.sin(v * 5 + t * 0.9) * 0.018;
    return rolo + onda + Math.cos(v * 3) * 0.02 - (px * px) * 0.14;
  };
  function dobrarRecibo(t) {
    const pos = geoRecibo.attributes.position;
    for (let i = 0; i < pos.count; i++) pos.setZ(i, curvaRecibo(baseRecibo[i * 3], baseRecibo[i * 3 + 1], t));
    pos.needsUpdate = true;
    geoRecibo.computeVertexNormals();
  }
  dobrarRecibo(0);

  // Sombra macia, para o papel descolar do fundo.
  const sombraRecibo = (() => {
    const t = document.createElement("canvas");
    t.width = 128; t.height = 256;
    const x = t.getContext("2d");
    x.filter = "blur(10px)";
    x.fillStyle = "#000";
    x.fillRect(22, 22, 84, 212);
    const m = new THREE.Mesh(new THREE.PlaneGeometry(RECIBO_LARG * 1.3, RECIBO_ALT * 1.16), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(t), transparent: true, opacity: 0.32, depthWrite: false, toneMapped: false }));
    m.position.set(0.05, -0.05, -0.14);
    return m;
  })();

  // Feixe de leitura: o miolo é forte e o brilho se espalha para os lados.
  const feixe = (() => {
    const t = document.createElement("canvas");
    t.width = 8; t.height = 128;
    const x = t.getContext("2d");
    const g = x.createLinearGradient(0, 0, 0, 128);
    g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(0.47, "rgba(245,207,95,.55)"); g.addColorStop(0.5, "#fff"); g.addColorStop(0.53, "rgba(245,207,95,.55)"); g.addColorStop(1, "rgba(0,0,0,0)");
    x.fillStyle = g;
    x.fillRect(0, 0, 8, 128);
    return new THREE.Mesh(new THREE.PlaneGeometry(RECIBO_LARG * 1.08, 0.3), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(t), color: COR.ouro, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false, toneMapped: false }));
  })();
  cupom.add(sombraRecibo, papelRecibo, feixe);

  [["gato", "img/logo-gato.webp"], ["nome", "img/logo-nome.webp"], ["comida", "img/comida.webp"]].forEach(([nome, url]) => {
    const im = new Image();
    im.onload = () => { imagensRecibo[nome] = im; desenharRecibo(); };
    im.src = url;
  });
  document.fonts?.ready.then(desenharRecibo);
  if (reduzirMovimento) { reciboMarcados = ITENS_RECIBO.length; reciboCarimbo = true; feixe.visible = false; }
  desenharRecibo();

  // O feixe desce, cada item ganha um ✓ e, no fim, vem o carimbo. Depois recomeça.
  const CICLO_RECIBO = 7, DESCIDA_RECIBO = 3;
  function atualizarRecibo(t) {
    if (reduzirMovimento) return;
    dobrarRecibo(t);
    const ciclo = t % CICLO_RECIBO;
    const u = Math.min(ciclo / DESCIDA_RECIBO, 1);
    const yFeixe = RECIBO_ALT / 2 - u * RECIBO_ALT;
    feixe.visible = ciclo < DESCIDA_RECIBO;
    feixe.position.set(0, yFeixe, curvaRecibo(0, yFeixe, t) + 0.05);
    feixe.material.opacity = Math.min(1, Math.min(u, 1 - u) * 14 + 0.05);
    // Os itens ficam entre 23% e 52% da altura do papel.
    const marcados = Math.max(0, Math.min(ITENS_RECIBO.length, Math.floor((u - 0.23) / 0.058)));
    const carimbo = ciclo >= DESCIDA_RECIBO;
    if (marcados !== reciboMarcados || carimbo !== reciboCarimbo) {
      reciboMarcados = marcados;
      reciboCarimbo = carimbo;
      desenharRecibo();
    }
  }

  cena.add(cestaHero, cestaResultado, moedaGrande, radar, cupom);

  // Com `grudar`, o objeto para logo abaixo da barra do topo até o palco inteiro passar.
  function ancorar(obj, seletor, escala, grudar, proporcao = 0.72) {
    const alvo = document.querySelector(seletor);
    const caixa = alvo?.offsetParent ? alvo.getBoundingClientRect() : null;
    if (!caixa || !caixa.height) { obj.visible = false; return; }
    let topo = caixa.top;
    if (grudar) {
      const teto = document.querySelector(".barra-topo")?.getBoundingClientRect().bottom ?? 0;
      const fim = alvo.closest(".hero").getBoundingClientRect().bottom;
      topo = Math.min(Math.max(topo, teto + 12), fim - caixa.height);
    }
    obj.visible = topo + caixa.height > -120 && topo < innerHeight + 120;
    if (!obj.visible) return;
    obj.position.x = ((caixa.left + caixa.width / 2) / innerWidth - 0.5) * larguraMundo;
    obj.position.y = -((topo + caixa.height / 2) / innerHeight - 0.5) * alturaMundo;
    // A menor medida do palco manda, para o objeto nunca passar da largura da tela.
    const medida = Math.min(caixa.height, caixa.width * proporcao);
    obj.scale.setScalar((medida / innerHeight) * alturaMundo * escala);
  }

  // ---------- A cesta recebe os alimentos de verdade ----------
  const caindo = [];
  const estouro = [];

  function encherCesta({ itens, animar, coube }) {
    caindo.splice(0).forEach((c) => cestaResultado.remove(c.obj));
    estouro.splice(0).forEach((m) => cestaResultado.remove(m.obj));
    const lista = itens.slice(0, fraco ? 14 : 24);
    lista.forEach((id, i) => {
      const obj = criarAlimento(id);
      const a = i * 2.4, r = 0.36 * Math.sqrt((i + 0.5) / lista.length);
      const alvoY = -0.12 + (i / lista.length) * 0.42;
      obj.scale.setScalar(0.34);
      obj.position.set(Math.cos(a) * r, animar && !reduzirMovimento ? 2.8 + i * 0.25 : alvoY, Math.sin(a) * r);
      obj.material.rotation = Math.sin(a) * 0.5;
      cestaResultado.add(obj);
      caindo.push({ obj, alvoY, v: 0, parado: !animar || reduzirMovimento });
    });
    if (animar && coube && !reduzirMovimento) {
      for (let i = 0; i < (fraco ? 12 : 26); i++) {
        const obj = new THREE.Mesh(tiposMoeda[0].geo, tiposMoeda[0].mat);
        obj.scale.setScalar(0);
        obj.position.y = 0.3;
        cestaResultado.add(obj);
        const a = Math.random() * 6.28;
        estouro.push({ obj, espera: 1 + Math.random() * 0.5, vx: Math.cos(a) * (0.5 + Math.random()), vy: 1.6 + Math.random() * 1.3, vz: Math.sin(a) * 0.6, vida: 1.7 });
      }
    }
  }
  document.addEventListener("economia:cesta", (e) => encherCesta(e.detail));
  if (window.economia?.cesta) encherCesta({ ...window.economia.cesta, animar: false });

  let mouseX = 0, mouseY = 0;
  addEventListener("pointermove", (e) => {
    mouseX = e.clientX / innerWidth - 0.5;
    mouseY = e.clientY / innerHeight - 0.5;
  }, { passive: true });

  // ---------- Quadro a quadro ----------
  let ultimo = performance.now(), tempo = 0, quadros = 0, inicioMedida = ultimo, resolucaoReduzida = false;

  // Título, texto e botão: moeda nenhuma passa por trás deles.
  const zonasSeguras = () => [...document.querySelectorAll("#palco-hero h1, #palco-hero .hero-texto, #palco-hero .botao-hero")]
    .map((el) => el.getBoundingClientRect()).filter((z) => z.height);

  // ---------- Moeda vira comida, comida cai na cesta, cesta alimenta o anel ----------
  const easeBack = (t) => 1 + 3.2 * (t - 1) ** 3 + 2.2 * (t - 1) ** 2;
  const QUANTAS_VAGAS = fraco ? 10 : 14;
  const VAGAS = Array.from({ length: QUANTAS_VAGAS }, (_, i) => {
    const a = i * 2.4, r = 0.4 * Math.sqrt((i % 7 + 0.5) / 7);
    return { x: Math.cos(a) * r, y: -0.14 + (i / QUANTAS_VAGAS) * 0.48, z: Math.sin(a) * r * 0.6 };
  });
  const TAMANHO_COMIDA = 0.34;
  const naCesta = [];
  const voando = [];
  let esperaProxima = 0.6, cheiaHa = 0, wobble = 0, wobbleV = 0, proximoBrilho = 0.4, avisouCheia = false;
  const vagaLivre = () => VAGAS.findIndex((_, i) => !naCesta.some((c) => c.vaga === i) && !voando.some((c) => c.vaga === i));

  function iniciarTransformacao() {
    const vaga = vagaLivre();
    if (vaga < 0) return;
    const opcoes = pecas.filter((q) => !q.ocupada && q.visivel > 0.9 && q.y > 0.15 && q.y < 0.85);
    if (!opcoes.length) return;
    const q = opcoes[Math.floor(Math.random() * opcoes.length)];
    q.ocupada = true;
    const id = ATLAS[Math.floor(Math.random() * ATLAS.length)];
    const obj = criarAlimento(id);
    obj.visible = false;
    cena.add(obj);
    voando.push({ q, id, obj, vaga, fase: "antecipa", t: 0, de: new THREE.Vector3(), para: new THREE.Vector3() });
  }

  function recompensa(id) {
    document.dispatchEvent(new CustomEvent("economia:comida-caiu"));
    // Só voa até o anel se ele estiver na tela.
    const i = anelDe(id);
    const anel = document.querySelectorAll("#inicio-metas .mini-anel .anel")[i];
    const destino = anel?.offsetParent ? anel.getBoundingClientRect() : null;
    if (!destino || destino.bottom < 0 || destino.top > innerHeight) return;
    const px = (cestaHero.position.x / larguraMundo + 0.5) * innerWidth;
    const py = (0.5 - cestaHero.position.y / alturaMundo) * innerHeight;
    const ponto = document.createElement("span");
    ponto.className = "faisca-anel";
    ponto.style.background = ANEIS[i].cor;
    ponto.style.left = `${px}px`;
    ponto.style.top = `${py}px`;
    document.body.append(ponto);
    const dx = destino.left + destino.width / 2 - px, dy = destino.top + destino.height / 2 - py;
    ponto.animate(
      [{ transform: "translate(-50%, -50%) scale(1)" }, { transform: `translate(calc(${dx}px - 50%), calc(${dy}px - 50%)) scale(0.5)` }],
      { duration: 620, easing: "cubic-bezier(.45,.05,.3,1)" },
    ).onfinish = () => {
      ponto.remove();
      anel.animate([{ transform: "scale(1)" }, { transform: "scale(1.06)" }, { transform: "scale(1)" }], { duration: 320, easing: "ease-out" });
    };
  }

  function atualizarVoos(dt, noHero, progresso) {
    if (!noHero || !cestaHero.visible) {
      // Saiu da tela inicial: encerra o que estava no ar, sem deixar comida solta.
      voando.splice(0).forEach((v) => { cena.remove(v.obj); v.obj.material.map.dispose(); v.obj.material.dispose(); v.q.ocupada = false; v.q.encolhe = 1; v.q.rv = Math.min(v.q.rv, 2.2); });
      return;
    }
    esperaProxima -= dt * (1 + progresso * 7);
    // A rolagem acelera: no fim da tela inicial, a cesta já está cheia.
    const meta = Math.floor(progresso * VAGAS.length);
    if ((esperaProxima <= 0 || naCesta.length + voando.length < meta) && voando.length < 4) {
      iniciarTransformacao();
      esperaProxima = 1.7;
    }
    const escala = cestaHero.scale.x;
    for (let i = voando.length - 1; i >= 0; i--) {
      const v = voando[i];
      v.t += dt;
      if (v.fase === "antecipa") {
        const t = Math.min(v.t / 0.15, 1);
        v.q.rv = 2 + t * 10;
        v.q.encolhe = 1 - t * 0.1;
        if (t === 1) {
          v.fase = "pop"; v.t = 0;
          v.de.set(v.q.x, v.q.py, v.q.z);
          v.obj.position.copy(v.de);
          v.obj.visible = true;
          for (let k = 0; k < (fraco ? 4 : 9); k++) {
            const a = (k / 9) * 6.28 + Math.random();
            faisca(v.de.x, v.de.y, v.de.z, k % 3 ? 0xf5cf5f : ANEIS[anelDe(v.id)].cor, 0.32, Math.cos(a) * 2.2, Math.sin(a) * 2.2 + 0.8, 0.5);
          }
        }
      } else if (v.fase === "pop") {
        const t = Math.min(v.t / 0.25, 1);
        v.q.encolhe = 0.9 * (1 - t) ** 2;
        v.obj.scale.setScalar(Math.max(easeBack(t) * TAMANHO_COMIDA * escala, 0.0001));
        if (t === 1) { v.fase = "queda"; v.t = 0; }
      } else if (v.fase === "queda") {
        const t = Math.min(v.t / 0.55, 1);
        const vaga = VAGAS[v.vaga];
        v.para.set(vaga.x, vaga.y, vaga.z).applyMatrix4(cestaHero.matrixWorld);
        const queda = t * t;
        v.obj.position.lerpVectors(v.de, v.para, queda);
        v.obj.position.y += Math.sin(Math.PI * t) * 0.6;
        // Estica no sentido da queda.
        const estica = Math.sin(Math.PI * t) * 0.16;
        v.obj.scale.set(TAMANHO_COMIDA * escala * (1 - estica), TAMANHO_COMIDA * escala * (1 + estica), 1);
        v.obj.material.rotation = t * 0.5;
        if (t === 1) {
          cena.remove(v.obj);
          cestaHero.add(v.obj);
          v.obj.position.set(vaga.x, vaga.y, vaga.z);
          naCesta.push({ obj: v.obj, vaga: v.vaga, impacto: 0.22, sai: 0 });
          wobbleV += 2.6 * (Math.random() < 0.5 ? -1 : 1);
          recompensa(v.id);
          // A moeda volta do alto da tela.
          Object.assign(v.q, { ocupada: false, encolhe: 1, y: 1.1, u: Math.random(), rv: 0.6 + Math.random() * 1.6, visivel: 0 });
          voando.splice(i, 1);
        }
      }
    }
    // Impacto: amassa e quica um pouco ao tocar o fundo da vaga.
    for (let i = naCesta.length - 1; i >= 0; i--) {
      const c = naCesta[i];
      const vaga = VAGAS[c.vaga];
      if (c.sai > 0) {
        c.sai -= dt * 2.5;
        c.obj.scale.setScalar(Math.max(c.sai, 0.0001) * TAMANHO_COMIDA);
        if (c.sai <= 0) { cestaHero.remove(c.obj); c.obj.material.map.dispose(); c.obj.material.dispose(); naCesta.splice(i, 1); }
        continue;
      }
      if (c.impacto > 0) {
        c.impacto = Math.max(0, c.impacto - dt);
        const t = 1 - c.impacto / 0.22;
        const amassa = Math.sin(Math.PI * t) * 0.15;
        c.obj.scale.set(TAMANHO_COMIDA * (1 + amassa), TAMANHO_COMIDA * (1 - amassa), 1);
        c.obj.position.y = vaga.y + Math.sin(Math.PI * t) * 0.04;
      }
    }
    if (!avisouCheia && naCesta.length === VAGAS.length) {
      avisouCheia = true;
      cheiaHa = 0;
      document.dispatchEvent(new CustomEvent("economia:cesta-cheia"));
    }
    if (avisouCheia && (cheiaHa += dt) > 6 && progresso < 0.3) {
      // Depois de um tempo cheia, abre espaço para a história recomeçar.
      avisouCheia = false;
      naCesta.slice(0, 5).forEach((c) => { c.sai = 1; });
    }
    proximoBrilho -= dt;
    if (proximoBrilho <= 0) {
      proximoBrilho = 0.3 + Math.random() * 0.5;
      const q = pecas[Math.floor(Math.random() * pecas.length)];
      if (q.visivel > 0.9) faisca(q.x, q.py, q.z + 0.3, 0xffffff, 0.5 * q.s, 0, 0, 0.14);
    }
  }

  function atualizarChuva(dt) {
    const aba = window.economia?.aba ?? "inicio";
    const hero = document.querySelector("#palco-hero");
    const caixa = aba === "inicio" && hero?.offsetParent ? hero.getBoundingClientRect() : null;
    const noHero = !!caixa && caixa.bottom > 40;
    const p = caixa ? Math.min(1, Math.max(0, -caixa.top / (caixa.height * 0.6))) : 0;
    // Com menos movimento pedido, não há chuva: a cesta aparece cheia e parada.
    const ativos = reduzirMovimento ? 0 : noHero ? TOTAL : Math.min(6, TOTAL);
    const zonas = noHero ? zonasSeguras() : [];
    // Em tela larga, a chuva fica só na coluna à direita do texto.
    const conteudo = noHero && innerWidth >= 1024 ? document.querySelector("#palco-hero .hero-conteudo")?.getBoundingClientRect() : null;
    const esquerda = conteudo ? conteudo.right / innerWidth - 0.5 + 0.03 : -0.5;
    pecas.forEach((q, i) => {
      if (!q.ocupada) q.y -= q.v * dt;
      if (q.y < -0.1) { q.y = 1.1; q.u = Math.random(); }
      q.r += q.rv * dt;
      q.oscila += dt * 1.3;
      const profundidade = (camera.position.z - q.z) / camera.position.z;
      let x = (esquerda + q.u * (0.48 - esquerda)) * larguraMundo * profundidade;
      const y = (q.y - 0.5) * alturaMundo * profundidade;
      if (!noHero) x = (i % 2 ? 1 : -1) * (0.36 + (q.u * 0.12)) * larguraMundo * profundidade;
      q.x = x;
      q.py = y;
      // Longe do texto a moeda aparece; perto dele, encolhe até sumir.
      const px = (x / (larguraMundo * profundidade) + 0.5) * innerWidth, py = (0.5 - y / (alturaMundo * profundidade)) * innerHeight;
      const folga = 46;
      const naZona = zonas.some((r) => px > r.left - folga && px < r.right + folga && py > r.top - folga && py < r.bottom + folga);
      q.visivel += ((naZona || i >= ativos ? 0 : 1) - q.visivel) * Math.min(1, dt * 9);
      auxiliar.position.set(x, y, q.z);
      // Duas rotações com oscilação: a moeda nunca gira em um eixo só.
      auxiliar.rotation.set(Math.PI / 2 + q.r, Math.sin(q.oscila) * 0.5, Math.cos(q.oscila * 0.7) * 0.4);
      auxiliar.scale.setScalar(Math.max(q.s * q.visivel * q.encolhe * (noHero ? 1 : 0.7), 0.0001));
      auxiliar.updateMatrix();
      q.tipo.malha.setMatrixAt(q.indice, auxiliar.matrix);
    });
    tiposMoeda.forEach((tipo) => { tipo.malha.instanceMatrix.needsUpdate = true; });
    if (!reduzirMovimento) {
      atualizarVoos(dt, noHero, p);
      atualizarFaiscas(dt);
    }
  }

  if (reduzirMovimento) {
    VAGAS.forEach((vaga, i) => {
      const obj = criarAlimento(ATLAS[i % ATLAS.length]);
      obj.position.set(vaga.x, vaga.y, vaga.z);
      obj.scale.set(TAMANHO_COMIDA, TAMANHO_COMIDA, 1);
      cestaHero.add(obj);
    });
  }

  function quadro(agora) {
    requestAnimationFrame(quadro);
    if (document.hidden) { ultimo = agora; return; }
    const dt = Math.min((agora - ultimo) / 1000, 0.05);
    ultimo = agora;
    tempo += dt;
    const aba = window.economia?.aba ?? "inicio";

    atualizarChuva(dt);
    camera.position.x += (mouseX * 0.8 - camera.position.x) * 0.04;
    camera.position.y += (-mouseY * 0.5 - camera.position.y) * 0.04;
    camera.lookAt(0, 0, 0);

    ancorar(cestaHero, aba === "inicio" ? "#ancora-cesta-hero" : "#nada", 0.95, true);
    ancorar(cestaResultado, aba === "cesta" ? "#palco-cesta" : "#nada", 0.8);
    ancorar(radar, aba === "perto" ? "#palco-perto" : "#nada", 0.62);
    ancorar(cupom, aba === "cupom" ? "#palco-cupom" : "#nada", 0.54, false, 2);
    ancorar(moedaGrande, aba === "precos" ? "#palco-precos" : "#nada", 0.72);

    // A cesta balança sem dar a volta, com a boca sempre para a câmera.
    wobbleV += (-wobble * 90 - wobbleV * 7) * dt;
    wobble += wobbleV * dt;
    cestaHero.rotation.y = Math.sin(tempo * 0.5) * 0.2;
    cestaHero.rotation.x = 0.34;
    cestaHero.rotation.z = wobble * 0.14;
    cestaResultado.rotation.y = Math.sin(tempo * 0.4) * 0.25;
    cestaResultado.rotation.x = 0.34;
    moedaGrande.rotation.set(Math.PI / 2 + Math.sin(tempo) * 0.2, 0, Math.sin(tempo * 0.8) * 0.5);
    varredura.rotation.z = -tempo * 1.2;
    pinos.children.forEach((pino, i) => { pino.position.z = 0.11 + Math.abs(Math.sin(tempo * 1.5 + i)) * 0.06; });
    cupom.rotation.y = Math.sin(tempo * 0.5) * 0.22;
    cupom.rotation.x = -0.06 + Math.sin(tempo * 0.37) * 0.04;
    cupom.rotation.z = 0.04;
    if (cupom.visible) atualizarRecibo(tempo);

    for (const c of caindo) {
      if (c.parado) continue;
      c.v -= 7 * dt;
      c.obj.position.y += c.v * dt;
      c.obj.material.rotation += dt * 2;
      if (c.obj.position.y <= c.alvoY) {
        c.obj.position.y = c.alvoY;
        if (Math.abs(c.v) < 0.5) c.parado = true;
        c.v = -c.v * 0.28;
      }
    }
    for (let i = estouro.length - 1; i >= 0; i--) {
      const m = estouro[i];
      if ((m.espera -= dt) > 0) continue;
      m.vida -= dt;
      m.vy -= 3.2 * dt;
      m.obj.position.x += m.vx * dt;
      m.obj.position.y += m.vy * dt;
      m.obj.position.z += m.vz * dt;
      m.obj.rotation.x += dt * 8;
      m.obj.scale.setScalar(Math.max(Math.min(m.vida, 0.14), 0));
      if (m.vida <= 0) { cestaResultado.remove(m.obj); estouro.splice(i, 1); }
    }

    renderer.render(cena, camera);

    // Se o aparelho não acompanhar, reduz a resolução, sem desligar o 3D.
    if (++quadros === 90) {
      const fps = 90000 / (agora - inicioMedida);
      quadros = 0;
      inicioMedida = agora;
      if (fps < 24 && !document.hidden && !resolucaoReduzida) {
        resolucaoReduzida = true;
        renderer.setPixelRatio(1);
        redimensionar();
      }
    }
  }
  requestAnimationFrame(quadro);
}

// Espera o site abrir antes de baixar o 3D, para não atrasar quem só quer usar o app.
const comecar = () => iniciar().catch((e) => console.warn("3D desligado:", e.message));
if ("requestIdleCallback" in window) requestIdleCallback(comecar, { timeout: 1500 });
else setTimeout(comecar, 400);
