# Como actualizar las cifras de desaparecidos

La web publica lee siempre `cifras.json`.

## Automatico cada 6 horas

Hay un micro-backend Vercel en `api/cifras.js` y un workflow
`.github/workflows/cifras.yml`. El Action corre cada 6 horas, llama a Vercel y actualiza
`cifras.json`.

No instala Chrome/Selenium: no hace falta. La fuente correcta para cron es un endpoint
autorizado de solo agregados.

Configura estos secrets en Vercel:

- `STATS_URL`: URL del endpoint autorizado. Debe devolver una de estas formas:
  `{"total":57164,"sinContacto":49475,"localizado":7689}` o
  `{"counts":{"total":57164,"sinContacto":49475,"localizado":7689}}`.
- `STATS_TOKEN` opcional: se manda como `Authorization: Bearer ...`.
- `STATS_AUTH_HEADER` y `STATS_AUTH_VALUE` opcionales: para un header propio, por ejemplo
  `X-Stats-Token`.
- `API_SECRET`: secreto para proteger `POST /api/cifras`.

Configura estos secrets en GitHub -> Settings -> Secrets and variables -> Actions:

- `VERCEL_API_URL`: `https://tu-app.vercel.app/api/cifras`.
- `API_SECRET`: el mismo valor que en Vercel.
- `STATS_SOURCE_NAME` opcional: texto que aparecera como fuente en `cifras.json`.

Tambien puedes saltarte Vercel y poner `STATS_URL` directamente en GitHub; el script lo
soporta. Vercel es util si quieres centralizar el secreto de la fuente.

Si el desarrollador solo puede tocar una cosa, pide esto:

```txt
GET /api/agregados
Authorization: Bearer <token>

200 {"total":57164,"sinContacto":49475,"localizado":7689}
```

El Action actualiza `cifras.json`, hace commit y GitHub Pages publica el cambio.

## Manual en 30 segundos

Mientras no exista el endpoint de agregados:

1. Entra a https://desaparecidosterremotovenezuela.com y resuelve el captcha como humano.
2. Apunta los 3 numeros: total reportados, sin contacto, localizados.
3. Edita `cifras.json` en este repositorio y pon los numeros + la fecha:
   ```json
   {
     "desaparecidos": 48620,
     "sinContacto": 43332,
     "localizados": 5288,
     "actualizado": "2026-06-26 12:00 CEST",
     "fuente": "desaparecidosterremotovenezuela.com"
   }
   ```
4. Commit. En torno a 1 minuto GitHub Pages muestra las cifras nuevas.

> Pacientes en hospital se actualizan solos desde el registro oficial de pacientes.

## Cruce de sin contacto contra hospitales

Para operadores, no publico:

```powershell
python cruzar_sin_contacto_hospitales.py
```

Genera `cruces_sin_contacto_hospitales.csv` con posibles coincidencias. Hay que revisarlo
manualmente antes de contactar familias; nombres comunes dan falsos positivos.
