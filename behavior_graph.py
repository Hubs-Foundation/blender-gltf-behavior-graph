from .sockets import *
from .nodes import *
import json
from io_scene_gltf2.io.com.gltf2_io_constants import TextureFilter, TextureWrap
from io_scene_gltf2.io.com import gltf2_io
import bpy
import os
from bpy.props import StringProperty
from bpy.types import Node, NodeTree, NodeSocket, NodeReroute, NodeSocketString
from bpy.utils import register_class, unregister_class
from nodeitems_utils import NodeCategory, NodeItem, register_node_categories, unregister_node_categories
from io_hubs_addon.io.utils import gather_property, gather_image

auto_casts = {
    ("BGHubsEntitySocket", "NodeSocketString"): "BGNode_hubs_entity_toString",

    ("NodeSocketFloat", "NodeSocketString"): "BGNode_math_toString_float",
    ("NodeSocketBool", "NodeSocketString"): "BGNode_math_toString_boolean",
    ("NodeSocketInt", "NodeSocketString"): "BGNode_math_toString_integer",
    ("NodeSocketVectorXYZ", "NodeSocketString"): "BGNode_math_toString_vec3",

    ("NodeSocketString", "NodeSocketFloat"): "BGNode_math_toFloat_string",
    ("NodeSocketBool", "NodeSocketFloat"): "BGNode_math_toFloat_boolean",
    ("NodeSocketInt", "NodeSocketFloat"): "BGNode_math_toFloat_integer",

    ("NodeSocketFloat", "NodeSocketInt"): "BGNode_math_toInteger_float",
    ("NodeSocketString", "NodeSocketInt"): "BGNode_math_toInteger_string",
    ("NodeSocketBool", "NodeSocketInt"): "BGNode_math_toInteger_boolean",

    ("NodeSocketString", "NodeSocketBool"): "BGNode_math_toBoolean_string",
    ("NodeSocketInt", "NodeSocketBool"): "BGNode_math_toBoolean_integer",

    ("NodeSocketVectorXYZ", "NodeSocketVectorEuler"): "BGNode_math_vec3_toEuler",
    ("NodeSocketVectorEuler", "NodeSocketVectorXYZ"): "BGNode_math_euler_toVec3",

    ("NodeSocketVectorXYZ", "NodeSocketFloat"): "BGNode_math_toFloat_vec3",
    ("NodeSocketFloat", "NodeSocketVectorXYZ"): "BGNode_math_toVec3_float",
}


class BGTree(NodeTree):
    bl_idname = "BGTree"
    bl_label = "Behavior Graph"
    bl_icon = "NODETREE"

    # TODO HACK to stop log spam when editing group inputs
    type: StringProperty("BGTREE")

    def mark_invalid_links(self):
        print("mark invalid links")
        for link in self.links:
            if type(link.from_socket) != type(link.to_socket):
                link.is_valid = False

    def update(self):
        from .sockets import BGEnumSocket
        for link in self.links:
            if type(link.from_socket) != type(link.to_socket):
                cast_key = (link.from_socket.bl_idname,
                            link.to_socket.bl_idname)
                # if link.from_socket.bl_idname.startswith("NodeSocketVector") and link.to_socket.bl_idname.startswith("NodeSocketVector"):
                #     continue
                if isinstance(link.from_socket.node, NodeReroute):
                    from_node = link.from_socket.node
                    from_node.outputs.clear()
                    from_node.outputs.new(link.to_socket.bl_idname, "Output")
                    self.links.new(from_node.outputs["Output"], link.to_socket)
                elif isinstance(link.to_socket.node, NodeReroute):
                    to_node = link.to_socket.node
                    to_node.inputs.clear()
                    to_node.inputs.new(link.from_socket.bl_idname, "Input")
                    self.links.new(link.from_socket, to_node.inputs["Input"])
                elif cast_key in auto_casts:
                    try:
                        node = self.nodes.new(auto_casts[cast_key])
                        node.location = [link.from_node.location[0] + abs(
                            link.from_node.location[0] - link.to_node.location[0])/2, link.from_node.location[1]]
                        self.links.new(link.from_socket, node.inputs[0])
                        self.links.new(node.outputs[0], link.to_socket)
                        node.hide = len(node.inputs) <= 1 and len(
                            node.outputs) <= 1
                        link.from_node.select = False
                        node.select = True
                    except:
                        self.links.remove(link)
                elif type(link.to_socket) == BGEnumSocket and type(link.from_socket) == NodeSocketString:
                    pass
                else:
                    self.links.remove(link)

        for node in self.nodes:
            if hasattr(node, "update") and callable(getattr(node, "update")):
                node.update()


class BGCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        # return True
        return context.space_data.tree_type == "BGTree"


behavior_graph_node_categories = {
    "Event": [
        NodeItem("BGNode_hubs_onInteract"),
        NodeItem("BGNode_hubs_onCollisionEnter"),
        NodeItem("BGNode_hubs_onCollisionStay"),
        NodeItem("BGNode_hubs_onCollisionExit"),
        NodeItem("BGNode_hubs_onPlayerCollisionEnter"),
        NodeItem("BGNode_hubs_onPlayerCollisionStay"),
        NodeItem("BGNode_hubs_onPlayerCollisionExit"),
        NodeItem("BGNode_customEvent_onTriggered"),
    ],
    "Entity": [
        NodeItem("BGHubsSetEntityProperty"),
    ],
    "Variables": [
        NodeItem("BGNode_variable_get"),
        NodeItem("BGNode_variable_set"),
    ],
    "Flow": [
        NodeItem("BGNode_flow_sequence"),
    ],
    "Action": [
        NodeItem("BGNode_customEvent_trigger"),
    ],
    "Components": [
        NodeItem("BGNode_networkedVariable_get"),
        NodeItem("BGNode_networkedVariable_set")
    ]
}


all_classes = [
    BGTree,
    BGFlowSocket,
    BGHubsEntitySocket,
    BGHubsEntitySocketInterface,
    BGHubsAnimationActionSocket,
    BGHubsAnimationActionSocketInterface,
    BGHubsPlayerSocket,
    BGHubsPlayerSocketInterface,
    BGCustomEventSocket,
    BGCustomEventSocketInterface,

    BGEnumSocketChoice,
    BGEnumSocket,

    BGNode_variable_get,
    BGNode_variable_set,
    BGNode_flow_sequence,

    BGNode_hubs_onInteract,
    BGNode_hubs_onCollisionEnter,
    BGNode_hubs_onCollisionStay,
    BGNode_hubs_onCollisionExit,
    BGNode_hubs_onPlayerCollisionEnter,
    BGNode_hubs_onPlayerCollisionStay,
    BGNode_hubs_onPlayerCollisionExit,
    BGNode_customEvent_onTriggered,

    BGHubsSetEntityProperty,
    BGNode_customEvent_trigger,
    BGNode_networkedVariable_get,
    BGNode_networkedVariable_set
]

hardcoded_nodes = {
    node.node_type for node in all_classes if hasattr(node, "node_type")}

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
    "color": "NodeSocketColor"
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

category_colors = {
    "Event":  (0.6, 0.2, 0.2),
    "Flow":  (0.2, 0.2, 0.2),
    "Time":  (0.3, 0.3, 0.3),
    "Action":  (0.2, 0.2, 0.6),
    "None": (0.6, 0.6, 0.2)
}


def create_node_class(node_data):
    from .nodes import BGNode
    label = node_data["type"]
    if "label" in node_data:
        # label = "%s (%s)" % (node_data["label"], node_data["type"])
        label = node_data["label"]

    class CustomNode(BGNode, Node):
        bl_label = label

        node_type = node_data["type"]

        def init(self, context):
            super().init(context)

            if node_data["category"] in category_colors:
                self.color = category_colors[node_data["category"]]
            else:
                self.color = category_colors["None"]

            for input_data in node_data["inputs"]:

                if "choices" in input_data:
                    sock = self.inputs.new("BGEnumSocket", input_data["name"])
                    for choice_data in input_data["choices"]:
                        choice = sock.choices.add()
                        choice.text = choice_data["text"]
                        choice.value = choice_data["value"]
                else:
                    socket_type = type_to_socket[input_data["valueType"]]
                    sock = self.inputs.new(socket_type, input_data["name"])

                if "defaultValue" in input_data:
                    if (input_data["valueType"] == 'vec3' or input_data["valueType"] == "euler"):
                        sock.default_value[0] = input_data["defaultValue"]["x"]
                        sock.default_value[1] = input_data["defaultValue"]["y"]
                        sock.default_value[2] = input_data["defaultValue"]["z"]
                    else:
                        sock.default_value = input_data["defaultValue"]
                if "description" in input_data:
                    sock.description = input_data["description"]

            for output_data in node_data["outputs"]:
                socket_type = type_to_socket[output_data["valueType"]]
                sock = self.outputs.new(socket_type, output_data["name"])
                if (output_data["valueType"] != 'vec3' and output_data["valueType"] != "euler") and "defaultValue" in output_data:
                    sock.default_value = output_data["defaultValue"]
                if "description" in output_data:
                    sock.description = output_data["description"]

    CustomNode.__name__ = "BGNode_" + node_data['type'].replace("/", "_")
    print(CustomNode.__name__)

    return CustomNode


def read_nodespec(filename):
    with open(filename, "r") as file:
        nodes = json.load(file)
        for node_spec in nodes:
            if node_spec["type"] in hardcoded_nodes:
                print("SKIP", node_spec["type"])
                continue
            category = node_spec["category"]
            if not category in behavior_graph_node_categories:
                behavior_graph_node_categories[category] = []
            node_class = create_node_class(node_spec)
            all_classes.append(node_class)
            behavior_graph_node_categories[category].append(
                NodeItem(node_class.__name__))
            # bpy.utils.register_class(node_class)
        # print(test_classes)
        #


def resolve_input_link(input_socket: bpy.types.NodeSocket) -> bpy.types.NodeLink:
    while isinstance(input_socket.links[0].from_node, bpy.types.NodeReroute):
        input_socket = input_socket.links[0].from_node.inputs[0]
    return input_socket.links[0]


def resolve_output_link(output_socket: bpy.types.NodeSocket) -> bpy.types.NodeLink:
    while isinstance(output_socket.links[0].to_node, bpy.types.NodeReroute):
        output_socket = output_socket.links[0].to_node.outputs[0]
    return output_socket.links[0]


if bpy.app.version >= (3, 6, 0):
    from io_scene_gltf2.blender.exp.material import gltf2_blender_gather_materials
else:
    from io_scene_gltf2.blender.exp import gltf2_blender_gather_materials


def gather_material_property(export_settings, blender_object, target, property_name):
    blender_material = getattr(target, property_name)
    if blender_material:
        material = gltf2_blender_gather_materials.gather_material(
            blender_material, -1, export_settings)
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


def get_socket_value(export_settings, socket: NodeSocket):
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
        return gather_property(export_settings, socket, socket, "target")
    elif socket_type == "material":
        return gather_material_property(export_settings, socket, socket, "default_value")
    elif socket_type == "texture":
        return gather_texture_property(export_settings, socket, socket, "default_value")
    elif socket_type == "color":
        a = socket.default_value
        return [a[0], a[1], a[2]]
    elif socket_type == "vec3":  # TODO gather_property seems to not handle this correctly
        a = socket.default_value
        return {"x": a[0], "y": a[1], "z": a[2]}
    elif hasattr(socket, "default_value"):
        return gather_property(export_settings, socket, socket, "default_value")
    else:
        return None


def gather_events_and_variables(slots, export_settings):
    ev_idx = 0
    var_idx = 0
    events = {}
    variables = {}
    for slot in slots:
        for i, socket in enumerate(slot.graph.inputs):
            if socket.bl_socket_idname == "BGCustomEventSocket":
                value = get_socket_value(export_settings, socket)
                print(f'socket: {socket.name}, value: {value}')
                if socket.name not in events:
                    events[socket.name] = {
                        "name": socket.name,
                        "id": ev_idx
                    }
                    ev_idx += 1
            else:
                value = get_socket_value(export_settings, socket)
                socket_type = socket_to_type[socket.bl_socket_idname]
                print(f'socket: {socket.name}, type: {socket_type}, value: {value}')
                if socket.name not in variables:
                    variables[socket.name] = {
                        "name": socket.name,
                        "id": var_idx,
                        "valueTypeName": socket_type,
                        "initialValue": value
                    }
                    var_idx += 1

    return (events, variables)


def gather_nodes(slot, export_settings, events, variables):
    from .sockets import BGFlowSocket, BGHubsEntitySocket
    from .nodes import BGNode, BGNode_variable_set, BGNode_variable_get, BGNode_customEvent_trigger, BGNode_customEvent_onTriggered

    nodes = []

    for node in slot.graph.nodes:
        if not isinstance(node, BGNode):
            continue

        node_data = {
            "id": f"{slot.name}_{node.name}",
            "type": node.node_type,
            "parameters": {},
            "configuration": {},
            "flows": {}
        }

        for output_socket in node.outputs:
            if isinstance(output_socket, BGFlowSocket) and output_socket.is_linked:
                link = resolve_output_link(output_socket)
                print(link)
                node_data["flows"][output_socket.identifier] = {
                    "nodeId": f"{slot.name}_{link.to_node.name}",
                    "socket": link.to_socket.identifier
                }

        for input_socket in node.inputs:
            if isinstance(input_socket, BGFlowSocket):
                pass
            else:
                if input_socket.is_linked:
                    link = resolve_input_link(input_socket)
                    node_data["parameters"][input_socket.identifier] = {
                        "link": {
                            "nodeId": f"{slot.name}_{link.from_node.name}",
                            "socket": link.from_socket.identifier
                        }
                    }
                elif isinstance(input_socket, BGHubsEntitySocket):
                    node_data["parameters"][input_socket.identifier] = {
                        "value": gather_property(export_settings, input_socket, input_socket, "target")}

                elif isinstance(node, BGNode_networkedVariable_set):
                    if node.prop_type == input_socket.identifier:
                        value = get_socket_value(export_settings, input_socket)
                        node_data["parameters"][node.prop_type] = {
                            "value": value}

                else:
                    value = get_socket_value(export_settings, input_socket)
                    node_data["parameters"][input_socket.identifier] = {
                        "value": value}

        if isinstance(node, BGNode_variable_get) or isinstance(node, BGNode_variable_set):
            if node.variableId:
                print(f'variable node: {node.variableId}, id: {slot.graph.inputs.find(node.variableId)}')
                node_data["configuration"]["variableId"] = variables[node.variableId]["id"]

        elif isinstance(node, BGNode_customEvent_trigger) or isinstance(node, BGNode_customEvent_onTriggered):
            if node.customEventId:
                print(f'variable node: {node.customEventId}, id: {slot.graph.inputs.find(node.customEventId)}')
                node_data["configuration"]["customEventId"] = events[node.customEventId]["id"]

        elif hasattr(node, "__annotations__"):
            for key in node.__annotations__.keys():
                node_data["configuration"][key] = gather_property(
                    export_settings, node, node, key)

        nodes.append(node_data)

    return nodes


class glTF2ExportUserExtension:
    def __init__(self):
        # We need to wait until we create the gltf2UserExtension to import the gltf2 modules
        # Otherwise, it may fail because the gltf2 may not be loaded yet
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension

        self.Extension = Extension
        self.delayed_gathers = []

    def gather_gltf_extensions_hook(self, gltf2_object, export_settings):
        print("GATHERING BG")

        # This is a hack to allow multi-graph while we have proper per gltf node graph support
        slots = []
        for ob in list(bpy.data.scenes) + list(bpy.data.objects):
            slots.extend(list(map(lambda slot: slot, ob.bg_slots)))

        glob_events, glob_variables = gather_events_and_variables(slots, export_settings)

        variables = []
        customEvents = []
        for var in glob_variables:
            variables.append(glob_variables[var])
        for event in glob_events:
            customEvents.append(glob_events[event])

        nodes = []
        for slot in slots:
            nodes.extend(gather_nodes(slot, export_settings, glob_events, glob_variables))

        if nodes:
            if gltf2_object.extensions is None:
                gltf2_object.extensions = {}
            gltf2_object.extensions["MOZ_behavior"] = self.Extension(
                name="MOZ_behavior",
                extension={
                    "behaviors": [{
                        "customEvents": customEvents,
                        "variables": variables,
                        "nodes": nodes
                    }]
                },
                required=False
            )


def register():
    read_nodespec(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "nodespec.json"))

    for cls in all_classes:
        register_class(cls)

    print(behavior_graph_node_categories)
    categories = [BGCategory("BEHAVIOR_GRAPH_" + category.replace(" ", "_"), category, items=items)
                  for category, items in behavior_graph_node_categories.items()]
    print(categories)
    register_node_categories("BEHAVIOR_GRAPH_NODES", categories)


def unregister():
    unregister_node_categories("BEHAVIOR_GRAPH_NODES")

    for cls in all_classes:
        unregister_class(cls)


if __name__ == "__main__":
    register()
