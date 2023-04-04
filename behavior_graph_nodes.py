import bpy
from bpy.props import StringProperty, PointerProperty
from bpy.types import GeometryNode, Node, NodeTree, NodeSocket, NodeSocketStandard, ShaderNode, TextureNode, Operator, NodeGroupInput, NodeReroute, NodeSocketString
from bpy.utils import register_class, unregister_class
from nodeitems_utils import NodeCategory, NodeItem, register_node_categories, unregister_node_categories

auto_casts = {
    ("BGHubsEntitySocket", "NodeSocketString"): "BGHubsEntityToStringNode",
    ("NodeSocketFloat", "NodeSocketString"): "BGToStringFloatNode"
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
        for link in self.links:
            if type(link.from_socket) != type(link.to_socket):
                cast_key = (link.from_socket.bl_idname, link.to_socket.bl_idname)
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
                    node = self.nodes.new(auto_casts[cast_key])
                    node.location = [link.from_node.location[0] + abs(link.from_node.location[0] - link.to_node.location[0])/2, link.from_node.location[1]]
                    self.links.new(link.from_socket, node.inputs[0])
                    self.links.new(node.outputs[0], link.to_socket)
                    node.hide = True
                    link.from_node.select = False
                    node.select = True
                else:
                    self.links.remove(link)
        # bpy.app.timers.register(self.mark_invalid_links)

    # def update(self):
    #     print("TREE UPDATE")

class BGFlowSocket(NodeSocketStandard):
    bl_label = "Behavior Graph Flow Socket"

    def __init__(self):
        self.display_shape = "DIAMOND"
        if self.is_output:
            self.link_limit = 1
        else: 
            self.link_limit = 0

    def draw(self, context, layout, node, text):
        if text == "flow":
            layout.label(text="▶")
        elif self.is_output:
            layout.label(text= text + " ▶")
        else:
            layout.label("▶ " + text)

    def draw_color(self, context, node):
        return (1.0, 1.0, 1.0, 1.0)

class BGHubsEntitySocket(NodeSocketStandard):
    bl_label = "Behavior Graph Entity Socket"

    target: PointerProperty(
        name="Target",
        type=bpy.types.Object,
        # poll=filter_on_component
    )

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "target", text=text)

    def draw_color(self, context, node):
        return (0.2, 1.0, 0.2, 1.0)

class BGNode():
    bl_label = "Behavior Graph Node"
    bl_icon = "NODE"

    def init(self, context):
        self.use_custom_color = True

    @classmethod
    def poll(cls, ntree):
        # return True
        return ntree.bl_idname == 'BGTree'

class BGEventNode():
    def init(self, context):
        super().init(context)
        self.color = (0.6, 0.2, 0.2)
        self.outputs.new("BGFlowSocket", "flow")

class BGActionNode():
    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.2, 0.6)
        self.inputs.new("BGFlowSocket", "flow")
        self.outputs.new("BGFlowSocket", "flow")

class BGQueryNode():
    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.6, 0.2)

class BGUtilNode(BGNode, Node):
    def init(self, context):
        super().init(context)
        self.color = (0.6, 0.6, 0.2)

class BGFlowNode():
    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.2, 0.2)

class BGBranchNode(BGFlowNode, BGNode, Node):
    bl_label = "Branch"
    node_type = "flow/branch"

    def init(self, context):
        super().init(context)
        self.inputs.new("BGFlowSocket", "flow")
        self.inputs.new("NodeSocketBool", "condition")
        self.outputs.new("BGFlowSocket", "true")
        self.outputs.new("BGFlowSocket", "false")



class BGLifecycleOnStartNode(BGEventNode, BGNode, Node):
    bl_label = "On Start"
    node_type = "lifecycle/onStart"

class BGDebugLogNode(BGActionNode, BGNode, Node):
    bl_label = "Debug Log"
    node_type = "debug/log"

    def init(self, context):
        super().init(context)
        self.inputs.new("NodeSocketString", "text")


class BGOnTickNode(BGEventNode, BGNode, Node):
    bl_label = "On Tick"
    node_type = "lifecycle/onTick"

    def init(self, context):
        super().init(context)
        self.outputs.new("NodeSocketFloat", "deltaSeconds")


# from io_hubs_addon.components.utils import has_component

# def filter_on_component(self, ob):
#     return has_component(ob, dep_name)
#
#
#

class BGHubsGetEntityProperties(BGQueryNode, BGNode, Node):
    bl_label = "Get Entity Properties"
    node_type = "hubs/entity/properties"

    def init(self, context):
        super().init(context)
        self.inputs.new("BGHubsEntitySocket", "entity")
        self.outputs.new("BGHubsEntitySocket", "entity")
        self.outputs.new("NodeSocketString", "name")
        self.outputs.new("NodeSocketBool", "visible")
        self.outputs.new("NodeSocketVectorXYZ", "position")

socket_type_for_property = {
    "visible": "NodeSocketBool",
    "position": "NodeSocketVectorXYZ",
}

def update_target_property(self, context):
    if self.inputs and len(self.inputs) > 2:
        self.outputs.remove(self.inputs[2])
    setattr(self, "node_type",  "hubs/entity/set/" + self.targetProperty)
    self.inputs.new(socket_type_for_property[self.targetProperty], self.targetProperty)

class BGHubsSetEntityProperty(BGActionNode, BGNode, Node):
    bl_label = "Set Entity Property"

    node_type: bpy.props.StringProperty()

    targetProperty: bpy.props.EnumProperty(
        name="",
        items=[
            ("visible", "visible", ""),
            ("position", "position", "")
        ],
        default="visible",
        update=update_target_property
    )

    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.6, 0.2)
        self.inputs.new("BGHubsEntitySocket", "entity")
        update_target_property(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "targetProperty")


class BGHubsOnInteract(BGEventNode, BGNode, Node):
    bl_label = "On Interact"
    node_type = "hubs/onInteract"

    target: PointerProperty(
        name="Target",
        type=bpy.types.Object,
        # poll=filter_on_component
    )

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsEntitySocket", "entity")

    def draw_buttons(self, context, layout):
        layout.prop(self, "target")


class BGHubsOnCollisionEnter(BGEventNode, BGNode, Node):
    bl_label = "On Collision Enter"
    node_type = "hubs/onCollisionEnter"

    target: PointerProperty(
        name="Target",
        type=bpy.types.Object,
        # poll=filter_on_component
    )

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsEntitySocket", "entity")

    def draw_buttons(self, context, layout):
        layout.prop(self, "target")


class BGHubsOnCollisionExit(BGEventNode, BGNode, Node):
    bl_label = "On Collision Exit"
    node_type = "hubs/onCollisionExit"

    target: PointerProperty(
        name="Target",
        type=bpy.types.Object,
        # poll=filter_on_component
    )

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsEntitySocket", "entity")

    def draw_buttons(self, context, layout):
        layout.prop(self, "target")


def get_available_input_sockets(self, context):
    tree = context.space_data.edit_tree
    if tree is not None:
        return [(socket.name, socket.name, socket.name) for socket in tree.inputs]
    else:
        return []

def update_selected_variable_input(self, context):
    # Remove previous socket
    if self.inputs and len(self.inputs) > 1:
        self.inputs.remove(self.inputs[1])

    # Create a new socket based on the selected variable type
    tree = context.space_data.edit_tree
    if tree is not None:
        selected_socket = tree.inputs[self.variableId]
        socket_type = selected_socket.bl_socket_idname
        self.inputs.new(socket_type, "value")
        self.variableName = self.variableId

    return None

def update_selected_variable_output(self, context):
    # Remove previous socket
    if self.outputs:
        self.outputs.remove(self.outputs[0])

    # Create a new socket based on the selected variable type
    tree = context.space_data.edit_tree
    if tree is not None:
        print(self.variableId)
        selected_socket = tree.inputs[self.variableId]
        socket_type = selected_socket.bl_socket_idname
        self.outputs.new(socket_type, "value")
        self.variableName = self.variableId

    return None

class BGGetVariableNode(BGNode, Node):
    bl_label = "Get Variable"
    node_type = "variable/get"

    variableId: bpy.props.EnumProperty(
        name="Variable",
        description="Variable",
        items=get_available_input_sockets,
        update=update_selected_variable_output,
    )
    variableName: bpy.props.StringProperty()

    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.6, 0.2)

    def draw_buttons(self, context, layout):
        layout.prop(self, "variableId")


class BGSetVariableNode(BGActionNode, BGNode, Node):
    bl_label = "Set Variable"
    node_type = "variable/set"

    variableId: bpy.props.EnumProperty(
        name="Value",
        description="Variable Value",
        items=get_available_input_sockets,
        update=update_selected_variable_input
    )
    variableName: bpy.props.StringProperty()

    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.6, 0.2)

    def draw_buttons(self, context, layout):
        layout.prop(self, "variableId")

class BGHubsEntityHasComponent(BGUtilNode, BGNode, Node):
    bl_label = "Entity Has Component"
    node_type = "hubs/entity/hasComponent"

    def init(self, context):
        super().init(context)
        self.inputs.new("BGHubsEntitySocket", "entity")
        self.inputs.new("NodeSocketString", "name")
        self.inputs.new("NodeSocketBool", "includeAncestors")
        self.outputs.new("NodeSocketBool", "result")
        self.inputs["includeAncestors"].default_value = True

class BGAddFloatNode(BGUtilNode, BGNode, Node):
    bl_label = "Add Float"
    node_type = "math/add/float"

    def init(self, context):
        super().init(context)
        self.inputs.new("NodeSocketFloat", "a")
        self.inputs.new("NodeSocketFloat", "b")
        self.outputs.new("NodeSocketFloat", "result")

class BGToStringFloatNode(BGUtilNode, BGNode, Node):
    bl_label = "To String Float"
    node_type = "math/toString/float"

    def init(self, context):
        super().init(context)
        self.inputs.new("NodeSocketFloat", "a")
        self.outputs.new("NodeSocketString", "result")

class BGStringEqualsNode(BGUtilNode, BGNode, Node):
    bl_label = "String Equals"
    node_type = "math/equal/string"

    def init(self, context):
        super().init(context)
        self.inputs.new("NodeSocketString", "a")
        self.inputs.new("NodeSocketString", "b")
        self.outputs.new("NodeSocketBool", "result")

class BGStringIncludesNode(BGUtilNode, BGNode, Node):
    bl_label = "String Includes"
    node_type = "logic/includes/string"

    def init(self, context):
        super().init(context)
        self.inputs.new("NodeSocketString", "a")
        self.inputs.new("NodeSocketString", "b")
        self.outputs.new("NodeSocketBool", "result")

class BGHubsEntityToStringNode(BGUtilNode, BGNode, Node):
    bl_label = "To String Entity"
    node_type = "hubs/entity/toString"

    def init(self, context):
        super().init(context)
        self.inputs.new("BGHubsEntitySocket", "entity")
        self.outputs.new("NodeSocketString", "result")

class BGConcatStringNode(BGUtilNode, BGNode, Node):
    bl_label = "Concat String"
    node_type = "logic/concat/string"

    def init(self, context):
        super().init(context)
        self.inputs.new("NodeSocketString", "a")
        self.inputs.new("NodeSocketString", "b")
        self.outputs.new("NodeSocketString", "result")

class BGMathNegateBoolean(BGUtilNode, BGNode, Node):
    bl_label = "Boolean Not"
    node_type = "math/negate/boolean"

    def init(self, context):
        super().init(context)
        self.label = "NOT"
        self.hide = True
        self.width = 0
        self.inputs.new("NodeSocketBool", "a")
        self.outputs.new("NodeSocketBool", "result")

class BGMathVec3Separate(BGUtilNode, BGNode, Node):
    bl_label = "Separate Vec3"
    node_type = "math/vec3/separate"

    def init(self, context):
        super().init(context)
        self.inputs.new("NodeSocketVectorXYZ", "v")
        self.outputs.new("NodeSocketFloat", "x")
        self.outputs.new("NodeSocketFloat", "y")
        self.outputs.new("NodeSocketFloat", "z")

class BGMathVec3Combine(BGUtilNode, BGNode, Node):
    bl_label = "Combine Vec3"
    node_type = "math/vec3/combine"

    def init(self, context):
        super().init(context)
        self.inputs.new("NodeSocketFloat", "x")
        self.inputs.new("NodeSocketFloat", "y")
        self.inputs.new("NodeSocketFloat", "z")
        self.outputs.new("NodeSocketVectorXYZ", "v")

class BGCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        # return True
        return context.space_data.tree_type == "BGTree"

behavior_graph_node_categories = [
    BGCategory("BEHAVIOR_GRAPH_EVENTS", "Events", items=[
        NodeItem("BGLifecycleOnStartNode"),
        NodeItem("BGOnTickNode"),
        NodeItem("BGHubsOnInteract"),
        NodeItem("BGHubsOnCollisionEnter"),
        NodeItem("BGHubsOnCollisionExit"),
    ]),
    BGCategory("BEHAVIOR_GRAPH_ENTITY", "Entity", items=[
        NodeItem("BGHubsGetEntityProperties"),
        NodeItem("BGHubsSetEntityProperty"),
        NodeItem("BGHubsEntityToStringNode"),
        NodeItem("BGHubsEntityHasComponent"),
    ]),
    BGCategory("BEHAVIOR_GRAPH_ACTIONS", "Actions", items=[
        NodeItem("BGDebugLogNode"),
    ]),
    BGCategory("BEHAVIOR_GRAPH_FLOW", "Flow", items=[
        NodeItem("BGBranchNode"),
    ]),
    BGCategory("BEHAVIOR_GRAPH_MATH", "Math", items=[
        NodeItem("BGAddFloatNode"),
        NodeItem("BGMathNegateBoolean"),
        NodeItem("BGToStringFloatNode"),
        NodeItem("BGMathVec3Combine"),
        NodeItem("BGMathVec3Separate"),
    ]),
    BGCategory("BEHAVIOR_GRAPH_DATA", "Data", items=[
        NodeItem("BGGetVariableNode"),
        NodeItem("BGSetVariableNode"),
        NodeItem("BGConcatStringNode"),
        NodeItem("BGStringEqualsNode"),
        NodeItem("BGStringIncludesNode"),
        # NodeItem("ShaderNodeMath"),
    ]),
]

all_classes = [
    BGTree,
    BGFlowSocket,
    BGHubsEntitySocket,

    BGLifecycleOnStartNode,
    BGDebugLogNode,

    BGBranchNode,

    BGOnTickNode,
    BGHubsOnInteract,
    BGHubsOnCollisionEnter,
    BGHubsOnCollisionExit,

    BGGetVariableNode,
    BGSetVariableNode,

    BGAddFloatNode,
    BGMathNegateBoolean,
    BGMathVec3Combine,
    BGMathVec3Separate,
    BGToStringFloatNode,
    BGConcatStringNode,
    BGStringEqualsNode,
    BGStringIncludesNode,

    BGHubsGetEntityProperties,
    BGHubsSetEntityProperty,

    BGHubsEntityToStringNode,
    BGHubsEntityHasComponent,
]


from io_hubs_addon.io.utils import gather_property

def resolve_input_link(input_socket: bpy.types.NodeSocket) -> bpy.types.NodeLink:
    while isinstance(input_socket.links[0].from_node, bpy.types.NodeReroute):
        input_socket = input_socket.links[0].from_node.inputs[0]
    return input_socket.links[0]

def resolve_output_link(output_socket: bpy.types.NodeSocket) -> bpy.types.NodeLink:
    while isinstance(output_socket.links[0].to_node, bpy.types.NodeReroute):
        output_socket = output_socket.links[0].to_node.outputs[0]
    return output_socket.links[0]


def extract_behavior_graph_data(node_tree, export_settings):
    data = {
        "variables": [],
        "nodes": []
    }

    for i, socket in enumerate(node_tree.inputs):
        data["variables"].append({
            "name": socket.name,
            "id": i,
            "valueTypeName": socket.bl_socket_idname.replace("NodeSocket", "").lower(),
            "initialValue": socket.default_value
        })

    for node in node_tree.nodes:
        if not isinstance(node, BGNode):
            continue

        node_data = {
            "id": str(node.name),
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
                    "nodeId": link.to_node.name,
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
                            "nodeId": link.from_node.name,
                            "socket": link.from_socket.identifier
                        }
                    }
                elif isinstance(input_socket, BGHubsEntitySocket):
                    node_data["parameters"][input_socket.identifier] = { "value": gather_property(export_settings, input_socket, input_socket, "target") }
                else:
                    node_data["parameters"][input_socket.identifier] = { "value": gather_property(export_settings, input_socket, input_socket, "default_value") }
        if isinstance(node, BGGetVariableNode) or isinstance(node, BGSetVariableNode):
            node_data["configuration"]["variableId"] = node_tree.inputs.find(getattr(node, 'variableName'))
        elif hasattr(node, "__annotations__"):
            for key in node.__annotations__.keys():
                node_data["configuration"][key] = gather_property(export_settings, node, node, key)

        data["nodes"].append(node_data)

    return data

# behavior_graph_data_list = []
# for node_group in bpy.data.node_groups:
#     if node_group.bl_idname == "BGTree":
#         behavior_graph_data = extract_behavior_graph_data(node_group)
#         behavior_graph_data_list.append(behavior_graph_data)
# pprint(behavior_graph_data_list)


class glTF2ExportUserExtension:
    def __init__(self):
        # We need to wait until we create the gltf2UserExtension to import the gltf2 modules
        # Otherwise, it may fail because the gltf2 may not be loaded yet
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension

        self.Extension = Extension

    def gather_gltf_extensions_hook(self, gltf2_object, export_settings):
        print("GATHERING BG")
        behaviors = [extract_behavior_graph_data(node_group, export_settings) for node_group in bpy.data.node_groups if node_group.bl_idname == "BGTree"]
        if behaviors:
            gltf2_object.extensions["KHR_behavior"] = self.Extension(
                name="KHR_behavior",
                extension={
                    "behaviors": behaviors
                },
                required=False
            )


def register():
    for cls in all_classes:
        register_class(cls)

    register_node_categories("BEHAVIOR_GRAPH_NODES", behavior_graph_node_categories)

def unregister():
    unregister_node_categories("BEHAVIOR_GRAPH_NODES")

    for cls in reversed(all_classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()
