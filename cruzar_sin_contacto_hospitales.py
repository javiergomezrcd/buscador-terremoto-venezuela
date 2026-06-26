#!/usr/bin/env python3
"""Cruza desaparecidos "sin contacto" contra pacientes hospitalarios.

Genera un CSV local para verificacion humana. No se publica: puede contener falsos
positivos y datos sensibles de salud.
"""
import argparse
import csv
import json
import re
import ssl
import sys
import unicodedata
import urllib.parse
import urllib.request
from difflib import SequenceMatcher


JINA_URL = "https://r.jina.ai/https://desaparecidosterremotovenezuela.com/"
SUPA_URL = "https://ghswopasaynslycpaldj.supabase.co/rest/v1/pacientes"
SUPA_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdoc3"
    "dvcGFzYXluc2x5Y3BhbGRqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI0MDU0MDcsImV4cCI6"
    "MjA5Nzk4MTQwN30.MifuBb6C54KQdhuv_4gMoNAGJl997ycU299OcFeoyzU"
)
OUT = "cruces_sin_contacto_hospitales.csv"
STOP = {
    "DE", "DEL", "LA", "LAS", "LOS", "EL", "Y", "E", "DA", "DO", "DOS",
    "FAMILIA", "SR", "SRA", "NINO", "NINA",
}


def get_text(url):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "cruce-humanitario/1.0",
            "X-No-Cache": "true",
            "X-Timeout": "30",
        },
    )
    with urllib.request.urlopen(req, timeout=60, context=ssl.create_default_context()) as r:
        body = r.read().decode("utf-8")
    try:
        data = json.loads(body)
        return data.get("data", {}).get("content", body)
    except json.JSONDecodeError:
        return body


def get_pacientes():
    out = []
    page = 1000
    offset = 0
    while True:
        qs = urllib.parse.urlencode({
            "select": "nombre,apellido,hospital,estado,edad",
            "deleted_at": "is.null",
            "limit": str(page),
            "offset": str(offset),
        })
        req = urllib.request.Request(
            f"{SUPA_URL}?{qs}",
            headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}"},
        )
        with urllib.request.urlopen(req, timeout=60, context=ssl.create_default_context()) as r:
            chunk = json.loads(r.read().decode("utf-8"))
        out.extend(chunk)
        if len(chunk) < page:
            return out
        offset += page


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"[^A-Za-z0-9 ]+", " ", s.upper())
    return re.sub(r"\s+", " ", s).strip()


def tokens(s):
    return [t for t in norm(s).split() if len(t) > 2 and t not in STOP and not t.isdigit()]


def score(a, b):
    ta, tb = set(tokens(a)), set(tokens(b))
    if not ta or not tb:
        return 0
    overlap = len(ta & tb) / max(len(ta), len(tb))
    seq = SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()
    return round(max(overlap, seq), 3)


def posibles_personas(nombre):
    parts = re.split(r",|;|\s+\+\s+|\s+/\s+", nombre)
    out = []
    for p in parts:
        p = p.strip()
        if len(tokens(p)) >= 2:
            out.append(p)
    return out or [nombre.strip()]


def extraer_sin_contacto(markdown):
    lines = [line.strip() for line in markdown.splitlines()]
    encontrados = []
    for i, line in enumerate(lines):
        if not line.startswith("### "):
            continue
        ventana = "\n".join(lines[max(0, i - 3): i + 5])
        if "Sin contacto" not in ventana:
            continue
        nombre = line[4:].strip()
        for persona in posibles_personas(nombre):
            encontrados.append(persona)
    return sorted(set(encontrados), key=norm)


def cruzar(desaparecidos, pacientes, min_score):
    rows = []
    for d in desaparecidos:
        for p in pacientes:
            paciente = f"{p.get('apellido') or ''} {p.get('nombre') or ''}".strip()
            s = score(d, paciente)
            if s >= min_score:
                rows.append({
                    "score": s,
                    "desaparecido_sin_contacto": d,
                    "paciente": paciente,
                    "hospital": p.get("hospital") or "",
                    "estado": p.get("estado") or "",
                    "edad": p.get("edad") or "",
                })
    return sorted(rows, key=lambda r: (-r["score"], r["desaparecido_sin_contacto"]))


def escribir_csv(rows, path):
    cols = ["score", "desaparecido_sin_contacto", "paciente", "hospital", "estado", "edad"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def self_check():
    assert score("Maria Elena Sanchez", "SANCHEZ MARIA ELENA") >= 0.9
    assert score("Pedro Veloz", "Maria Perez") < 0.65
    md = "![Image]Sin contacto\n\n### Pedro Veloz\n\nVargas\n\n![Image]Localizado\n\n### Ana Perez"
    assert extraer_sin_contacto(md) == ["Pedro Veloz"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-score", type=float, default=0.82)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()

    if args.self_check:
        self_check()
        print("self-check OK")
        return 0

    desaparecidos = extraer_sin_contacto(get_text(JINA_URL))
    pacientes = get_pacientes()
    rows = cruzar(desaparecidos, pacientes, args.min_score)
    escribir_csv(rows, args.out)
    print(f"OK: {len(desaparecidos)} sin contacto, {len(pacientes)} pacientes, {len(rows)} cruces -> {args.out}")
    print("Revisar manualmente antes de contactar familias. No publicar el CSV.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
