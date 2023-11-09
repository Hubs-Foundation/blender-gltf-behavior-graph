from io_hubs_addon.components.components_registry import register_component, unregister_component, __components_registry
from io_scene_gltf2.io.com.gltf2_io_constants import TextureFilter, TextureWrap
from io_scene_gltf2.io.com import gltf2_io
from io_hubs_addon.io.utils import gather_property, gather_image, gather_vec_property, gather_color_property
from io_hubs_addon.components.utils import has_component
from bpy.types import NodeSocket
import bpy


def redraw_area(context, area_id):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == area_id:
                area.tag_redraw()
                context.window_manager.update_tag()


def gather_material_property(export_settings, blender_object, target, property_name):
    blender_material = getattr(target, property_name)
    if blender_material:
        material = gltf2_blender_gather_materials.gather_material(
            blender_material, 0, export_settings)
        return {
            "__mhc_link_type": "material",
            "index": material
        }
    else:
        return None


def __gather_mag_filter(blender_shader_node, export_settings):
    if blender_shader_node.use_interpolation:
        return TextureFilter.Linear
    return TextureFilter.Nearest


def __gather_min_filter(blender_shader_node, export_settings):
    if blender_shader_node.use_interpolation:
        if blender_shader_node.use_mipmap:
            return TextureFilter.LinearMipmapLinear
        else:
            return TextureFilter.Linear
    if blender_shader_node.use_mipmap:
        return TextureFilter.NearestMipmapNearest
    else:
        return TextureFilter.Nearest


def __gather_wrap(blender_shader_node, export_settings):
    # First gather from the Texture node
    if blender_shader_node.extension == 'EXTEND':
        wrap_s = TextureWrap.ClampToEdge
    elif blender_shader_node.extension == 'CLIP':
        # Not possible in glTF, but ClampToEdge is closest
        wrap_s = TextureWrap.ClampToEdge
    elif blender_shader_node.extension == 'MIRROR':
        wrap_s = TextureWrap.MirroredRepeat
    else:
        wrap_s = TextureWrap.Repeat
    wrap_t = wrap_s

    # Omit if both are repeat
    if (wrap_s, wrap_t) == (TextureWrap.Repeat, TextureWrap.Repeat):
        wrap_s, wrap_t = None, None

    return wrap_s, wrap_t


if bpy.app.version >= (3, 6, 0):
    from io_scene_gltf2.blender.exp.material import gltf2_blender_gather_materials
else:
    from io_scene_gltf2.blender.exp import gltf2_blender_gather_materials


def gather_texture_property(export_settings, blender_object, target, property_name):
    blender_texture = getattr(target, property_name)

    wrap_s, wrap_t = __gather_wrap(blender_texture, export_settings)
    sampler = gltf2_io.Sampler(
        extensions=None,
        extras=None,
        mag_filter=__gather_mag_filter(blender_texture, export_settings),
        min_filter=__gather_min_filter(blender_texture, export_settings),
        name=None,
        wrap_s=wrap_s,
        wrap_t=wrap_t,
    )

    if blender_texture:
        texture = gltf2_io.Texture(
            extensions=None,
            extras=None,
            name=blender_texture.name,
            sampler=sampler,
            source=gather_image(blender_texture.image, export_settings)
        )
        return {
            "__mhc_link_type": "texture",
            "index": texture
        }
    else:
        return None


def gather_object_property(export_settings, blender_object):
    if blender_object:
        if bpy.app.version < (3, 2, 0):
            node = gltf2_blender_gather_nodes.gather_node(
                blender_object,
                blender_object.library.name if blender_object.library else None,
                blender_object.users_scene[0],
                None,
                export_settings
            )
        else:
            vtree = export_settings['vtree']
            vnode = vtree.nodes[next((uuid for uuid in vtree.nodes if (
                vtree.nodes[uuid].blender_object == blender_object)), None)]
            node = vnode.node or gltf2_blender_gather_nodes.gather_node(
                vnode,
                export_settings
            )

        return {
            "__mhc_link_type": "node",
            "index": node
        }
    else:
        return None


def get_hubs_ext(export_settings):
    exts = export_settings["gltf_user_extensions"]
    for ext in exts:
        import io_hubs_addon
        if type(ext) == io_hubs_addon.io.gltf_exporter.glTF2ExportUserExtension:
            return ext


def add_component_to_node(gltf2_object, dep, value, export_settings):
    from io_hubs_addon.io.gltf_exporter import hubs_config
    hubs_ext = get_hubs_ext(export_settings)
    hubs_ext_name = hubs_config["gltfExtensionName"]
    if gltf2_object.extensions is None:
        gltf2_object.extensions = {}
    if hubs_ext_name not in gltf2_object.extensions:
        gltf2_object.extensions[hubs_ext_name] = {dep.get_name(): value}
    else:
        if hasattr(gltf2_object.extensions[hubs_ext_name], "extension"):
            if not dep.get_name() in gltf2_object.extensions[hubs_ext_name].extension:
                gltf2_object.extensions[hubs_ext_name].extension.update({dep.get_name(): value})
            else:
                gltf2_object.extensions[hubs_ext_name].extension[dep.get_name()].update(value)
        else:
            gltf2_object.extensions[hubs_ext_name].update({dep.get_name(): value})


def update_gltf_network_dependencies(node, export_settings, blender_object, dep, value={"networked": "true"}):
    if type(blender_object) == bpy.types.Object:
        vtree = export_settings['vtree']
        vnode = vtree.nodes[next((uuid for uuid in vtree.nodes if (
            vtree.nodes[uuid].blender_object == blender_object)), None)]
        gltf_object = vnode.node or gltf2_blender_gather_nodes.gather_node(
            vnode,
            export_settings
        )
        add_component_to_node(gltf_object, dep, value, export_settings)
    elif type(blender_object) == bpy.types.Material:
        gltf_object = gltf2_blender_gather_materials.gather_material(
            blender_object, 0, export_settings)
        add_component_to_node(gltf_object, dep, value, export_settings)


def get_socket_value(ob, export_settings, socket: NodeSocket):
    if hasattr(socket, "bl_socket_idname"):
        socket_idname = socket.bl_socket_idname
    else:
        socket_idname = socket.bl_idname

    socket_type = socket_to_type[socket_idname]

    if socket_idname == "BGEnumSocket":
        return socket.default_value
    if socket_idname == "BGCustomEventSocket":
        return socket.name
    if socket_type == "entity":
        if socket.entity_type == "self":
            return gather_object_property(export_settings, ob)
        else:
            entity = gather_property(export_settings, socket, socket, "target")
            if entity:
                return entity
            else:
                raise Exception(f"Input socket {socket.name} not set")
    elif socket_type == "material":
        mat = gather_material_property(export_settings, socket, socket, "default_value")
        if mat:
            return mat
        else:
            raise Exception(f"Input socket {socket.name} not set")
    elif socket_type == "texture":
        if socket.is_linked:
            return gather_texture_property(export_settings, socket, socket, "default_value")
        else:
            raise Exception("Linked textures not yet supported")
    elif socket_type == "color":
        return gather_color_property(export_settings, socket, socket, "default_value", "COLOR_GAMMA")
    elif socket_type == "vec3":
        return gather_vec_property(export_settings, socket, socket, "default_value")
    elif hasattr(socket, "default_value"):
        return gather_property(export_settings, socket, socket, "default_value")
    else:
        return None


def get_variable_value(var, export_settings):
    value = None
    if var.type == "integer":
        value = var.defaultInt
    elif var.type == "boolean":
        value = var.defaultBoolean
    elif var.type == "float":
        value = var.defaultFloat
    elif var.type == "string":
        value = var.defaultString
    elif var.type == "vec3":
        value = gather_vec_property(export_settings, var, var, "defaultVec3")
    elif var.type == "animationAction":
        value = var.defaultAnimationAction
    elif var.type == "color":
        value = gather_color_property(export_settings, var, var, "defaultColor", "COLOR_GAMMA")
    elif var.type == "entity":
        if var.defaultEntity.name not in bpy.context.view_layer.objects:
            raise Exception(f"Entity {var.defaultEntity.name} does not exist")
        else:
            value = gather_property(export_settings, var, var, "defaultEntity")

    return value


def resolve_input_link(input_socket: bpy.types.NodeSocket) -> bpy.types.NodeLink:
    while isinstance(input_socket.links[0].from_node, bpy.types.NodeReroute):
        input_socket = input_socket.links[0].from_node.inputs[0]
    return input_socket.links[0]


def resolve_output_link(output_socket: bpy.types.NodeSocket) -> bpy.types.NodeLink:
    while isinstance(output_socket.links[0].to_node, bpy.types.NodeReroute):
        output_socket = output_socket.links[0].to_node.outputs[0]
    return output_socket.links[0]


def filter_on_components(self, ob):
    if hasattr(self, "poll_components") and self.poll_components:
        result = False
        components = self.poll_components.split(",")
        for component in components:
            result = result or has_component(ob, component)
        return result
    return True


type_to_socket = {
    "float": "NodeSocketFloat",
    "integer": "NodeSocketInt",
    "boolean": "NodeSocketBool",
    "entity": "BGHubsEntitySocket",
    "flow": "BGFlowSocket",
    "string": "NodeSocketString",
    "vec3": "NodeSocketVectorXYZ",
    "euler": "NodeSocketVectorEuler",
    "animationAction": "BGHubsAnimationActionSocket",
    "player": "BGHubsPlayerSocket",
    "material": "NodeSocketMaterial",
    "texture": "NodeSocketTexture",
    "color": "NodeSocketColor",
    "enum": "BGEnumSocket"
}

socket_to_type = {
    "NodeSocketFloat": "float",
    "NodeSocketInt": "integer",
    "NodeSocketBool": "boolean",
    "BGHubsEntitySocket": "entity",
    "BGFlowSocket": "flow",
    "NodeSocketString": "string",
    "NodeSocketVector": "vec3",
    "NodeSocketVectorXYZ": "vec3",
    "NodeSocketMaterial": "material",
    "NodeSocketTexture": "texture",
    "NodeSocketColor": "color",
    "NodeSocketVectorEuler": "euler",
    "BGHubsAnimationActionSocket": "animationAction",
    "BGEnumSocket": "string",
    "BGHubsPlayerSocket": "player",
    "BGCustomEventSocket": "string"
}

prop_to_type = {
    "FloatProperty": "float",
    "IntProperty": "integer",
    "BoolProperty": "boolean",
    "PointerProperty": "entity",
    "StringProperty": "string",
    "FloatVectorProperty": "vec3",
    "EnumProperty": "enum"
}


def propToType(property_definition):
    prop_type = property_definition.bl_rna.identifier
    prop_subtype = property_definition.subtype
    isArray = getattr(property_definition, 'is_array', None)
    if isArray and property_definition.is_array:
        if prop_subtype.startswith('COLOR'):
            return "color"
        else:
            return "vec3"
    elif prop_type in prop_to_type:
        return prop_to_type[prop_type]


# This function is used by several node entity_type properties and
# it returns different values based on the node type (custom_type) and the
# object that it's attached to. We decide what type of object it's attached to by
# checking context.scene.bg_node_type but when exporting we can't trust
# context.scene.bg_node_type as that will point to the currently selected graph node type
# not to the actual object that's being exported.
# To workaround that we use context.scene.bg_export_type that will be set to
# the object type that is currently being exported.
# Quite a hack for so far I didn't find a better workaround.

def filter_entity_type(self, context):
    # Used for general nodes that have an entity socket
    if not hasattr(self, "custom_type") or self.custom_type == "default":
        types = [("other", "Other", "Other")]

        # If bg_export_type is not None, it's export time
        if context.scene.bg_export_type != "none":
            if context.scene.bg_export_type != "scene":
                types.insert(0, ("self", "Self", "Self"))

        #  Execution time, bg_node_type will be set to the type of the current object
        elif context.scene.bg_node_type != 'SCENE':
            types.insert(0, ("self", "Self", "Self"))

    # Used for custom variables and events entity sockets
    elif self.custom_type == "event_variable":
        types = [("scene", "Scene", "Scene"),
                 ("graph", "Graph", "Graph"),
                 ("other", "Other", "Other")]

        # If bg_export_type is not None, it's export time
        if context.scene.bg_export_type != "none":
            if context.scene.bg_export_type != "scene":
                types.insert(0, ("object", "Self", "Self"))

        #  Execution time, bg_node_type will be set to the type of the current object
        elif context.scene.bg_node_type != 'SCENE':
            types.insert(0, ("object", "Self", "Self"))

    return types


def update_nodes(self, context):
    if context.scene.bg_node_type == 'OBJECT':
        if hasattr(context.object, "bg_active_graph") and context.object.bg_active_graph != None:
            for node in context.object.bg_active_graph.nodes:
                if hasattr(node, "refresh") and callable(getattr(node, "refresh")):
                    node.refresh()
    else:
        if hasattr(context.scene, "bg_active_graph") and context.scene.bg_active_graph != None:
            for node in context.scene.bg_active_graph.nodes:
                if hasattr(node, "refresh") and callable(getattr(node, "refresh")):
                    node.refresh()


def update_graphs(self, context):
    if hasattr(context.object, "bg_active_graph") and context.object.bg_active_graph != None:
        context.object.bg_active_graph.update()
    if hasattr(context.scene, "bg_active_graph") and context.scene.bg_active_graph != None:
        context.scene.bg_active_graph.update()


def get_graph_from_node(node):
    return node.id_data


def object_exists(ob):
    from .behavior_graph import BGTree
    if type(ob) == bpy.types.Scene:
        return ob.name in bpy.data.scenes
    elif type(ob) == BGTree:
        return ob.name in bpy.data.node_groups
    elif type(ob) == bpy.types.Object:
        return ob.name in bpy.context.view_layer.objects
    return False


def get_prefs():
    return bpy.context.preferences.addons[__package__].preferences


def do_register(ComponentClass):
    register_component(ComponentClass)
    __components_registry[ComponentClass.get_name()] = ComponentClass


def do_unregister(ComponentClass):
    if ComponentClass.is_registered:
        unregister_component(ComponentClass)
        __components_registry.pop(ComponentClass.get_name())
