const { normalizar } = require("./cifras.js");

// Fallback: cifras.json (numeros manuales AUTORIZADOS). Se empaqueta con la funcion.
let fallback = null;
try {
  fallback = require("../cifras.json");
} catch {
  fallback = null;
}

const DEFAULT_SOURCE = "https://r.jina.ai/https://desaparecidosterremotovenezuela.com/";

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

  // 1) Intento en vivo (via r.jina.ai). Si la fuente esta tras reCAPTCHA o cambia el
  //    texto, falla: NO reventamos (no mas 500) -> caemos al cifras.json autorizado.
  try {
    const r = await fetch(process.env.STATS_URL || DEFAULT_SOURCE, {
      headers: {
        Accept: "application/json",
        "User-Agent": "cifras-public/1.0",
        "X-No-Cache": "true",
        "X-Timeout": "30",
      },
      cache: "no-store",
    });
    if (!r.ok) throw new Error(`fuente devolvio ${r.status}`);

    const body = await r.text();
    let raw = body;
    try {
      raw = JSON.parse(body);
    } catch {
      // r.jina.ai puede responder markdown plano.
    }
    const c = normalizar(raw);
    return res.status(200).json({
      desaparecidos: c.total,
      sinContacto: c.sinContacto,
      localizados: c.localizado,
      actualizado: new Date().toISOString(),
      fuente: "desaparecidosterremotovenezuela.com (en vivo)",
      origen: "vivo",
    });
  } catch (error) {
    // 2) Fallback autorizado: cifras.json (lo edita un humano tras resolver el captcha).
    console.error("cifras en vivo no disponibles, uso cifras.json:", error.message);
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
