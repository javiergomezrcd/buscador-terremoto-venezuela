#!/usr/bin/env python3
"""
actualizar_cifras.py — Actualiza cifras.json con las cifras de desaparecidos usando un
token reCAPTCHA generado por un HUMANO (uso autorizado por el sitio, solo agregados).

NO automatiza el reCAPTCHA: un humano abre la web oficial, el token se genera solo (v3),
y se usa ese token. Por eso hay que correrlo EN LOCAL justo después de copiar el token
(caduca en ~2 min). Un GitHub Action programado NO sirve: el token llegaría muerto.

USO (en segundos tras copiar el token):
  1. Abre https://desaparecidosterremotovenezuela.com (humano).
  2. DevTools (F12) -> pestaña Network -> mira la petición a .../api/personas
     -> copia el valor de la cabecera del token (p.ej. 'g-recaptcha-response' o
        'X-Recaptcha-Token'; mira cuál usa). OJO: probablemente NO es el de localStorage.
  3. set RECAPTCHA_TOKEN=...   (y opcional RECAPTCHA_HEADER=nombre-cabecera)
     python actualizar_cifras.py
  4. git add cifras.json && git commit -m "cifras" && git push

Si la API rechaza el token (403), es porque caducó o la cabecera no es la correcta.
En ese caso usa el método infalible: copia los 3 números a mano en cifras.json.
"""
import datetime
import json
import os
import ssl
import sys
import urllib.parse
import urllib.request

API = "https://desaparecidos-terremoto-api.theempire.tech/api/personas"
TOKEN = os.environ.get("RECAPTCHA_TOKEN", "").strip()
HEADER = os.environ.get("RECAPTCHA_HEADER", "X-Recaptcha-Token").strip()
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

if not TOKEN:
    print("Falta RECAPTCHA_TOKEN. Cópialo de la petición a la API (DevTools > Network).")
    sys.exit(1)

# manda el token en cabecera Y como query param, por si la API lo espera de otra forma
qs = urllib.parse.urlencode({"page": 1, "pageSize": 1,
                             "recaptcha": TOKEN, "token": TOKEN})
req = urllib.request.Request(
    f"{API}?{qs}",
    headers={"User-Agent": UA, "Accept": "application/json",
             HEADER: TOKEN, "g-recaptcha-response": TOKEN,
             "Referer": "https://desaparecidosterremotovenezuela.com/",
             "Origin": "https://desaparecidosterremotovenezuela.com"})
try:
    with urllib.request.urlopen(req, timeout=30, context=ssl.create_default_context()) as r:
        d = json.loads(r.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read()[:200]!r}")
    print("Token caducado o cabecera incorrecta. Usa el método manual (3 numeros a mano).")
    sys.exit(1)

c = d.get("counts", {})
cifras = {
    "desaparecidos": c.get("total") or d.get("total"),
    "sinContacto": c.get("sinContacto"),
    "localizados": c.get("localizado"),
    "actualizado": datetime.datetime.now().strftime("%d-%m-%Y %H:%M"),
    "fuente": "desaparecidosterremotovenezuela.com",
}
with open("cifras.json", "w", encoding="utf-8") as f:
    json.dump(cifras, f, ensure_ascii=False, indent=2)
print("OK cifras.json:", cifras)
print("Ahora: git add cifras.json && git commit -m 'cifras' && git push")
