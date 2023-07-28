import bpy
from bpy.props import PointerProperty
from bpy.types import Node
from io_hubs_addon.components.utils import has_component


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
        from .sockets import BGFlowSocket
        super().init(context)
        self.color = (0.6, 0.2, 0.2)
        BGFlowSocket.create(self.outputs)


class BGActionNode():
    def init(self, context):
        from .sockets import BGFlowSocket
        super().init(context)
        self.color = (0.2, 0.2, 0.6)
        BGFlowSocket.create(self.inputs)
        BGFlowSocket.create(self.outputs)


entity_property_settings = {
    "visible": ("NodeSocketBool", False),
    "position": ("NodeSocketVectorXYZ", [0.0, 0.0, 0.0]),
    "rotation": ("NodeSocketVectorEuler", [0.0, 0.0, 0.0]),
    "scale": ("NodeSocketVectorXYZ", [1.0, 1.0, 1.0]),
}


def update_target_property(self, context):
    if self.inputs and len(self.inputs) > 2:
        self.outputs.remove(self.inputs[2])
    setattr(self, "node_type",  "hubs/entity/set/" + self.targetProperty)
    (socket_type,
     default_value) = entity_property_settings[self.targetProperty]
    sock = self.inputs.new(socket_type, self.targetProperty)
    sock.default_value = default_value


class BGHubsSetEntityProperty(BGActionNode, BGNode, Node):
    bl_label = "Set Entity Property"

    node_type: bpy.props.StringProperty()

    targetProperty: bpy.props.EnumProperty(
        name="",
        items=[
            ("visible", "visible", ""),
            ("position", "position", ""),
            ("rotation", "rotation", ""),
            ("scale", "scale", "")
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


class BGNode_hubs_onInteract(BGEventNode, BGNode, Node):
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


def has_collider(self, ob):
    return has_component(ob, "physics-shape")


class BGNode_hubs_onCollisionEnter(BGEventNode, BGNode, Node):
    bl_label = "On Collision Enter"
    node_type = "hubs/onCollisionEnter"

    target: PointerProperty(
        name="Target", type=bpy.types.Object, poll=has_collider)

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsEntitySocket", "entity")

    def draw_buttons(self, context, layout):
        layout.prop(self, "target")


class BGNode_hubs_onCollisionStay(BGEventNode, BGNode, Node):
    bl_label = "On Collision Stay"
    node_type = "hubs/onCollisionStay"

    target: PointerProperty(
        name="Target", type=bpy.types.Object, poll=has_collider)

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsEntitySocket", "entity")

    def draw_buttons(self, context, layout):
        layout.prop(self, "target")


class BGNode_hubs_onCollisionExit(BGEventNode, BGNode, Node):
    bl_label = "On Collision Exit"
    node_type = "hubs/onCollisionExit"

    target: PointerProperty(
        name="Target", type=bpy.types.Object, poll=has_collider)

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsEntitySocket", "entity")

    def draw_buttons(self, context, layout):
        layout.prop(self, "target")


class BGNode_hubs_onPlayerCollisionEnter(BGEventNode, BGNode, Node):
    bl_label = "On Player Collision Enter"
    node_type = "hubs/onPlayerCollisionEnter"

    target: PointerProperty(
        name="Target", type=bpy.types.Object, poll=has_collider)

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsPlayerSocket", "player")

    def draw_buttons(self, context, layout):
        layout.prop(self, "target")


class BGNode_hubs_onPlayerCollisionStay(BGEventNode, BGNode, Node):
    bl_label = "On Player Collision Stay"
    node_type = "hubs/onPlayerCollisionStay"

    target: PointerProperty(
        name="Target", type=bpy.types.Object, poll=has_collider)

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsPlayerSocket", "player")

    def draw_buttons(self, context, layout):
        layout.prop(self, "target")


class BGNode_hubs_onPlayerCollisionExit(BGEventNode, BGNode, Node):
    bl_label = "On Player Collision Exit"
    node_type = "hubs/onPlayerCollisionExit"

    target: PointerProperty(
        name="Target", type=bpy.types.Object, poll=has_collider)

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsPlayerSocket", "player")

    def draw_buttons(self, context, layout):
        layout.prop(self, "target")


def update_output_sockets(self, context):
    from .sockets import BGFlowSocket
    existing_outputs = len(self.outputs)
    print("existing", existing_outputs, "desired", self.numOutputs)
    if (existing_outputs < self.numOutputs):
        for i in range(existing_outputs, self.numOutputs):
            BGFlowSocket.create(self.outputs, f"{i+1}")
    elif existing_outputs > self.numOutputs:
        for i in range(self.numOutputs, existing_outputs):
            self.outputs.remove(self.outputs[f"{i+1}"])


class BGNode_flow_sequence(BGNode, Node):
    bl_label = "Sequence"
    node_type = "flow/sequence"

    numOutputs: bpy.props.IntProperty(
        name="Outputs",
        default=2,
        min=1,
        update=update_output_sockets
    )

    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.2, 0.2)
        from .sockets import BGFlowSocket
        BGFlowSocket.create(self.inputs)
        update_output_sockets(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "numOutputs")


def get_available_input_sockets(self, context):
    from .sockets import BGCustomEventSocketInterface
    tree = self.id_data
    result = []
    if tree is not None:
        result.extend([(socket.name, socket.name, socket.name) for socket in tree.inputs if not hasattr(
            socket, "bl_idname") or socket.bl_idname != BGCustomEventSocketInterface.bl_idname])
    return result


def update_selected_variable_input(self, context):
    # Remove previous socket
    if self.inputs and len(self.inputs) > 1:
        self.inputs.remove(self.inputs[1])

    # Create a new socket based on the selected variable type
    tree = self.id_data
    if tree is not None and self.variableId:
        selected_socket = tree.inputs[self.variableId]
        socket_type = selected_socket.bl_socket_idname
        if socket_type == "NodeSocketVector":
            socket_type = "NodeSocketVectorXYZ"
        self.inputs.new(socket_type, "value")

    return None


def update_selected_variable_output(self, context):
    # Remove previous socket
    if self.outputs:
        self.outputs.remove(self.outputs[0])

    # Create a new socket based on the selected variable type
    tree = self.id_data
    if tree is not None and self.variableId:
        print(self.variableId)
        selected_socket = tree.inputs[self.variableId]
        socket_type = selected_socket.bl_socket_idname
        if socket_type == "NodeSocketVector":
            socket_type = "NodeSocketVectorXYZ"
        self.outputs.new(socket_type, "value")

    return None


class BGNode_variable_get(BGNode, Node):
    bl_label = "Get Variable"
    node_type = "variable/get"

    variableId: bpy.props.EnumProperty(
        name="Variable",
        description="Variable",
        items=get_available_input_sockets,
        update=update_selected_variable_output,
    )

    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.6, 0.2)
        update_selected_variable_output(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "variableId")


class BGNode_variable_set(BGActionNode, BGNode, Node):
    bl_label = "Set Variable"
    node_type = "variable/set"

    variableId: bpy.props.EnumProperty(
        name="Value",
        description="Variable Value",
        items=get_available_input_sockets,
        update=update_selected_variable_input
    )

    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.6, 0.2)
        update_selected_variable_input(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "variableId")


def get_available_custom_event_input_sockets(self, context):
    from .sockets import BGCustomEventSocketInterface
    tree = self.id_data
    result = []
    if tree is not None:
        result.extend([(socket.name, socket.name, socket.name) for socket in tree.inputs if hasattr(
            socket, "bl_idname") and socket.bl_idname == BGCustomEventSocketInterface.bl_idname])
    return result


class BGNode_customEvent_trigger(BGActionNode, BGNode, Node):
    bl_label = "Trigger"
    node_type = "customEvent/trigger"

    customEventId: bpy.props.EnumProperty(
        name="Custom Event",
        description="Custom Event",
        items=get_available_custom_event_input_sockets,
    )

    def init(self, context):
        super().init(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "customEventId")


class BGNode_customEvent_onTriggered(BGEventNode, BGNode, Node):
    bl_label = "On Trigger"
    node_type = "customEvent/onTriggered"

    customEventId: bpy.props.EnumProperty(
        name="Custom Event",
        description="Custom Event",
        items=get_available_custom_event_input_sockets,
    )

    def init(self, context):
        super().init(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "customEventId")


def get_available_networkedBehavior_properties(self, context):
    result = [("None", "None", "None")]
    if self.target:
        for prop in self.target.hubs_component_networked_behavior.props_list:
            result.append((prop.name, prop.name, prop.name))
    return result


def filter_on_networked_behavior(self, ob):
    from .components.networked_behavior import NetworkedBehavior
    return has_component(ob, NetworkedBehavior.get_name())


def networkedBehavior_properties_updated(self, context):
    if self.target:
        has_prop = self.prop_name in self.target.hubs_component_networked_behavior.props_list
        prop_type = self.target.hubs_component_networked_behavior.props_list[self.prop_name].type if has_prop else None

        for socket_id in ["boolean", "float", "int", "string", "vec3",]:
            if socket_id in self.inputs:
                self.inputs[socket_id].hide = not prop_type or prop_type != socket_id
            if socket_id in self.outputs:
                self.outputs[socket_id].hide = not prop_type or prop_type != socket_id

        if self.prop_type != prop_type:
            for output in self.outputs:
                for link in output.links:
                    bpy.context.object.bg_active_graph.links.remove(link)
            for input in self.inputs:
                for link in input.links:
                    bpy.context.object.bg_active_graph.links.remove(link)

        self.prop_type = prop_type


class BGNode_networkedVariable_set(BGActionNode, BGNode, Node):
    bl_label = "Networked Variable Set"
    node_type = "networkedVariable/set"

    target: PointerProperty(
        name="Target",
        type=bpy.types.Object,
        poll=filter_on_networked_behavior
    )

    prop_name: bpy.props.EnumProperty(
        name="Property",
        description="Property",
        items=get_available_networkedBehavior_properties,
        update=networkedBehavior_properties_updated,
        default=0
    )

    prop_type: bpy.props.StringProperty(default="")

    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.6, 0.2)
        self.inputs.new("NodeSocketBool", "boolean")
        self.inputs['boolean'].hide = True
        self.inputs.new("NodeSocketFloat", "float")
        self.inputs['float'].hide = True
        self.inputs.new("NodeSocketInt", "int")
        self.inputs['int'].hide = True
        self.inputs.new("NodeSocketString", "string")
        self.inputs['string'].hide = True
        self.inputs.new("NodeSocketVectorXYZ", "vec3")
        self.inputs['vec3'].hide = True

    def draw_buttons(self, context, layout):
        layout.prop(self, "target")
        if self.target:
            layout.prop(self, "prop_name")

    def update(self):
        if self.prop_name:
            self.prop_name = self.prop_name


class BGNode_networkedVariable_get(BGNode, Node):
    bl_label = "Networked Variable Get"
    node_type = "networkedVariable/get"

    target: PointerProperty(
        name="Target",
        type=bpy.types.Object,
        poll=filter_on_networked_behavior
    )

    prop_name: bpy.props.EnumProperty(
        name="Property",
        description="Property",
        items=get_available_networkedBehavior_properties,
        update=networkedBehavior_properties_updated,
        default=0
    )

    prop_type: bpy.props.StringProperty(default="")

    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.6, 0.2)
        self.outputs.new("NodeSocketBool", "boolean")
        self.outputs['boolean'].hide = True
        self.outputs.new("NodeSocketFloat", "float")
        self.outputs['float'].hide = True
        self.outputs.new("NodeSocketInt", "int")
        self.outputs['int'].hide = True
        self.outputs.new("NodeSocketString", "string")
        self.outputs['string'].hide = True
        self.outputs.new("NodeSocketVectorXYZ", "vec3")
        self.outputs['vec3'].hide = True

    def draw_buttons(self, context, layout):
        layout.prop(self, "target")
        if self.target:
            layout.prop(self, "prop_name")

    def update(self):
        if self.prop_name:
            self.prop_name = self.prop_name
