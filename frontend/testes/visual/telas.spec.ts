// Cada tela nas três larguras pedidas. A cena 3D fica escondida, porque muda a cada quadro;
// ela é conferida à mão (ver docs/desenvolvimento/27-frontend-react.md).
import { expect, test, type Page } from "@playwright/test";

const LARGURAS = { celular: 390, tablet: 768, computador: 1440 } as const;

async function abrir(page: Page, projeto: string) {
  if (projeto === "novo") {
    // Sessão dos dados falsos já aberta, para cair direto no Início, como o site antigo.
    await page.addInitScript(() => sessionStorage.setItem("economia-falso-renovacao", JSON.stringify({ email: "teste@exemplo.test", nome: "teste" })));
  }
  await page.goto("/");
  await page.locator("#aba-inicio").waitFor();
  await page.addStyleTag({ content: "#cena-3d { visibility: hidden !important; }" });
  await page.evaluate(() => document.fonts.ready);
  // As fotos carregam aos poucos (loading="lazy"); rolar até o fim faz todas carregarem.
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 400) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 30)); }
    window.scrollTo(0, 0);
  });
  await page.waitForLoadState("networkidle");
}

async function irPara(page: Page, aba: string) {
  const botao = aba === "config" ? page.locator(".botao-icone[data-ir=config]")
    : aba === "precos" ? page.locator("button[data-ir=precos]")
    : page.locator(`.nav-baixo [data-aba=${aba}]`);
  await botao.click();
  await page.locator(`#aba-${aba}`).waitFor();
  await page.waitForTimeout(400);
}

for (const [nome, largura] of Object.entries(LARGURAS)) {
  test.describe(nome, () => {
    test.use({ viewport: { width: largura, height: 900 } });

    for (const aba of ["inicio", "cesta", "perto", "chat", "cupom", "config", "precos"]) {
      test(`${aba}`, async ({ page }, info) => {
        await abrir(page, info.project.name);
        if (aba !== "inicio") await irPara(page, aba);
        await expect(page).toHaveScreenshot(`${aba}-${nome}.png`, { fullPage: true });
      });
    }

    test("cesta montada", async ({ page }, info) => {
      await abrir(page, info.project.name);
      await irPara(page, "cesta");
      await page.locator("#form-cesta button[type=submit]").click();
      await page.locator("#resultado:not([hidden])").waitFor();
      await page.waitForLoadState("networkidle");
      // A rolagem suave até o resultado move a barra fixa; espera ela parar no topo.
      await page.waitForTimeout(1200);
      await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
      await page.waitForFunction(() => window.scrollY === 0);
      await page.waitForTimeout(300);
      await expect(page).toHaveScreenshot(`cesta-montada-${nome}.png`, { fullPage: true });
    });
  });
}
