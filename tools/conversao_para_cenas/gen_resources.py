"""Etapa 1 da conversao: gera recursos (texturas auxiliares, SpriteFrames, TileSet, stats, shader, tema).
Rodar da raiz do projeto: python3 tools/conversao_para_cenas/gen_resources.py [--force]"""
import json, math, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from tscn import *

ACT = json.load(open('tools/data/actors.json'))
PROPS = json.load(open('tools/data/props.json'))

# ---------------------------------------------------------------- texturas auxiliares
def make_shadow():
    img = np.zeros((32, 64, 4), np.uint8)
    for y in range(32):
        for x in range(64):
            dx, dy = (x + .5 - 32) / 32, (y + .5 - 16) / 16
            d = math.hypot(dx, dy)
            a = (max(0.0, 1 - d) ** 0.7) * 0.8
            img[y, x] = (0, 0, 0, int(a * 255))
    Image.fromarray(img, 'RGBA').save('assets/effects/shadow.png', optimize=True)


def make_light():
    n = 256
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + .5 - n / 2, yy + .5 - n / 2) / (n / 2)
    a = np.interp(r, [0, .35, 1.0], [1.0, .55, 0.0])
    img = np.zeros((n, n, 4), np.uint8)
    img[..., :3] = 255
    img[..., 3] = (a * 255).astype(np.uint8)
    Image.fromarray(img, 'RGBA').save('assets/effects/light.png', optimize=True)


def make_floor_atlas():
    atlas = Image.new('RGBA', (64 * 8, 32), (0, 0, 0, 0))
    for i in range(8):
        atlas.paste(Image.open(f'assets/environments/floor_{i:02d}.png').convert('RGBA'), (i * 64, 0))
    atlas.save('assets/environments/chao_atlas.png', optimize=True)


# ---------------------------------------------------------------- SpriteFrames
def spriteframes(path, anims):
    """anims: lista de (nome, png_res_path, fw, fh, frames, fps, loop)."""
    d = Doc('resource', 'SpriteFrames')
    anim_txt = []
    idx = 0
    for name, png, fw, fh, n, fps, loop in anims:
        tex = d.ext_res('Texture2D', png)
        fr = []
        for i in range(n):
            sid = d.sub('AtlasTexture', [('atlas', tex), ('region', rect2(i * fw, 0, fw, fh))], rid=f'AtlasTexture_{idx}')
            idx += 1
            fr.append('{\n"duration": 1.0,\n"texture": ' + sid + '\n}')
        anim_txt.append('{\n"frames": [' + ', '.join(fr) + '],\n"loop": ' + ('true' if loop else 'false') +
                        ',\n"name": &"' + name + '",\n"speed": ' + num(fps) + '\n}')
    d.prop('animations', '[' + ', '.join(anim_txt) + ']')
    d.save(path)


def actor_frames():
    for actor, m in ACT.items():
        anims = []
        for an, info in m['anims'].items():
            for view in ('front', 'back'):
                anims.append((f'{an}_{view}', f"res://assets/{m['folder']}/{actor}_{an}_{view}.png", m['fw'], m['fh'], info['frames'], info['fps'], info['loop']))
        spriteframes(f'resources/frames/{actor}.tres', anims)


def prop_frames():
    for name, m in PROPS.items():
        if m['frames'] > 1:
            spriteframes(f'resources/frames/prop_{name}.tres', [('default', m['file'], m['fw'], m['fh'], m['frames'], m['fps'], True)])


def fx_frames():
    spriteframes('resources/frames/fx_spark.tres', [('default', 'res://assets/effects/spark.png', 32, 32, 4, 24, False)])
    spriteframes('resources/frames/fx_slash.tres', [('default', 'res://assets/effects/slash.png', 96, 96, 5, 30, False)])


# ---------------------------------------------------------------- TileSet do chao (isometrico 2:1)
def floor_tileset():
    d = Doc('resource', 'TileSet')
    tex = d.ext_res('Texture2D', 'res://assets/environments/chao_atlas.png')
    tiles = [(f'{i}:0/0', '0') for i in range(8)]
    src = d.sub('TileSetAtlasSource', [('texture', tex), ('texture_region_size', v2i(64, 32))] + tiles, rid='TileSetAtlasSource_chao')
    d.prop('tile_shape', '1')
    d.prop('tile_layout', '5')
    d.prop('tile_size', v2i(64, 32))
    d.prop('sources/0', src)
    d.save('resources/tilesets/chao.tres')


# ---------------------------------------------------------------- stats dos inimigos
STATS = {
    'soldier': dict(max_health=60, body_radius=11, walk_speed=46, chase_speed=84, detect_range=200, lose_range=360, attack_range=46,
                    attack_reach=58, attack_arc_deg=100, windup_time=0.55, active_time=0.12, recover_time=0.80, cooldown_time=0.6, damage=14,
                    lunge_speed=90, stagger_time=0.38, knockback_multiplier=1.0, souls_reward=40),
    'guardian': dict(max_health=150, body_radius=16, walk_speed=40, chase_speed=54, detect_range=210, lose_range=380, attack_range=60,
                     attack_reach=74, attack_arc_deg=150, windup_time=0.95, active_time=0.16, recover_time=1.25, cooldown_time=0.9, damage=32,
                     lunge_speed=70, stagger_time=0.0, knockback_multiplier=0.25, souls_reward=150),
    'wraith': dict(max_health=44, body_radius=11, walk_speed=50, chase_speed=70, detect_range=300, lose_range=420, attack_range=340,
                   attack_reach=0, attack_arc_deg=0, windup_time=0.85, active_time=0.10, recover_time=0.90, cooldown_time=2.0, damage=16,
                   lunge_speed=0, stagger_time=0.30, knockback_multiplier=1.0, souls_reward=70, bolt_speed=150,
                   preferred_distance_min=150, preferred_distance_max=250),
    'sentinela': dict(max_health=480, body_radius=26, walk_speed=58, chase_speed=58, detect_range=9999, lose_range=9999, attack_range=100,
                      attack_reach=0, attack_arc_deg=0, windup_time=1.0, active_time=0.16, recover_time=1.0, cooldown_time=0, damage=34,
                      lunge_speed=0, stagger_time=0.0, knockback_multiplier=0.0, souls_reward=1500),
}


def stats():
    for name, vals in STATS.items():
        d = Doc('resource', 'Resource', script_class='EnemyStats')
        sc = d.ext_res('Script', 'res://scripts/enemies/enemy_stats.gd')
        d.prop('script', sc)
        for k, v in vals.items():
            d.prop(k, str(int(v)) if k == 'souls_reward' else repr(float(v)))
        d.save(f'resources/stats/{name}.tres')


# ---------------------------------------------------------------- shader e tema
SHADER = '''shader_type canvas_item;

// Faz o sprite piscar em uma cor (usado no dano e na cura).
// O script Actor altera "flash" (0 a 1) e "flash_color".
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	COLOR = vec4(mix(c.rgb, flash_color.rgb, flash), c.a);
}
'''


def theme():
    d = Doc('resource', 'Theme')
    font = d.ext_res('FontFile', 'res://assets/fonts/CrimsonPro-Regular.ttf')

    def style(tex):
        t = d.ext_res('Texture2D', f'res://assets/ui/{tex}.png')
        return d.sub('StyleBoxTexture', [('texture', t), ('texture_margin_left', '8.0'), ('texture_margin_top', '6.0'),
                                         ('texture_margin_right', '8.0'), ('texture_margin_bottom', '6.0')])
    normal, hover = style('button'), style('button_hover')
    d.prop('default_font', font)
    d.prop('default_font_size', '13')
    d.prop('Button/colors/font_color', col(0.86, 0.72, 0.42))
    d.prop('Button/colors/font_focus_color', col(1, 0.92, 0.7))
    d.prop('Button/colors/font_hover_color', col(1, 0.92, 0.7))
    d.prop('Button/colors/font_pressed_color', col(1, 1, 1))
    d.prop('Button/font_sizes/font_size', '13')
    d.prop('Button/fonts/font', font)
    d.prop('Button/styles/focus', hover)
    d.prop('Button/styles/hover', hover)
    d.prop('Button/styles/normal', normal)
    d.prop('Button/styles/pressed', hover)
    d.prop('Label/colors/font_outline_color', col(0, 0, 0, 0.9))
    d.prop('Label/constants/outline_size', '3')
    d.prop('Label/fonts/font', font)
    d.save('resources/themes/tema_medieval.tres')


def main():
    make_shadow(); make_light(); make_floor_atlas()
    actor_frames(); prop_frames(); fx_frames()
    floor_tileset(); stats(); theme()
    write_file('resources/shaders/flash.gdshader', SHADER)
    print('recursos ok')


if __name__ == '__main__':
    main()
