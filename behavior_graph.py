from .sockets import *
from .nodes import *
import json
import bpy
import os
from bpy.props import StringProperty
from bpy.types import Node, NodeTree, NodeReroute, NodeSocketString
from bpy.utils import register_class, unregister_class
from nodeitems_utils import NodeCategory, NodeItem, register_node_categories, unregister_node_categories
from io_hubs_addon.io.utils import gather_property, gather_vec_property, gather_color_property
from .utils import get_socket_value, type_to_socket, resolve_input_link, resolve_output_link

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


class NODE_MT_behavior_graphs_subcategory_Media_Frame(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_Media_Frame"
    bl_label = "Media Frame"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        node_add_menu.add_node_type(layout, "BGNode_media_frame_setMediaFrameProperty")


class NODE_MT_behavior_graphs_subcategory_Physics(bpy.types.Menu):
    bl_idname = "NODE_MT_behavior_graphs_subcategory_Physics"
    bl_label = "Media Frame"

    def draw(self, context):
        layout = self.layout
        from bl_ui import node_add_menu
        node_add_menu.add_node_type(layout, "BGNode_physics_setRigidBodyProperties")


class BGSubcategory(NodeItem):

    def draw(self, ob, layout, context):
        suffix = self.label.replace(" ", "_")
        layout.menu(f"NODE_MT_behavior_graphs_subcategory_{suffix}", text=self.label)


behavior_graph_node_categories = {
    "Event": [
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Events_Lifecycle", label="Lifecycle Events"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Events_Entity", label="Entity Events"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Events_Player", label="Player Events"),
        NodeItem("BGNode_customEvent_trigger"),
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
    "Components": [
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Networked_Behavior", label="Networked Behavior"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Media", label="Media"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Text", label="Text"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Custom_Tags", label="Custom Tags"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Media_Frame", label="Media Frame"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Physics", label="Physics")
    ],
    "Math": [
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_String_Math", label="String Math"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Bool_Math", label="Bool Math"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Int_Math", label="Int Math"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Float_Math", label="Float Math"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Vec3_Math", label="Vec3 Math"),
        BGSubcategory(f"BEHAVIOR_GRAPH_Subcategory_Euler_Math", label="Euler Math")
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
    NODE_MT_behavior_graphs_subcategory_Custom_Tags,
    NODE_MT_behavior_graphs_subcategory_Media_Frame,
    NODE_MT_behavior_graphs_subcategory_Physics
]

hardcoded_nodes = {
    node.node_type for node in all_classes if hasattr(node, "node_type")}

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
                    if socket_type == "BGFlowSocket":
                        sock = BGFlowSocket.create(self.inputs, input_data["name"])
                    else:
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
                if socket_type == "BGFlowSocket":
                    sock = BGFlowSocket.create(self.outputs, output_data["name"])
                else:
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


def get_object_variables(ob, variables, export_settings):
    for var in ob.bg_global_variables:
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
        elif var.type == "entity":
            default = gather_property(export_settings, var, var, "defaultEntity")
        variables[f"{ob.name}_{var.name}"] = {
            "name": f"{ob.name}_{var.name}",
            "id": len(variables),
            "valueTypeName": var.type,
            "initialValue": default
        }


def get_object_custom_events(ob, events, export_settings):
    for event in ob.bg_custom_events:
        events[f"{ob.name}_{event.name}"] = {
            "name": f"{ob.name}_{event.name}",
            "id": list(ob.bg_custom_events).index(event)
        }


def gather_events_and_variables(slots, export_settings):
    events = {}
    variables = {}

    get_object_variables(bpy.context.scene, variables, export_settings)
    for ob in bpy.context.view_layer.objects:
        get_object_variables(ob, variables, export_settings)

    get_object_custom_events(bpy.context.scene, events, export_settings)
    for ob in bpy.context.view_layer.objects:
        get_object_custom_events(ob, events, export_settings)

    return (events, variables)


def gather_nodes(ob, idx, slot, export_settings, events, variables):
    from .sockets import BGFlowSocket
    from .nodes import BGNode

    nodes = []

    for node in slot.graph.nodes:
        if not isinstance(node, BGNode):
            continue

        prefix = f"{ob.name}_{slot.graph.name}_{idx}"
        node_data = {
            "id": f"{prefix}_{node.name}",
            "type": node.node_type,
            "parameters": {},
            "configuration": {},
            "flows": {}
        }

        for output_socket in node.outputs:
            if isinstance(output_socket, BGFlowSocket) and output_socket.is_linked:
                link = resolve_output_link(output_socket)
                node_data["flows"][output_socket.identifier] = {
                    "nodeId": f"{prefix}_{link.to_node.name}",
                    "socket": link.to_socket.identifier
                }

        for input_socket in node.inputs:
            if input_socket.is_linked and not input_socket.hide:
                link = resolve_input_link(input_socket)
                node_data["parameters"][input_socket.identifier] = {
                    "link": {
                        "nodeId": f"{prefix}_{link.from_node.name}",
                        "socket": link.from_socket.identifier
                    }
                }

            elif hasattr(input_socket, "gather_parameters") and callable(getattr(input_socket, "gather_parameters")):
                parameters = input_socket.gather_parameters(ob, export_settings)
                if parameters != None:
                    node_data["parameters"].update({input_socket.identifier: parameters})

            elif hasattr(node, "gather_parameters") and callable(getattr(node, "gather_parameters")):
                parameters = node.gather_parameters(ob, input_socket, export_settings)
                if parameters != None:
                    node_data["parameters"].update({input_socket.identifier: parameters})

            else:
                value = get_socket_value(ob, export_settings, input_socket)
                if value != None:
                    node_data["parameters"].update({input_socket.identifier: {"value": value}})

        if hasattr(node, "gather_configuration") and callable(getattr(node, "gather_configuration")):
            configuration = node.gather_configuration(ob, variables, events, export_settings)
            if configuration != None:
                node_data["configuration"] = configuration

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
        for ob in list(bpy.data.scenes) + list(bpy.context.view_layer.objects):
            slots.append({"ob": ob, "slots": list(ob.bg_slots)})

        glob_events, glob_variables = gather_events_and_variables(slots, export_settings)

        variables = []
        customEvents = []
        for var in glob_variables:
            variables.append(glob_variables[var])
        for event in glob_events:
            customEvents.append(glob_events[event])

        nodes = []
        for item in slots:
            ob = item["ob"]
            slots = item["slots"]
            for slot in slots:
                if slot is not None:
                    idx = slots.index(slot)
                    nodes.extend(gather_nodes(ob, idx, slot, export_settings, glob_events, glob_variables))

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
                       "Bool Math", "Int Math", "Float Math", "Vec3 Math", "Euler Math", "Physics", "Media Frame"]


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
