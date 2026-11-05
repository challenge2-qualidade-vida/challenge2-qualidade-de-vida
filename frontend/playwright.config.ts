// Comparação visual entre o site antigo (src/web, servido pelo protótipo em :8000) e o novo.
// 1) Gerar a referência:  npx playwright test --project=antigo --update-snapshots
// 2) Comparar o novo:     npx playwright test --project=novo
// As capturas ficam com o mesmo nome nos dois projetos, então o novo é comparado com o antigo.
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "testes/visual",
  snapshotPathTemplate: "{testDir}/capturas/{arg}{ext}",
  timeout: 60_000,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  expect: { toHaveScreenshot: { maxDiffPixelRatio: Number(process.env.LIMITE_VISUAL ?? 0.01), animations: "disabled", caret: "hide" } },
  use: { reducedMotion: "reduce", colorScheme: "dark", locale: "pt-BR", timezoneId: "America/Sao_Paulo" },
  projects: [
    { name: "antigo", use: { baseURL: process.env.SITE_ANTIGO ?? "http://localhost:8000" } },
    { name: "novo", use: { baseURL: process.env.SITE_NOVO ?? "http://localhost:5173" } },
  ],
});
