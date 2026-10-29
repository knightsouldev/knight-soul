"""Verificador estrutural de cenas (.tscn/.tres) e scripts. Nao substitui abrir na Godot.
Uso: python3 tools/check_scenes.py"""
import glob, os, re, sys
from collections import defaultdict

errors, notes = [], []
scripts = {f: open(f, encoding='utf-8').read() for f in glob.glob('scripts/**/*.gd', recursive=True)}

# ---- mapa class_name -> arquivo, e base nativa de cada script
cls_file, extends = {}, {}
for f, t in scripts.items():
    m = re.search(r'^class_name\s+(\w+)', t, re.M)
    if m: cls_file[m.group(1)] = f
    e = re.search(r'^extends\s+(\w+)', t, re.M)
    extends[f] = e.group(1) if e else 'RefCounted'

def native_base(f):
    seen = 0
    while seen < 20:
        b = extends[f]
        if b in cls_file: f = cls_file[b]; seen += 1
        else: return b
    return '?'

def script_chain(f):
    out = [f]
    while extends[f] in cls_file:
        f = cls_file[extends[f]]; out.append(f)
    return out

def exports_of(f):
    ex = set()
    for g in script_chain(f):
        for m in re.finditer(r'^@export[^\n]*?\bvar\s+(\w+)', scripts[g], re.M):
            ex.add(m.group(1))
        for m in re.finditer(r'^@export_enum\([^\n]*\)\s*var\s+(\w+)', scripts[g], re.M):
            ex.add(m.group(1))
        for m in re.finditer(r'^@export_range\([^\n]*\)\s*var\s+(\w+)', scripts[g], re.M):
            ex.add(m.group(1))
    return ex

def methods_of(f):
    ms = set()
    for g in script_chain(f):
        ms |= set(re.findall(r'^func\s+(\w+)', scripts[g], re.M))
    return ms

NATIVE_OK = set('''position scale rotation z_index z_as_relative y_sort_enabled modulate self_modulate visible material texture offset centered
 flip_h flip_v sprite_frames animation autoplay frame speed_scale collision_layer collision_mask motion_mode shape polygon points disabled
 color energy texture_scale shadow_enabled script layer process_mode unique_name_in_owner layout_mode anchors_preset anchor_left anchor_top anchor_right
 anchor_bottom offset_left offset_top offset_right offset_bottom grow_horizontal grow_vertical mouse_filter text horizontal_alignment theme expand_mode
 stretch_mode custom_minimum_size patch_margin_left patch_margin_top patch_margin_right patch_margin_bottom max_value step value nine_patch_stretch
 stretch_margin_left stretch_margin_top stretch_margin_right stretch_margin_bottom texture_progress tile_map_data tile_set motion_scale motion_mirroring
 amount lifetime preprocess local_coords emission_shape emission_rect_extents direction spread gravity initial_velocity_min initial_velocity_max
 scale_amount_min scale_amount_max position_smoothing_enabled position_smoothing_speed blend_mode resource_local_to_scene region atlas
 theme_override_fonts/font theme_override_colors/font_color theme_override_colors/font_outline_color theme_override_constants/outline_size
 theme_override_font_sizes/font_size theme_override_constants/separation'''.split())

def parse(path):
    t = open(path, encoding='utf-8').read()
    ext, subs, nodes, conns = {}, {}, [], []
    for m in re.finditer(r'^\[ext_resource ([^\]]*)\]', t, re.M):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        if a['id'] in ext: errors.append(f'{path}: id ext duplicado {a["id"]}')
        ext[a['id']] = a
    for m in re.finditer(r'^\[sub_resource type="(\w+)" id="([^"]+)"\]', t, re.M):
        subs[m.group(2)] = m.group(1)
    # nos + propriedades
    blocks = re.split(r'^(?=\[node |\[connection |\[resource\]|\[sub_resource |\[ext_resource |\[gd_)', t, flags=re.M)
    for b in blocks:
        if b.startswith('[node '):
            head = b.split('\n', 1)[0]
            a = dict(re.findall(r'(\w+)="([^"]*)"', head))
            inst = re.search(r'instance=ExtResource\("([^"]+)"\)', head)
            groups = re.findall(r'"(\w+)"', re.search(r'groups=\[([^\]]*)\]', head).group(1)) if 'groups=[' in head else []
            props = {}
            for line in b.split('\n')[1:]:
                mm = re.match(r'^([\w/]+) = (.*)$', line)
                if mm: props[mm.group(1)] = mm.group(2)
            nodes.append(dict(name=a['name'], type=a.get('type'), parent=a.get('parent'), inst=inst.group(1) if inst else None, props=props, groups=groups))
        elif b.startswith('[connection '):
            a = dict(re.findall(r'(\w+)="([^"]*)"', b))
            conns.append(a)
    return t, ext, subs, nodes, conns

scene_files = sorted(glob.glob('scenes/**/*.tscn', recursive=True))
res_files = sorted(glob.glob('resources/**/*.tres', recursive=True))
unique_nodes_by_script = defaultdict(set)
scene_info = {}
for path in scene_files + res_files:
    t, ext, subs, nodes, conns = parse(path)
    for rid, a in ext.items():
        p = a['path'].replace('res://', '')
        if not os.path.exists(p): errors.append(f'{path}: ext_resource inexistente {a["path"]}')
    for m in re.finditer(r'ExtResource\("([^"]+)"\)', t):
        if m.group(1) not in ext: errors.append(f'{path}: ExtResource sem definicao {m.group(1)}')
    for m in re.finditer(r'SubResource\("([^"]+)"\)', t):
        if m.group(1) not in subs: errors.append(f'{path}: SubResource sem definicao {m.group(1)}')
    if path.endswith('.tres'): continue
    # hierarquia
    paths = {}
    if not nodes: errors.append(f'{path}: sem nos'); continue
    root = nodes[0]
    if root['parent'] is not None: errors.append(f'{path}: raiz com parent')
    paths['.'] = root
    names_by_parent = defaultdict(set)
    for n in nodes[1:]:
        par = n['parent']
        if par is None: errors.append(f'{path}: no sem parent {n["name"]}'); continue
        if par not in paths: errors.append(f'{path}: parent inexistente "{par}" para {n["name"]}'); continue
        full = n['name'] if par == '.' else f'{par}/{n["name"]}'
        if full in paths: errors.append(f'{path}: no duplicado {full}')
        paths[full] = n
        n['full'] = full
    root['full'] = '.'
    # scripts x tipos x exports
    uniq = set()
    for full, n in paths.items():
        if 'unique_name_in_owner' in n['props']: uniq.add(n['name'])
        sc = n['props'].get('script')
        if sc:
            rid = re.search(r'"([^"]+)"', sc).group(1)
            f = ext[rid]['path'].replace('res://', '')
            if f not in scripts: errors.append(f'{path}: script {f} nao esta em scripts/'); continue
            nb = native_base(f)
            if n['type'] and n['type'] != nb and not (nb in ('Node2D',) and n['type'] == 'Node2D'):
                errors.append(f'{path}: no "{n["name"]}" tipo {n["type"]} mas script {f} estende {nb}')
            ex = exports_of(f)
            for k in n['props']:
                if k in ('script',) or k in NATIVE_OK: continue
                if k not in ex: errors.append(f'{path}: propriedade "{k}" em "{n["name"]}" nao e @export de {os.path.basename(f)} nem conhecida')
            unique_nodes_by_script[f]  # touch
            scene_info.setdefault(f, []).append((path, n))
    # instancias: overrides validos?
    for full, n in paths.items():
        if n['inst']:
            ip = ext[n['inst']]['path'].replace('res://', '')
            if not os.path.exists(ip): continue
            # script da raiz da cena instanciada
            _, e2, _, nodes2, _ = parse(ip)
            sc2 = nodes2[0]['props'].get('script')
            ex2 = set()
            if sc2:
                f2 = e2[re.search(r'"([^"]+)"', sc2).group(1)]['path'].replace('res://', '')
                ex2 = exports_of(f2)
            base2 = nodes2[0]['type']
            for k in n['props']:
                if k in NATIVE_OK or k in ex2: continue
                errors.append(f'{path}: override "{k}" em instancia "{n["name"]}" ({ip}) desconhecido')
    # sinais
    for c in conns:
        tgt = paths.get(c['to'])
        frm = paths.get(c['from'])
        if tgt is None or frm is None: errors.append(f'{path}: connection com no inexistente {c}'); continue
        sc = tgt['props'].get('script')
        if sc:
            f = ext[re.search(r'"([^"]+)"', sc).group(1)]['path'].replace('res://', '')
            if c['method'] not in methods_of(f): errors.append(f'{path}: metodo {c["method"]} nao existe em {f}')
    # NodePaths exportados
    for full, n in paths.items():
        for k, v in n['props'].items():
            for m in re.finditer(r'NodePath\("([^"]+)"\)', v):
                rel = m.group(1)
                base = full if full != '.' else ''
                parts = [p for p in base.split('/') if p]
                for seg in rel.split('/'):
                    if seg == '..':
                        if not parts: parts = None; break
                        parts.pop()
                    elif seg != '.': parts.append(seg)
                if parts is None: errors.append(f'{path}: NodePath sai da cena {rel}'); continue
                tgt = '/'.join(parts) if parts else '.'
                if tgt not in paths: errors.append(f'{path}: NodePath "{rel}" (de {n["name"]}) nao resolve -> {tgt}')
    scene_info[path] = dict(nodes_list=nodes, nodes=len(nodes), unique=uniq, paths=set(paths), root_script=root['props'].get('script'), ext=ext)

# ---- scripts: %Nome e $Nome existem nas cenas que os usam
users = defaultdict(list)
for path in scene_files:
    info = scene_info.get(path)
    if not info: continue
    ext = info['ext']
    for n in info['nodes_list']:
        sc = n['props'].get('script')
        if sc:
            f = ext[re.search(r'"([^"]+)"', sc).group(1)]['path'].replace('res://', '')
            users[f].append((path, n))
for f, t in scripts.items():
    t2 = re.sub(r'#.*', '', t)
    uniq_refs = set(re.findall(r'%([A-Za-z_]\w*)', re.sub(r'"[^"]*"', '""', t2)))
    child_refs = set(re.findall(r'\$([A-Za-z_]\w*)', t2))
    if not (uniq_refs or child_refs): continue
    chain_users = []
    for g, lst in users.items():
        if f in script_chain(g): chain_users += lst
    if not chain_users:
        errors.append(f'{f}: usa %/$ mas nenhuma cena o usa'); continue
    for path, n in chain_users:
        info = scene_info[path]
        for r in uniq_refs:
            if r not in info['unique'] and not re.search(rf'%{r}\b', open(path).read()):
                errors.append(f'{f}: %{r} nao e unique na cena {path}')
        for r in child_refs:
            full = n['full']
            child = r if full == '.' else f'{full}/{r}'
            if child not in info['paths']: errors.append(f'{f}: ${r} nao existe sob "{n["name"]}" em {path}')

print('cenas:', len(scene_files), ' recursos .tres:', len(res_files))
for k in ['scenes/areas/ruinas.tscn', 'scenes/player/player.tscn', 'scenes/ui/hud.tscn', 'scenes/bosses/sentinela.tscn']:
    print(f'  {k}: {scene_info[k]["nodes"]} nos')
if errors:
    print('ERROS:')
    for e in sorted(set(errors))[:80]:
        print(' -', e)
    print(f'({len(set(errors))} erros)')
    sys.exit(1)
print('verificacao de cenas OK')
