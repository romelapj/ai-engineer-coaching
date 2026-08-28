// Pon aquí el código de tu sitio de GoatCounter (el subdominio que elegiste al
// crear la cuenta en https://www.goatcounter.com). Mientras esté vacío, este
// archivo no carga nada ni envía una sola petición.
const CODIGO_GOATCOUNTER = "";

(function () {
  const local = ["localhost", "127.0.0.1", "::1", ""].includes(location.hostname);
  if (!CODIGO_GOATCOUNTER || local) return;
  const s = document.createElement("script");
  s.async = true;
  s.src = "//gc.zgo.at/count.js";
  s.dataset.goatcounter =
    "https://" + CODIGO_GOATCOUNTER + ".goatcounter.com/count";
  document.head.appendChild(s);
})();

window.avance = function (taller, paso) {
  try {
    if (!window.goatcounter || !window.goatcounter.count) return;
    window.goatcounter.count({
      path: "avance/" + taller + "/" + paso,
      title: "Paso completado",
      event: true,
    });
  } catch (e) {}
};
