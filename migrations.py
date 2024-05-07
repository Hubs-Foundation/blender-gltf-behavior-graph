import bpy


def migrate_coords(version):
    ''' Since v0.0.2 we use the Blender coordinate system for all vectors and we swizzle when exporting.
        This migration updates all existing vectors for pre 0.0.2 files.'''
    def migrate_sockets_coords(socket):
        if not socket.is_linked:
            if socket.bl_idname == "NodeSocketVectorXYZ" or socket.bl_idname == "NodeSocketVectorEuler":
                copy = socket.default_value.copy()
                socket.default_value.y = copy.z
                socket.default_value.z = copy.y

    def migrate_nodes(graph):
        for node in graph.nodes:
            for socket in node.inputs:
                migrate_sockets_coords(socket)

    def migrate_variables(target):
        for var in target.bg_global_variables:
            if var.type == "vec3":
                copy = var.defaultVec3.copy()
                var.defaultVec3.y = copy.z
                var.defaultVec3.z = copy.y

    def migrate_events(target):
        for event in target.bg_custom_events:
            if (len(event.parameters) > 0):
                for parameter in event.parameters:
                    if parameter.type == "vec3":
                        copy = parameter.defaultVec3.copy()
                        parameter.defaultVec3.y = copy.z
                        parameter.defaultVec3.z = copy.y

    for node_tree in bpy.data.node_groups:
        authoring_version = node_tree.bg_global_props.version
        if (authoring_version[0], authoring_version[1], authoring_version[2]) < version:
            migrate_nodes(node_tree)
            migrate_variables(node_tree)
            migrate_events(node_tree)

    for scene in bpy.data.scenes:
        authoring_version = scene.bg_global_props.version
        if (authoring_version[0], authoring_version[1], authoring_version[2]) < version:
            migrate_variables(scene)
            migrate_events(scene)

    for object in bpy.data.objects:
        authoring_version = object.bg_global_props.version
        if (authoring_version[0], authoring_version[1], authoring_version[2]) < version:
            migrate_variables(object)
            migrate_events(object)


def migrate():
    for version in MIGRATIONS:
        for step in MIGRATIONS[version]:
            step(version)


MIGRATIONS = {
    (0, 0, 1): [migrate_coords]
}
