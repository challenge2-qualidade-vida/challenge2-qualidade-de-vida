// Animações da EconoMIA (tópico 24), com GSAP e Lenis. Portado de src/web/animacoes.js.
// Tudo aqui só anima o que já está na tela, e nada roda quando a pessoa pede menos movimento.
// As telas chamam estas funções depois de desenhar, no lugar dos seletores soltos do site antigo.
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";

export const semMovimento = matchMedia("(prefers-reduced-motion: reduce)").matches;
let preparado = false;

/** Rolagem suave, refresh do ScrollTrigger ao trocar de tela e o pulinho da Mia com a cesta cheia. */
export function prepararAnimacoes() {
  if (semMovimento || preparado) return;
  preparado = true;
  gsap.registerPlugin(ScrollTrigger);
  // Rolagem suave só com mouse; no toque, a rolagem do próprio aparelho é melhor.
  if (matchMedia("(pointer: fine)").matches) {
    const lenis = new Lenis({ lerp: 0.12 });
    lenis.on("scroll", ScrollTrigger.update);
    gsap.ticker.add((t) => lenis.raf(t * 1000));
    gsap.ticker.lagSmoothing(0);
  }
  document.addEventListener("economia:aba", () => requestAnimationFrame(() => ScrollTrigger.refresh()));
  // Cesta da abertura cheia: a Mia dá um pulinho de alegria.
  document.addEventListener("economia:cesta-cheia", () => {
    gsap.fromTo(".hero-gato", { y: 0 }, { y: -26, duration: 0.2, yoyo: true, repeat: 3, ease: "power1.out", clearProps: "y" });
  });
}

/** Abertura: o título entra palavra por palavra e a Mia pula para a cena.
 * Devolve a limpeza, que desfaz a animação: o React pode montar o efeito duas vezes. */
export function animarAbertura(palco: HTMLElement) {
  if (semMovimento) return () => {};
  const contexto = gsap.context(() => {
    gsap.timeline({ defaults: { ease: "back.out(1.5)" } })
      .from(".palavra > span", { yPercent: 115, rotate: 7, duration: 0.8, stagger: 0.07 })
      .from(".hero-texto, .botao-hero", { y: 22, opacity: 0, duration: 0.5, stagger: 0.1, ease: "power2.out" }, "-=0.35")
      .from(".hero-gato", { y: 180, rotate: -14, scale: 0.75, duration: 0.95, ease: "elastic.out(1, 0.65)" }, "-=0.6");
  }, palco);
  return () => contexto.revert();
}

/** A turma entra girando conforme a rolagem. */
export function animarTurma(personagens: HTMLElement[]) {
  if (semMovimento) return () => {};
  const contexto = gsap.context(() => {
    personagens.forEach((p, i) => gsap.from(p, {
      rotateY: i % 2 ? 42 : -42, y: 60, opacity: 0.1, transformPerspective: 900,
      scrollTrigger: { trigger: p, start: "top 95%", end: "top 62%", scrub: 0.6 },
    }));
  });
  return () => contexto.revert();
}

/** Cesta pronta: os cartões, as metas e os itens entram, e o gato do cabeçalho comemora. */
export function animarCestaPronta(tela: HTMLElement) {
  if (semMovimento) return;
  gsap.from(tela.querySelectorAll("#resumo .opcao"), { scale: 0.86, y: 18, opacity: 0, duration: 0.55, stagger: 0.09, ease: "back.out(1.7)" });
  gsap.from(tela.querySelectorAll("#metas .mini-anel"), { scale: 0, duration: 0.65, stagger: 0.09, delay: 0.25, ease: "back.out(2.2)" });
  gsap.from(tela.querySelectorAll("#itens .item"), {
    x: -24, opacity: 0, duration: 0.42, stagger: 0.035, delay: 0.35, ease: "power2.out", clearProps: "transform,opacity",
  });
  gsap.fromTo(tela.querySelectorAll(".cabecalho-tela > :is(img, canvas)"), { y: 0 }, { y: -24, duration: 0.24, yoyo: true, repeat: 3, ease: "power1.out" });
}

/** O total sobe contando até o valor final. `aoMudar` recebe os centavos de cada quadro. */
export function contarAte(centavos: number, aoMudar: (valor: number) => void) {
  if (semMovimento) {
    aoMudar(centavos);
    return () => {};
  }
  const contador = { n: 0 };
  const animacao = gsap.to(contador, { n: centavos, duration: 1.3, ease: "power3.out", onUpdate: () => aoMudar(contador.n) });
  return () => animacao.kill();
}

/** Cardápio: cada refeição entra na ordem do dia. */
export function animarCardapio(area: HTMLElement) {
  if (semMovimento) return;
  const novos = area.querySelectorAll(".cardapio-refeicao");
  if (novos.length) gsap.from(novos, { y: 18, opacity: 0, duration: 0.35, stagger: 0.04, ease: "power2.out", clearProps: "transform,opacity" });
}
