// Animações da EconoMIA (tópico 24), com GSAP e Lenis.
// O site funciona sem este arquivo: tudo aqui só anima o que já está visível,
// e nada roda quando a pessoa pede menos movimento no sistema.
(() => {
  const semMovimento = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (semMovimento || !window.gsap) return;

  const ponteiroFino = matchMedia("(pointer: fine)").matches;
  gsap.registerPlugin(ScrollTrigger);

  // Rolagem suave só com mouse; no toque, a rolagem do próprio aparelho é melhor.
  if (ponteiroFino && window.Lenis) {
    const lenis = new Lenis({ lerp: 0.12 });
    lenis.on("scroll", ScrollTrigger.update);
    gsap.ticker.add((t) => lenis.raf(t * 1000));
    gsap.ticker.lagSmoothing(0);
  }

  // Abertura: o título entra palavra por palavra e a Mia pula para a cena.
  const titulo = document.querySelector("#palco-hero h1");
  if (titulo) {
    const palavras = titulo.textContent.trim().split(/\s+/);
    titulo.setAttribute("aria-label", titulo.textContent.trim());
    titulo.replaceChildren(...palavras.flatMap((p, i) => {
      const caixa = document.createElement("span");
      caixa.className = "palavra";
      caixa.setAttribute("aria-hidden", "true");
      const dentro = document.createElement("span");
      dentro.textContent = p;
      caixa.append(dentro);
      return i ? [" ", caixa] : [caixa];
    }));
    gsap.timeline({ defaults: { ease: "back.out(1.5)" } })
      .from("#palco-hero .palavra > span", { yPercent: 115, rotate: 7, duration: 0.8, stagger: 0.07 })
      .from("#palco-hero .hero-texto, #palco-hero .botao-hero", { y: 22, opacity: 0, duration: 0.5, stagger: 0.1, ease: "power2.out" }, "-=0.35")
      .from("#palco-hero .hero-gato", { y: 180, rotate: -14, scale: 0.75, duration: 0.95, ease: "elastic.out(1, 0.65)" }, "-=0.6");
  }

  // A turma entra girando conforme a rolagem.
  gsap.utils.toArray(".personagem").forEach((p, i) => {
    gsap.from(p, {
      rotateY: i % 2 ? 42 : -42, y: 60, opacity: 0.1, transformPerspective: 900,
      scrollTrigger: { trigger: p, start: "top 95%", end: "top 62%", scrub: 0.6 },
    });
  });
  document.addEventListener("economia:aba", () => requestAnimationFrame(() => ScrollTrigger.refresh()));

  // Cesta pronta: o total sobe contando, os itens entram e o gato comemora.
  document.addEventListener("economia:cesta", (e) => {
    if (!e.detail.animar) return;
    const valor = document.querySelector("#resumo .opcao.recomendada .valor");
    if (valor) {
      const fim = Number(valor.textContent.replace(/[^\d,]/g, "").replace(",", "."));
      const contador = { n: 0 };
      gsap.to(contador, {
        n: fim, duration: 1.3, ease: "power3.out",
        onUpdate: () => { valor.textContent = contador.n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }); },
      });
    }
    gsap.from("#resumo .opcao", { scale: 0.86, y: 18, opacity: 0, duration: 0.55, stagger: 0.09, ease: "back.out(1.7)" });
    gsap.from("#metas .mini-anel", { scale: 0, duration: 0.65, stagger: 0.09, delay: 0.25, ease: "back.out(2.2)" });
    gsap.from("#itens .item", {
      x: -24, opacity: 0, duration: 0.42, stagger: 0.035, delay: 0.35, ease: "power2.out", clearProps: "transform,opacity",
    });
    gsap.fromTo("#aba-cesta .cabecalho-tela > :is(img, canvas)", { y: 0 }, { y: -24, duration: 0.24, yoyo: true, repeat: 3, ease: "power1.out" });
  });

  // Cardápio: cada refeição entra na ordem do dia.
  new MutationObserver(() => {
    const novos = document.querySelectorAll("#cardapio .cardapio-refeicao");
    if (novos.length) gsap.from(novos, { y: 18, opacity: 0, duration: 0.35, stagger: 0.04, ease: "power2.out", clearProps: "transform,opacity" });
  }).observe(document.querySelector("#cardapio"), { childList: true });
})();
