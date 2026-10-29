"""Verificacoes estaticas do projeto (nao substitui rodar na Godot).
Uso: python3 tools/check_project.py"""
import glob, os, re, sys, json

errors, warns = [], []
gd = glob.glob('scripts/**/*.gd', recursive=True)
tscn = glob.glob('scenes/**/*.tscn', recursive=True)
allfiles = gd + tscn + ['project.godot']
src = {f: open(f, encoding='utf-8').read() for f in allfiles}

# 1) res:// existe (expande %d/%s em curingas)
for f, t in src.items():
    for m in re.finditer(r'res://[A-Za-z0-9_\-./%]+', t):
        p = m.group(0).rstrip('.,')
        path = p[len('res://'):]
        pat = re.sub(r'%[0-9]*[ds]', '*', path)
        if '*' in pat:
            if not glob.glob(pat):
                errors.append(f'{f}: padrao res:// sem arquivos: {p}')
        elif not os.path.exists(path):
            errors.append(f'{f}: res:// inexistente: {p}')

# 2) indentacao e balanceamento
for f in gd:
    lines = src[f].split('\n')
    for i, l in enumerate(lines, 1):
        if l.startswith(' ') and l.strip():
            errors.append(f'{f}:{i}: indentado com espacos')
        if '\t ' in l.lstrip('\t')[:0] or re.match(r'^\t+ +\S', l):
            errors.append(f'{f}:{i}: mistura tab/espaco')
    t = re.sub(r'"(\\.|[^"\\])*"', '""', src[f])
    t = re.sub(r'#.*', '', t)
    for a, b in ('()', '[]', '{}'):
        if t.count(a) != t.count(b):
            errors.append(f'{f}: {a}{b} desbalanceado ({t.count(a)} vs {t.count(b)})')

# 3) := sobre expressoes Variant
bad = re.compile(r':=\s*(?:min|max|clamp|lerp|abs|sign|round|floor|ceil|snapped|wrap|move_toward)\(|:=\s*[A-Za-z_\.]+\[|:=\s*[^#\n]*\.get\(|:=\s*get_node')
for f in gd:
    for i, l in enumerate(src[f].split('\n'), 1):
        s = l.strip()
        if ':=' in s and bad.search(s) and ' as ' not in s:
            errors.append(f'{f}:{i}: inferencia sobre Variant: {s}')

# 4) simbolos entre classes
def defs(path):
    t = open(path, encoding='utf-8').read()
    names = set(re.findall(r'^(?:static\s+)?func\s+(\w+)', t, re.M))
    names |= set(re.findall(r'^(?:static\s+)?var\s+(\w+)', t, re.M))
    names |= set(re.findall(r'^const\s+(\w+)', t, re.M))
    names |= set(re.findall(r'^signal\s+(\w+)', t, re.M))
    names |= set(re.findall(r'^enum\s+(\w+)', t, re.M))
    return names
classes = {'Fx': 'scripts/systems/fx.gd', 'Game': 'scripts/systems/game.gd',
           'Sfx': 'scripts/systems/sfx.gd', 'Iso': 'scripts/systems/iso.gd',
           'CombatUtil': 'scripts/combat/combat_util.gd'}
for cname, path in classes.items():
    d = defs(path)
    for f in gd:
        for m in re.finditer(r'\b' + cname + r'\.(\w+)', src[f]):
            if m.group(1) not in d and f != path:
                errors.append(f'{f}: {cname}.{m.group(1)} nao existe em {path}')

# 5) class_name unicos e nomes de classe usados
cn = {}
for f in gd:
    m = re.search(r'^class_name\s+(\w+)', src[f], re.M)
    if m:
        if m.group(1) in cn:
            errors.append(f'class_name duplicado {m.group(1)}')
        cn[m.group(1)] = f
print('classes:', ', '.join(sorted(cn)))

# 6) metadados de arte referenciados
meta = json.load(open('tools/data/actors.json'))
props = json.load(open('tools/data/props.json'))
for a, m in meta.items():
    for an, info in m['anims'].items():
        for v in ('front', 'back'):
            p = f"assets/{m['folder']}/{a}_{an}_{v}.png"
            if not os.path.exists(p):
                errors.append('sprite ausente ' + p)
for k, m in props.items():
    if not os.path.exists(m['file'].replace('res://', '')):
        errors.append('prop ausente ' + k)
lvl = json.load(open('tools/data/ruinas.json'))
for p in lvl['props']:
    if not p['k'].startswith('rune_') and p['k'] not in props:
        errors.append('prop do nivel sem meta ' + p['k'])
# paredes usadas existem
for w in lvl['walls']:
    h = w['h']
    if w['deco'] and w['face']:
        pth = f"assets/environments/wall_h{h}_{w['deco']}_{w['face']}.png"
    else:
        pth = f"assets/environments/wall_h{h}_v{w['v']}.png"
    if not os.path.exists(pth):
        errors.append('parede ausente ' + pth)
# animacoes referenciadas no codigo existem
code = '\n'.join(src[f] for f in gd)
used = set(re.findall(r'(?:play_loop|play_once|show_frame)\("(\w+)"', code))
used |= set(re.findall(r'show_frame\("(\w+)%d"', code))
for u in sorted(used):
    ok = any(u in m['anims'] for m in meta.values())
    if not ok:
        errors.append('animacao nao gerada: ' + u)
sfx = set(re.findall(r'Sfx\.play\("(\w+)"', code)) | {'swing_0', 'swing_1'}
for s in sorted(sfx):
    if not os.path.exists(f'assets/audio/{s}.wav'):
        errors.append('sfx ausente: ' + s)

print('arquivos .gd:', len(gd), ' .tscn:', len(tscn))
for w in warns:
    print('AVISO', w)
if errors:
    print('ERROS:')
    for e in errors:
        print(' -', e)
    sys.exit(1)
print('verificacao estatica OK')
