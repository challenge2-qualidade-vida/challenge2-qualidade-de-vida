"""Tópico 25: modela e renderiza um gato em 3D no Blender, com pelo de verdade.

Rodar (sem abrir a janela do Blender):
    Blender --background --python experimentos/gatos3d/gato.py -- --gato mia --teste saida.png

A cabeça gira em torno do pescoço; as poses renderizadas viram a grade que o site usa
para olhar na direção do mouse (ver grade.py).
"""

import argparse
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

# ---------- Personagens ----------
GATOS = {
    "mia": {"pelo": (0.035, 0.035, 0.045), "branco": (1.0, 0.97, 0.9), "olho": (0.85, 0.52, 0.05), "coleira": (0.75, 0.12, 0.10)},
}


# Poses da grade, em graus. O site escolhe a pose conforme a posição do mouse.
YAWS = tuple(range(-36, 37, 6))
PITCHES = tuple(range(16, -17, -4))


def limpar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(nome, cor, rugosidade=0.5, metal=0.0, emissao=0.0):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*cor, 1)
    b.inputs["Roughness"].default_value = rugosidade
    b.inputs["Metallic"].default_value = metal
    return m


def metabolas(nome, elementos, resolucao=0.03):
    """Une bolas e elipsoides em uma superfície orgânica contínua."""
    dados = bpy.data.metaballs.new(nome)
    dados.resolution = resolucao
    dados.render_resolution = resolucao
    dados.threshold = 0.6
    for tipo, pos, medida in elementos:
        e = dados.elements.new(type=tipo)
        e.co = pos
        if tipo == "BALL":
            e.radius = medida
        else:
            e.radius = 1.0
            e.size_x, e.size_y, e.size_z = medida
    obj = bpy.data.objects.new(nome, dados)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    malha = bpy.context.view_layer.objects.active
    malha.name = nome
    bpy.ops.object.shade_smooth()
    r = malha.modifiers.new("alisar", "SMOOTH")
    r.iterations = 12
    r.factor = 0.7
    bpy.ops.object.modifier_apply(modifier="alisar")
    malha.select_set(False)
    return malha


def corrente(a, b, n, r1, r2):
    """Bolas em linha, para pernas e rabo."""
    return [("BALL", tuple(Vector(a).lerp(Vector(b), i / (n - 1))), r1 + (r2 - r1) * i / (n - 1)) for i in range(n)]


def elipsoide(nome, pos, escala, mat, pai=None, seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, location=pos)
    o = bpy.context.active_object
    o.name = nome
    o.scale = escala
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    if pai:
        o.parent = pai
        o.matrix_parent_inverse = pai.matrix_world.inverted()
    return o


def mat_olho(cor):
    """Íris com anel escuro, pupila e córnea brilhante, em uma esfera voltada para -Y."""
    m = bpy.data.materials.new("olho")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.02
    coord = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(coord.outputs["Object"], sep.inputs[0])
    # Distância ao eixo de visão do olho (Y local).
    mx, mz, som, raiz = n.new("ShaderNodeMath"), n.new("ShaderNodeMath"), n.new("ShaderNodeMath"), n.new("ShaderNodeMath")
    mx.operation = mz.operation = "POWER"
    mx.inputs[1].default_value = mz.inputs[1].default_value = 2
    l.new(sep.outputs["X"], mx.inputs[0])
    l.new(sep.outputs["Z"], mz.inputs[0])
    som.operation = "ADD"
    l.new(mx.outputs[0], som.inputs[0])
    l.new(mz.outputs[0], som.inputs[1])
    raiz.operation = "SQRT"
    l.new(som.outputs[0], raiz.inputs[0])
    rampa = n.new("ShaderNodeValToRGB")
    r = rampa.color_ramp
    r.interpolation = "LINEAR"
    r.elements[0].position = 0.0
    r.elements[0].color = (0.005, 0.004, 0.003, 1)
    r.elements[1].position = 1.0
    r.elements[1].color = (0.92, 0.9, 0.85, 1)
    claro = tuple(min(1, c * 1.5) for c in cor)
    escuro = tuple(c * 0.35 for c in cor)
    for pos, c in [(0.36, (0.005, 0.004, 0.003)), (0.39, claro), (0.58, cor), (0.64, escuro), (0.67, (0.01, 0.008, 0.005)), (0.695, (0.95, 0.93, 0.88))]:
        e = r.elements.new(pos)
        e.color = (*c, 1)
    l.new(raiz.outputs[0], rampa.inputs["Fac"])
    l.new(rampa.outputs["Color"], b.inputs["Base Color"])
    return m


def pintar(malha, peso_branco, excluir=None):
    """Grupos de vértices para o pelo escuro e o branco, e a cor da pele por baixo."""
    gb, ge = malha.vertex_groups.new(name="branco"), malha.vertex_groups.new(name="escuro")
    cores = malha.data.color_attributes.new("cor", "FLOAT_COLOR", "POINT")
    for v in malha.data.vertices:
        w = malha.matrix_world @ v.co
        b = max(0.0, min(1.0, peso_branco(w)))
        fora = excluir(w) if excluir else False
        gb.add([v.index], 0.0 if fora else b, "REPLACE")
        ge.add([v.index], 0.0 if fora else 1 - b, "REPLACE")
        cores.data[v.index].color = (b, b, b, 1)


def mat_pele(g):
    m = bpy.data.materials.new("pele")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.8
    at = n.new("ShaderNodeVertexColor")
    at.layer_name = "cor"
    mix = n.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*g["pelo"], 1)
    mix.inputs["B"].default_value = (*g["branco"], 1)
    l.new(at.outputs["Color"], mix.inputs["Factor"])
    l.new(mix.outputs["Result"], b.inputs["Base Color"])
    return m


def mat_pelo(nome, cor):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    saida = n.new("ShaderNodeOutputMaterial")
    h = n.new("ShaderNodeBsdfHairPrincipled")
    h.parametrization = "COLOR"
    h.inputs["Color"].default_value = (*cor, 1)
    h.inputs["Roughness"].default_value = 0.42
    h.inputs["Radial Roughness"].default_value = 0.65
    h.inputs["Random Roughness"].default_value = 0.3
    l.new(h.outputs[0], saida.inputs[0])
    return m


def pelo(malha, grupo, indice_mat, qtd, comprimento, penteado=(0, 0.2, -0.75), filhos=10, raio=0.0017):
    """Pelo curto e penteado: `penteado` é a direção do fio, como fração do comprimento."""
    mod = malha.modifiers.new(f"pelo_{grupo}", "PARTICLE_SYSTEM")
    ps = mod.particle_system
    ps.vertex_group_density = grupo
    s = ps.settings
    s.type = "HAIR"
    s.count = qtd
    s.emit_from = "FACE"
    s.use_modifier_stack = True
    s.material = indice_mat
    s.hair_step = 4
    s.display_step = 3
    s.render_step = 4
    s.hair_length = comprimento
    s.normal_factor = comprimento * 0.42
    s.tangent_factor = 0.0
    s.factor_random = comprimento * 0.1
    s.object_align_factor = tuple(comprimento * c for c in penteado)
    s.child_type = "INTERPOLATED"
    s.child_percent = 2
    s.rendered_child_count = filhos
    s.child_radius = 0.02
    s.clump_factor = 0.18
    s.clump_shape = -0.2
    s.roughness_1 = comprimento * 0.015
    s.roughness_1_size = 1.0
    s.roughness_2 = comprimento * 0.02
    s.roughness_2_size = 3.0
    s.roughness_endpoint = comprimento * 0.05
    s.root_radius = 1.0
    s.tip_radius = 0.05
    s.radius_scale = raio
    return ps


def montar(nome, qualidade=1.0):
    g = GATOS[nome]
    pele = mat_pele(g)
    escuro = mat_pelo("pelo_escuro", g["pelo"])
    branco = mat_pelo("pelo_branco", g["branco"])

    # ---------- Corpo sentado, de frente para -Y ----------
    corpo = metabolas("corpo", [
        ("ELLIPSOID", (0, 0.02, 0.66), (0.40, 0.36, 0.42)),
        ("ELLIPSOID", (0, 0.16, 0.34), (0.50, 0.50, 0.36)),
        ("BALL", (0.36, 0.25, 0.27), 0.42), ("BALL", (-0.36, 0.25, 0.27), 0.42),
        ("BALL", (0, -0.02, 0.98), 0.5),
        *corrente((0.17, -0.2, 0.62), (0.18, -0.29, 0.12), 6, 0.27, 0.22),
        *corrente((-0.17, -0.2, 0.62), (-0.18, -0.29, 0.12), 6, 0.27, 0.22),
        ("ELLIPSOID", (0.19, -0.37, 0.07), (0.12, 0.16, 0.08)), ("ELLIPSOID", (-0.19, -0.37, 0.07), (0.12, 0.16, 0.08)),
        ("ELLIPSOID", (0.5, -0.1, 0.07), (0.13, 0.2, 0.08)), ("ELLIPSOID", (-0.5, -0.1, 0.07), (0.13, 0.2, 0.08)),
        *corrente((0.3, 0.55, 0.12), (0.72, 0.28, 0.1), 6, 0.2, 0.18),
        *corrente((0.72, 0.28, 0.1), (0.78, -0.25, 0.12), 6, 0.18, 0.15),
    ])
    corpo.data.materials.append(pele)
    corpo.data.materials.append(escuro)
    corpo.data.materials.append(branco)

    def branco_corpo(p):
        peito = 1.3 - (abs(p.x) / 0.27) ** 2 - ((p.z - 0.6) / 0.56) ** 2 if p.y < 0.05 else -1
        patas = (0.24 - p.z) / 0.06 if abs(p.x) < 0.4 and p.y < 0.0 else -1
        ponta_rabo = (-0.05 - p.y) / 0.08 if p.x > 0.6 else -1
        return max(peito * 3, patas, ponta_rabo)

    pintar(corpo, branco_corpo)

    # ---------- Cabeça: tudo aqui gira junto em torno do pescoço ----------
    pivo = bpy.data.objects.new("pivo_cabeca", None)
    pivo.location = (0, 0, 1.25)   # as peças são criadas aqui e depois descem e crescem
    bpy.context.collection.objects.link(pivo)
    bpy.context.view_layer.update()

    cabeca = metabolas("cabeca", [
        ("ELLIPSOID", (0, -0.05, 1.68), (0.56, 0.48, 0.47)),
        ("BALL", (0.3, -0.2, 1.52), 0.32), ("BALL", (-0.3, -0.2, 1.52), 0.32),
        ("ELLIPSOID", (0.11, -0.45, 1.52), (0.15, 0.13, 0.11)), ("ELLIPSOID", (-0.11, -0.45, 1.52), (0.15, 0.13, 0.11)),
        ("ELLIPSOID", (0, -0.42, 1.44), (0.11, 0.11, 0.08)),
    ], 0.022)
    cabeca.data.materials.append(pele)
    cabeca.data.materials.append(escuro)
    cabeca.data.materials.append(branco)

    OLHO_X, OLHO_Y, OLHO_Z, OLHO_R = 0.235, -0.372, 1.71, 0.17
    NARIZ = Vector((0, -0.59, 1.56))

    def branco_cabeca(p):
        # Máscara branca: focinho, queixo e uma listra que sobe entre os olhos.
        focinho = 1.0 - ((p.x / 0.3) ** 2 + ((p.z - 1.46) / 0.17) ** 2) if p.y < -0.12 else -1
        listra = 1.0 - (p.x / (0.05 + max(0, 1.6 - p.z) * 0.6)) ** 2 if p.y < -0.05 and p.z < 2.0 else -1
        return max(focinho * 4, listra * 3)

    def sem_pelo(p):
        olho = any((p - Vector((s * OLHO_X, OLHO_Y, OLHO_Z))).length < OLHO_R * 0.98 for s in (1, -1))
        return olho or (p - NARIZ).length < 0.05

    pintar(cabeca, branco_cabeca, sem_pelo)
    cabeca.parent = pivo
    cabeca.matrix_parent_inverse = pivo.matrix_world.inverted()

    # Orelhas: pirâmides achatadas, com a parte de dentro rosada.
    def orelha(s):
        bm = bmesh.new()
        topo = (s * 0.47, 0.0, 2.2)
        base = [(s * 0.2, -0.11, 1.96), (s * 0.54, -0.07, 1.82), (s * 0.48, 0.17, 1.82), (s * 0.18, 0.13, 1.98)]
        vs = [bm.verts.new(p) for p in base]
        t = bm.verts.new(topo)
        for i in range(4):
            bm.faces.new((vs[i], vs[(i + 1) % 4], t))
        bm.faces.new(vs[::-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
        d = bpy.data.meshes.new("orelha")
        bm.to_mesh(d)
        bm.free()
        o = bpy.data.objects.new("orelha", d)
        bpy.context.collection.objects.link(o)
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.ops.object.shade_smooth()
        r = o.modifiers.new("alisar", "SMOOTH")
        r.iterations = 10
        bpy.ops.object.modifier_apply(modifier="alisar")
        o.select_set(False)
        o.data.materials.append(pele)
        o.data.materials.append(escuro)
        o.data.materials.append(branco)
        pintar(o, lambda p: 0.0)
        o.parent = pivo
        o.matrix_parent_inverse = pivo.matrix_world.inverted()
        return o

    orelhas = [orelha(1), orelha(-1)]
    rosa = material("rosa", (0.75, 0.32, 0.32), 0.55)
    for s in (1, -1):
        interno = elipsoide("orelha_dentro", (s * 0.385, -0.078, 1.97), (0.08, 0.02, 0.145), rosa, pivo)
        interno.rotation_euler = (0, s * 0.42, 0)

    # Olhos: cada um gira no próprio centro, para olhar além do que a cabeça vira.
    olhos = []
    mo = mat_olho(g["olho"])
    for s in (1, -1):
        o = elipsoide("olho", (s * OLHO_X, OLHO_Y, OLHO_Z), (OLHO_R, OLHO_R, OLHO_R), mo, pivo, 64)
        olhos.append(o)
    # Pálpebra: uma casca colada no olho, cobrindo só a parte de cima.
    mat_palpebra = material("palpebra", g["pelo"], 0.65)
    for lado in (1, -1):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=OLHO_R * 1.04)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < OLHO_R * 0.42], context="VERTS")
        d = bpy.data.meshes.new("palpebra")
        bm.to_mesh(d)
        bm.free()
        for pol in d.polygons:
            pol.use_smooth = True
        d.materials.append(mat_palpebra)
        o = bpy.data.objects.new("palpebra", d)
        o.location = (lado * OLHO_X, OLHO_Y, OLHO_Z)
        o.rotation_euler = (0, lado * 0.16, 0)
        bpy.context.collection.objects.link(o)
        bpy.context.view_layer.update()
        o.parent = pivo
        o.matrix_parent_inverse = pivo.matrix_world.inverted()

    nariz = elipsoide("nariz", tuple(NARIZ), (0.05, 0.03, 0.033), material("nariz", (0.55, 0.16, 0.2), 0.25), pivo)
    boca = material("boca", (0.02, 0.01, 0.01), 0.6)
    for s in (1, -1):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.058, minor_radius=0.0075, location=(s * 0.057, -0.565, 1.5))
        t = bpy.context.active_object
        t.rotation_euler = (math.pi / 2, 0, 0)
        t.data.materials.append(boca)
        bpy.ops.object.shade_smooth()
        t.parent = pivo
        t.matrix_parent_inverse = pivo.matrix_world.inverted()
        # Metade de baixo do arco forma o "w" da boca de gato.
        bm = bmesh.new()
        bm.from_mesh(t.data)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y > 0.004 or True and (t.matrix_world @ v.co).z > 1.5], context="VERTS")
        bm.to_mesh(t.data)
        bm.free()

    # Bigodes.
    mb = material("bigode", (0.9, 0.88, 0.82), 0.4)
    for s in (1, -1):
        for i, (dz, dx) in enumerate([(0.05, 0.62), (0.0, 0.68), (-0.05, 0.6)]):
            c = bpy.data.curves.new("bigode", "CURVE")
            c.dimensions = "3D"
            c.bevel_depth = 0.0028
            spl = c.splines.new("BEZIER")
            spl.bezier_points.add(1)
            a, b = spl.bezier_points
            a.co = (s * 0.16, -0.5, 1.5 + dz * 0.4)
            b.co = (s * (0.16 + dx), -0.34, 1.5 + dz * 2.2 - 0.03)
            a.handle_left_type = a.handle_right_type = b.handle_left_type = b.handle_right_type = "AUTO"
            ob = bpy.data.objects.new("bigode", c)
            c.materials.append(mb)
            bpy.context.collection.objects.link(ob)
            ob.parent = pivo
            ob.matrix_parent_inverse = pivo.matrix_world.inverted()

    # Coleira com moeda, a marca da EconoMIA.
    bpy.ops.mesh.primitive_torus_add(major_radius=0.43, minor_radius=0.04, location=(0, -0.02, 0.97), major_segments=64, minor_segments=16)
    col = bpy.context.active_object
    col.scale = (1.0, 0.95, 0.7)
    col.rotation_euler = (0.16, 0, 0)
    bpy.ops.object.shade_smooth()
    col.data.materials.append(material("coleira", g["coleira"], 0.5))
    ouro = material("ouro", (1.0, 0.72, 0.2), 0.22, 1.0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.1, depth=0.02, location=(0, -0.475, 0.86), rotation=(math.pi / 2 + 0.12, 0, 0))
    moeda = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    moeda.data.materials.append(ouro)

    # A cabeça desce sobre o pescoço e cresce, como nos personagens de animação.
    pivo.location = (0, -0.03, 0.96)
    pivo.scale = (1.36, 1.36, 1.36)

    # ---------- Pelo ----------
    q = qualidade
    bpy.context.view_layer.update()
    pelo(corpo, "escuro", 2, int(16000 * q), 0.085)
    pelo(corpo, "branco", 3, int(14000 * q), 0.08)
    # Na cabeça, o pelo sai do focinho e corre para trás e para cima.
    pelo(cabeca, "escuro", 2, int(16000 * q), 0.045, penteado=(0, 0.85, 0.35), raio=0.0013)
    pelo(cabeca, "branco", 3, int(9000 * q), 0.03, penteado=(0, 0.75, -0.1), raio=0.0013)
    for o in orelhas:
        pelo(o, "escuro", 2, int(1600 * q), 0.02, penteado=(0, 0.1, 0.7), raio=0.0011)
    return pivo, olhos


def luz_e_camera():
    mundo = bpy.data.worlds.new("mundo")
    bpy.context.scene.world = mundo
    mundo.use_nodes = True
    fundo = mundo.node_tree.nodes["Background"]
    fundo.inputs[0].default_value = (1.0, 0.86, 0.55, 1)
    fundo.inputs[1].default_value = 0.22

    def luz(nome, pos, energia, tam, cor, alvo=(0, 0, 1.2)):
        d = bpy.data.lights.new(nome, "AREA")
        d.energy = energia
        d.size = tam
        d.color = cor
        o = bpy.data.objects.new(nome, d)
        o.location = pos
        bpy.context.collection.objects.link(o)
        direcao = Vector(alvo) - Vector(pos)
        o.rotation_euler = direcao.to_track_quat("-Z", "Y").to_euler()

    luz("principal", (-3, -4.5, 4), 150, 4.5, (1, 0.96, 0.88))
    luz("preenche", (3.5, -3.5, 1.5), 50, 5, (1, 0.92, 0.76))
    luz("recorte", (0.5, 4, 3.6), 110, 3, (1, 0.9, 0.7))
    luz("recorte2", (-3, 3, 1.8), 40, 3, (1, 0.85, 0.6))

    cam = bpy.data.cameras.new("cam")
    cam.lens = 85
    o = bpy.data.objects.new("cam", cam)
    o.location = (0, -8.2, 1.35)
    bpy.context.collection.objects.link(o)
    o.rotation_euler = (Vector((0, 0, 1.0)) - Vector(o.location)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = o


def configurar_render(largura, altura, amostras):
    c = bpy.context.scene
    c.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
    c.cycles.device = "GPU"
    c.cycles.samples = amostras
    c.cycles.use_denoising = True
    c.render.film_transparent = True
    c.render.resolution_x, c.render.resolution_y = largura, altura
    c.render.image_settings.file_format = "PNG"
    c.render.image_settings.color_mode = "RGBA"
    c.view_settings.view_transform = "Standard"
    c.view_settings.exposure = 0.55
    c.render.use_persistent_data = True   # não recria o pelo a cada pose


def pose(pivo, olhos, yaw, pitch, olhar=1.6):
    """Graus: yaw > 0 olha para a direita da tela; pitch > 0 olha para baixo."""
    pivo.rotation_euler = (math.radians(pitch), 0, math.radians(yaw))
    for o in olhos:
        o.rotation_euler = (math.radians(pitch * (olhar - 1)), 0, math.radians(yaw * (olhar - 1)))


def main():
    arg = argparse.ArgumentParser()
    arg.add_argument("--gato", default="mia")
    arg.add_argument("--teste")
    arg.add_argument("--grade", help="pasta onde salvar uma imagem por pose")
    arg.add_argument("--yaw", type=float, default=0)
    arg.add_argument("--pitch", type=float, default=0)
    arg.add_argument("--amostras", type=int, default=48)
    arg.add_argument("--largura", type=int, default=520)
    arg.add_argument("--altura", type=int, default=720)
    arg.add_argument("--qualidade", type=float, default=1.0)
    a = arg.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    limpar()
    pivo, olhos = montar(a.gato, a.qualidade)
    luz_e_camera()
    configurar_render(a.largura, a.altura, a.amostras)
    if a.grade:
        pasta = Path(a.grade).resolve()
        pasta.mkdir(parents=True, exist_ok=True)
        for iy, pitch in enumerate(PITCHES):
            for ix, yaw in enumerate(YAWS):
                arquivo = pasta / f"p_{iy}_{ix}.png"
                if arquivo.exists():
                    continue
                pose(pivo, olhos, yaw, pitch)
                bpy.context.scene.render.filepath = str(arquivo)
                bpy.ops.render.render(write_still=True)
                print("POSE", iy, ix, flush=True)
        print("GRADE PRONTA")
        return
    pose(pivo, olhos, a.yaw, a.pitch)
    bpy.context.scene.render.filepath = str(Path(a.teste).resolve())
    bpy.ops.render.render(write_still=True)
    print("PRONTO", a.teste)


if __name__ == "__main__":
    main()
