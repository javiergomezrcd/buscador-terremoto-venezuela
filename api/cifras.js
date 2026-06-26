function parseIntStrict(value, name) {
  const n = Number(value);
  if (!Number.isInteger(n) || n < 0) throw new Error(`${name} invalido`);
  return n;
}

function normalizar(payload) {
  const raw = payload && typeof payload === "object" ? payload.counts || payload : {};
  const total = raw.total ?? raw.desaparecidos ?? raw.reportadas;
  const sinContacto = raw.sinContacto ?? raw.sin_contacto;
  const localizado = raw.localizado ?? raw.localizados;
  const cifras = {
    total: parseIntStrict(total, "total"),
    sinContacto: parseIntStrict(sinContacto, "sinContacto"),
    localizado: parseIntStrict(localizado, "localizado"),
  };
  if (cifras.sinContacto + cifras.localizado !== cifras.total) {
    // ponytail: contrato actual de 3 estados. Si aparece otro estado, ampliar aqui.
    throw new Error("cifras inconsistentes");
  }
  return cifras;
}

async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "metodo no permitido" });
  }

  if (!process.env.API_SECRET || req.headers.authorization !== `Bearer ${process.env.API_SECRET}`) {
    return res.status(401).json({ error: "no autorizado" });
  }

  if (!process.env.STATS_URL) {
    return res.status(500).json({ error: "STATS_URL no configurado" });
  }

  try {
    const headers = { Accept: "application/json", "User-Agent": "cifras-vercel/1.0" };
    if (process.env.STATS_TOKEN) headers.Authorization = `Bearer ${process.env.STATS_TOKEN}`;
    if (process.env.STATS_AUTH_HEADER && process.env.STATS_AUTH_VALUE) {
      headers[process.env.STATS_AUTH_HEADER] = process.env.STATS_AUTH_VALUE;
    }

    const r = await fetch(process.env.STATS_URL, { headers, cache: "no-store" });
    if (!r.ok) return res.status(502).json({ error: `fuente devolvio ${r.status}` });

    const cifras = normalizar(await r.json());
    return res.status(200).json(cifras);
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: "error obteniendo cifras" });
  }
}

module.exports = handler;
module.exports.normalizar = normalizar;

if (require.main === module) {
  const sample = { total: 57164, sinContacto: 49475, localizado: 7689 };
  const out = normalizar(sample);
  console.assert(out.total === 57164 && out.localizado === 7689, "normaliza formato API");
  try {
    normalizar({ total: 10, sinContacto: 8, localizado: 1 });
    throw new Error("debe rechazar cifras inconsistentes");
  } catch (error) {
    if (error.message === "debe rechazar cifras inconsistentes") throw error;
  }
  console.log("self-check OK");
}
