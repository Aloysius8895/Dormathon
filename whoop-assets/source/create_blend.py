"""Run inside Blender: blender --background --python source/create_blend.py
Produces model/whoop-source.blend from the supplied standard GLB.
Blender >= 4.0 required. No add-on or network dependency.
"""
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parent.parent
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'model/whoop-web.glb'))
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1.0
bpy.context.scene['asset_status']='Concept reconstruction; internal structure illustrative'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'model/whoop-source.blend'))
print('Saved editable .blend with groups, materials and animation clips.')
