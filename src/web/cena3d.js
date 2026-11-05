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

// Cores dos alimentos e da marca.
const COR = {
  ouro: 0xf5cf5f, mata: 0x6f8f4f, cesta: 0x2f6b3f, floresta: 0x463708, creme: 0xfaf5ea, tomate: 0xd93b2b, laranja: 0xf08a24,
  banana: 0xf5cf3a, terra: 0x9a6b3f, cebola: 0xb98a5a, folha: 0x6fb34a, abobora: 0xd97b1f, pacote: 0xe9e2d0,
  feijao: 0x6d3f25, preto: 0x2a2a33, macarrao: 0xe8c04f, carne: 0xa8413a, frango: 0xe0b483, lata: 0xb9c2c9, leite: 0xf4f6f4,
};

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
  const fosco = (cor) => new THREE.MeshStandardMaterial({ color: cor, roughness: 0.7, flatShading: true });
  const geo = {
    bola: new THREE.IcosahedronGeometry(0.5, 1), oval: new THREE.IcosahedronGeometry(0.5, 2), caixa: new THREE.BoxGeometry(0.7, 0.9, 0.4),
    pacote: new THREE.BoxGeometry(0.75, 0.55, 0.35), cone: new THREE.ConeGeometry(0.3, 0.95, 7), lata: new THREE.CylinderGeometry(0.4, 0.4, 0.22, 12),
    garrafa: new THREE.CapsuleGeometry(0.22, 0.65, 3, 8), pao: new THREE.CapsuleGeometry(0.26, 0.5, 3, 8), folha: new THREE.ConeGeometry(0.14, 0.3, 5),
    banana: new THREE.TubeGeometry(new THREE.CatmullRomCurve3([new THREE.Vector3(-0.5, 0.2, 0), new THREE.Vector3(-0.2, -0.2, 0), new THREE.Vector3(0.25, -0.22, 0), new THREE.Vector3(0.55, 0.15, 0)]), 12, 0.13, 7),
  };
  const receita = {
    tomate: [geo.bola, COR.tomate, 0.95, COR.folha], laranja: [geo.bola, COR.laranja, 0.95], maca: [geo.bola, COR.tomate, 0.9, COR.folha],
    banana: [geo.banana, COR.banana, 1], ovo: [geo.oval, COR.creme, 0.8, null, [1, 1.28, 1]], batata: [geo.bola, COR.terra, 0.85, null, [1.25, 0.85, 0.9]],
    mandioca: [geo.pao, COR.terra, 1], cenoura: [geo.cone, COR.laranja, 1, COR.folha], cebola: [geo.bola, COR.cebola, 0.85], repolho: [geo.bola, COR.folha, 1.05],
    abobora: [geo.bola, COR.abobora, 1, COR.folha, [1.2, 0.8, 1.2]], arroz: [geo.pacote, COR.pacote, 1], feijao_carioca: [geo.pacote, COR.feijao, 1], feijao_preto: [geo.pacote, COR.preto, 1],
    lentilha: [geo.pacote, COR.terra, 0.9], macarrao: [geo.pacote, COR.macarrao, 1], farinha_mandioca: [geo.pacote, COR.cebola, 1], aveia: [geo.caixa, COR.creme, 0.8], acucar: [geo.pacote, COR.leite, 0.95],
    leite: [geo.caixa, COR.leite, 1], oleo_soja: [geo.garrafa, COR.banana, 1], sardinha: [geo.lata, COR.lata, 1], frango_coxa: [geo.bola, COR.frango, 0.95], frango_peito: [geo.bola, COR.frango, 0.95, null, [1.2, 0.75, 0.9]],
    patinho: [geo.bola, COR.carne, 0.95, null, [1.2, 0.7, 1]], lombo_porco: [geo.bola, COR.carne, 0.95, null, [1.3, 0.7, 0.9]], mucarela: [geo.caixa, COR.banana, 0.75], pao_frances: [geo.pao, COR.frango, 1],
  };
  const materiais = new Map();
  const material = (cor) => materiais.get(cor) ?? (materiais.set(cor, fosco(cor)), materiais.get(cor));

  function criarAlimento(id) {
    const [g, cor, escala, topo, deforma] = receita[id] ?? [geo.bola, COR.folha, 0.9];
    const grupo = new THREE.Group();
    const corpo = new THREE.Mesh(g, material(cor));
    corpo.scale.setScalar(escala);
    if (deforma) corpo.scale.set(escala * deforma[0], escala * deforma[1], escala * deforma[2]);
    grupo.add(corpo);
    if (topo) {
      const f = new THREE.Mesh(geo.folha, material(topo));
      f.position.y = g === geo.cone ? 0.55 : 0.5 * escala * (deforma?.[1] ?? 1);
      grupo.add(f);
    }
    return grupo;
  }

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
  const IDS = ["tomate", "banana", "ovo", "arroz", "cenoura", "laranja", "feijao_carioca", "repolho", "abobora", "leite", "frango_coxa", "macarrao"];
  // Sorteia para os tipos ficarem misturados na chuva; u é a posição dentro da coluna livre.
  const pecas = tipoDaPeca.sort(() => Math.random() - 0.5).map(({ tipo, indice }, i) => ({
    tipo, indice, u: Math.random(), y: Math.random(), z: -6 + Math.random() * 5,
    r: Math.random() * 6, rv: 0.6 + Math.random() * 1.6, oscila: Math.random() * 6, s: (0.72 + Math.random() * 0.5) * tipo.escala,
    v: 0, visivel: 1,
    comida: i < (fraco ? 6 : 12) ? criarAlimento(IDS[i % IDS.length]) : null,
  }));
  // As do fundo são menores na tela e caem mais devagar, o que dá profundidade.
  pecas.forEach((q) => { q.v = 0.05 + (q.z + 6) * 0.018; });
  const comidaChuva = new THREE.Group();
  pecas.forEach((p) => p.comida && comidaChuva.add(p.comida));
  cena.add(comidaChuva);

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
      obj.scale.setScalar(0.2);
      obj.position.set(Math.cos(a) * r, animar && !reduzirMovimento ? 2.8 + i * 0.25 : alvoY, Math.sin(a) * r);
      obj.rotation.set(a, a * 0.6, 0);
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

  function atualizarChuva(dt) {
    const aba = window.economia?.aba ?? "inicio";
    const hero = document.querySelector("#palco-hero");
    const caixa = aba === "inicio" && hero?.offsetParent ? hero.getBoundingClientRect() : null;
    const noHero = !!caixa && caixa.bottom > 40;
    const p = caixa ? Math.min(1, Math.max(0, -caixa.top / (caixa.height * 0.55))) : 0;
    const e = p * p * (3 - 2 * p);
    // Fora do hero, poucas moedas nas beiradas, para não atrapalhar a leitura.
    const ativos = noHero ? TOTAL : Math.min(6, TOTAL);
    const alvo = cestaHero.position;
    const zonas = noHero ? zonasSeguras() : [];
    // Em tela larga, a chuva fica só na coluna à direita do texto.
    const conteudo = noHero && innerWidth >= 1024 ? document.querySelector("#palco-hero .hero-conteudo")?.getBoundingClientRect() : null;
    const esquerda = conteudo ? conteudo.right / innerWidth - 0.5 + 0.03 : -0.5;
    pecas.forEach((q, i) => {
      q.y -= q.v * dt;
      if (q.y < -0.1) { q.y = 1.1; q.u = Math.random(); }
      q.r += q.rv * dt;
      q.oscila += dt * 1.3;
      const profundidade = (camera.position.z - q.z) / camera.position.z;
      let x = (esquerda + q.u * (0.48 - esquerda)) * larguraMundo * profundidade;
      let y = (q.y - 0.5) * alturaMundo * profundidade;
      let z = q.z;
      if (!noHero) x = (i % 2 ? 1 : -1) * (0.36 + (q.u * 0.12)) * larguraMundo * profundidade;
      if (noHero && cestaHero.visible) {
        const giro = i * 2.4, raio = 0.35 * cestaHero.scale.x * Math.sqrt((i % 16 + 0.5) / 16);
        x += (alvo.x + Math.cos(giro) * raio - x) * e;
        y += (alvo.y + cestaHero.scale.x * (-0.1 + (i % 16) * 0.024) - y) * e;
        z += (Math.sin(giro) * raio - z) * e;
      }
      // Longe do texto a moeda aparece; perto dele, encolhe até sumir.
      const px = (x / (larguraMundo * profundidade) + 0.5) * innerWidth, py = (0.5 - y / (alturaMundo * profundidade)) * innerHeight;
      const folga = 46;
      const naZona = zonas.some((r) => px > r.left - folga && px < r.right + folga && py > r.top - folga && py < r.bottom + folga);
      q.visivel += ((naZona || i >= ativos ? 0 : 1) - q.visivel) * Math.min(1, dt * 9);
      auxiliar.position.set(x, y, z);
      // Duas rotações com oscilação: a moeda nunca gira em um eixo só.
      auxiliar.rotation.set(Math.PI / 2 + q.r, Math.sin(q.oscila) * 0.5, Math.cos(q.oscila * 0.7) * 0.4);
      const escalaMoeda = (q.comida && noHero ? 1 - e : 1) * q.s * q.visivel * (noHero ? 1 : 0.7);
      // As moedas somem ao entrar na cesta; quem fica é a comida.
      auxiliar.scale.setScalar(Math.max(escalaMoeda * (noHero ? 1 - e : 1), 0.0001));
      auxiliar.updateMatrix();
      q.tipo.malha.setMatrixAt(q.indice, auxiliar.matrix);
      if (q.comida) {
        q.comida.visible = noHero && e > 0.02;
        q.comida.position.set(x, y, z);
        q.comida.rotation.set(q.r * (1 - e), q.r * 0.7 * (1 - e), 0);
        q.comida.scale.setScalar(Math.max(e * (cestaHero.scale.x * 0.26 || 0.6), 0.0001));
      }
    });
    tiposMoeda.forEach((tipo) => { tipo.malha.instanceMatrix.needsUpdate = true; });
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
    cestaHero.rotation.y = Math.sin(tempo * 0.5) * 0.2;
    cestaHero.rotation.x = 0.34;
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
      c.obj.rotation.x += dt * 3;
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
