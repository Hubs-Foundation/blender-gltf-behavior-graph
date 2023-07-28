from . import (behavior_graph, components, ui)
bl_info = {
    "name": "Behavior Graph Editor",
    "blender": (3, 2, 0),
    "category": "Node",
    "author": "netpro2k, keianhzo",
    "version": (0, 0, 1),
    "location": "Node Editor > Sidebar > Behavior Graph",
    "description": "Create and export GLTF KHR_behavior graphs using Blender's node group editor"
}

glTF2ExportUserExtension = behavior_graph.glTF2ExportUserExtension


def register():
    components.register()
    ui.register()
    behavior_graph.register()


def unregister():
    behavior_graph.unregister()
    ui.unregister()
    components.unregister()


if __name__ == "__main__":
    register()
