import bpy
from bpy.props import PointerProperty, StringProperty
from bpy.types import Node
from io_hubs_addon.components.definitions import text, video, audio, media_frame, visible
from .components import networked_animation, networked_behavior, networked_transform, rigid_body, physics_shape
from io_hubs_addon.io.utils import gather_property
from .utils import gather_object_property, get_socket_value, filter_on_components, filter_entity_type


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


class BGEntityPropertyNode():
    entity_type: bpy.props.EnumProperty(
        name="",
        description="Target Entity",
        items=filter_entity_type,
        default=0
    )

    target: PointerProperty(
        name="Target",
        type=bpy.types.Object,
        poll=filter_on_components
    )

    export_type: bpy.props.EnumProperty(
        name="Entity Type",
        description="Entity Type",
        items=[("none", "None", "None"), ("object", "Object", "Object"), ("scene", "Scene", "Scene")],
        options={'HIDDEN'},
    )

    def draw_buttons(self, context, layout):
        layout.prop(self, "entity_type")
        if self.entity_type != "self":
            layout.prop(self, "target")

    def gather_configuration(self, ob, variables, events, export_settings):
        self.export_type = "object" if type(ob) == bpy.types.Object else "scene"
        from .behavior_graph import gather_object_property
        target = ob if self.entity_type == "self" else self.target
        if not self.target and type(ob) == bpy.types.Scene:
            self.export_type = "none"
            raise Exception('Empty entity cannot be used for Scene objects in this context')
        else:
            self.export_type = "none"
            return {
                "target": gather_object_property(export_settings, target)
            }

    def gather_parameters(self, ob, input_socket, export_settings):
        if not self.target:
            if type(ob) == bpy.types.Scene:
                raise Exception('Empty entity cannot be used for Scene objects in this context')
            else:
                return {
                    "value": gather_object_property(export_settings, ob)
                }
        else:
            return {
                "value": gather_object_property(export_settings, input_socket.target)
            }

    def get_target(self):
        return self.target

    def get_entity_type(self):
        return self.entity_type


entity_property_settings = {
    "visible": ("NodeSocketBool", False),
    "position": ("NodeSocketVectorXYZ", [0.0, 0.0, 0.0]),
    "rotation": ("NodeSocketVectorEuler", [0.0, 0.0, 0.0]),
    "scale": ("NodeSocketVectorXYZ", [1.0, 1.0, 1.0]),
}


def update_target_property(self, context):
    if self.inputs and len(self.inputs) > 2:
        self.outputs.remove(self.inputs[2])

    # context can be null here sometimes so using the global context
    entity_type = self.inputs.get("entity").entity_type
    if entity_type == "self" and bpy.context.scene.bg_node_type == 'SCENE':
        return

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
        entity_type = self.inputs.get("entity").entity_type
        if (entity_type == "self" and context.scene.bg_node_type != 'SCENE') or entity_type != "self":
            layout.prop(self, "targetProperty")


class BGNode_hubs_onInteract(BGEventNode, BGEntityPropertyNode, BGNode, Node):
    bl_label = "On Interact"
    node_type = "hubs/onInteract"

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsEntitySocket", "entity")


class BGNode_hubs_onCollisionEnter(BGEventNode, BGEntityPropertyNode, BGNode, Node):
    bl_label = "On Collision Enter"
    node_type = "hubs/onCollisionEnter"

    poll_components: StringProperty(default="physics-shape")

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsEntitySocket", "entity")


class BGNode_hubs_onCollisionStay(BGEventNode, BGEntityPropertyNode, BGNode, Node):
    bl_label = "On Collision Stay"
    node_type = "hubs/onCollisionStay"

    poll_components: StringProperty(default="physics-shape")

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsEntitySocket", "entity")


class BGNode_hubs_onCollisionExit(BGEventNode, BGEntityPropertyNode, BGNode, Node):
    bl_label = "On Collision Exit"
    node_type = "hubs/onCollisionExit"

    poll_components: StringProperty(default="physics-shape")

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsEntitySocket", "entity")


class BGNode_hubs_onPlayerCollisionEnter(BGEventNode, BGEntityPropertyNode, BGNode, Node):
    bl_label = "On Player Collision Enter"
    node_type = "hubs/onPlayerCollisionEnter"

    poll_components: StringProperty(default="physics-shape")

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsPlayerSocket", "player")


class BGNode_hubs_onPlayerCollisionStay(BGEventNode, BGEntityPropertyNode, BGNode, Node):
    bl_label = "On Player Collision Stay"
    node_type = "hubs/onPlayerCollisionStay"

    poll_components: StringProperty(default="physics-shape")

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsPlayerSocket", "player")


class BGNode_hubs_onPlayerCollisionExit(BGEventNode, BGEntityPropertyNode, BGNode, Node):
    bl_label = "On Player Collision Exit"
    node_type = "hubs/onPlayerCollisionExit"

    poll_components: StringProperty(default="physics-shape")

    def init(self, context):
        super().init(context)
        self.outputs.new("BGHubsPlayerSocket", "player")


class BGNode_media_onMediaEvent(BGEventNode, BGEntityPropertyNode, BGNode, Node):
    bl_label = "On Media Event"
    node_type = "media/onMediaEvent"

    poll_components: StringProperty(default="video,audio")

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
        super().draw_buttons(context, layout)


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


def get_variable_target(node, context, ob=None):
    target = None
    entity_socket = node.inputs.get("entity")
    if entity_socket:
        target = entity_socket.target
        if node.inputs.get("entity").is_linked and len(entity_socket.links) > 0:
            link = entity_socket.links[0]
            # When copying entities the variable is updated in the networked behavior  list
            # but not on the socket so we pull the variable value directly from the list
            node = link.from_socket.node
            if node.bl_idname == "BGNode_variable_get" and ob:
                target = ob.bg_global_variables.get(node.variableName).defaultEntity
            else:
                target = link.from_socket.target
        else:
            if entity_socket.entity_type == "object":
                target = ob if ob else context.object
            elif entity_socket.entity_type == "scene":
                target = context.scene
            elif entity_socket.entity_type == "graph":
                if context.scene.bg_node_type == 'OBJECT':
                    target = context.object.bg_active_graph
                else:
                    target = context.scene.bg_active_graph

    return target


def get_available_variables(self, context):
    get_available_variables.cached_enum = [("None", "None", "None")]

    target = get_variable_target(self, context)
    if target:
        for var in target.bg_global_variables:
            get_available_variables.cached_enum.append((var.name, var.name, var.name))

    return get_available_variables.cached_enum


# Bug: https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty
# Workaround: https://blender.stackexchange.com/a/216233
get_available_variables.cached_enum = []


def update_selected_variable_output(self, context):
    # Remove previous socket
    if self.outputs:
        self.outputs.remove(self.outputs[0])

    if not context:
        return

    target = get_variable_target(self, context)

    if not target:
        return

    has_var = self.variableName in target.bg_global_variables
    var_type = target.bg_global_variables.get(self.variableName).type if has_var else "None"

    # Create a new socket based on the selected variable type
    from .utils import type_to_socket
    if var_type != "None":
        self.outputs.new(type_to_socket[var_type], "value")
        if var_type == "entity":
            self.outputs[0].target = target.bg_global_variables.get(self.variableName).defaultEntity


def getVariableId(self):
    target = get_variable_target(self, bpy.context)
    if target and self.variableName in target.bg_global_variables:
        return target.bg_global_variables.find(self.variableName) + 1
    return 0


def setVariableId(self, value):
    target = get_variable_target(self, bpy.context)
    if not target or value == 0:
        self.variableName = 'None'
    elif value <= len(target.bg_global_variables):
        self.variableName = target.bg_global_variables[value - 1].name
    else:
        self.variableName = 'None'


class BGNode_variable_get(BGNode, Node):
    bl_label = "Get Variable"
    node_type = "variable/get"

    variableName: bpy.props.StringProperty(
        name="Variable Name",
        description="Variable Name",
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
        self.inputs.new("BGHubsEntitySocket", "entity")
        entity = self.inputs.get("entity")
        entity.custom_type = "event_variable"
        entity.export = False
        update_selected_variable_output(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "variableId")

    def refresh(self):
        from .utils import socket_to_type
        target = get_variable_target(self, bpy.context)
        has_var = self.variableName in target.bg_global_variables
        var_type = target.bg_global_variables.get(self.variableName).type if has_var else "None"
        cur_type = socket_to_type[self.outputs[0].bl_idname] if self.outputs and len(self.outputs) > 0 else 'None'
        if not has_var or var_type != cur_type:
            if target and len(self.outputs) > 0 and len(self.outputs[0].links) > 0:
                has_var = self.variableId in target.bg_global_variables
                var_type = target.bg_global_variables.get(
                    self.variableId).type if has_var else "None"
                if self.outputs[0] != None and var_type != socket_to_type[self.outputs[0].bl_idname]:
                    try:
                        target.bg_active_graph.links.remove(self.outputs[0].links[0])
                    except Exception as e:
                        print(e)

    def gather_configuration(self, ob, variables, events, export_settings):
        target = get_variable_target(self, bpy.context, ob)
        var_name = f"{target.name}_{self.variableName}"
        if self.variableName == 'None' or var_name not in variables:
            raise Exception(f'variable node: {self.variableName}[{var_name}],  id: "None"')
        else:
            print(f'variable node: {self.variableName}, id: {variables[var_name]["id"]}')
            return {
                "variableId": variables[var_name]["id"]
            }


def update_selected_variable_input(self, context):
    # Remove previous socket
    if self.inputs and len(self.inputs) > 2:
        self.inputs.remove(self.inputs[2])

    if not context:
        return

    target = get_variable_target(self, context)

    if not target:
        return

    has_var = self.variableName in target.bg_global_variables
    var_type = target.bg_global_variables.get(self.variableName).type if has_var else "None"

    # Create a new socket based on the selected variable type
    from .utils import type_to_socket
    if var_type != "None":
        self.inputs.new(type_to_socket[var_type], "value")


class BGNode_variable_set(BGActionNode, BGNode, Node):
    bl_label = "Set Variable"
    node_type = "variable/set"

    variableName: bpy.props.StringProperty(
        name="Variable Name",
        description="Variable Name",
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
        self.inputs.new("BGHubsEntitySocket", "entity")
        entity = self.inputs.get("entity")
        entity.custom_type = "event_variable"
        entity.export = False
        update_selected_variable_input(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "variableId")

    def refresh(self):
        from .utils import socket_to_type
        target = get_variable_target(self, bpy.context)
        if not target:
            return

        has_var = self.variableName in target.bg_global_variables
        var_type = target.bg_global_variables.get(self.variableName).type if has_var else "None"
        cur_type = socket_to_type[self.inputs[1].bl_idname] if self.inputs and len(self.inputs) > 1 else 'None'
        if not has_var or var_type != cur_type:
            update_selected_variable_input(self, bpy.context)
            if target and len(self.inputs) > 1 and len(self.inputs[1].links) > 0:
                has_var = self.variableId in target.bg_global_variables
                var_type = target.bg_global_variables.get(
                    self.variableId).type if has_var else "None"
                if self.inputs[1] != None and var_type != socket_to_type[self.inputs[1].bl_idname]:
                    target.bg_active_graph.links.remove(self.inputs[1].links[0])

    def gather_configuration(self, ob, variables, events, export_settings):
        target = get_variable_target(self, bpy.context, ob)
        var_name = f"{target.name}_{self.variableName}"
        if self.variableName == 'None' or var_name not in variables:
            raise Exception(f'variable node: {self.variableName}[{var_name}],  id: "None"')
        else:
            print(f'variable node: {self.variableName}, id: {variables[var_name]["id"]}')
            return {
                "variableId": variables[var_name]["id"]
            }


def get_available_custom_events(self, context):
    get_available_custom_events.cached_enum = [("None", "None", "None")]
    target = get_variable_target(self, context)
    if target:
        for var in target.bg_custom_events:
            get_available_custom_events.cached_enum.append((var.name, var.name, var.name))

    return get_available_custom_events.cached_enum


# Bug: https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty
# Workaround: https://blender.stackexchange.com/a/216233
get_available_custom_events.cached_enum = []


def getCustomEventId(self):
    target = get_variable_target(self, bpy.context)
    if target and self.customEventName in target.bg_custom_events:
        return target.bg_custom_events.find(self.customEventName) + 1
    return 0


def setCustomEventId(self, value):
    target = get_variable_target(self, bpy.context)
    if not target or value == 0:
        self.customEventName = 'None'
    elif value <= len(target.bg_custom_events):
        self.customEventName = target.bg_custom_events[value - 1].name
    else:
        self.customEventName = 'None'


class BGNode_customEvent_trigger(BGActionNode, BGNode, Node):
    bl_label = "Trigger"
    node_type = "customEvent/trigger"

    customEventName: bpy.props.StringProperty(
        name="Custom Event Name",
        description="Custom Event Name",
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
        self.inputs.new("BGHubsEntitySocket", "entity")
        entity = self.inputs.get("entity")
        entity.custom_type = "event_variable"
        entity.export = False

    def draw_buttons(self, context, layout):
        layout.prop(self, "customEventId")

    def refresh(self):
        self.customEventId = self.customEventId

    def gather_configuration(self, ob, variables, events, export_settings):
        target = get_variable_target(self, bpy.context, ob)
        event_name = f"{target.name}_{self.customEventName}"
        if self.customEventName == 'None' or event_name not in events:
            raise Exception(f' custom event node: {self.variableName}[{event_name}],  id: "None"')
        else:
            print(f'custom event node: {self.customEventName}, id: {events[event_name]["id"]}')
            return {
                "customEventId": events[event_name]["id"]
            }


class BGNode_customEvent_onTriggered(BGEventNode, BGNode, Node):
    bl_label = "On Trigger"
    node_type = "customEvent/onTriggered"

    customEventName: bpy.props.StringProperty(
        name="Custom Event Name",
        description="Custom Event Name",
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
        self.inputs.new("BGHubsEntitySocket", "entity")
        entity = self.inputs.get("entity")
        entity.custom_type = "event_variable"
        entity.export = False

    def draw_buttons(self, context, layout):
        layout.prop(self, "customEventId")

    def refresh(self):
        self.customEventId = self.customEventId

    def gather_configuration(self, ob, variables, events, export_settings):
        target = get_variable_target(self, bpy.context, ob)
        event_name = f"{target.name}_{self.customEventName}"
        if self.customEventName == 'None' or event_name not in events:
            raise Exception(f' custom event node: {self.variableName}[{event_name}],  id: "None"')
        else:
            print(f'custom event node: {self.customEventName}, id: {events[event_name]["id"]}')
            return {
                "customEventId": events[event_name]["id"]
            }


def get_available_networkedBehavior_properties(self, context):
    target = get_target(self, context)

    get_available_networkedBehavior_properties.cached_enum = [("None", "None", "None")]
    if target and hasattr(target, "hubs_component_networked_behavior"):
        for prop in target.hubs_component_networked_behavior.props_list:
            get_available_networkedBehavior_properties.cached_enum.append((prop.name, prop.name, prop.name))

    return get_available_networkedBehavior_properties.cached_enum


# Bug: https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty
# Workaround: https://blender.stackexchange.com/a/216233
get_available_networkedBehavior_properties.cached_enum = []


def get_target(self, context):
    target = None
    entity_socket = self.inputs.get("entity")
    if entity_socket:
        target = entity_socket.target
        if self.inputs.get("entity").is_linked and len(entity_socket.links) > 0:
            link = entity_socket.links[0]
            target = link.from_socket.target
        else:
            entity_type = entity_socket.entity_type
            if entity_type == "self":
                target = context.object if context.scene.bg_node_type == 'OBJECT' else context.scene

    return target


def networkedBehavior_properties_updated(self, context):
    target = get_target(self, context)
    if not target or not hasattr(target, "hubs_component_networked_behavior"):
        return

    has_prop = self.prop_name in target.hubs_component_networked_behavior.props_list
    prop_type = target.hubs_component_networked_behavior.props_list[self.prop_name].type if has_prop else "None"

    for socket_id in ["boolean", "float", "integer", "string", "vec3"]:
        if socket_id in self.inputs:
            self.inputs[socket_id].hide = not prop_type or prop_type != socket_id
        if socket_id in self.outputs:
            self.outputs[socket_id].hide = not prop_type or prop_type != socket_id

    if self.prop_type != prop_type and (self.prop_type != "" and self.prop_type != "None"):
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
        self.inputs.new("BGHubsEntitySocket", "entity")
        entity = self.inputs.get("entity")
        entity.poll_components = "networked-behavior"
        self.inputs.new("NodeSocketBool", "boolean")
        self.inputs['boolean'].hide = True
        self.inputs.new("NodeSocketFloat", "float")
        self.inputs['float'].hide = True
        self.inputs.new("NodeSocketInt", "integer")
        self.inputs['integer'].hide = True
        self.inputs.new("NodeSocketString", "string")
        self.inputs['string'].hide = True
        self.inputs.new("NodeSocketVectorXYZ", "vec3")
        self.inputs['vec3'].hide = True
        self.inputs.new("NodeSocketVectorXYZ", "color")
        self.inputs['color'].hide = True

    def draw_buttons(self, context, layout):
        layout.prop(self, "prop_name")

    def refresh(self):
        if self.prop_name:
            self.prop_name = self.prop_name

    def gather_parameters(self, ob, input_socket, export_settings):
        if self.prop_type == input_socket.identifier:
            return {
                "value": get_socket_value(ob, export_settings, input_socket)
            }

    def gather_configuration(self, ob, variables, events, export_settings):
        return {
            "prop_name": gather_property(export_settings, self, self, "prop_name"),
            "prop_type": gather_property(export_settings, self, self, "prop_type")
        }


class BGNode_networkedVariable_get(BGNode, Node):
    bl_label = "Networked Variable Get"
    node_type = "networkedVariable/get"

    poll_components: StringProperty(default="networked-behavior")

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
        self.inputs.new("BGHubsEntitySocket", "entity")
        entity = self.inputs.get("entity")
        entity.poll_components = "networked-behavior"
        self.outputs.new("NodeSocketBool", "boolean")
        self.outputs['boolean'].hide = True
        self.outputs.new("NodeSocketFloat", "float")
        self.outputs['float'].hide = True
        self.outputs.new("NodeSocketInt", "integer")
        self.outputs['integer'].hide = True
        self.outputs.new("NodeSocketString", "string")
        self.outputs['string'].hide = True
        self.outputs.new("NodeSocketVectorXYZ", "vec3")
        self.outputs['vec3'].hide = True
        self.outputs.new("NodeSocketVectorXYZ", "color")
        self.outputs['color'].hide = True

    def draw_buttons(self, context, layout):
        layout.prop(self, "prop_name")

    def refresh(self):
        if self.prop_name:
            self.prop_name = self.prop_name

    def gather_parameters(self, ob, input_socket, export_settings):
        if self.prop_type == input_socket.identifier:
            return {
                "value": get_socket_value(ob, export_settings, input_socket)
            }

    def gather_configuration(self, ob, variables, events, export_settings):
        return {
            "prop_name": gather_property(export_settings, self, self, "prop_name"),
            "prop_type": gather_property(export_settings, self, self, "prop_type")
        }


SUPPORTED_COMPONENTS = [
    video.Video.get_name(),
    audio.Audio.get_name(),
    text.Text.get_name(),
    networked_animation.NetworkedAnimation.get_name(),
    rigid_body.RigidBody.get_name(),
    physics_shape.PhysicsShape.get_name(),
    networked_transform.NetworkedTransform.get_name(),
    networked_behavior.NetworkedBehavior.get_name(),
    media_frame.MediaFrame.get_name(),
    visible.Visible.get_name()
]


def get_children(ob):
    children = []
    for ob in bpy.context.view_layer.objects:
        if ob.parent == ob:
            children.append(ob)
    return children


def get_object_components(ob):
    items = []
    items.extend(ob.hubs_component_list.items.keys())
    for child in get_children(ob):
        items.extend(child.hubs_component_list.items.keys())
    return items


def getAvailableComponents(self, context):
    from io_hubs_addon.components.components_registry import get_components_registry
    registry = get_components_registry()
    getAvailableComponents.cached_enum = [("None", "None", "None")]

    target = get_target(self, context)
    if target:
        all_object_components = get_object_components(target)
        for component_name, component_class in registry.items():
            if target and component_name in all_object_components and component_name in SUPPORTED_COMPONENTS:
                getAvailableComponents.cached_enum.append(
                    (component_name, component_class.get_display_name(),
                        component_class.get_display_name()))

    return getAvailableComponents.cached_enum


# Bug: https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty
# Workaround: https://blender.stackexchange.com/a/216233
getAvailableComponents.cached_enum = []


def component_updated(self, context):
    self.inputs.get("entity").component = self.component_name
    self.inputs.get("component").default_value = self.component_name

    target = get_target(self, context)
    self.outputs.get("entity").target = target


class BGNode_get_component(BGNode, Node):
    bl_label = "Get Component"
    node_type = "entity/getEntityComponent"

    component_name: bpy.props.EnumProperty(
        name="Component",
        description="Component",
        items=getAvailableComponents,
        update=component_updated,
        default=0
    )

    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.6, 0.2)
        self.inputs.new("BGHubsEntitySocket", "entity")
        component = self.inputs.new("NodeSocketString", "component")
        component.hide = True
        self.outputs.new("BGHubsEntitySocket", "entity")

    def draw_buttons(self, context, layout):
        layout.prop(self, "component_name")


def getComponentId(self):
    target = get_target(self, bpy.context)
    if target:
        components = [item[0] for item in getAvailableComponents(self, bpy.context)]
        if target and self.componentName in components:
            return components.index(self.componentName)
    return 0


def setComponentId(self, value):
    target = get_target(self, bpy.context)
    if target:
        components = [item[0] for item in getAvailableComponents(self, bpy.context)]
        if not target or value == 0:
            self.componentName = 'None'
        elif value <= len(components):
            self.componentName = components[value]
        else:
            self.componentName = 'None'
    else:
        self.componentName = 'None'


SUPPORTED_PROPERTY_COMPONENTS = [
    video.Video.get_name(),
    audio.Audio.get_name(),
    text.Text.get_name(),
    rigid_body.RigidBody.get_name(),
    media_frame.MediaFrame.get_name(),
    visible.Visible.get_name(),
]


def getPropertyComponents(self, context):
    from io_hubs_addon.components.components_registry import get_components_registry
    registry = get_components_registry()
    getPropertyComponents.cached_enum = [("None", "None", "None")]

    target = get_target(self, context)
    if target:
        all_object_components = get_object_components(target)
        for component_name, component_class in registry.items():
            if target and component_name in all_object_components and component_name in SUPPORTED_PROPERTY_COMPONENTS:
                getPropertyComponents.cached_enum.append(
                    (component_name, component_class.get_display_name(),
                        component_class.get_display_name()))

    return getPropertyComponents.cached_enum


# Bug: https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty
# Workaround: https://blender.stackexchange.com/a/216233
getPropertyComponents.cached_enum = []


def getAvailableProperties(self, context):
    from io_hubs_addon.components.components_registry import get_component_by_name
    getAvailableProperties.cached_enum = [("None", "None", "None")]
    if self.componentName != "None":
        component_class = get_component_by_name(self.componentName)
        for property_name in component_class.get_properties():
            component_id = component_class.get_id()
            target = get_target(self, context)
            if target:
                component = getattr(target, component_id)
                property = component.bl_rna.properties[property_name]
                if not property.is_hidden:
                    getAvailableProperties.cached_enum.append(
                        (property.identifier, property.name, property.description))

    return getAvailableProperties.cached_enum


# Bug: https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty
# Workaround: https://blender.stackexchange.com/a/216233
getAvailableProperties.cached_enum = []


def get_component_properties(target, componentName):
    properties = []
    from io_hubs_addon.components.components_registry import get_component_by_name
    component_class = get_component_by_name(componentName)
    if component_class:
        for property_name in component_class.get_properties():
            component_id = component_class.get_id()
            component = getattr(target, component_id)
            property = component.bl_rna.properties[property_name]
            if not property.is_hidden:
                properties.append(property.identifier)
    return properties


def getPropertyId(self):
    target = get_target(self, bpy.context)
    if target:
        properties = get_component_properties(target, self.componentName)
        if target and self.propertyName in properties and self.componentName != "None" and self.componentName in target.hubs_component_list.items:
            return properties.index(self.propertyName) + 1
    return 0


def setPropertyId(self, value):
    target = get_target(self, bpy.context)
    if target:
        if self.componentName not in target.hubs_component_list.items:
            self.propertyName = 'None'
        else:
            properties = get_component_properties(target, self.componentName)
            if not target or value == 0:
                self.propertyName = 'None'
            elif value <= len(properties):
                self.propertyName = properties[value - 1]
            else:
                self.propertyName = 'None'
    else:
        self.propertyName = 'None'


def update_set_component_property(self, context):
    # Remove previous socket
    if self.inputs and len(self.inputs) > 2:
        self.inputs.remove(self.inputs[2])

    if not context:
        return

    target = get_target(self, context)
    if not target or self.componentName == "None" or self.propertyName == "None" or self.componentName not in target.hubs_component_list.items:
        return

    properties = get_component_properties(target, self.componentName)
    if self.propertyName not in properties:
        return

    from .utils import propToType, type_to_socket
    from io_hubs_addon.components.components_registry import get_component_by_name

    component_class = get_component_by_name(self.componentName)
    component_id = component_class.get_id()
    component = getattr(target, component_id)

    property_definition = component.bl_rna.properties[self.propertyName]
    var_type = propToType(property_definition)

    # Create a new socket based on the selected variable type
    if var_type:
        prop_value = getattr(component, self.propertyName)
        if var_type == "enum":
            self.inputs.new(type_to_socket[var_type], "string")
            socket = self.inputs.get("string")
            for item in property_definition.enum_items:
                choice = socket.choices.add()
                choice.text = item.identifier
                choice.value = item.name
        else:
            self.inputs.new(type_to_socket[var_type], var_type)
            socket = self.inputs.get(var_type)
            socket.default_value = prop_value


class BGNode_set_component_property(BGActionNode, BGNode, Node):
    bl_label = "Set Component Property"
    node_type = "components/setComponentProperty"

    componentId: bpy.props.EnumProperty(
        name="Component",
        description="Component",
        items=getPropertyComponents,
        update=update_set_component_property,
        get=getComponentId,
        set=setComponentId,
        default=0
    )

    componentName: bpy.props.StringProperty(
        name="Component Name",
        description="Component Name",
        default="None"
    )

    propertyId: bpy.props.EnumProperty(
        name="Property",
        description="Property",
        items=getAvailableProperties,
        update=update_set_component_property,
        get=getPropertyId,
        set=setPropertyId,
        default=0
    )

    propertyName: bpy.props.StringProperty(
        name="Property Name",
        description="Property Name",
        default="None"
    )

    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.6, 0.2)
        self.inputs.new("BGHubsEntitySocket", "entity")

    def draw_buttons(self, context, layout):
        layout.prop(self, "componentId")
        layout.prop(self, "propertyId")

    def gather_parameters(self, ob, input_socket, export_settings):
        return {
            "value": get_socket_value(ob, export_settings, input_socket)
        }

    def gather_configuration(self, ob, variables, events, export_settings):
        if len(self.inputs) > 2:
            from .utils import socket_to_type
            prop_type = socket_to_type[self.inputs[2].bl_idname]
            return {
                "component": gather_property(export_settings, self, self, "componentName"),
                "property": gather_property(export_settings, self, self, "propertyName"),
                "type": prop_type
            }


def update_get_component_property(self, context):
    # Remove previous socket
    if self.outputs and len(self.outputs) > 1:
        self.outputs.remove(self.outputs[1])

    if not context:
        return

    target = get_target(self, context)
    if not target or self.componentName == "None" or self.propertyName == "None" or self.componentName not in target.hubs_component_list.items:
        return

    properties = get_component_properties(target, self.componentName)
    if self.propertyName not in properties:
        return

    from .utils import propToType, type_to_socket
    from io_hubs_addon.components.components_registry import get_component_by_name

    component_class = get_component_by_name(self.componentName)
    component_id = component_class.get_id()
    component = getattr(target, component_id)

    property_definition = component.bl_rna.properties[self.propertyName]
    var_type = propToType(property_definition)

    # Create a new socket based on the selected variable type
    if var_type:
        prop_value = getattr(component, self.propertyName)
        if var_type == "enum":
            self.outputs.new(type_to_socket[var_type], "string")
            socket = self.outputs.get("string")
            for item in property_definition.enum_items:
                choice = socket.choices.add()
                choice.text = item.identifier
                choice.value = item.name
        else:
            self.outputs.new(type_to_socket[var_type], var_type)
            socket = self.outputs.get(var_type)
            socket.default_value = prop_value


class BGNode_get_component_property(BGNode, Node):
    bl_label = "Get Component Property"
    node_type = "components/getComponentProperty"

    componentId: bpy.props.EnumProperty(
        name="Component",
        description="Component",
        items=getPropertyComponents,
        update=update_get_component_property,
        get=getComponentId,
        set=setComponentId,
        default=0
    )

    componentName: bpy.props.StringProperty(
        name="Component Name",
        description="Component Name",
        default="None"
    )

    propertyId: bpy.props.EnumProperty(
        name="Property",
        description="Property",
        items=getAvailableProperties,
        update=update_get_component_property,
        get=getPropertyId,
        set=setPropertyId,
        default=0
    )

    propertyName: bpy.props.StringProperty(
        name="Property Name",
        description="Property Name",
        default="None"
    )

    def init(self, context):
        super().init(context)
        self.color = (0.2, 0.6, 0.2)
        self.inputs.new("BGHubsEntitySocket", "entity")

    def draw_buttons(self, context, layout):
        layout.prop(self, "componentId")
        layout.prop(self, "propertyId")

    def gather_configuration(self, ob, variables, events, export_settings):
        if len(self.outputs) > 0:
            from .utils import socket_to_type
            prop_type = socket_to_type[self.outputs[0].bl_idname]
            return {
                "component": gather_property(export_settings, self, self, "componentName"),
                "property": gather_property(export_settings, self, self, "propertyName"),
                "type": prop_type
            }
