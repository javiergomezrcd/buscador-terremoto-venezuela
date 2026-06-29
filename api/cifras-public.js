// Fuente EN VIVO: endpoint oficial de metricas agregadas (sin reCAPTCHA, sin PII).
// El CORS bloquea al navegador, pero esta funcion corre server-side -> sin problema.
const METRICAS = "https://desaparecidos-terremoto-api.theempire.tech/api/metricas";

// Fallback: cifras.json (ultimos numeros conocidos). Se empaqueta con la funcion.
let fallback = null;
try {
  fallback = require("../cifras.json");
} catch {
  fallback = null;
}

module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Cache-Control", "public, max-age=0, s-maxage=60, stale-while-revalidate=300");
  res.setHeader("CDN-Cache-Control", "public, s-maxage=60, stale-while-revalidate=300");
  res.setHeader("Vercel-CDN-Cache-Control", "public, s-maxage=60, stale-while-revalidate=300");

  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "GET") {
    res.setHeader("Allow", "GET, OPTIONS");
    return res.status(405).json({ error: "metodo no permitido" });
  }

  // 1) En vivo desde /api/metricas (agregados oficiales, sin captcha).
  try {
    const r = await fetch(METRICAS, {
      headers: {
        Accept: "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          + "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
      },
      cache: "no-store",
    });
    if (!r.ok) throw new Error(`metricas devolvio ${r.status}`);
    const d = await r.json();
    const g = d.geo || {};
    if (!g.totalPersonas) throw new Error("metricas sin totalPersonas");
    return res.status(200).json({
      desaparecidos: g.totalPersonas,
      sinContacto: g.sinContacto,
      localizados: g.localizados,
      localizadosHospital: g.localizadosHospital,
      actualizado: d.lastUpdatedAt ? new Date(d.lastUpdatedAt).toISOString() : new Date().toISOString(),
      fuente: "desaparecidosterremotovenezuela.com/api/metricas",
      origen: "vivo",
    });
  } catch (error) {
    // 2) Fallback: ultimos numeros conocidos (cifras.json).
    console.error("metricas no disponible, uso cifras.json:", error.message);
    if (fallback && fallback.desaparecidos) {
      return res.status(200).json({
        desaparecidos: fallback.desaparecidos,
        sinContacto: fallback.sinContacto,
        localizados: fallback.localizados,
        actualizado: fallback.actualizado || null,
        fuente: fallback.fuente || "desaparecidosterremotovenezuela.com",
        origen: "manual",
      });
    }
    return res.status(503).json({ error: "cifras no disponibles ahora mismo" });
  }
};
