
# frozen crystal look: clear glass with a soft violet core, only the risen sculpture frosts (slab stays clear)
gvol.inputs['Absorption Color'].default_value = (0.92, 0.82, 1.0, 1)
gvol.inputs['Color'].default_value = (0.85, 0.7, 1.0, 1)
gvol.inputs['Emission Color'].default_value = (0.55, 0.2, 1.0, 1)
_geo = gn.nodes.new('ShaderNodeNewGeometry')
_sep = gn.nodes.new('ShaderNodeSeparateXYZ'); gn.links.new(_geo.outputs['Position'], _sep.inputs[0])
_mr = gn.nodes.new('ShaderNodeMapRange')
_mr.inputs['From Min'].default_value = PT + 0.02; _mr.inputs['From Max'].default_value = PT + 0.35
gn.links.new(_sep.outputs['Z'], _mr.inputs['Value'])
_FZ = gn.nodes.new('ShaderNodeValue'); _FZ.outputs[0].default_value = 0.0
def _mul(a_, k):
    m = gn.nodes.new('ShaderNodeMath'); m.operation = 'MULTIPLY'
    gn.links.new(_mr.outputs['Result'], m.inputs[0])
    m2 = gn.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = k
    gn.links.new(m.outputs[0], m2.inputs[0]); gn.links.new(_FZ.outputs[0], m.inputs[1])
    return m2
gn.links.new(_mul(0, 0.05).outputs[0], g.inputs['Roughness'])
gn.links.new(_mul(0, 0.35).outputs[0], gvol.inputs['Density'])
gn.links.new(_mul(0, 0.5).outputs[0], gvol.inputs['Emission Strength'])
_old_update = update
def update(t):
    _old_update(t)
    _FZ.outputs[0].default_value = sm(FREEZE, FREEZE + 0.12, t) * (1 - sm(SHATTER, SHATTER + 0.05, t))
for _o in sc.objects:
    if _o.type == 'LIGHT':
        _o.visible_camera = False
