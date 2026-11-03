// Gatos em 3D (tópico 25): renderizados no Blender em uma grade de poses.
// O site escolhe a pose conforme o mouse e mistura as vizinhas, então cabeça e olhos
// acompanham o cursor com a qualidade de um filme, sem custo de 3D em tempo real.
// Até a grade carregar, e sem JavaScript, fica a imagem parada de frente.
(() => {
  const COLUNAS = 13, LINHAS = 9;
  const semMovimento = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const dados = navigator.connection?.saveData;
  const limite = (v, a, b) => Math.min(b, Math.max(a, v));
  const suave = (t) => { const u = limite((t - 0.2) / 0.6, 0, 1); return u * u * (3 - 2 * u); };
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

      function desenhar() {
        const cx = limite(Math.floor(x), 0, COLUNAS - 2), cy = limite(Math.floor(y), 0, LINHAS - 2);
        const fx = suave(x - cx), fy = suave(y - cy);
        ctx.clearRect(0, 0, cw, ch);
        // Mistura as quatro poses vizinhas, cada uma com o peso certo, para a cabeça
        // deslizar sem saltos. A curva encurta a mistura, que é quando os traços duplicam.
        const poses = [
          [cx, cy, (1 - fx) * (1 - fy)], [cx + 1, cy, fx * (1 - fy)],
          [cx, cy + 1, (1 - fx) * fy], [cx + 1, cy + 1, fx * fy],
        ];
        let acumulado = 0;
        for (const [c, l, peso] of poses) {
          acumulado += peso;
          if (peso < 0.01) continue;
          ctx.globalAlpha = peso / acumulado;
          ctx.drawImage(grade, c * cw, l * ch, cw, ch, 0, 0, cw, ch);
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
        const nx = ((alvoX + 1) / 2) * (COLUNAS - 1), ny = ((alvoY + 1) / 2) * (LINHAS - 1);
        const antes = [x, y];
        x += (nx - x) * 0.09;
        y += (ny - y) * 0.09;
        if (Math.abs(x - antes[0]) + Math.abs(y - antes[1]) > 0.0008) desenhar();
      }
      desenhar();
      requestAnimationFrame(quadro);
    };
  }

  // No toque não há cursor para seguir: a grade pesada não compensa e fica a imagem,
  // que respira pelo CSS. O mesmo vale para economia de dados e menos movimento.
  const toque = !matchMedia("(pointer: fine)").matches;
  if (!toque && !dados && !semMovimento) document.querySelectorAll("img[data-grade]").forEach(iniciar);
})();
