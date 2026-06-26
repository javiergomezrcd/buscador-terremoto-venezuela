# Cómo actualizar las cifras de desaparecidos

La API de desaparecidos (`desaparecidosterremotovenezuela.com`) ahora exige **reCAPTCHA**
y **no permite CORS**, así que la web pública no puede leerla sola (y no se debe saltar el
captcha). Por eso las cifras se actualizan a mano en 30 segundos:

1. Entra a https://desaparecidosterremotovenezuela.com y resuelve el captcha (como humano).
2. Apunta los 3 números: total reportados, sin contacto, localizados.
3. Edita `cifras.json` en este repositorio (botón ✏️ en GitHub) y pon los números + la fecha:
   ```json
   {
     "desaparecidos": 48620,
     "sinContacto": 43332,
     "localizados": 5288,
     "actualizado": "26-jun-2026 12:00",
     "fuente": "desaparecidosterremotovenezuela.com"
   }
   ```
4. Commit. En ~1 minuto GitHub Pages publica y el dashboard muestra las cifras nuevas.

> Pacientes en hospital sí se actualizan solos (registro oficial, sin captcha).
> Si los del sitio de desaparecidos dan una API key / nos meten en allowlist, esto pasa a
> ser automático también.
