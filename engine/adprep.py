"""Prepara words.json + spec.json de cada anuncio (corrige texto de whisper con el guion canónico)."""
import json, os, re, subprocess, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ads')
BODY = ("Antes de comprar un sistema solar, necesitas saber algo que muchos vendedores pasan por alto: ¿cuánto consume realmente tu casa? "
        "Un sistema demasiado pequeño puede dejarte pagando electricidad. Y uno demasiado grande podría hacerte gastar dinero innecesariamente. "
        "Por eso creé una calculadora solar diseñada para Puerto Rico. Solo necesitas el consumo de tu factura de LUMA. "
        "Ingresa tus datos y descubre cuántas placas solares podría necesitar tu hogar. Soy Eliot Angueira. "
        "Presiona el enlace y calcula tu sistema solar sin compromiso.")
HOOKS = {
    'ad001': '¿10 placas? ¿15 placas? ¿O necesitas 25?',
    'ad002': 'No compres placas solares sin hacer esto primero.',
    'ad003': 'El error más caro al comprar placas solares.',
    'ad004': 'Tu factura de LUMA esconde la respuesta.',
    'ad005': 'No todos los hogares necesitan la misma cantidad de placas.',
}
for ad, hook in HOOKS.items():
    d = os.path.join(ROOT, ad)
    W = json.load(open(os.path.join(d, 'a.words.json')))
    canon = (hook + ' ' + BODY).split()
    if len(canon) != len(W):
        print(ad, 'MISMATCH', len(canon), len(W)); print([w[0] for w in W]); sys.exit(1)
    W = [[c, float(w[1]), float(w[2])] for c, w in zip(canon, W)]
    json.dump(W, open(os.path.join(d, 'words.json'), 'w'), ensure_ascii=False)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', os.path.join(d, 'a.mp3')], capture_output=True, text=True).stdout)
    spec = {'T': round(dur + 0.7, 3), 'words': os.path.join(d, 'words.json'), 'audio': os.path.join(d, 'a.mp3'), 'ep': 'AD.' + ad[2:], 'ad': ad,
            'hook': hook}
    json.dump(spec, open(os.path.join(d, 'spec.json'), 'w'), ensure_ascii=False, indent=1)
    print(ad, 'ok', len(W), spec['T'])
