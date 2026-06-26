const { normalizar } = require("./cifras.js");

const DEFAULT_SOURCE = "https://r.jina.ai/https://desaparecidosterremotovenezuela.com/";

function freshUrl(url) {
  return `${url}${url.includes("?") ? "&" : "?"}_=${Date.now()}`;
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

  try {
    const r = await fetch(freshUrl(process.env.STATS_URL || DEFAULT_SOURCE), {
      headers: { Accept: "application/json", "User-Agent": "cifras-public/1.0" },
      cache: "no-store",
    });
    if (!r.ok) return res.status(502).json({ error: `fuente devolvio ${r.status}` });

    const body = await r.text();
    let raw = body;
    try {
      raw = JSON.parse(body);
    } catch {
      // r.jina.ai tambien puede responder markdown plano.
    }
    const c = normalizar(raw);
    return res.status(200).json({
      desaparecidos: c.total,
      sinContacto: c.sinContacto,
      localizados: c.localizado,
      actualizado: new Date().toISOString(),
      fuente: "desaparecidosterremotovenezuela.com via r.jina.ai",
    });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: "error obteniendo cifras" });
  }
};
