#!/usr/bin/env python3
"""Actualiza cifras.json desde un endpoint autorizado de solo agregados.

No usa Selenium ni automatiza reCAPTCHA. En GitHub Actions no hay humano presente,
asi que la fuente correcta para el cron es un endpoint machine-to-machine que el
dueno del sistema deje exento o protegido con un token propio.
"""
import argparse
import datetime as dt
import json
import os
import re
import ssl
import sys
import urllib.request
import unicodedata
from zoneinfo import ZoneInfo


OUT = "cifras.json"


def _int(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name} no es un entero")
    try:
        n = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} no es un entero") from exc
    if n < 0:
        raise ValueError(f"{name} no puede ser negativo")
    return n


def _count(text, label):
    normalized = unicodedata.normalize("NFD", text)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower()
    match = re.search(r"(\d[\d., ]*)\s+" + re.escape(label), normalized)
    if not match:
        raise ValueError(f"no encontre {label}")
    return int(re.sub(r"\D", "", match.group(1)))


def normalizar(payload):
    if isinstance(payload, str):
        return {
            "desaparecidos": _count(payload, "personas reportadas"),
            "sinContacto": _count(payload, "aun sin contacto"),
            "localizados": _count(payload, "localizados"),
        }
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        content = payload["data"].get("content")
        if isinstance(content, str):
            return normalizar(content)

    raw = payload.get("counts", payload) if isinstance(payload, dict) else {}
    total = raw.get("total", raw.get("desaparecidos", raw.get("reportadas")))
    sin_contacto = raw.get("sinContacto", raw.get("sin_contacto"))
    localizados = raw.get("localizado", raw.get("localizados"))

    cifras = {
        "desaparecidos": _int(total, "total"),
        "sinContacto": _int(sin_contacto, "sinContacto"),
        "localizados": _int(localizados, "localizados"),
    }
    if cifras["sinContacto"] + cifras["localizados"] != cifras["desaparecidos"]:
        # ponytail: contrato actual de 3 estados. Si aparece otro estado, ampliar aqui.
        raise ValueError("sinContacto + localizados debe igualar desaparecidos")
    return cifras


def fetch_json(url):
    headers = {"Accept": "application/json", "User-Agent": "cifras-gh-action/1.0"}
    token = os.environ.get("STATS_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    header_name = os.environ.get("STATS_AUTH_HEADER", "").strip()
    header_value = os.environ.get("STATS_AUTH_VALUE", "").strip()
    if header_name and header_value:
        headers[header_name] = header_value

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30, context=ssl.create_default_context()) as r:
        body = r.read().decode("utf-8")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return body


def fetch_vercel_json(url):
    secret = os.environ.get("API_SECRET", "").strip()
    if not secret:
        raise ValueError("Falta API_SECRET para llamar a VERCEL_API_URL")
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
            "User-Agent": "cifras-gh-action/1.0",
        },
        data=b"{}",
    )
    with urllib.request.urlopen(req, timeout=60, context=ssl.create_default_context()) as r:
        return json.loads(r.read().decode("utf-8"))


def guardar(cifras, fuente):
    now = dt.datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d %H:%M %Z")
    out = {
        **cifras,
        "actualizado": now,
        "fuente": fuente,
        "nota": "Actualizado automaticamente desde endpoint autorizado de agregados.",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return out


def self_check():
    sample = {"total": 57164, "sinContacto": 49475, "localizado": 7689}
    assert normalizar(sample) == {
        "desaparecidos": 57164,
        "sinContacto": 49475,
        "localizados": 7689,
    }
    sample2 = {"counts": {"desaparecidos": "10", "sinContacto": "7", "localizados": "3"}}
    assert normalizar(sample2)["desaparecidos"] == 10
    text = "57218 Personas reportadas\n\n49497 Aun sin contacto\n\n7721 Localizados"
    assert normalizar(text) == {
        "desaparecidos": 57218,
        "sinContacto": 49497,
        "localizados": 7721,
    }
    assert normalizar({"data": {"content": text}})["localizados"] == 7721
    try:
        normalizar({"total": 10, "sinContacto": 8, "localizado": 1})
    except ValueError:
        pass
    else:
        raise AssertionError("debe rechazar cifras inconsistentes")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        self_check()
        print("self-check OK")
        return 0

    vercel_url = os.environ.get("VERCEL_API_URL", "").strip()
    stats_url = os.environ.get("STATS_URL", "").strip()
    if vercel_url:
        payload = fetch_vercel_json(vercel_url)
        fuente = os.environ.get("STATS_SOURCE_NAME", "").strip() or "vercel api"
    elif stats_url:
        payload = fetch_json(stats_url)
        fuente = os.environ.get("STATS_SOURCE_NAME", "").strip() or "endpoint autorizado"
    else:
        print("Falta VERCEL_API_URL o STATS_URL.", file=sys.stderr)
        return 2

    cifras = normalizar(payload)
    out = guardar(cifras, fuente)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
