// Cena 3D da EconoMIA (tópico 24): moedas que viram comida e caem na cesta.
// O canvas fica fixo atrás do site, e os objetos seguem "palcos" do HTML, então
// rolam junto com a página. Sem WebGL, em aparelho fraco ou com economia de dados,
// o Three.js nem é baixado e o site continua igual, só sem o 3D.

const reduzirMovimento = matchMedia("(prefers-reduced-motion: reduce)").matches;

function efeitosPermitidos() {
  const preferencia = window.economia?.efeitos ?? "auto";
  if (preferencia === "desligado") return false;
  const teste = document.createElement("canvas");
  if (!teste.getContext("webgl2") && !teste.getContext("webgl")) return false;
  if (preferencia === "ligado") return true;
  const rede = navigator.connection;
  if (reduzirMovimento || rede?.saveData || /(^|-)2g$/.test(rede?.effectiveType ?? "")) return false;
  if ((navigator.deviceMemory ?? 8) <= 2 || (navigator.hardwareConcurrency ?? 8) <= 2) return false;
  return true;
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
  if (!efeitosPermitidos()) return;
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
  renderer.setPixelRatio(fraco ? 1 : Math.min(devicePixelRatio, 1.5));
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
  const cupom = new THREE.Group();
  const papel = (() => {
    const t = document.createElement("canvas");
    t.width = 256; t.height = 512;
    const x = t.getContext("2d");
    x.fillStyle = "#fbf8f0"; x.fillRect(0, 0, 256, 512);
    x.fillStyle = "#3a4a42";
    for (let y = 40; y < 320; y += 26) x.fillRect(24, y, 110 + ((y * 7) % 90), 9);
    for (let i = 0; i < 12; i++) for (let j = 0; j < 12; j++) if ((i * 7 + j * 13 + i * j) % 3) x.fillRect(68 + i * 10, 360 + j * 10, 10, 10);
    const tx = new THREE.CanvasTexture(t);
    tx.colorSpace = THREE.SRGBColorSpace;
    return new THREE.Mesh(new THREE.PlaneGeometry(0.75, 1.5), new THREE.MeshStandardMaterial({ map: tx, side: THREE.DoubleSide, roughness: 0.9 }));
  })();
  const feixe = new THREE.Mesh(new THREE.PlaneGeometry(0.95, 0.05), new THREE.MeshBasicMaterial({ color: COR.ouro, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false }));
  feixe.position.z = 0.02;
  cupom.add(papel, feixe);
  cena.add(cestaHero, cestaResultado, moedaGrande, radar, cupom);

  // Com `grudar`, o objeto para logo abaixo da barra do topo até o palco inteiro passar.
  function ancorar(obj, seletor, escala, grudar) {
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
    const medida = Math.min(caixa.height, caixa.width * 0.72);
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
  let ultimo = performance.now(), tempo = 0, quadros = 0, inicioMedida = ultimo, avisos = 0, ligado = true;

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
    if (!ligado) return;
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
    ancorar(cupom, aba === "cupom" ? "#palco-cupom" : "#nada", 0.62);
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
    cupom.rotation.y = Math.sin(tempo * 0.6) * 0.3;
    cupom.rotation.z = 0.06;
    feixe.position.y = Math.sin(tempo * 1.4) * 0.7;

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

    // Se o aparelho não acompanhar, primeiro reduz a resolução; depois desliga o 3D.
    if (++quadros === 90) {
      const fps = 90000 / (agora - inicioMedida);
      quadros = 0;
      inicioMedida = agora;
      if (fps < 24 && !document.hidden) {
        avisos++;
        if (avisos === 1) { renderer.setPixelRatio(1); redimensionar(); }
        if (avisos >= 3) {
          ligado = false;
          document.documentElement.classList.remove("com-3d");
          canvas.remove();
          renderer.dispose();
        }
      } else avisos = Math.max(0, avisos - 1);
    }
  }
  requestAnimationFrame(quadro);
}

// Espera o site abrir antes de baixar o 3D, para não atrasar quem só quer usar o app.
const comecar = () => iniciar().catch((e) => console.warn("3D desligado:", e.message));
if ("requestIdleCallback" in window) requestIdleCallback(comecar, { timeout: 1500 });
else setTimeout(comecar, 400);
