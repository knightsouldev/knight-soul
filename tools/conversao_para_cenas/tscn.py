"""Escritor minimo de arquivos .tscn/.tres do Godot 4 (usado so na conversao do projeto para cenas editaveis)."""
import base64, os, struct, sys, zlib

FORCE = '--force' in sys.argv


def num(n):
    n = float(n)
    if n == int(n) and abs(n) < 1e9:
        return str(int(n))
    return ('%.4f' % n).rstrip('0').rstrip('.')


def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def v2(x, y):
    return f'Vector2({num(x)}, {num(y)})'


def v2i(x, y):
    return f'Vector2i({int(x)}, {int(y)})'


def rect2(x, y, w, h):
    return f'Rect2({num(x)}, {num(y)}, {num(w)}, {num(h)})'


def col(r, g, b, a=1.0):
    return f'Color({num(r)}, {num(g)}, {num(b)}, {num(a)})'


def pva2(points):
    return 'PackedVector2Array(' + ', '.join(f'{num(x)}, {num(y)}' for x, y in points) + ')'


def nodepath(p):
    return f'NodePath({q(p)})'


def tile_data(cells):
    """cells: (x, y, source_id, atlas_x, atlas_y). Formato de TileMapLayer.tile_map_data (cabecalho uint16=0 + 12 bytes/celula)."""
    b = struct.pack('<H', 0)
    for x, y, s, ax, ay in cells:
        b += struct.pack('<hhHHHH', x, y, s, ax, ay, 0)
    return 'PackedByteArray("' + base64.b64encode(b).decode() + '")'


def write_file(path, text):
    if os.path.exists(path) and not FORCE and os.environ.get('KS_ALLOW_OVERWRITE') != '1':
        raise SystemExit(f'RECUSADO: {path} ja existe e pode conter edicoes suas. Use --force para sobrescrever.')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


class Doc:
    """Documento .tscn (kind='scene') ou .tres (kind='resource')."""

    def __init__(self, kind='scene', res_type=None, script_class=None):
        self.kind = kind
        self.res_type = res_type
        self.script_class = script_class
        self.ext = []
        self._ext = {}
        self.subs = []
        self.nodes = []
        self.conns = []
        self.res_props = []
        self._n = 0

    def ext_res(self, typ, path):
        key = (typ, path)
        if key not in self._ext:
            self._n += 1
            rid = f'{self._n}_{zlib.crc32(path.encode()) % 100000:05d}'
            self._ext[key] = rid
            self.ext.append((typ, path, rid))
        return f'ExtResource("{self._ext[key]}")'

    def sub(self, typ, props, rid=None):
        self._n += 1
        rid = rid or f'{typ}_{self._n}'
        self.subs.append((typ, rid, props))
        return f'SubResource("{rid}")'

    def node(self, name, typ=None, parent=None, instance=None, groups=None, props=None):
        self.nodes.append(dict(name=name, type=typ, parent=parent, instance=instance, groups=groups or [], props=props or []))

    def connect(self, signal, frm, to, method):
        self.conns.append((signal, frm, to, method))

    def prop(self, k, v):
        self.res_props.append((k, v))

    def text(self):
        steps = len(self.ext) + len(self.subs) + 1
        out = []
        if self.kind == 'scene':
            out.append(f'[gd_scene load_steps={steps} format=3]\n')
        else:
            sc = f' script_class="{self.script_class}"' if self.script_class else ''
            out.append(f'[gd_resource type="{self.res_type}"{sc} load_steps={steps} format=3]\n')
        for typ, path, rid in self.ext:
            out.append(f'[ext_resource type="{typ}" path="{path}" id="{rid}"]')
        if self.ext:
            out.append('')
        for typ, rid, props in self.subs:
            out.append(f'[sub_resource type="{typ}" id="{rid}"]')
            for k, v in props:
                out.append(f'{k} = {v}')
            out.append('')
        if self.kind == 'resource':
            out.append('[resource]')
            for k, v in self.res_props:
                out.append(f'{k} = {v}')
            return '\n'.join(out) + '\n'
        for n in self.nodes:
            head = f'[node name="{n["name"]}"'
            if n['type']:
                head += f' type="{n["type"]}"'
            if n['parent'] is not None:
                head += f' parent="{n["parent"]}"'
            if n['groups']:
                head += ' groups=[' + ', '.join(f'"{g}"' for g in n['groups']) + ']'
            if n['instance']:
                head += f' instance={n["instance"]}'
            out.append(head + ']')
            for k, v in n['props']:
                out.append(f'{k} = {v}')
            out.append('')
        for s, f, t, m in self.conns:
            out.append(f'[connection signal="{s}" from="{f}" to="{t}" method="{m}"]')
        return '\n'.join(out) + '\n'

    def save(self, path):
        write_file(path, self.text())
