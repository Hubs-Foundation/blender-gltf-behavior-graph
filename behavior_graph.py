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
from io_hubs_addon.io.utils import gather_property, gather_image, gather_vec_property, gather_color_property

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


class BGCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        # return True
        return context.space_data.tree_type == "BGTree"


class NODE_MT_behavior_graphs_subcategory_Media(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_Media"
    bl_label = "Media"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        node_add_menu.add_node_type(layout, "BGNode_media_mediaPlayback")
        node_add_menu.add_node_type(layout, "BGNode_media_onMediaEvent")


class NODE_MT_behavior_graphs_subcategory_Text(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_Text"
    bl_label = "Text"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        node_add_menu.add_node_type(layout, "BGNode_text_setTextProperties")


class NODE_MT_behavior_graphs_subcategory_Networked_Behavior(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_Networked_Behavior"
    bl_label = "Networked Behavior"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        node_add_menu.add_node_type(layout, "BGNode_networkedVariable_get")
        node_add_menu.add_node_type(layout, "BGNode_networkedVariable_set")


class NODE_MT_behavior_graphs_subcategory_Custom_Tags(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_Custom_Tags"
    bl_label = "Custom Tags"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        node_add_menu.add_node_type(layout, "BGNode_hubs_entity_components_custom_tags_addTag")
        node_add_menu.add_node_type(layout, "BGNode_hubs_entity_components_custom_tags_removeTag")
        node_add_menu.add_node_type(layout, "BGNode_hubs_entity_components_custom_tags_hasTag")


class NODE_MT_behavior_graphs_subcategory_String_Math(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_String_Math"
    bl_label = "String Math"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        values = next(values for key, values in behavior_graph_node_categories.items() if key == self.bl_label)
        for value in values:
            node_add_menu.add_node_type(layout, value.nodetype)


class NODE_MT_behavior_graphs_subcategory_Bool_Math(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_Bool_Math"
    bl_label = "Bool Math"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        values = next(values for key, values in behavior_graph_node_categories.items() if key == self.bl_label)
        for value in values:
            node_add_menu.add_node_type(layout, value.nodetype)


class NODE_MT_behavior_graphs_subcategory_Int_Math(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_Int_Math"
    bl_label = "Int Math"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        values = next(values for key, values in behavior_graph_node_categories.items() if key == self.bl_label)
        for value in values:
            node_add_menu.add_node_type(layout, value.nodetype)


class NODE_MT_behavior_graphs_subcategory_Float_Math(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_Float_Math"
    bl_label = "Float Math"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        values = next(values for key, values in behavior_graph_node_categories.items() if key == self.bl_label)
        for value in values:
            node_add_menu.add_node_type(layout, value.nodetype)


class NODE_MT_behavior_graphs_subcategory_Vec3_Math(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_Vec3_Math"
    bl_label = "Vec3 Math"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        values = next(values for key, values in behavior_graph_node_categories.items() if key == self.bl_label)
        for value in values:
            node_add_menu.add_node_type(layout, value.nodetype)


class NODE_MT_behavior_graphs_subcategory_Euler_Math(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_Euler_Math"
    bl_label = "Euler Math"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        values = next(values for key, values in behavior_graph_node_categories.items() if key == self.bl_label)
        for value in values:
            node_add_menu.add_node_type(layout, value.nodetype)


class NODE_MT_behavior_graphs_subcategory_Entity_Events(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_Entity_Events"
    bl_label = "Entity Events"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        node_add_menu.add_node_type(layout, "BGNode_hubs_onInteract")
        node_add_menu.add_node_type(layout, "BGNode_hubs_onCollisionEnter")
        node_add_menu.add_node_type(layout, "BGNode_hubs_onCollisionStay")
        node_add_menu.add_node_type(layout, "BGNode_hubs_onCollisionExit")


class NODE_MT_behavior_graphs_subcategory_Player_Events(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_Player_Events"
    bl_label = "Player Events"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        node_add_menu.add_node_type(layout, "BGNode_hubs_onPlayerCollisionEnter")
        node_add_menu.add_node_type(layout, "BGNode_hubs_onPlayerCollisionStay")
        node_add_menu.add_node_type(layout, "BGNode_hubs_onPlayerCollisionExit")
        node_add_menu.add_node_type(layout, "BGNode_hubs_onPlayerJoined")
        node_add_menu.add_node_type(layout, "BGNode_hubs_onPlayerLeft")


class NODE_MT_behavior_graphs_subcategory_Lifecycle_Events(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_Lifecycle_Events"
    bl_label = "Lifecycle Events"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        node_add_menu.add_node_type(layout, "BGNode_lifecycle_onStart")
        node_add_menu.add_node_type(layout, "BGNode_lifecycle_onEnd")
        node_add_menu.add_node_type(layout, "BGNode_lifecycle_onTick")


class BGSubcategory(NodeItem):

    def draw(self, ob, layout, context):
        suffix = self.label.replace(" ", "_")
        layout.menu(f"NODE_MT_behavior_graphs_subcategory_{suffix}", text=self.label)


behavior_graph_node_categories = {
    "Event": [
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Events_Lifecycle", label="Lifecycle Events"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Events_Entity", label="Entity Events"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Events_Player", label="Player Events"),
        NodeItem("BGNode_customEvent_onTriggered"),
    ],
    "Entity": [
        NodeItem("BGHubsSetEntityProperty"),
        NodeItem("BGNode_get_component"),
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
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Networked_Behavior", label="Networked Behavior"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Media", label="Media"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Text", label="Text"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Custom_Tags", label="Custom Tags")
    ],
    "Math": [
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_String_Math", label="String Math"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Bool_Math", label="Bool Math"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Int_Math", label="Int Math"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Float_Math", label="Float Math"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Vec3_Math", label="Vec3 Math"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Euler_Math", label="Euler Math")
    ],
    "Media": [
        # NodeItem("BGNode_media_onCreate"),
        # NodeItem("BGNode_media_onPlay"),
        # NodeItem("BGNode_media_onPause"),
        # NodeItem("BGNode_media_onEnd"),
        # NodeItem("BGNode_media_onDestroy"),
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
    BGNode_get_component,
    BGNode_customEvent_trigger,
    BGNode_networkedVariable_get,
    BGNode_networkedVariable_set,

    # BGNode_media_onCreate,
    # BGNode_media_onPlay,
    # BGNode_media_onPause,
    # BGNode_media_onEnd,
    # BGNode_media_onDestroy,
    BGNode_media_onMediaEvent,

    NODE_MT_behavior_graphs_subcategory_Media,
    NODE_MT_behavior_graphs_subcategory_Text,
    NODE_MT_behavior_graphs_subcategory_Networked_Behavior,
    NODE_MT_behavior_graphs_subcategory_String_Math,
    NODE_MT_behavior_graphs_subcategory_Bool_Math,
    NODE_MT_behavior_graphs_subcategory_Int_Math,
    NODE_MT_behavior_graphs_subcategory_Float_Math,
    NODE_MT_behavior_graphs_subcategory_Vec3_Math,
    NODE_MT_behavior_graphs_subcategory_Euler_Math,
    NODE_MT_behavior_graphs_subcategory_Entity_Events,
    NODE_MT_behavior_graphs_subcategory_Player_Events,
    NODE_MT_behavior_graphs_subcategory_Lifecycle_Events,
    NODE_MT_behavior_graphs_subcategory_Custom_Tags
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


FILTERED_NODES = ["BGNode_hubs_onPlayerJoined", "BGNode_hubs_onPlayerLeft", "BGNode_lifecycle_onStart",
                  "BGNode_lifecycle_onEnd", "BGNode_lifecycle_onTick",
                  "BGNode_hubs_entity_components_custom_tags_removeTag",
                  "BGNode_hubs_entity_components_custom_tags_addTag",
                  "BGNode_hubs_entity_components_custom_tags_hasTag"]


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
            if node_class.__name__ not in FILTERED_NODES:
                behavior_graph_node_categories[category].append(
                    NodeItem(node_class.__name__))


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
        return gather_color_property(export_settings, socket, socket, "default_value", "COLOR_GAMMA")
    elif socket_type == "vec3":
        return gather_vec_property(export_settings, socket, socket, "default_value")
    elif hasattr(socket, "default_value"):
        return gather_property(export_settings, socket, socket, "default_value")
    else:
        return None


def gather_events_and_variables(slots, export_settings):
    events = {}
    variables = {}

    for var in bpy.context.scene.bg_global_variables:
        default = None
        if var.type == "integer":
            default = var.defaultInt
        elif var.type == "boolean":
            default = var.defaultBoolean
        elif var.type == "float":
            default = var.defaultFloat
        elif var.type == "string":
            default = var.defaultString
        elif var.type == "vec3":
            default = gather_vec_property(export_settings, var, var, "defaultVec3")
        elif var.type == "animationAction":
            default = var.defaultAnimationAction
        elif var.type == "color":
            default = gather_color_property(export_settings, var, var, "defaultColor", "COLOR_GAMMA")
        variables[var.name] = {
            "name": var.name,
            "id": list(bpy.context.scene.bg_global_variables).index(var),
            "valueTypeName": var.type,
            "initialValue": default
        }

    for event in bpy.context.scene.bg_custom_events:
        events[event.name] = {
            "name": event.name,
            "id": list(bpy.context.scene.bg_custom_events).index(event)
        }

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
                if node.variableId == 'None':
                    print(f'WARNING: variable node: {node.variableId}, id: "None"')
                else:
                    print(f'variable node: {node.variableId}, id: {variables[node.variableId]["id"]}')
                    node_data["configuration"]["variableId"] = variables[node.variableId]["id"]

        elif isinstance(node, BGNode_customEvent_trigger) or isinstance(node, BGNode_customEvent_onTriggered):
            if node.customEventId:
                if node.customEventId == 'None':
                    print(f'WARNING: custom event node: {node.customEventId}, id: "None"')
                else:
                    print(f'custom event node: {node.customEventId}, id: {events[node.customEventId]["id"]}')
                    node_data["configuration"]["customEventId"] = events[node.customEventId]["id"]

        elif hasattr(node, "__annotations__"):
            for key in node.__annotations__.keys():
                if not node.is_property_hidden(key):
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


def get_category(category, items):
    cat_items = []
    for item in items:
        if isinstance(item, NodeItem) or isinstance(item, BGSubcategory):
            cat_items.append(item)
    return BGCategory("BEHAVIOR_GRAPH_" + category.replace(" ", "_"), category, items=cat_items)


FILTERED_CATEGORIES = ["Media", "Text",  "String Math",
                       "Bool Math", "Int Math", "Float Math", "Vec3 Math", "Euler Math"]


def register():
    read_nodespec(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "nodespec.json"))

    for cls in all_classes:
        register_class(cls)

    categories = []
    for category, items in behavior_graph_node_categories.items():
        if category not in FILTERED_CATEGORIES:
            categories.append(get_category(category, items))

    register_node_categories("BEHAVIOR_GRAPH_NODES", categories)


def unregister():
    unregister_node_categories("BEHAVIOR_GRAPH_NODES")

    for cls in all_classes:
        unregister_class(cls)

    del behavior_graph_node_categories


if __name__ == "__main__":
    register()
