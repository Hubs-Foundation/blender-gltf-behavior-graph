import bpy
from . import bl_info


def migrate_0_0_1():
    ''' Since v0.0.2 we use the Blender coordinate system for all vectors and we swizzle when exporting.
        This migration updates all existing vectors for pre 0.0.2 files.'''
    def migrate_sockets_coords(socket):
        if not socket.is_linked:
            if socket.bl_idname == "NodeSocketVectorXYZ" or socket.bl_idname == "NodeSocketVectorEuler":
                copy = socket.default_value.copy()
                socket.default_value[1] = copy[2]
                socket.default_value[2] = copy[1]

    def migrate_graph(graph):
        for node in graph.nodes:
            for socket in node.inputs:
                migrate_sockets_coords(socket)

    def migrate_graphs(target):
        for graph in target.bg_slots:
            migrate_graph(graph.graph)

    def migrate_variables(target):
        for var in target.bg_global_variables:
            if var.type == "vec3":
                copy = var.defaultVec3.copy()
                var.defaultVec3[1] = copy[2]
                var.defaultVec3[2] = copy[1]

    def migrate_events(target):
        for event in target.bg_custom_events:
            if (len(event.parameters) > 0):
                parameter = event.parameters[event.parameter_index]
                if parameter.type == "vec3":
                    copy = parameter.defaultVec3.copy()
                    parameter.defaultVec3[1] = copy[2]
                    parameter.defaultVec3[2] = copy[1]

    for scene in bpy.data.scenes:
        migrate_graphs(scene)
        migrate_variables(scene)
        migrate_events(scene)

    for object in bpy.data.objects:
        migrate_graphs(object)
        migrate_variables(object)
        migrate_events(object)

    for graph in bpy.data.node_groups:
        migrate_variables(graph)
        migrate_events(graph)


def migrate():
    authoring_version = bpy.context.scene.bg_global_props.version

    for version in MIGRATIONS:
        if (authoring_version[0], authoring_version[1], authoring_version[2]) < version:
            MIGRATIONS[version]()


MIGRATIONS = {
    (0, 0, 1): migrate_0_0_1
}
