import bpy
from bpy.props import PointerProperty
from bpy.types import Node
from io_hubs_addon.components.utils import has_component
from io_hubs_addon.components.definitions import text, video, audio
from .components import networked_animation, networked_behavior, networked_transform, rigid_body, physics_shape


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


def has_media(self, ob):
    return has_component(ob, "video") or has_component(ob, "audio")


# class BGNode_media_onCreate(BGEventNode, BGNode, Node):
#     bl_label = "On Media Create"
#     node_type = "media/onCreate"

#     target: PointerProperty(
#         name="Target", type=bpy.types.Object, poll=has_media)

#     def init(self, context):
#         super().init(context)
#         self.outputs.new("BGHubsEntitySocket", "entity")

#     def draw_buttons(self, context, layout):
#         layout.prop(self, "target")


# class BGNode_media_onPlay(BGEventNode, BGNode, Node):
#     bl_label = "On Media Play"
#     node_type = "media/onPlay"

#     target: PointerProperty(
#         name="Target", type=bpy.types.Object, poll=has_media)

#     def init(self, context):
#         super().init(context)
#         self.outputs.new("BGHubsEntitySocket", "entity")

#     def draw_buttons(self, context, layout):
#         layout.prop(self, "target")


# class BGNode_media_onPause(BGEventNode, BGNode, Node):
#     bl_label = "On Media Pause"
#     node_type = "media/onPause"

#     target: PointerProperty(
#         name="Target", type=bpy.types.Object, poll=has_media)

#     def init(self, context):
#         super().init(context)
#         self.outputs.new("BGHubsEntitySocket", "entity")

#     def draw_buttons(self, context, layout):
#         layout.prop(self, "target")


# class BGNode_media_onEnd(BGEventNode, BGNode, Node):
#     bl_label = "On Media End"
#     node_type = "media/onEnd"

#     target: PointerProperty(
#         name="Target", type=bpy.types.Object, poll=has_media)

#     def init(self, context):
#         super().init(context)
#         self.outputs.new("BGHubsEntitySocket", "entity")

#     def draw_buttons(self, context, layout):
#         layout.prop(self, "target")


# class BGNode_media_onDestroy(BGEventNode, BGNode, Node):
#     bl_label = "On Media Destroy"
#     node_type = "media/onDestroy"

#     target: PointerProperty(
#         name="Target", type=bpy.types.Object, poll=has_media)

#     def init(self, context):
#         super().init(context)
#         self.outputs.new("BGHubsEntitySocket", "entity")

#     def draw_buttons(self, context, layout):
#         layout.prop(self, "target")


class BGNode_media_onMediaEvent(BGEventNode, BGNode, Node):
    bl_label = "On Media Event"
    node_type = "media/onMediaEvent"

    target: PointerProperty(
        name="Target", type=bpy.types.Object, poll=has_media)

    def init(self, context):
        self.use_custom_color = True
        self.color = (0.6, 0.2, 0.2)
        from .sockets import BGFlowSocket
        BGFlowSocket.create(self.outputs, name="create")
        BGFlowSocket.create(self.outputs, name="play")
        BGFlowSocket.create(self.outputs, name="pause")
        BGFlowSocket.create(self.outputs, name="end")
        BGFlowSocket.create(self.outputs, name="destroy")
        self.outputs.new("BGHubsEntitySocket", "entity")

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


def get_available_variables(self, context):
    result = [("None", "None", "None")]
    for var in context.scene.bg_global_variables:
        result.append((var.name, var.name, var.name))
    return result


def update_selected_variable_output(self, context):
    # Remove previous socket
    if self.outputs:
        self.outputs.remove(self.outputs[0])

    if not context:
        return

    has_var = self.variableName in context.scene.bg_global_variables
    var_type = context.scene.bg_global_variables.get(self.variableName).type if has_var else "None"

    # Create a new socket based on the selected variable type
    from .behavior_graph import type_to_socket
    if var_type != "None":
        self.outputs.new(type_to_socket[var_type], "value")


def getVariableId(self):
    if self.variableName in bpy.context.scene.bg_global_variables:
        return bpy.context.scene.bg_global_variables.find(self.variableName) + 1
    return 0


def setVariableId(self, value):
    if value == 0:
        self.variableName = 'None'
    elif value <= len(bpy.context.scene.bg_global_variables):
        self.variableName = bpy.context.scene.bg_global_variables[value - 1].name
    else:
        self.variableName = 'None'


class BGNode_variable_get(BGNode, Node):
    bl_label = "Get Variable"
    node_type = "variable/get"

    variableName: bpy.props.StringProperty(
        name="Variable Name",
        description="Variable Name",
        options={"HIDDEN"},
        default="None"
    )

    variableId: bpy.props.EnumProperty(
        name="Variable",
        description="Variable",
        items=get_available_variables,
        update=update_selected_variable_output,
        get=getVariableId,
        set=setVariableId,
    )

    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.6, 0.2)
        update_selected_variable_output(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "variableId")

    def refresh(self):
        from .behavior_graph import socket_to_type
        has_var = self.variableName in bpy.context.scene.bg_global_variables
        var_type = bpy.context.scene.bg_global_variables.get(self.variableName).type if has_var else "None"
        cur_type = socket_to_type[self.outputs[0].bl_idname] if self.outputs and len(self.outputs) > 0 else 'None'
        if not has_var or var_type != cur_type:
            update_selected_variable_output(self, bpy.context)
            if bpy.context.scene and len(self.outputs) > 0 and len(self.outputs[0].links) > 0:
                has_var = self.variableId in bpy.context.scene.bg_global_variables
                var_type = bpy.context.scene.bg_global_variables.get(
                    self.variableId).type if has_var else "None"
                if self.outputs[0] != None and var_type != socket_to_type[self.outputs[0].bl_idname]:
                    bpy.context.scene.bg_active_graph.links.remove(self.outputs[0].links[0])


def update_selected_variable_input(self, context):
    # Remove previous socket
    if self.inputs and len(self.inputs) > 1:
        self.inputs.remove(self.inputs[1])

    if not context:
        return

    has_var = self.variableName in context.scene.bg_global_variables
    var_type = context.scene.bg_global_variables.get(self.variableName).type if has_var else "None"

    # Create a new socket based on the selected variable type
    from .behavior_graph import type_to_socket
    if var_type != "None":
        self.inputs.new(type_to_socket[var_type], "value")


class BGNode_variable_set(BGActionNode, BGNode, Node):
    bl_label = "Set Variable"
    node_type = "variable/set"

    variableName: bpy.props.StringProperty(
        name="Variable Name",
        description="Variable Name",
        options={"HIDDEN"},
        default="None"
    )

    variableId: bpy.props.EnumProperty(
        name="Value",
        description="Variable Value",
        items=get_available_variables,
        update=update_selected_variable_input,
        get=getVariableId,
        set=setVariableId,
    )

    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.6, 0.2)
        update_selected_variable_input(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "variableId")

    def refresh(self):
        from .behavior_graph import socket_to_type
        has_var = self.variableName in bpy.context.scene.bg_global_variables
        var_type = bpy.context.scene.bg_global_variables.get(self.variableName).type if has_var else "None"
        cur_type = socket_to_type[self.inputs[1].bl_idname] if self.inputs and len(self.inputs) > 1 else 'None'
        if not has_var or var_type != cur_type:
            update_selected_variable_input(self, bpy.context)
            if bpy.context.scene and len(self.inputs) > 1 and len(self.inputs[1].links) > 0:
                has_var = self.variableId in bpy.context.scene.bg_global_variables
                var_type = bpy.context.scene.bg_global_variables.get(
                    self.variableId).type if has_var else "None"
                if self.inputs[1] != None and var_type != socket_to_type[self.inputs[1].bl_idname]:
                    bpy.context.scene.bg_active_graph.links.remove(self.inputs[1].links[0])


def get_available_custom_events(self, context):
    result = [("None", "None", "None")]
    for var in context.scene.bg_custom_events:
        result.append((var.name, var.name, var.name))
    return result


def getCustomEventId(self):
    if self.customEventName in bpy.context.scene.bg_custom_events:
        return bpy.context.scene.bg_custom_events.find(self.customEventName) + 1
    return 0


def setCustomEventId(self, value):
    if value == 0:
        self.customEventName = 'None'
    elif value <= len(bpy.context.scene.bg_custom_events):
        self.customEventName = bpy.context.scene.bg_custom_events[value - 1].name
    else:
        self.customEventName = 'None'


class BGNode_customEvent_trigger(BGActionNode, BGNode, Node):
    bl_label = "Trigger"
    node_type = "customEvent/trigger"

    customEventName: bpy.props.StringProperty(
        name="Custom Event Name",
        description="Custom Event Name",
        options={"HIDDEN"},
        default="None"
    )

    customEventId: bpy.props.EnumProperty(
        name="Custom Event",
        description="Custom Event",
        items=get_available_custom_events,
        get=getCustomEventId,
        set=setCustomEventId,
    )

    def init(self, context):
        super().init(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "customEventId")

    def refresh(self):
        self.customEventId = self.customEventId


class BGNode_customEvent_onTriggered(BGEventNode, BGNode, Node):
    bl_label = "On Trigger"
    node_type = "customEvent/onTriggered"

    customEventName: bpy.props.StringProperty(
        name="Custom Event Name",
        description="Custom Event Name",
        options={"HIDDEN"},
        default="None"
    )

    customEventId: bpy.props.EnumProperty(
        name="Custom Event",
        description="Custom Event",
        items=get_available_custom_events,
        get=getCustomEventId,
        set=setCustomEventId,
    )

    def init(self, context):
        super().init(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "customEventId")

    def refresh(self):
        self.customEventId = self.customEventId


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
        prop_type = self.target.hubs_component_networked_behavior.props_list[self.prop_name].type if has_prop else "None"

        for socket_id in ["boolean", "float", "int", "string", "vec3"]:
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
        self.inputs.new("NodeSocketVectorXYZ", "color")
        self.inputs['color'].hide = True

    def draw_buttons(self, context, layout):
        layout.prop(self, "target")
        if self.target:
            layout.prop(self, "prop_name")

    def refresh(self):
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
        self.outputs.new("NodeSocketVectorXYZ", "color")
        self.outputs['color'].hide = True

    def draw_buttons(self, context, layout):
        layout.prop(self, "target")
        if self.target:
            layout.prop(self, "prop_name")

    def refresh(self):
        if self.prop_name:
            self.prop_name = self.prop_name


COMPONENTS_FILTER = [
    video.Video.get_name(),
    audio.Audio.get_name(),
    text.Text.get_name(),
    networked_animation.NetworkedAnimation.get_name(),
    rigid_body.RigidBody.get_name(),
    physics_shape.PhysicsShape.get_name(),
    networked_transform.NetworkedTransform.get_name(),
    networked_behavior.NetworkedBehavior.get_name()
]


def map_registry(component):
    component_name, component_class = component
    return (component_name,
            component_class.get_display_name(),
            component[1].get_display_name()) if component_name in COMPONENTS_FILTER else None


def getAvailableComponents(self, context):
    from io_hubs_addon.components.components_registry import get_components_registry
    registry = get_components_registry()
    return map(map_registry, registry.items())


def component_updated(self, context):
    self.inputs[0].component = self.component_name
    self.inputs[1].default_value = self.component_name
    if self.inputs[0].target is not None and not has_component(self.inputs[0].target, self.component_name):
        self.inputs[0].target = None


class BGNode_get_component(BGNode, Node):
    bl_label = "Get Component"
    node_type = "entity/getEntityComponent"

    component_name: bpy.props.EnumProperty(
        name="Component",
        description="Component",
        items=getAvailableComponents,
        update=component_updated,
        options={"HIDDEN"},
        default=0
    )

    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.6, 0.2)
        self.inputs.new("BGHubsEntitySocket", "entity")
        component = self.inputs.new("NodeSocketString", "component")
        component.hide = False
        self.outputs.new("BGHubsEntitySocket", "entity")

    def draw_buttons(self, context, layout):
        layout.prop(self, "component_name")
