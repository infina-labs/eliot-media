# EL NEGOCIO DE LA ENERGÍA — Manual de producción y publicación

Serie de Reels de **ELIOT ANGUEIRA · Energy Advisor** para Instagram **@eliotangueira**.
Eliot dio control total: producir y publicar sin pedir aprobación. Profit Formula Studio y Profit Engine NUNCA aparecen en videos, portadas ni captions.

## Identidad
- Fondo negro cálido (#080A0D), amarillo #FFC400 / #D49B00, blanco. Estilo limpio tipo infografía (una ilustración protagonista por momento), subtítulos palabra por palabra.
- Voz: ElevenLabs **"Ivan - Puerto Rico"** `voice_id = zwDSHuqO0tEVwNUuHmR1`, modelo `eleven_v4`, flow `e7WXhO7hgy8aZtCLpJyQ`. Usar la toma A (primera).
- Duración 40–50 s. **Guion circular**: la última frase lleva de vuelta a la primera (loop).
- **Formato**: vertical 9:16, a sangre completa, sin bordes, márgenes ni marcas de agua. En todo spec nuevo poner `"full_bleed": true` (fondo con retícula y brillo en movimiento; sin él Instagram marca "Your video has a border").
- Sin CTA en el video. CTA solo en el caption: `👇 Comenta la palabra "CONSUMO" y te envío la Calculadora de Consumo.` (NO poner el website en el caption).

## Estrategia de contenido (definida por Eliot)
- **70 % autoridad y viralidad**: educación solar, controversias, mitos, noticias, errores de los consumidores, investigaciones y realidades de la industria energética de Puerto Rico (LUMA, Genera PR, Negociado de Energía, Junta de Control Fiscal, compañías solares). Objetivo: viralidad y posicionar a ELIOT ANGUEIRA como autoridad.
- **20 % comercial educativo**: casos reales, análisis de facturas, comparaciones de leasing y financiamiento, dimensionamiento de sistemas solares, beneficios económicos. Objetivo: prospectos y ventas para Profit Solar Energy.
- **10 % experimental**: formatos nuevos, storytelling, humor, animaciones, simulaciones, tendencias, opiniones personales. Objetivo: alcance y diferenciar la marca personal.
- No eliminar publicaciones con pocas visualizaciones.
- Replicar los temas, formatos y ganchos de los reels más exitosos.

## Calendario automático 4 al día (28-nov al 12-dic-2026)
- Horarios (hora PR): 08:43, 12:43, 16:43, 19:43, en orden numérico. EP.005–EP.060 los publica la tarea recurrente «Eliot · Publicador 4/día» (las tareas individuales de EP.005–EP.014 se desactivaron). EP.015 se publicó antes por error de orden y se republica en su turno (status "produced", con `first_publish`).
- `pillar` en schedule.json: A = 70 % autoridad, C = 20 % comercial educativo, X = 10 % experimental. Status: `planned` → `produced` → `published`.
- La tarea «Eliot · Producción diaria» produce de madrugada los episodios del día. Mínimo 3,000 créditos de ElevenLabs de margen; si no alcanza, avisar y no generar.
- Nunca publicar dos veces: antes de publicar, `git pull` y revisar el status en schedule.json.

## Archivos
- `schedule.json`: calendario (hora Puerto Rico), estado de cada episodio. Actualizar `status` a `produced` / `published` y guardar `media_id`.
- `media/epNNN/`: `video.mp4`, `cover.jpg`, `caption.txt`, `spec.json`, `script.txt`, `words.json`, `a.mp3`.
- `engine/`: motor. `episode.py` (genérico por spec), `render2.py` (estilo, subtítulos, transiciones), `audio2.py` (música + efectos + mezcla), `transcribe.py`.

## Producir un episodio (epNNN)
1. **Investigar** el tema con búsqueda web. Cualquier dato de tarifas, leyes, LUMA, Genera PR, Negociado, Junta: verificar con fuentes recientes (2026). Si no se puede verificar, NO decir la cifra; hablar en términos generales. Cifras de ejemplo en pantalla llevan pill "EJEMPLO ILUSTRATIVO".
2. **Guion** en español de Puerto Rico, 100–140 palabras, frases cortas, gancho fuerte, final circular. Guardar en `media/epNNN/script.txt`.
3. **Voz**: `creative_generate_speech` (voz y modelo de arriba). Descargar toma A con `creative_get_generations` → `media/epNNN/a.mp3`.
4. **Palabras**: `pip install --break-system-packages faster-whisper` si falta; `python engine/transcribe.py media/epNNN/a.mp3` → produce `a.words.json`; copiar a `words.json` y corregir palabras mal transcritas (LUMA en mayúsculas, $ en cifras, acentos).
5. **Spec** `media/epNNN/spec.json`:
   ```json
   {"T": <frames/30, frames = round(duración_mp3*30)>, "words": "<ruta absoluta words.json>", "audio": "<ruta absoluta a.mp3>",
    "ep": "EP.NNN", "keys": ["PALABRAS","CLAVE"], "impacts": [<índices de palabra>],
    "loop_start": <índice de la última frase>,
    "beats": [ {"start": 0, "type": "...", ...}, {"start": <índice palabra>, "type": "...", ...} ],
    "cover": {"lines": [{"text":"LÍNEA","color":"w"},{"text":"LÍNEA","color":"y"}], "sub": "SUBTÍTULO CORTO."}}
   ```
   - El beat 0 (gancho) se muestra completo desde el primer cuadro; el loop final reconstruye ese mismo beat → transición invisible.
   - Tipos de escena (`at` = índice de palabra en que aparece cada elemento):
     - `statement` {lines:[{text,color:'w'|'y',size,at}]}
     - `icons` {title?, pill?, items:[{icon,label,sub?,at,hl?,stamp?}]} (1–6)
     - `network` {hub, hub_icon?, nodes:[{icon,label,at}]} (2–6)
     - `bars` {title, pill, rows:[{label,value,frac,color:'y'|'w'|'r',at}], note?, note_at?}
     - `bill` {title, subtitle, rows:[{label,value,at,old?,new_at?}], stamp?, stamp_at?, pill?, pill_at?}
     - `compare` {left:{icon,title:[..],lines:[..],at}, right:{...}, mid:'>'|'VS', mid_at, winner:'left'|'right', emph_at}
     - `bignum` {title?, label, value, at, sub?, sub_at?, count?, prefix?, suffix?}
     - `battery` {from,to,drain_at,drain_dur,label,label_at}
     - `chart` {title, pill, label, values:[0..1], draw_at, draw_dur}
     - `city` {mode:'lit'|'blackout'|'relight'|'dark', at}, `house` {day, night_at, flow:1|-1, flow_at, bill, pill, pill_at, small}, `map` {lit, relight_at, pins}, `focus` {}
   - Íconos: gen fuel batt wrench panel siren bulb house doc dollar plant tower meter warning people key bank calendar sun moon check x fridge car ac fan shield question chart gov
6. **Control**: `python engine/episode.py media/epNNN/spec.json stills 1 8 15 ...` → revisar `media/epNNN/stills/` (nada encimado sobre subtítulos, ~y 1300–1420).
7. **Render**: `python engine/episode.py media/epNNN/spec.json render` → `video.mp4` + `cover.jpg` (~8 min).
8. **Caption** `caption.txt`: 2–3 líneas de valor, `EL NEGOCIO DE LA ENERGÍA · EP. NNN`, `Entiende tu consumo. Toma el control. ⚡`, CTA CONSUMO, 6–8 hashtags (#EliotAngueira #ElNegocioDeLaEnergia #PuertoRico ...).
9. Borrar `stills/`, `git add`, commit, `git push` (no subir archivos .f32 ni temporales).

## Publicar
- URL pública: `https://raw.githubusercontent.com/infina-labs/eliot-media/main/media/epNNN/video.mp4` (y `cover.jpg`).
- Windsor.ai: `execute_action` connector `instagram`, account `17841405483597181`, action `create_video_post`, params `{video_url, cover_url, caption, share_to_feed: true}`.
- Actualizar `schedule.json` (status `published`, `media_id`) y hacer push.
- Nunca publicar dos veces el mismo episodio: revisar `schedule.json` antes.

## Respuestas a "CONSUMO"
- Enlace de la calculadora: **https://calculatuconsumo.netlify.app**
- Comentarios que contengan "CONSUMO" (cualquier mayúscula/minúscula) en los Reels de @eliotangueira: responder con Windsor `reply_to_comment`, por ejemplo: `¡Aquí la tienes! 👉 calculatuconsumo.netlify.app ⚡ Cualquier duda, escríbeme.` (variar un poco el texto).
- DMs que digan "CONSUMO": `reply_to_message` (solo dentro de 24 h del mensaje) con el enlace.
- Registrar cada `comment_id` / mensaje respondido en `replied.json` para no responder dos veces. Leer datos con Windsor `get_data` (connector `instagram`, cuenta `17841405483597181`; usar `get_fields` primero).
