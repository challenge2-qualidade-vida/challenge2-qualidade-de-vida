// Gatos em 3D (tópico 25): renderizados no Blender em uma grade de poses.
// O site escolhe a pose conforme o mouse, então cabeça e olhos acompanham o cursor
// com a qualidade de um filme, sem custo de 3D em tempo real.
// Até a grade carregar, e sem JavaScript, fica a imagem parada de frente.
(() => {
  const COLUNAS = 13, LINHAS = 9, TROCA_MS = 80;
  const semMovimento = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const dados = navigator.connection?.saveData;
  const limite = (v, a, b) => Math.min(b, Math.max(a, v));
  let mouseX = null, mouseY = null, ultimoMouse = 0;

  addEventListener("pointermove", (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    ultimoMouse = performance.now();
  }, { passive: true });

  function iniciar(imgParada) {
    const grade = new Image();
    grade.decoding = "async";
    grade.src = imgParada.dataset.grade;
    grade.onload = () => {
      const cw = grade.width / COLUNAS, ch = grade.height / LINHAS;
      const canvas = document.createElement("canvas");
      canvas.width = cw;
      canvas.height = ch;
      canvas.className = imgParada.className;
      canvas.setAttribute("role", "img");
      canvas.setAttribute("aria-label", imgParada.alt);
      imgParada.replaceWith(canvas);
      const ctx = canvas.getContext("2d");
      let x = (COLUNAS - 1) / 2, y = (LINHAS - 1) / 2, fim = false;
      let pose = [x, y], anterior = null, troca = 0;

      function pintar([c, l], alfa = 1) {
        ctx.globalAlpha = alfa;
        ctx.drawImage(grade, c * cw, l * ch, cw, ch, 0, 0, cw, ch);
      }

      // Parado, o gato mostra sempre uma pose pura: misturar poses vizinhas duplica olhos
      // e boca. A mistura existe só durante a troca, rápida demais para o olho perceber.
      function desenhar(agora) {
        const t = anterior ? (agora - troca) / TROCA_MS : 1;
        ctx.clearRect(0, 0, cw, ch);
        if (t < 1) {
          pintar(anterior);
          pintar(pose, t);
        } else {
          anterior = null;
          pintar(pose);
        }
        ctx.globalAlpha = 1;
      }

      function quadro(agora) {
        if (fim) return;
        requestAnimationFrame(quadro);
        if (document.hidden || !canvas.isConnected) return;
        const caixa = canvas.getBoundingClientRect();
        if (!caixa.width || caixa.bottom < 0 || caixa.top > innerHeight) return;
        let alvoX = 0, alvoY = 0;
        if (mouseX !== null && agora - ultimoMouse < 6000) {
          // A cabeça fica acima do meio da imagem: é daí que o gato "olha".
          const olhoX = caixa.left + caixa.width / 2, olhoY = caixa.top + caixa.height * 0.34;
          alvoX = limite((mouseX - olhoX) / (innerWidth * 0.42), -1, 1);
          alvoY = limite((mouseY - olhoY) / (innerHeight * 0.5), -1, 1);
        } else {
          // Com o mouse parado, o gato olha em volta devagar.
          alvoX = Math.sin(agora / 3100) * 0.45;
          alvoY = Math.sin(agora / 4300) * 0.25;
        }
        // Na grade, a primeira linha olha para baixo: mouse em cima (alvoY -1) vai para a última.
        const nx = ((alvoX + 1) / 2) * (COLUNAS - 1), ny = ((1 - alvoY) / 2) * (LINHAS - 1);
        x += (nx - x) * 0.09;
        y += (ny - y) * 0.09;
        // A folga acima de 0,5 evita o gato ficar trocando de pose com o mouse quase parado.
        if (Math.abs(x - pose[0]) > 0.6 || Math.abs(y - pose[1]) > 0.6) {
          anterior = pose;
          pose = [Math.round(x), Math.round(y)];
          troca = agora;
        }
        if (anterior) desenhar(agora);
      }
      pintar(pose);
      requestAnimationFrame(quadro);
    };
  }

  // No toque não há cursor para seguir: a grade pesada não compensa e fica a imagem,
  // que respira pelo CSS. O mesmo vale para economia de dados e menos movimento.
  const toque = !matchMedia("(pointer: fine)").matches;
  if (!toque && !dados && !semMovimento) document.querySelectorAll("img[data-grade]").forEach(iniciar);
})();
