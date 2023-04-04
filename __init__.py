bl_info = {
    "name": "Behavior Graph Editor",
    "blender": (3, 2, 0),
    "category": "Node",
    "author": "netpro2k",
    "version": (0, 0, 1),
    "location": "Node Editor > Sidebar > Behavior Graph",
    "description": "Create and export GLTF KHR_behavior graphs using Blender's node group editor"
}

# import bpy
from . import behavior_graph_nodes

glTF2ExportUserExtension = behavior_graph_nodes.glTF2ExportUserExtension

def register():
    behavior_graph_nodes.register()
    # behavior_graph_exporter.register()

def unregister():
    behavior_graph_nodes.unregister()
    # behavior_graph_exporter.unregister()

if __name__ == "__main__":
    register()
