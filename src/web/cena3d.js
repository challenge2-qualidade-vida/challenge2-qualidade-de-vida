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
  ouro: 0xf5cf5f, mata: 0x6f8f4f, floresta: 0x463708, creme: 0xfaf5ea, tomate: 0xd93b2b, laranja: 0xf08a24,
  banana: 0xf5cf3a, terra: 0x9a6b3f, cebola: 0xb98a5a, folha: 0x6fb34a, abobora: 0xd97b1f, pacote: 0xe9e2d0,
  feijao: 0x6d3f25, preto: 0x2a2a33, macarrao: 0xe8c04f, carne: 0xa8413a, frango: 0xe0b483, lata: 0xb9c2c9, leite: 0xf4f6f4,
};

const FUNDO_MOEDA = (ctx, t) => {
  ctx.fillStyle = "#f5cf5f"; ctx.fillRect(0, 0, t, t);
  ctx.strokeStyle = "#c98f1c"; ctx.lineWidth = t * 0.05;
  ctx.beginPath(); ctx.arc(t / 2, t / 2, t * 0.4, 0, 7); ctx.stroke();
  ctx.fillStyle = "#b87f12"; ctx.font = `800 ${t * 0.55}px Nunito, sans-serif`;
  ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText("$", t / 2, t * 0.53);
};

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
  renderer.setPixelRatio(Math.min(devicePixelRatio, fraco ? 1.5 : 2));
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
  ceu.width = 64; ceu.height = 32;
  const c = ceu.getContext("2d");
  const grad = c.createLinearGradient(0, 0, 0, 32);
  grad.addColorStop(0, "#fff4d6"); grad.addColorStop(0.5, "#d9b64f"); grad.addColorStop(1, "#463708");
  c.fillStyle = grad; c.fillRect(0, 0, 64, 32);
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

  const texturaMoeda = (() => {
    const t = document.createElement("canvas");
    t.width = t.height = 128;
    FUNDO_MOEDA(t.getContext("2d"), 128);
    const tx = new THREE.CanvasTexture(t);
    tx.colorSpace = THREE.SRGBColorSpace;
    return tx;
  })();
  const geoMoeda = new THREE.CylinderGeometry(0.5, 0.5, 0.09, 24);
  const matLateral = new THREE.MeshStandardMaterial({ color: COR.ouro, metalness: 1, roughness: 0.3 });
  const matFace = new THREE.MeshStandardMaterial({ map: texturaMoeda, metalness: 0.35, roughness: 0.4, emissive: 0x6e4a08, emissiveIntensity: 0.55 });
  const matsMoeda = [matLateral, matFace, matFace];

  function criarCesta() {
    const g = new THREE.Group();
    const trama = new THREE.Mesh(
      new THREE.CylinderGeometry(0.62, 0.42, 0.56, 14, 3, true),
      new THREE.MeshStandardMaterial({ color: COR.mata, wireframe: true, metalness: 0.4, roughness: 0.4 }),
    );
    const miolo = new THREE.Mesh(
      new THREE.CylinderGeometry(0.6, 0.41, 0.55, 14, 1, true),
      new THREE.MeshStandardMaterial({ color: COR.floresta, side: THREE.DoubleSide, transparent: true, opacity: 0.45, roughness: 0.8 }),
    );
    const fundo = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.02, 14), material(COR.floresta));
    fundo.position.y = -0.28;
    const borda = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.035, 8, 28), matLateral);
    borda.rotation.x = Math.PI / 2;
    borda.position.y = 0.28;
    const alca = new THREE.Mesh(new THREE.TorusGeometry(0.6, 0.028, 8, 24, Math.PI), matLateral);
    alca.position.y = 0.28;
    g.add(miolo, trama, fundo, borda, alca);
    return g;
  }

  // ---------- Chuva de moedas (e comida, conforme a pessoa rola a tela inicial) ----------
  const TOTAL = fraco ? 34 : 80;
  const moedas = new THREE.InstancedMesh(geoMoeda, matsMoeda, TOTAL);
  moedas.frustumCulled = false;
  cena.add(moedas);
  const auxiliar = new THREE.Object3D();
  const IDS = ["tomate", "banana", "ovo", "arroz", "cenoura", "laranja", "feijao_carioca", "repolho", "abobora", "leite", "frango_coxa", "macarrao"];
  const pecas = Array.from({ length: TOTAL }, (_, i) => ({
    // As moedas ficam mais para a direita, longe do título, em telas largas.
    x: innerWidth >= 1024 ? -0.1 + Math.random() * 0.62 : Math.random() - 0.5, y: Math.random(), z: innerWidth >= 1024 ? -5 + Math.random() * 4 : -13 + Math.random() * 5,
    v: 0.05 + Math.random() * 0.08, r: Math.random() * 6, rv: 0.6 + Math.random() * 1.6, s: 0.55 + Math.random() * 0.5,
    comida: i < (fraco ? 10 : 16) ? criarAlimento(IDS[i % IDS.length]) : null,
  }));
  const comidaChuva = new THREE.Group();
  pecas.forEach((p) => p.comida && comidaChuva.add(p.comida));
  cena.add(comidaChuva);

  // ---------- Objetos presos aos palcos ----------
  const cestaHero = criarCesta();
  const cestaResultado = criarCesta();
  const moedaGrande = new THREE.Mesh(geoMoeda, matsMoeda);
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

  function ancorar(obj, seletor, escala) {
    const alvo = document.querySelector(seletor);
    const caixa = alvo?.offsetParent ? alvo.getBoundingClientRect() : null;
    obj.visible = !!caixa && caixa.height > 0 && caixa.bottom > -120 && caixa.top < innerHeight + 120;
    if (!obj.visible) return;
    obj.position.x = ((caixa.left + caixa.width / 2) / innerWidth - 0.5) * larguraMundo;
    obj.position.y = -((caixa.top + caixa.height / 2) / innerHeight - 0.5) * alturaMundo;
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
        const obj = new THREE.Mesh(geoMoeda, matsMoeda);
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

  function atualizarChuva(dt) {
    const aba = window.economia?.aba ?? "inicio";
    const hero = document.querySelector("#palco-hero");
    const caixa = aba === "inicio" && hero?.offsetParent ? hero.getBoundingClientRect() : null;
    const noHero = !!caixa && caixa.bottom > 40;
    const p = caixa ? Math.min(1, Math.max(0, -caixa.top / (caixa.height * 0.55))) : 0;
    const e = p * p * (3 - 2 * p);
    // Fora do hero, poucas moedas nas beiradas, para não atrapalhar a leitura.
    const ativos = noHero ? TOTAL : Math.ceil(TOTAL * 0.22);
    const alvo = cestaHero.position;
    pecas.forEach((q, i) => {
      q.y -= q.v * dt;
      if (q.y < -0.1) q.y = 1.1;
      q.r += q.rv * dt;
      let x = q.x * larguraMundo, y = (q.y - 0.5) * alturaMundo, z = q.z;
      if (!noHero) x = Math.sign(q.x || 1) * (0.33 + Math.abs(q.x) * 0.35) * larguraMundo;
      if (noHero && cestaHero.visible) {
        const giro = i * 2.4, raio = 0.35 * cestaHero.scale.x * Math.sqrt((i % 16 + 0.5) / 16);
        x += (alvo.x + Math.cos(giro) * raio - x) * e;
        y += (alvo.y + cestaHero.scale.x * (-0.1 + (i % 16) * 0.024) - y) * e;
        z += (Math.sin(giro) * raio - z) * e;
      }
      const visivel = i < ativos ? 1 : 0;
      auxiliar.position.set(x, y, z);
      auxiliar.rotation.set(q.r, q.r * 0.7, 0);
      const escalaMoeda = (q.comida && noHero ? 1 - e : 1) * q.s * visivel * (noHero ? 1 : 0.7);
      // As moedas somem ao entrar na cesta; quem fica é a comida.
      auxiliar.scale.setScalar(Math.max(escalaMoeda * (noHero ? 1 - e : 1), 0.0001));
      auxiliar.updateMatrix();
      moedas.setMatrixAt(i, auxiliar.matrix);
      if (q.comida) {
        q.comida.visible = noHero && e > 0.02;
        q.comida.position.set(x, y, z);
        q.comida.rotation.set(q.r * (1 - e), q.r * 0.7 * (1 - e), 0);
        q.comida.scale.setScalar(Math.max(e * (cestaHero.scale.x * 0.26 || 0.6), 0.0001));
      }
    });
    moedas.instanceMatrix.needsUpdate = true;
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

    ancorar(cestaHero, aba === "inicio" ? "#ancora-cesta-hero" : "#nada", 0.95);
    ancorar(cestaResultado, aba === "cesta" ? "#palco-cesta" : "#nada", 0.8);
    ancorar(radar, aba === "perto" ? "#palco-perto" : "#nada", 0.62);
    ancorar(cupom, aba === "cupom" ? "#palco-cupom" : "#nada", 0.62);
    ancorar(moedaGrande, aba === "precos" ? "#palco-precos" : "#nada", 0.72);

    cestaHero.rotation.y = tempo * 0.35;
    cestaHero.rotation.x = 0.3;
    cestaResultado.rotation.y = tempo * 0.25;
    cestaResultado.rotation.x = 0.28;
    moedaGrande.rotation.set(Math.PI / 2 + Math.sin(tempo) * 0.12, 0, tempo * 1.1);
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
