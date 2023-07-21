from . import hubs_components, behavior_graph_nodes, ui
bl_info = {
    "name": "Behavior Graph Editor",
    "blender": (3, 2, 0),
    "category": "Node",
    "author": "netpro2k, keianhzo",
    "version": (0, 0, 1),
    "location": "Node Editor > Sidebar > Behavior Graph",
    "description": "Create and export GLTF KHR_behavior graphs using Blender's node group editor"
}

glTF2ExportUserExtension = behavior_graph_nodes.glTF2ExportUserExtension


def register():
    ui.register()
    behavior_graph_nodes.register()
    hubs_components.register()


def unregister():
    behavior_graph_nodes.unregister()
    hubs_components.unregister()
    ui.unregister()


if __name__ == "__main__":
    register()
