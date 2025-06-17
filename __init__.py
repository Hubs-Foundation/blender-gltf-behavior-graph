from . import (behavior_graph, components, ui)
from bpy.app.handlers import persistent
import bpy
from bpy.types import PropertyGroup
from bpy.props import IntVectorProperty, PointerProperty


bl_info = {
    "name": "Behavior Graph Editor",
    "blender": (3, 2, 0),
    "category": "Node",
    "author": "netpro2k, keianhzo",
    "version": (0, 0, 4),
    "location": "Node Editor > Sidebar > Behavior Graph",
    "description": "Create and export GLTF KHR_behavior graphs using Blender's node group editor"
}

glTF2ExportUserExtension = behavior_graph.glTF2ExportUserExtension
glTF2_pre_export_callback = behavior_graph.glTF2_pre_export_callback
glTF2_post_export_callback = behavior_graph.glTF2_post_export_callback


class BGGlobalProps(PropertyGroup):
    version: IntVectorProperty(name="version",
                               description="The BGs add-on version last used by this file",
                               default=(0, 0, 0),
                               size=3)


@persistent
def load_post(dummy):
    from .migrations import migrate
    migrate()


@persistent
def save_post(dummy):
    for scene in bpy.data.scenes:
        scene.bg_global_props.version = bl_info["version"]
    for object in bpy.data.objects:
        object.bg_global_props.version = bl_info["version"]
    for node_tree in bpy.data.node_groups:
        node_tree.bg_global_props.version = bl_info["version"]


def register():
    components.register()
    ui.register()
    behavior_graph.register()

    bpy.utils.register_class(BGGlobalProps)
    bpy.types.Scene.bg_global_props = PointerProperty(type=BGGlobalProps)
    bpy.types.Object.bg_global_props = PointerProperty(type=BGGlobalProps)
    bpy.types.NodeTree.bg_global_props = PointerProperty(type=BGGlobalProps)

    if load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_post)

    if load_post not in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.append(save_post)



def unregister():
    behavior_graph.unregister()
    ui.unregister()
    components.unregister()

    bpy.utils.unregister_class(BGGlobalProps)
    del bpy.types.Scene.bg_global_props
    del bpy.types.Object.bg_global_props
    del bpy.types.NodeTree.bg_global_props

    if load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post)

    if load_post in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.remove(save_post)


if __name__ == "__main__":
    register()
