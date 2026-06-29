#!/usr/bin/env python3
"""
actualizar_cifras.py — Actualiza cifras.json desde el endpoint oficial de metricas
agregadas. SIN reCAPTCHA, SIN token, solo cifras agregadas (sin datos personales).

Fuente: https://desaparecidos-terremoto-api.theempire.tech/api/metricas
Sirve a la pagina /metricas/ del sitio. Es server-side (el CORS no afecta a un script),
no necesita captcha. Apto para correr en cron (GitHub Action).

Uso:  python actualizar_cifras.py
"""
import datetime
import json
import ssl
import urllib.request

URL = "https://desaparecidos-terremoto-api.theempire.tech/api/metricas"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

req = urllib.request.Request(URL, headers={"User-Agent": UA, "Accept": "application/json"})
with urllib.request.urlopen(req, timeout=30, context=ssl.create_default_context()) as r:
    d = json.loads(r.read().decode("utf-8"))

g = d.get("geo", {})
if not g.get("totalPersonas"):
    raise SystemExit("respuesta sin geo.totalPersonas")

cifras = {
    "desaparecidos": g.get("totalPersonas"),
    "sinContacto": g.get("sinContacto"),
    "localizados": g.get("localizados"),
    "localizadosHospital": g.get("localizadosHospital"),
    "actualizado": (datetime.datetime.fromtimestamp(d["lastUpdatedAt"] / 1000,
                    datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                    if d.get("lastUpdatedAt") else
                    datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")),
    "fuente": "desaparecidosterremotovenezuela.com/api/metricas",
}
with open("cifras.json", "w", encoding="utf-8") as f:
    json.dump(cifras, f, ensure_ascii=False, indent=2)
print("OK cifras.json:", cifras)
