"""Etapa 2a: cenas de personagens, efeitos, props e peca de parede."""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from tscn import *

ACT = json.load(open('tools/data/actors.json'))
PROPS = json.load(open('tools/data/props.json'))
S = lambda p: f'res://{p}'


def ellipse_points(radius):
    pts = []
    for i in range(8):
        a = math.tau * i / 8 + math.tau / 16
        pts.append((round(math.cos(a) * radius * 0.8, 2), round(math.sin(a) * radius * 0.4, 2)))
    return pts


def actor_scene(path, root_name, actor, script, props, radius, extra_nodes=None, sombra_modulate=None):
    """Personagem: CharacterBody2D + Colisao + Sombra + Sprite + Vida (+ extras)."""
    d = Doc('scene')
    m = ACT[actor]
    off_y = -(m['fh'] / 2 - m['foot'])
    sc = d.ext_res('Script', S(script))
    d.node(root_name, 'CharacterBody2D', props=[('collision_layer', '2'), ('collision_mask', '1'), ('motion_mode', '1'),
                                              ('script', sc)] + props)
    shp = d.sub('ConvexPolygonShape2D', [('points', pva2(ellipse_points(radius)))])
    d.node('Colisao', 'CollisionShape2D', '.', props=[('shape', shp)])
    shadow = d.ext_res('Texture2D', S('assets/effects/shadow.png'))
    sp = [('z_index', '-4'), ('scale', v2(radius * 2.8 / 64, radius * 2.8 / 64)), ('texture', shadow)]
    if sombra_modulate:
        sp.insert(0, ('modulate', sombra_modulate))
    d.node('Sombra', 'Sprite2D', '.', props=sp)
    shader = d.ext_res('Shader', S('resources/shaders/flash.gdshader'))
    mat = d.sub('ShaderMaterial', [('resource_local_to_scene', 'true'), ('shader', shader)])
    frames = d.ext_res('SpriteFrames', S(f'resources/frames/{actor}.tres'))
    d.node('Sprite', 'AnimatedSprite2D', '.', props=[('material', mat), ('sprite_frames', frames), ('animation', '&"idle_front"'),
                                                 ('autoplay', '"idle_front"'), ('offset', v2(0, off_y))])
    hs = d.ext_res('Script', S('scripts/combat/health.gd'))
    d.node('Vida', 'Node', '.', props=[('script', hs)])
    if extra_nodes:
        extra_nodes(d)
    d.save(path)


def telegraph_node(d):
    ts = d.ext_res('Script', S('scripts/combat/telegraph.gd'))
    d.node('Telegrafo', 'Node2D', '.', props=[('script', ts)])


def light_node(d, color, energy, scale, pos, name='Luz', sq=0.6, script=None):
    tex = d.ext_res('Texture2D', S('assets/effects/light.png'))
    props = []
    if script:
        props.append(('script', d.ext_res('Script', S(script))))
    props += [('position', v2(*pos)), ('scale', v2(1, sq)), ('color', col(*color)), ('energy', num(energy)),
              ('texture', tex), ('texture_scale', num(scale))]
    d.node(name, 'PointLight2D', '.', props=props)


def player_scene():
    def extras(d):
        light_node(d, (0.62, 0.78, 1.0), 0.55, 1.15, (0, -14))
        cs = d.ext_res('Script', S('scripts/world/camera_rig.gd'))
        d.node('Camera', 'Camera2D', '.', props=[('position', v2(0, -16)), ('position_smoothing_enabled', 'true'),
                                              ('position_smoothing_speed', '7.0'), ('script', cs)])
        d.node('Poeira', 'CPUParticles2D', 'Camera', props=[
            ('z_index', '30'), ('amount', '50'), ('lifetime', '9.0'), ('preprocess', '9.0'), ('local_coords', 'true' if False else 'false'),
            ('emission_shape', '3'), ('emission_rect_extents', v2(460, 260)), ('direction', v2(1, -0.3)), ('spread', '180.0'),
            ('gravity', v2(0, 0)), ('initial_velocity_min', '2.0'), ('initial_velocity_max', '8.0'),
            ('scale_amount_min', '1.0'), ('scale_amount_max', '2.0'), ('color', col(0.75, 0.82, 1.0, 0.3))])
    actor_scene('scenes/player/player.tscn', 'Jogador', 'player', 'scripts/player/player.gd',
                [('max_health', '100.0'), ('body_radius', '8.0')], 8.0, extras)


def enemy_scene(path, root, actor, script, stats_name, radius, extra_props=None, extra_nodes=None, sombra_modulate=None):
    def ex(d):
        telegraph_node(d)
        if extra_nodes:
            extra_nodes(d)
    def propsfn(d):
        pass
    d = Doc('scene')
    # as props referenciam o recurso de stats -> precisa do doc; usa closure tardia
    def build(d_):
        pass
    # montagem direta (precisa de ext_res do stats dentro do mesmo Doc)
    doc = Doc('scene')
    m = ACT[actor]
    off_y = -(m['fh'] / 2 - m['foot'])
    sc = doc.ext_res('Script', S(script))
    st = doc.ext_res('Resource', S(f'resources/stats/{stats_name}.tres'))
    rp = [('collision_layer', '2'), ('collision_mask', '1'), ('motion_mode', '1'), ('script', sc), ('stats', st)]
    if extra_props:
        rp += extra_props(doc)
    doc.node(root, 'CharacterBody2D', props=rp)
    shp = doc.sub('ConvexPolygonShape2D', [('points', pva2(ellipse_points(radius)))])
    doc.node('Colisao', 'CollisionShape2D', '.', props=[('shape', shp)])
    shadow = doc.ext_res('Texture2D', S('assets/effects/shadow.png'))
    sp = [('z_index', '-4'), ('scale', v2(radius * 2.8 / 64, radius * 2.8 / 64)), ('texture', shadow)]
    if sombra_modulate:
        sp.insert(0, ('modulate', sombra_modulate))
    doc.node('Sombra', 'Sprite2D', '.', props=sp)
    shader = doc.ext_res('Shader', S('resources/shaders/flash.gdshader'))
    mat = doc.sub('ShaderMaterial', [('resource_local_to_scene', 'true'), ('shader', shader)])
    frames = doc.ext_res('SpriteFrames', S(f'resources/frames/{actor}.tres'))
    doc.node('Sprite', 'AnimatedSprite2D', '.', props=[('material', mat), ('sprite_frames', frames), ('animation', '&"idle_front"'),
                                                   ('autoplay', '"idle_front"'), ('offset', v2(0, off_y))])
    hs = doc.ext_res('Script', S('scripts/combat/health.gd'))
    doc.node('Vida', 'Node', '.', props=[('script', hs)])
    telegraph_node(doc)
    if extra_nodes:
        extra_nodes(doc)
    doc.save(path)


def enemies():
    enemy_scene('scenes/enemies/soldier.tscn', 'SoldadoCorrompido', 'soldier', 'scripts/enemies/enemy.gd', 'soldier', 11,
                extra_props=lambda d: [('blood_color', col(0.35, 0.1, 0.5))])
    enemy_scene('scenes/enemies/guardian.tscn', 'GuardiaoDecaido', 'guardian', 'scripts/enemies/enemy.gd', 'guardian', 16,
                extra_props=lambda d: [('attack_frames_windup', '5'), ('attack_frames_strike', '2'), ('attack_frames_recover', '4'),
                                       ('blood_color', col(0.35, 0.1, 0.5))])
    enemy_scene('scenes/enemies/wraith.tscn', 'Espectro', 'wraith', 'scripts/enemies/wraith.gd', 'wraith', 11,
                extra_props=lambda d: [('blood_color', col(0.4, 0.7, 1.0)),
                                       ('projectile_scene', d.ext_res('PackedScene', S('scenes/effects/projectile.tscn')))],
                sombra_modulate=col(1, 1, 1, 0.55))

    def boss_light(d):
        light_node(d, (0.65, 0.3, 1.0), 0.7, 1.6, (0, -50))
    enemy_scene('scenes/bosses/sentinela.tscn', 'SentinelaDaRuina', 'boss', 'scripts/bosses/boss.gd', 'sentinela', 26,
                extra_props=lambda d: [('blood_color', col(0.5, 0.15, 0.7))], extra_nodes=boss_light)


def effects():
    # faisca
    d = Doc('scene')
    sc = d.ext_res('Script', S('scripts/world/effect_once.gd'))
    fr = d.ext_res('SpriteFrames', S('resources/frames/fx_spark.tres'))
    d.node('Faisca', 'AnimatedSprite2D', props=[('z_index', '20'), ('scale', v2(1.3, 1.3)), ('sprite_frames', fr), ('script', sc)])
    d.save('scenes/effects/spark.tscn')
    # corte de espada
    d = Doc('scene')
    sc = d.ext_res('Script', S('scripts/world/slash_effect.gd'))
    fr = d.ext_res('SpriteFrames', S('resources/frames/fx_slash.tres'))
    d.node('CorteDeEspada', 'Node2D', props=[('z_index', '18'), ('scale', v2(1, 0.5)), ('script', sc)])
    d.node('Arco', 'AnimatedSprite2D', '.', props=[('scale', v2(1.25, 1.25)), ('sprite_frames', fr)])
    d.save('scenes/effects/slash.tscn')
    # projetil
    d = Doc('scene')
    sc = d.ext_res('Script', S('scripts/enemies/projectile.gd'))
    glow = d.ext_res('Texture2D', S('assets/effects/glow.png'))
    shadow = d.ext_res('Texture2D', S('assets/effects/shadow.png'))
    add = d.sub('CanvasItemMaterial', [('blend_mode', '1')])
    d.node('OrbeDeAlma', 'Node2D', props=[('z_index', '8'), ('script', sc)])
    d.node('Brilho', 'Sprite2D', '.', props=[('material', add), ('position', v2(0, -14)), ('scale', v2(0.9, 0.9)),
                                             ('modulate', col(0.75, 0.4, 1, 0.85)), ('texture', glow)])
    d.node('Nucleo', 'Sprite2D', '.', props=[('material', add), ('position', v2(0, -14)), ('scale', v2(0.3, 0.3)),
                                             ('modulate', col(1, 0.95, 1, 1)), ('texture', glow)])
    d.node('Sombra', 'Sprite2D', '.', props=[('z_index', '-4'), ('scale', v2(0.25, 0.25)), ('texture', shadow)])
    light_node(d, (0.7, 0.35, 1.0), 0.8, 0.7, (0, -14))
    d.save('scenes/effects/projectile.tscn')
    # pickup
    d = Doc('scene')
    sc = d.ext_res('Script', S('scripts/world/pickup.gd'))
    shadow = d.ext_res('Texture2D', S('assets/effects/shadow.png'))
    fr = d.ext_res('SpriteFrames', S('resources/frames/prop_soul_orb.tres'))
    flask = d.ext_res('Texture2D', S('assets/ui/icon_flask.png'))
    d.node('ItemColetavel', 'Node2D', props=[('script', sc)])
    d.node('Sombra', 'Sprite2D', '.', props=[('z_index', '-4'), ('scale', v2(0.4, 0.4)), ('texture', shadow)])
    d.node('Orbe', 'AnimatedSprite2D', '.', props=[('position', v2(0, -18)), ('scale', v2(1.2, 1.2)), ('sprite_frames', fr),
                                                  ('autoplay', '"default"')])
    d.node('IconeFrasco', 'Sprite2D', '.', props=[('visible', 'false'), ('position', v2(0, -18)), ('texture', flask)])
    light_node(d, (0.4, 0.7, 1.0), 0.8, 0.7, (0, -16))
    d.save('scenes/effects/pickup.tscn')
    # shockwave (so script)
    d = Doc('scene')
    sc = d.ext_res('Script', S('scripts/combat/shockwave.gd'))
    d.node('OndaDeChoque', 'Node2D', props=[('script', sc)])
    d.save('scenes/effects/shockwave.tscn')


PT = dict(pillar_tall='PilarAlto', pillar_short='PilarBaixo', pillar_stump='PilarCoto', pillar_broken='PilarQuebrado',
          statue_lantern='EstatuaLanterna', statue_prayer='EstatuaOracao', brazier='Braseiro', blue_pedestal='PedestalAzul',
          candles='Velas', crystal_0='CristalA', crystal_1='CristalB', plant_0='ArbustoA', plant_1='ArbustoB', plant_2='Hera',
          rubble_0='EntulhoA', rubble_1='EntulhoB', rubble_2='EntulhoC', signpost='Placa', gate_0='PortaoParte1', gate_1='PortaoParte2',
          gate_2='PortaoParte3', gate_3='PortaoParte4', gate_veil='VeuDoPortao', portal_plane='PortalRoxo')
BIAS = {'gate_0': 10, 'gate_1': 10, 'gate_2': 10, 'gate_3': 10, 'gate_veil': 10, 'portal_plane': 10}


def props():
    for name, m in PROPS.items():
        if name not in PT:
            continue
        bias = BIAS.get(name, 0)
        d = Doc('scene')
        sc = d.ext_res('Script', S('scripts/world/prop.gd'))
        rp = [('script', sc)]
        if m['solid'] > 0:
            rp.append(('blocks_navigation', 'true'))
        if m.get('tall'):
            rp.append(('fades_when_hiding_player', 'true'))
        d.node(PT[name], 'Node2D', props=rp)
        off = v2(-m['ax'], -m['ay'] - bias)
        if m['frames'] > 1:
            fr = d.ext_res('SpriteFrames', S(f'resources/frames/prop_{name}.tres'))
            d.node('Sprite', 'AnimatedSprite2D', '.', props=[('sprite_frames', fr), ('autoplay', '"default"'), ('centered', 'false'), ('offset', off)])
        else:
            tex = d.ext_res('Texture2D', m['file'])
            d.node('Sprite', 'Sprite2D', '.', props=[('texture', tex), ('centered', 'false'), ('offset', off)])
        if m['solid'] > 0:
            r = m['solid']
            d.node('Corpo', 'StaticBody2D', '.', props=[('collision_mask', '0')])
            d.node('Colisao', 'CollisionPolygon2D', 'Corpo', props=[('polygon', pva2([(0, -16 * r), (32 * r, 0), (0, 16 * r), (-32 * r, 0)]))])
        if 'light' in m:
            l = m['light']
            c = l['color']
            if name != 'candles':
                light_node(d, c, l['energy'], l['scale'] * 0.55, (l['dx'], l['dy'] - bias), script='scripts/world/flicker_light.gd')
                if not l.get('flicker'):
                    d.nodes[-1]['props'].append(('flicker', 'false'))
            glow = d.ext_res('Texture2D', S('assets/effects/glow.png'))
            add = d.sub('CanvasItemMaterial', [('blend_mode', '1')])
            gs = (0.5, 0.4) if name == 'candles' else (1.1, 0.8)
            d.node('Brilho', 'Sprite2D', '.', props=[('material', add), ('modulate', col(c[0], c[1], c[2], 0.3 if name == 'candles' else 0.45)),
                                                    ('position', v2(l['dx'], l['dy'] - bias)), ('scale', v2(*gs)), ('texture', glow)])
            if name in ('brazier', 'blue_pedestal'):
                pc = col(1.0, 0.7, 0.3, 0.9) if name == 'brazier' else col(0.5, 0.8, 1.0, 0.9)
                d.node('Brasas', 'CPUParticles2D', '.', props=[
                    ('z_index', '3'), ('position', v2(l['dx'], l['dy'] + 2)), ('amount', '5'), ('lifetime', '1.6'), ('direction', v2(0, -1)),
                    ('spread', '25.0'), ('gravity', v2(0, -6)), ('initial_velocity_min', '8.0'), ('initial_velocity_max', '22.0'),
                    ('scale_amount_min', '1.0'), ('scale_amount_max', '1.8'), ('color', pc)])
        d.save(f'scenes/world/props/{name}.tscn')
    # peca de parede
    d = Doc('scene')
    sc = d.ext_res('Script', S('scripts/world/wall_piece.gd'))
    tex = d.ext_res('Texture2D', S('assets/environments/wall_h3_v0.png'))
    d.node('Parede', 'Sprite2D', props=[('texture', tex), ('centered', 'false'), ('offset', v2(-32, -114)), ('script', sc)])
    d.save('scenes/world/pieces/parede.tscn')


def main():
    player_scene(); enemies(); effects(); props()
    print('cenas de atores, efeitos e props ok')


if __name__ == '__main__':
    main()
