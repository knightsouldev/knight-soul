"""Etapa 2b: cenas de interface (HUD, pausa, tela final, menu principal)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from tscn import *

S = lambda p: f'res://{p}'
GOLD = (0.86, 0.72, 0.42)
GOLD_DIM = (0.62, 0.5, 0.3)
THEME = S('resources/themes/tema_medieval.tres')


class UI:
    def __init__(self, root_name, root_type, root_props, theme=True):
        self.d = Doc('scene')
        self.root = root_name
        self.gloock = self.d.ext_res('FontFile', S('assets/fonts/Gloock-Regular.ttf'))
        self.d.node(root_name, root_type, props=root_props)

    def tex(self, n):
        return self.d.ext_res('Texture2D', S(f'assets/ui/{n}.png'))

    @staticmethod
    def pos(x, y, w, h):
        return [('layout_mode', '0'), ('offset_left', num(x)), ('offset_top', num(y)), ('offset_right', num(x + w)), ('offset_bottom', num(y + h))]

    @staticmethod
    def anch(ax, ay, x, y, w, h):
        return [('layout_mode', '1'), ('anchors_preset', '-1'), ('anchor_left', num(ax)), ('anchor_top', num(ay)), ('anchor_right', num(ax)),
                ('anchor_bottom', num(ay)), ('offset_left', num(x)), ('offset_top', num(y)), ('offset_right', num(x + w)),
                ('offset_bottom', num(y + h))]

    @staticmethod
    def full():
        return [('layout_mode', '1'), ('anchors_preset', '15'), ('anchor_right', '1.0'), ('anchor_bottom', '1.0'),
                ('grow_horizontal', '2'), ('grow_vertical', '2')]

    def add(self, name, typ, parent, props, unique=False, groups=None):
        p = list(props)
        if unique:
            p.append(('unique_name_in_owner', 'true'))
        self.d.node(name, typ, parent, props=p, groups=groups)

    def ctl(self, name, parent, props, unique=False):
        self.add(name, 'Control', parent, [('mouse_filter', '2')] + props, unique)

    def img(self, name, parent, tex, props, unique=False, stretch=False, mod=None):
        p = props + [('mouse_filter', '2'), ('texture', self.tex(tex))]
        if stretch:
            p = p[:-1] + [('texture', self.tex(tex)), ('expand_mode', '1'), ('stretch_mode', '0')]
        if mod:
            p.append(('modulate', mod))
        self.add(name, 'TextureRect', parent, p, unique)

    def nine(self, name, parent, tex, props, margins):
        l, t, r, b = margins
        self.add(name, 'NinePatchRect', parent, props + [('mouse_filter', '2'), ('texture', self.tex(tex)), ('patch_margin_left', str(l)),
                                                        ('patch_margin_top', str(t)), ('patch_margin_right', str(r)), ('patch_margin_bottom', str(b))])

    def label(self, name, parent, text, props, size=13, color=GOLD, title=False, align=0, outline=3, unique=False, autowrap=False):
        p = props + [('mouse_filter', '2'), ('text', q(text)), ('horizontal_alignment', str(align))]
        if title:
            p.append(('theme_override_fonts/font', self.gloock))
        p += [('theme_override_colors/font_color', col(*color)), ('theme_override_colors/font_outline_color', col(0, 0, 0, 0.9)),
              ('theme_override_constants/outline_size', str(outline)), ('theme_override_font_sizes/font_size', str(size))]
        self.add(name, 'Label', parent, p, unique)

    def bar(self, name, parent, x, y, w, h, fill_tex, prefix, frame_x, frame_y, frame_w, frame_h, frame_tex='bar_frame', margins=(10, 4, 10, 4)):
        """Barra com Fundo + Rastro (dano recente) + Preenchimento + Moldura."""
        self.ctl(name, parent, self.pos(x, y, w, h))
        self.img('Fundo', f'{parent}/{name}', 'bar_bg', self.pos(0, 0, w, h), stretch=True)
        for nm, tx, uniq in (('Rastro', 'bar_trail', f'{prefix}Rastro'), ('Preenchimento', fill_tex, f'{prefix}Preenchimento')):
            self.add(uniq, 'TextureProgressBar', f'{parent}/{name}',
                     self.pos(0, 0, w, h) + [('mouse_filter', '2'), ('max_value', '1.0'), ('step', '0.0001'), ('value', '1.0'),
                                            ('nine_patch_stretch', 'true'), ('stretch_margin_left', '2'), ('stretch_margin_top', '2'),
                                            ('stretch_margin_right', '2'), ('stretch_margin_bottom', '2'), ('texture_progress', self.tex(tx))],
                     unique=True)
        self.nine(f'Moldura{name}', parent, frame_tex, self.pos(frame_x, frame_y, frame_w, frame_h), margins)

    def connect(self, sig, frm, method):
        self.d.connect(sig, frm, '.', method)

    def save(self, path):
        self.d.save(path)


def hud():
    u = UI('Hud', 'CanvasLayer', [('layer', '10'), ('script', 'ExtResource("hudscript")')])
    sc = u.d.ext_res('Script', S('scripts/ui/hud.gd'))
    u.d.nodes[0]['props'] = [('layer', '10'), ('script', sc)]
    u.add('Raiz', 'Control', '.', u.full() + [('mouse_filter', '2'), ('theme', u.d.ext_res('Theme', THEME))])
    R = 'Raiz'
    u.img('Vinheta', R, 'vignette', u.full(), unique=True, stretch=True, mod=col(1, 1, 1, 0.55))
    # ---- canto superior esquerdo
    u.ctl('CantoSuperiorEsquerdo', R, u.pos(8, 6, 260, 72))
    P = f'{R}/CantoSuperiorEsquerdo'
    u.bar('BarraVida', P, 62, 14, 150, 8, 'bar_red', 'Vida', 58, 10, 158, 16)
    u.bar('BarraStamina', P, 62, 32, 118, 6, 'bar_green', 'Stamina', 58, 28, 126, 14)
    u.img('OrbeGema', P, 'orb_gem', u.pos(12, 12, 36, 36), unique=True)
    u.img('OrbeMoldura', P, 'orb_frame', u.pos(0, 0, 60, 60))
    u.ctl('Frascos', P, u.pos(0, 0, 130, 70))
    for i in range(4):
        u.img(f'Gota{i + 1}', f'{P}/Frascos', 'drop_full', u.pos(64 + i * 14, 48, 11, 14), unique=True)
    # ---- chefe
    u.ctl('PainelChefe', R, u.anch(0.5, 0, -190, 8, 380, 48), unique=True)
    PC = f'{R}/PainelChefe'
    u.label('Nome', PC, 'SENTINELA DA RUÍNA', u.pos(0, 0, 380, 18), 15, GOLD, True, 1)
    u.bar('BarraChefe', PC, 14, 22, 352, 8, 'bar_red', 'Chefe', 8, 17, 364, 18, 'boss_frame', (16, 5, 16, 5))
    u.label('Subtitulo', PC, 'Guardião das Almas Perdidas', u.pos(0, 34, 380, 14), 11, GOLD_DIM, False, 1, 2)
    # ---- atalhos (4 slots)
    u.ctl('Atalhos', R, u.anch(0, 1, 10, -52, 168, 44))
    A = f'{R}/Atalhos'
    icons = ['icon_sword', 'icon_oil', 'icon_flask', 'icon_cloak']
    names = ['Espada', 'Oleo', 'Frasco', 'Manto']
    for i in range(4):
        x = i * 42
        u.ctl(f'Slot{i + 1}_{names[i]}', A, u.pos(x, 0, 38, 38))
        sp = f'{A}/Slot{i + 1}_{names[i]}'
        u.img('Fundo', sp, 'slot', u.pos(0, 0, 38, 38))
        u.img('Icone', sp, icons[i], u.pos(5, 5, 28, 28))
        u.label('Numero', sp, str(i + 1), u.pos(4, 24, 14, 14), 10, GOLD, False, 0, 2)
    u.img('SelecaoSlot', A, 'slot_sel', u.pos(0, 0, 38, 38), unique=True)
    u.label('TextoOleo', f'{A}/Slot2_Oleo', '2', u.pos(27, 22, 14, 14), 11, (1, 0.85, 0.55), False, 0, 2, unique=True)
    u.label('TextoFrascos', f'{A}/Slot3_Frasco', '4', u.pos(27, 22, 14, 14), 11, (0.7, 0.88, 1.0), False, 0, 2, unique=True)
    # ---- almas
    u.ctl('Almas', R, u.anch(1, 1, -112, -38, 102, 28))
    u.nine('Moldura', f'{R}/Almas', 'soul_frame', u.pos(0, 0, 102, 28), (10, 8, 10, 8))
    u.img('Icone', f'{R}/Almas', 'soul_icon', u.pos(80, 6, 16, 16))
    u.label('TextoAlmas', f'{R}/Almas', '0', u.pos(8, 2, 68, 22), 15, (0.92, 0.82, 0.6), True, 2, unique=True)
    # ---- bussola
    u.ctl('Bussola', R, u.anch(0.5, 1, -130, -26, 260, 16))
    u.img('Fundo', f'{R}/Bussola', 'compass', u.pos(0, 0, 260, 14))
    u.img('MarcadorBussola', f'{R}/Bussola', 'compass_marker', u.pos(6, 0, 13, 13), unique=True)
    # ---- objetivo
    u.ctl('Objetivo', R, u.anch(1, 0, -216, 8, 208, 50))
    u.label('NomeArea', f'{R}/Objetivo', 'Ruínas Esquecidas', u.pos(0, 0, 208, 18), 14, GOLD, True, 2)
    u.label('TextoObjetivo', f'{R}/Objetivo', 'Encontre a passagem para a arena', u.pos(0, 20, 208, 14), 11, (0.75, 0.68, 0.55), False, 2, 2, unique=True)
    # ---- textos temporarios
    u.label('Aviso', R, '', u.anch(0.5, 1, -250, -62, 500, 18), 13, (0.95, 0.88, 0.7), False, 1, unique=True)
    u.label('Dica', R, 'WASD mover   Mouse/Clique atacar   Espaço esquivar   Q curar   E usar item   1-4 itens   Esc pausa',
            u.anch(0.5, 1, -330, -80, 660, 16), 11, (0.8, 0.74, 0.6), False, 1, 2, unique=True)
    u.label('TituloArea', R, 'RUÍNAS ESQUECIDAS', u.anch(0.5, 0.3, -300, -20, 600, 40), 30, (0.92, 0.8, 0.52), True, 1, 5, unique=True)
    u.label('SubtituloArea', R, 'Primeira área — Knight Souls', u.anch(0.5, 0.3, -300, 22, 600, 18), 13, GOLD_DIM, False, 1, 2, unique=True)
    u.save('scenes/ui/hud.tscn')


def pause():
    u = UI('MenuPausa', 'CanvasLayer', [])
    sc = u.d.ext_res('Script', S('scripts/ui/pause_menu.gd'))
    u.d.nodes[0]['props'] = [('process_mode', '3'), ('layer', '20'), ('script', sc)]
    u.add('Raiz', 'Control', '.', u.full() + [('theme', u.d.ext_res('Theme', THEME))])
    u.add('Escurecer', 'ColorRect', 'Raiz', u.full() + [('mouse_filter', '2'), ('color', col(0, 0, 0, 0.6))])
    u.nine('Painel', 'Raiz', 'panel', u.anch(0.5, 0.5, -150, -130, 300, 260), (14, 14, 14, 14))
    u.label('Titulo', 'Raiz/Painel', 'PAUSADO', u.pos(0, 16, 300, 28), 22, GOLD, True, 1, 4)
    u.img('Divisor', 'Raiz/Painel', 'divider', u.pos(40, 46, 220, 9), stretch=True)
    u.add('Botoes', 'VBoxContainer', 'Raiz/Painel', u.pos(75, 64, 150, 100) + [('theme_override_constants/separation', '6')])
    for nm, txt, uniq in (('BotaoContinuar', 'Continuar', True), ('BotaoReiniciar', 'Reiniciar', False), ('BotaoMenu', 'Menu principal', False), ('BotaoSair', 'Sair do jogo', False)):
        u.add(nm, 'Button', 'Raiz/Painel/Botoes', [('custom_minimum_size', v2(150, 22)), ('layout_mode', '2'), ('text', q(txt))], unique=uniq)
    u.label('Ajuda', 'Raiz/Painel', 'WASD mover · Clique atacar · Espaço esquivar\nQ curar · E usar item · 1-4 / roda escolhem item\nEsc pausar',
            u.pos(0, 176, 300, 60), 11, (0.75, 0.68, 0.55), False, 1, 2)
    for nm, m in (('BotaoContinuar', '_on_continuar_pressed'), ('BotaoReiniciar', '_on_reiniciar_pressed'), ('BotaoMenu', '_on_menu_pressed'), ('BotaoSair', '_on_sair_pressed')):
        u.connect('pressed', f'Raiz/Painel/Botoes/{nm}', m)
    u.save('scenes/ui/pause_menu.tscn')


def end_screen():
    u = UI('TelaFinal', 'CanvasLayer', [])
    sc = u.d.ext_res('Script', S('scripts/ui/end_screen.gd'))
    u.d.nodes[0]['props'] = [('process_mode', '3'), ('layer', '30'), ('script', sc)]
    u.add('Raiz', 'Control', '.', u.full() + [('theme', u.d.ext_res('Theme', THEME))])
    u.add('Escurecer', 'ColorRect', 'Raiz', u.full() + [('mouse_filter', '2'), ('color', col(0, 0, 0, 0))], unique=True)
    u.label('Titulo', 'Raiz', 'VOCÊ SUCUMBIU', u.anch(0.5, 0.5, -320, -70, 640, 50), 38, (0.72, 0.14, 0.14), True, 1, 6, unique=True)
    u.label('Subtitulo', 'Raiz', '', u.anch(0.5, 0.5, -320, -14, 640, 40), 14, (0.85, 0.78, 0.62), False, 1, 3, unique=True)
    u.add('Botoes', 'VBoxContainer', 'Raiz', u.anch(0.5, 0.5, -75, 40, 150, 100) + [('theme_override_constants/separation', '6')], unique=True)
    for nm, txt, uniq in (('BotaoTentar', 'Tentar novamente', True), ('BotaoContinuar', 'Continuar explorando', True), ('BotaoMenu', 'Menu principal', False)):
        u.add(nm, 'Button', 'Raiz/Botoes', [('custom_minimum_size', v2(150, 22)), ('layout_mode', '2'), ('text', q(txt))], unique=uniq)
    for nm, m in (('BotaoTentar', '_on_tentar_pressed'), ('BotaoContinuar', '_on_continuar_pressed'), ('BotaoMenu', '_on_menu_pressed')):
        u.connect('pressed', f'Raiz/Botoes/{nm}', m)
    u.save('scenes/ui/end_screen.tscn')


def main_menu():
    d = Doc('scene')
    sc = d.ext_res('Script', S('scripts/ui/main_menu.gd'))
    theme = d.ext_res('Theme', THEME)
    u = UI.__new__(UI)
    u.d = d
    u.gloock = d.ext_res('FontFile', S('assets/fonts/Gloock-Regular.ttf'))
    d.node('MenuPrincipal', 'Control', props=UI.full() + [('theme', theme), ('script', sc)])
    far = d.ext_res('Texture2D', S('assets/environments/far_ruins.png'))
    fog = d.ext_res('Texture2D', S('assets/environments/fog.png'))
    d.node('Fundo', 'ColorRect', '.', props=UI.full() + [('mouse_filter', '2'), ('color', col(0.03, 0.04, 0.08, 1))])
    d.node('RuinasAoFundo', 'TextureRect', '.', props=UI.full() + [('mouse_filter', '2'), ('modulate', col(0.6, 0.68, 0.95, 0.8)),
                                                                   ('texture', far), ('expand_mode', '1'), ('stretch_mode', '6')])
    d.node('Neblina', 'TextureRect', '.', props=UI.full() + [('mouse_filter', '2'), ('modulate', col(0.6, 0.7, 1.0, 0.35)),
                                                             ('texture', fog), ('expand_mode', '1'), ('stretch_mode', '0')])
    d.node('Cavaleiro', 'Node2D', '.', props=[('position', v2(560, 380)), ('scale', v2(4, 4))])
    fr = d.ext_res('SpriteFrames', S('resources/frames/player.tres'))
    d.node('Sprite', 'AnimatedSprite2D', 'Cavaleiro', props=[('sprite_frames', fr), ('animation', '&"idle_front"'), ('autoplay', '"idle_front"'),
                                                          ('offset', v2(0, -24))])
    vig = d.ext_res('Texture2D', S('assets/ui/vignette.png'))
    d.node('Vinheta', 'TextureRect', '.', props=UI.full() + [('mouse_filter', '2'), ('texture', vig), ('expand_mode', '1'), ('stretch_mode', '0')])
    u.label('Titulo', '.', 'KNIGHT SOULS', UI.anch(0, 0.5, 60, -150, 520, 60), 44, (0.92, 0.8, 0.5), True, 0, 8)
    u.label('Subtitulo', '.', 'Primeira demo jogável  ·  Ruínas Esquecidas', UI.anch(0, 0.5, 64, -92, 520, 20), 14, GOLD_DIM, False, 0, 3)
    dv = d.ext_res('Texture2D', S('assets/ui/divider.png'))
    d.node('Divisor', 'TextureRect', '.', props=UI.anch(0, 0.5, 60, -62, 260, 11) + [('mouse_filter', '2'), ('texture', dv), ('expand_mode', '1'), ('stretch_mode', '0')])
    d.node('Menu', 'VBoxContainer', '.', props=UI.anch(0, 0.5, 64, -40, 170, 130) + [('theme_override_constants/separation', '8')])
    for nm, txt, uniq in (('BotaoIniciar', 'Iniciar jornada', True), ('BotaoControles', 'Controles', False), ('BotaoSair', 'Sair', False)):
        pr = [('custom_minimum_size', v2(170, 22)), ('layout_mode', '2'), ('text', q(txt))]
        if uniq:
            pr.append(('unique_name_in_owner', 'true'))
        d.node(nm, 'Button', 'Menu', props=pr)
    panel = d.ext_res('Texture2D', S('assets/ui/panel.png'))
    d.node('PainelControles', 'NinePatchRect', '.', props=UI.anch(0, 0.5, 260, -40, 260, 128) + [
        ('mouse_filter', '2'), ('texture', panel), ('patch_margin_left', '14'), ('patch_margin_top', '14'), ('patch_margin_right', '14'),
        ('patch_margin_bottom', '14'), ('unique_name_in_owner', 'true')])
    u.label('Texto', 'PainelControles', 'WASD  mover\nMouse / clique esq.  atacar na direção do cursor\nEspaço  esquivar (invulnerável no início)\nQ  curar   E  usar item   1-4 / roda  escolher\nEsc  pausar',
            UI.pos(14, 12, 240, 104), 12, (0.85, 0.78, 0.62), False, 0, 2)
    d.connect('pressed', 'Menu/BotaoIniciar', '.', '_on_iniciar_pressed')
    d.connect('pressed', 'Menu/BotaoControles', '.', '_on_controles_pressed')
    d.connect('pressed', 'Menu/BotaoSair', '.', '_on_sair_pressed')
    d.save('scenes/main/main_menu.tscn')


def main():
    hud(); pause(); end_screen(); main_menu()
    print('cenas de interface ok')


if __name__ == '__main__':
    main()
