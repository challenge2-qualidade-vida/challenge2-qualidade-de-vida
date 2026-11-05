// Service worker da EconoMIA (tópico 20): abre o app sem internet.
// Sempre tenta a rede primeiro, para nunca mostrar preço velho quando há conexão.
// A posição do usuário e as respostas do chat nunca são guardadas: só estas rotas da API entram no cache.
const CACHE = "economia-v9";
const API_PERMITIDA = ["/api/opcoes", "/api/precos", "/api/creditos"];
const ESSENCIAIS = ["./", "index.html", "estilo.css", "app.js", "animacoes.js", "cena3d.js", "gatos.js", "manifest.webmanifest", "img/logo-gato.webp", "img/logo-nome.webp", "img/mia.webp"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ESSENCIAIS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((nomes) => Promise.all(nomes.filter((n) => n !== CACHE).map((n) => caches.delete(n))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (url.pathname.startsWith("/api/") && !API_PERMITIDA.includes(url.pathname)) return;
  e.respondWith(
    fetch(e.request)
      .then((r) => {
        if (r.ok) {
          const copia = r.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copia));
        }
        return r;
      })
      .catch(() => caches.match(e.request, { ignoreSearch: true }).then((r) => r ?? Response.error())),
  );
});
