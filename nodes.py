import bpy
from bpy.props import PointerProperty, StringProperty
from bpy.types import Node
from io_hubs_addon.io.utils import gather_property
from .utils import gather_object_property, get_socket_value, filter_on_components, filter_entity_type, get_prefs, object_exists
from .consts import MATERIAL_PROPERTIES_ENUM, MATERIAL_PROPERTIES_TO_TYPES, SUPPORTED_COMPONENTS, SUPPORTED_PROPERTY_COMPONENTS


def update_networked_color(self, context):
    if hasattr(self, "networked") and self.networked:
        self.color = get_prefs().network_node_color
    else:
        self.color = (0.2, 0.6, 0.2)


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


class BGNetworked():

    networked: bpy.props.BoolProperty(default=True, update=update_networked_color)

    def init(self, context):
        super().init(context)
        update_networked_color(self, context)

    def refresh(self):
        if hasattr(super(), "refresh") and callable(getattr(super(), "refresh")):
            super().refresh(self)
        update_networked_color(self, bpy.context)

    def gather_configuration(self, ob, variables, events, export_settings):
        return {
            "networked": self.networked
        }


def on_entity_property_update(node, context):
    if "entity" in node.outputs:
        node.outputs.get("entity").target = node.target


class BGEntityPropertyNode():
    entity_type: bpy.props.EnumProperty(
        name="",
        description="Target Entity",
        items=filter_entity_type,
        update=on_entity_property_update,
        default=0
    )

    target: PointerProperty(
        name="Target",
        type=bpy.types.Object,
        poll=filter_on_components,
        update=on_entity_property_update
    )

    def draw_buttons(self, context, layout):
        layout.prop(self, "entity_type")
        if self.entity_type != "self":
            layout.prop(self, "target")

    def gather_configuration(self, ob, variables, events, export_settings):
        from .behavior_graph import gather_object_property
        target = ob if self.entity_type == "self" else self.target
        if not self.target and type(ob) == bpy.types.Scene:
            raise Exception('Empty entity cannot be used for Scene objects in this context')
        elif not self.target and self.entity_type == "other":
            raise Exception('Entity not set')
        else:
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


entity_property_settings = {
    "name": ("NodeSocketString", ""),
    "visible": ("NodeSocketBool", False),
    "position": ("NodeSocketVectorXYZ", [0.0, 0.0, 0.0]),
    "rotation": ("NodeSocketVectorEuler", [0.0, 0.0, 0.0]),
    "scale": ("NodeSocketVectorXYZ", [1.0, 1.0, 1.0]),
}


def update_set_entity_property(self, context):
    if self.inputs and len(self.inputs) > 2:
        self.inputs.remove(self.inputs[2])

    target = get_input_entity(self, bpy.context)
    if not target:
        return

    setattr(self, "node_type",  "hubs/entity/set/" + self.targetProperty)
    (socket_type,
     default_value) = entity_property_settings[self.targetProperty]
    socket = self.inputs.new(socket_type, self.targetProperty)
    socket.default_value = default_value


class BGHubsSetEntityProperty(BGNetworked, BGActionNode, BGNode, Node):
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
        update=update_set_entity_property
    )

    def init(self, context):
        super().init(context)
        self.inputs.new("BGHubsEntitySocket", "entity")
        update_set_entity_property(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "networked")
        entity_type = self.inputs.get("entity").entity_type
        if (entity_type == "self" and context.scene.bg_node_type != 'SCENE') or entity_type != "self":
            layout.prop(self, "targetProperty")

    def update_network_dependencies(self, ob, export_settings):
        if self.networked:
            target = get_input_entity(self, bpy.context, ob)
            if not target:
                raise Exception("Entity not set")
            if not object_exists(target):
                raise Exception(f"Entity {target.name} does not exist")
            from .utils import update_gltf_network_dependencies
            from .components import networked_object_properties
            if self.targetProperty == "position" or self.targetProperty == "rotation" or self.targetProperty == "scale":
                value = {
                    "transform": True
                }
            elif self.targetProperty == "visible":
                value = {
                    self.targetProperty: True
                }
            update_gltf_network_dependencies(self, export_settings, target,
                                             networked_object_properties.NetworkedObjectProperties, value)


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


def get_available_variables(self, context):
    get_available_variables.cached_enum = [("None", "None", "None")]

    target = get_input_entity(self, context)
    if target:
        for var in target.bg_global_variables:
            get_available_variables.cached_enum.append((var.name, var.name, var.name))

    return get_available_variables.cached_enum


# Bug: https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty
# Workaround: https://blender.stackexchange.com/a/216233
get_available_variables.cached_enum = []


def update_selected_variable(self, context):
    isSetter = self.bl_idname == "BGNode_variable_set"

    has_socket = False
    old_type = "None"
    if isSetter:
        self.color = (0.2, 0.6, 0.2)
        if "value" in self.inputs:
            has_socket = True
            from .utils import socket_to_type
            old_type = socket_to_type[self.inputs.get("value").bl_idname]
    else:
        self.color = (0.6, 0.6, 0.2)
        if "value" in self.outputs:
            has_socket = True
            from .utils import socket_to_type
            old_type = socket_to_type[self.outputs.get("value").bl_idname]

    if not context:
        return

    remove_sockets = True
    target = get_input_entity(self, context)
    if target:
        has_var = self.variableName in target.bg_global_variables
        var = target.bg_global_variables.get(self.variableName)
        var_type = var.type if has_var else "None"
        if var_type == old_type:
            remove_sockets = False

    if remove_sockets and has_socket:
        if isSetter:
            if "value" in self.inputs:
                from .utils import socket_to_type
                self.inputs.remove(self.inputs.get("value"))
        elif "value" in self.outputs:
            from .utils import socket_to_type
            self.outputs.remove(self.outputs.get("value"))

    if not target:
        return

    # Create a new socket based on the selected variable type
    from .utils import type_to_socket
    if var_type != "None" and old_type != var_type:
        if isSetter:
            socket = self.inputs.new(type_to_socket[var_type], "value")
        else:
            socket = self.outputs.new(type_to_socket[var_type], "value")
            if var_type == "entity":
                self.outputs.get("value").target = target.bg_global_variables.get(self.variableName).defaultEntity
        if var_type == "entity":
            socket.refresh = False

    if isSetter:
        if var and hasattr(var, "networked") and var.networked and var_type != "entity":
            self.color = get_prefs().network_node_color

    self.prop_type = var_type


def getVariableId(self):
    target = get_input_entity(self, bpy.context)
    if target and self.variableName in target.bg_global_variables:
        return target.bg_global_variables.find(self.variableName) + 1
    return 0


def setVariableId(self, value):
    target = get_input_entity(self, bpy.context)
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
        update=update_selected_variable,
        get=getVariableId,
        set=setVariableId,
    )

    def init(self, context):
        super().init(context)
        self.color = (0.6, 0.6, 0.2)
        self.inputs.new("BGHubsEntitySocket", "entity")
        entity = self.inputs.get("entity")
        entity.custom_type = "event_variable"
        entity.export = False
        update_selected_variable(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "variableId")

    def refresh(self):
        update_selected_variable(self, bpy.context)

    def gather_configuration(self, ob, variables, events, export_settings):
        target = get_input_entity(self, bpy.context, ob)
        if not target:
            raise Exception("Entity not set")
        if not object_exists(target):
            raise Exception(f"Entity {target.name} does not exist")
        var_name = f"{target.name}_{self.variableName}"
        if self.variableName == 'None' or var_name not in variables:
            raise Exception(f'variable node: {self.variableName}[{var_name}],  id: "None"')
        else:
            print(f'variable node: {self.variableName}, id: {variables[var_name]["id"]}')
            return {
                "variableId": variables[var_name]["id"]
            }


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
        update=update_selected_variable,
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
        update_selected_variable(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "variableId")

    def refresh(self):
        update_selected_variable(self, bpy.context)

    def gather_configuration(self, ob, variables, events, export_settings):
        target = get_input_entity(self, bpy.context, ob)
        if not target:
            raise Exception("Entity not set")
        if not object_exists(target):
            raise Exception(f"Entity {target.name} does not exist")
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
    target = get_input_entity(self, context)
    if target:
        for var in target.bg_custom_events:
            get_available_custom_events.cached_enum.append((var.name, var.name, var.name))

    return get_available_custom_events.cached_enum


# Bug: https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty
# Workaround: https://blender.stackexchange.com/a/216233
get_available_custom_events.cached_enum = []


def getCustomEventId(self):
    target = get_input_entity(self, bpy.context)
    if target and self.customEventName in target.bg_custom_events:
        return target.bg_custom_events.find(self.customEventName) + 1
    return 0


def setCustomEventId(self, value):
    target = get_input_entity(self, bpy.context)
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
        target = get_input_entity(self, bpy.context, ob)
        if not target:
            raise Exception("Entity not set")
        if not object_exists(target):
            raise Exception(f"Entity {target.name} does not exist")
        event_name = f"{target.name}_{self.customEventName}"
        if self.customEventName == 'None' or event_name not in events:
            raise Exception(f' custom event node: {self.customEventName}[{event_name}],  id: "None"')
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
        target = get_input_entity(self, bpy.context, ob)
        if not target:
            raise Exception("Entity not set")
        if not object_exists(target):
            raise Exception(f"Entity {target.name} does not exist")
        event_name = f"{target.name}_{self.customEventName}"
        if self.customEventName == 'None' or event_name not in events:
            raise Exception(f' custom event node: {self.customEventName}[{event_name}],  id: "None"')
        else:
            print(f'custom event node: {self.customEventName}, id: {events[event_name]["id"]}')
            return {
                "customEventId": events[event_name]["id"]
            }


def get_available_networkedBehavior_properties(self, context):
    get_available_networkedBehavior_properties.cached_enum = [("None", "None", "None")]

    target = get_input_entity(self, context)
    if target:
        for var in target.bg_global_variables:
            get_available_networkedBehavior_properties.cached_enum.append((var.name, var.name, var.name))

    return get_available_networkedBehavior_properties.cached_enum


# Bug: https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty
# Workaround: https://blender.stackexchange.com/a/216233
get_available_networkedBehavior_properties.cached_enum = []


def get_input_entity(node, context, ob=None):
    target = None
    entity_socket = node.inputs.get("entity")
    if entity_socket:
        target = entity_socket.target
        if node.inputs.get("entity").is_linked and len(entity_socket.links) > 0:
            link = entity_socket.links[0]
            from_node = link.from_socket.node
            # This case should go away when we remove BGNode_variable_get
            if from_node.bl_idname == "BGNode_variable_get":
                from_target = get_input_entity(from_node, context, ob)
                # When copying entities the variable is updated in the variables list
                # but not on the socket so we pull the variable value directly from the list
                target = from_target.bg_global_variables.get(from_node.variableName).defaultEntity
            elif from_node.bl_idname == "BGNode_networkedVariable_get":
                from_target = get_input_entity(from_node, context, ob)
                # When copying entities the variable is updated in the variables list
                # but not on the socket so we pull the variable value directly from the list
                target = from_target.bg_global_variables.get(from_node.prop_name).defaultEntity
            elif from_node.bl_idname == "BGNode_hubs_entity_properties":
                from_target = get_input_entity(from_node, context, ob)
                target = from_target
            else:
                target = link.from_socket.target
        else:
            if entity_socket.entity_type == '':
                target = None
            elif entity_socket.entity_type in ["object", "self"]:
                target = ob if ob else context.object
            elif entity_socket.entity_type == "scene":
                target = context.scene
            elif entity_socket.entity_type == "graph":
                # When exporting we use the current exporting object as the target object
                if ob:
                    if type(ob) == bpy.types.Object:
                        target = context.object.bg_active_graph
                    else:
                        target = context.scene.bg_active_graph
                else:
                    if context.scene.bg_node_type == 'OBJECT':
                        target = context.object.bg_active_graph
                    else:
                        target = context.scene.bg_active_graph

    return target


def update_selected_networked_variable(self, context):
    isSetter = self.bl_idname == "BGNode_networkedVariable_set"

    has_socket = False
    old_type = "None"
    if isSetter:
        self.color = (0.2, 0.6, 0.2)
        if "value" in self.inputs:
            has_socket = True
            from .utils import socket_to_type
            old_type = socket_to_type[self.inputs.get("value").bl_idname]
    else:
        self.color = (0.6, 0.6, 0.2)
        if "value" in self.outputs:
            has_socket = True
            from .utils import socket_to_type
            old_type = socket_to_type[self.outputs.get("value").bl_idname]

    if not context:
        return

    remove_sockets = True
    target = get_input_entity(self, context)
    if target:
        has_var = self.prop_name in target.bg_global_variables
        var = target.bg_global_variables.get(self.prop_name)
        var_type = var.type if has_var else "None"
        if var_type == old_type:
            remove_sockets = False

    if remove_sockets:
        if has_socket:
            if isSetter:
                if "value" in self.inputs:
                    from .utils import socket_to_type
                    self.inputs.remove(self.inputs.get("value"))
            elif "value" in self.outputs:
                from .utils import socket_to_type
                self.outputs.remove(self.outputs.get("value"))
        else:
            # Path for migrating the old networked variable get/set nodes
            if isSetter:
                for i in range(len(self.inputs) - 1, 1, -1):
                    self.inputs.remove(self.inputs[i])
            elif len(self.outputs) > 1:
                for i in range(len(self.outputs) - 1, -1, -1):
                    self.outputs.remove(self.outputs[i])

    if not target:
        return

    # Create a new socket based on the selected variable type
    from .utils import type_to_socket
    if var_type != "None" and old_type != var_type:
        if isSetter:
            socket = self.inputs.new(type_to_socket[var_type], "value")
        else:
            socket = self.outputs.new(type_to_socket[var_type], "value")
            if var_type == "entity":
                self.outputs.get("value").target = target.bg_global_variables.get(self.prop_name).defaultEntity
        if var_type == "entity":
            socket.refresh = False

    if isSetter:
        if var and hasattr(var, "networked") and var.networked and var_type != "entity":
            self.color = get_prefs().network_node_color
            self.networked = True
        else:
            self.networked = False

    self.prop_type = var_type


def getNetworkedVariableId(self):
    target = get_input_entity(self, bpy.context)
    if target and self.prop_name in target.bg_global_variables:
        return target.bg_global_variables.find(self.prop_name) + 1
    return 0


def setNetworkedVariableId(self, value):
    target = get_input_entity(self, bpy.context)
    if not target or value == 0:
        self.prop_name = 'None'
    elif value <= len(target.bg_global_variables):
        self.prop_name = target.bg_global_variables[value - 1].name
    else:
        self.prop_name = 'None'


class BGNode_networkedVariable_set(BGNetworked, BGActionNode, BGNode, Node):
    bl_label = "Variable Set"
    node_type = "networkedVariable/set"

    prop_id: bpy.props.EnumProperty(
        name="Property",
        description="Property",
        items=get_available_networkedBehavior_properties,
        update=update_selected_networked_variable,
        get=getNetworkedVariableId,
        set=setNetworkedVariableId,
        default=0
    )

    prop_name: bpy.props.StringProperty(
        name="Property Name",
        description="Property Name",
        default="None"
    )

    prop_type: bpy.props.StringProperty(default="")

    networked: bpy.props.BoolProperty(default=True, update=update_networked_color)

    def init(self, context):
        super().init(context)
        self.inputs.new("BGHubsEntitySocket", "entity")
        entity = self.inputs.get("entity")
        entity.custom_type = "event_variable"
        update_selected_networked_variable(self, context)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, "networked")
        row.enabled = False
        layout.prop(self, "prop_id")

    def refresh(self):
        update_selected_networked_variable(self, bpy.context)

    def gather_parameters(self, ob, input_socket, export_settings):
        return {
            "value": get_socket_value(ob, export_settings, input_socket)
        }

    def gather_configuration(self, ob, variables, events, export_settings):
        config = super().gather_configuration(ob, variables, events, export_settings)
        target = get_input_entity(self, bpy.context, ob)
        if not target:
            raise Exception("Entity not set")
        if not object_exists(target):
            raise Exception(f"Entity {target.name} does not exist")
        has_prop = self.prop_name in target.bg_global_variables
        if not has_prop:
            raise Exception(f"Property {self.prop_name} does not exist")
        prop = target.bg_global_variables.get(self.prop_name)
        export_prop_name = self.prop_name if prop.networked else f"{target.name}_{self.prop_name}"
        config.update({
            "variableId": variables[export_prop_name]["id"] if not prop.networked else -1,
            "name": export_prop_name,
            "valueTypeName": self.prop_type
        })
        return config

    def update_network_dependencies(self, ob, export_settings):
        target = get_input_entity(self, bpy.context, ob)
        if not target:
            raise Exception("Entity not set")
        if not object_exists(target):
            raise Exception(f"Entity {target.name} does not exist")
        has_prop = self.prop_name in target.bg_global_variables
        if not has_prop:
            raise Exception(f"Property {self.prop_name} does not exist")
        prop = target.bg_global_variables.get(self.prop_name)
        if prop.networked:
            from .utils import update_gltf_network_dependencies, get_variable_value
            from .components.networked_behavior import NetworkedBehavior
            value = {
                self.prop_name: {
                    "type": prop.type,
                    "value": get_variable_value(target, prop, export_settings)
                }
            }
            update_gltf_network_dependencies(self, export_settings, target, NetworkedBehavior, value)


class BGNode_networkedVariable_get(BGNode, Node):
    bl_label = "Variable Get"
    node_type = "networkedVariable/get"

    poll_components: StringProperty(default="networked-behavior")

    prop_id: bpy.props.EnumProperty(
        name="Property",
        description="Property",
        items=get_available_networkedBehavior_properties,
        update=update_selected_networked_variable,
        get=getNetworkedVariableId,
        set=setNetworkedVariableId,
        default=0
    )

    prop_name: bpy.props.StringProperty(
        name="Property Name",
        description="Property Name",
        default="None"
    )

    prop_type: bpy.props.StringProperty(default="")

    def init(self, context):
        super().init(context)
        self.color = (0.6, 0.6, 0.2)
        self.inputs.new("BGHubsEntitySocket", "entity")
        entity = self.inputs.get("entity")
        entity.custom_type = "event_variable"
        update_selected_networked_variable(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "prop_id")

    def refresh(self):
        update_selected_networked_variable(self, bpy.context)

    def gather_parameters(self, ob, input_socket, export_settings):
        return {
            "value": get_socket_value(ob, export_settings, input_socket)
        }

    def gather_configuration(self, ob, variables, events, export_settings):
        target = get_input_entity(self, bpy.context, ob)
        if not target:
            raise Exception("Entity not set")
        has_prop = self.prop_name in target.bg_global_variables
        if not has_prop:
            raise Exception(f"Property {self.prop_name} does not exist")
        prop = target.bg_global_variables.get(self.prop_name)
        export_prop_name = self.prop_name if prop.networked else f"{target.name}_{self.prop_name}"
        return {
            "networked": prop.networked,
            "variableId": variables[export_prop_name]["id"] if not prop.networked else -1,
            "name": export_prop_name,
            "valueTypeName": self.prop_type
        }


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

    target = get_input_entity(self, context)
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

    target = get_input_entity(self, context)
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
        self.color = (0.6, 0.6, 0.2)
        self.inputs.new("BGHubsEntitySocket", "entity")
        component = self.inputs.new("NodeSocketString", "component")
        component.hide = True
        self.outputs.new("BGHubsEntitySocket", "entity")

    def draw_buttons(self, context, layout):
        layout.prop(self, "component_name")


def getComponentId(self):
    target = get_input_entity(self, bpy.context)
    if target:
        components = [item[0] for item in getAvailableComponents(self, bpy.context)]
        if target and self.componentName in components:
            return components.index(self.componentName)
    return 0


def setComponentId(self, value):
    target = get_input_entity(self, bpy.context)
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


def getPropertyComponents(self, context):
    from io_hubs_addon.components.components_registry import get_components_registry
    registry = get_components_registry()
    getPropertyComponents.cached_enum = [("None", "None", "None")]

    target = get_input_entity(self, context)
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
            target = get_input_entity(self, context)
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
    target = get_input_entity(self, bpy.context)
    if target:
        properties = get_component_properties(target, self.componentName)
        if target and self.propertyName in properties and self.componentName != "None" and self.componentName in target.hubs_component_list.items:
            return properties.index(self.propertyName) + 1
    return 0


def setPropertyId(self, value):
    target = get_input_entity(self, bpy.context)
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

    target = get_input_entity(self, context)
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


class BGNode_set_component_property(BGNetworked, BGActionNode, BGNode, Node):
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
        self.inputs.new("BGHubsEntitySocket", "entity")

    def draw_buttons(self, context, layout):
        layout.prop(self, "networked")
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
                "networked": self.networked,
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

    target = get_input_entity(self, context)
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
        self.color = (0.6, 0.6, 0.2)
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


def get_material_socket_value(socket, context):
    value = None
    if socket:
        if socket.is_linked and len(socket.links) > 0:
            link = socket.links[0]
            from_node = link.from_socket.node
            entity = get_input_entity(from_node, context)
            if len(entity.material_slots) > 0:
                value = entity.material_slots[0].material
        else:
            value = socket.default_value

    return value


class BGNode_set_material(BGNetworked, BGActionNode, BGNode, Node):
    bl_label = "Set Material"
    node_type = "material/set"

    def init(self, context):
        super().init(context)
        self.inputs.new("BGHubsEntitySocket", "entity")
        self.inputs.new("NodeSocketMaterial", "material")

    def draw_buttons(self, context, layout):
        layout.prop(self, "networked")

    def update_network_dependencies(self, ob, export_settings):
        if self.networked:
            target = get_input_entity(self, bpy.context, ob)
            if not target:
                raise Exception("Entity not set")
            if not object_exists(target):
                raise Exception(f"Entity {target.name} does not exist")
            material = get_material_socket_value(self.inputs.get("material"), bpy.context)
            if not material:
                raise Exception("Material not set")
            from .utils import update_gltf_network_dependencies
            from .components import networked_object_material
            from .components import networked_material
            update_gltf_network_dependencies(self, export_settings, target,
                                             networked_object_material.NetworkedObjectMaterial)
            update_gltf_network_dependencies(self, export_settings, material, networked_material.NetworkedMaterial)


def update_set_material_property(self, context):
    # Remove previous socket
    if self.inputs and len(self.inputs) > 2:
        self.inputs.remove(self.inputs[2])

    # Create a new socket based on the selected variable type
    from .utils import type_to_socket
    self.inputs.new(type_to_socket[MATERIAL_PROPERTIES_TO_TYPES[self.property_name]], self.property_name)


class BGNode_set_material_property(BGNetworked, BGActionNode, BGNode, Node):
    bl_label = "Set Material Property"
    node_type = "material/property/set"

    property_name: bpy.props.EnumProperty(
        name="Property",
        description="Property",
        items=MATERIAL_PROPERTIES_ENUM,
        update=update_set_material_property,
        default="color"
    )

    def init(self, context):
        super().init(context)
        self.inputs.new("NodeSocketMaterial", "material")
        update_set_material_property(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "networked")
        layout.prop(self, "property_name")

    def gather_configuration(self, ob, variables, events, export_settings):
        config = super().gather_configuration(ob, variables, events, export_settings)
        config.update({
            "property": gather_property(export_settings, self, self, "property_name"),
            "type": MATERIAL_PROPERTIES_TO_TYPES[self.property_name]
        })
        return config

    def update_network_dependencies(self, ob, export_settings):
        if self.networked:
            material = get_material_socket_value(self.inputs.get("material"), bpy.context)
            if not material:
                raise Exception("Material not set")
            from .utils import update_gltf_network_dependencies
            from .components import networked_material
            update_gltf_network_dependencies(self, export_settings, material, networked_material.NetworkedMaterial)


def update_get_material_property(self, context):
    # Remove previous socket
    if self.outputs and len(self.outputs) > 0:
        self.outputs.remove(self.outputs[0])

    # Create a new socket based on the selected variable type
    from .utils import type_to_socket
    self.outputs.new(type_to_socket[MATERIAL_PROPERTIES_TO_TYPES[self.property_name]], self.property_name)


class BGNode_get_material_property(BGNode, Node):
    bl_label = "Get Material Property"
    node_type = "material/property/get"

    property_name: bpy.props.EnumProperty(
        name="Property",
        description="Property",
        items=MATERIAL_PROPERTIES_ENUM,
        update=update_get_material_property,
        default="color"
    )

    def init(self, context):
        super().init(context)
        self.color = (0.6, 0.6, 0.2)
        self.inputs.new("NodeSocketMaterial", "material")
        update_get_material_property(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "property_name")

    def gather_configuration(self, ob, variables, events, export_settings):
        return {
            "networked": self.networked,
            "property": gather_property(export_settings, self, self, "property_name"),
            "type": MATERIAL_PROPERTIES_TO_TYPES[self.property_name]
        }


class BGNode_media_mediaPlayback(BGNetworked, BGActionNode, BGNode, Node):
    bl_label = "Media Playback"
    node_type = "media/mediaPlayback"

    def init(self, context):
        super().init(context)
        self.inputs.new("BGHubsEntitySocket", "entity")
        from .sockets import BGFlowSocket
        BGFlowSocket.create(self.inputs, name="play")
        BGFlowSocket.create(self.inputs, name="pause")
        BGFlowSocket.create(self.inputs, name="setMuted")
        self.inputs.new("NodeSocketBool", "muted")

    def draw_buttons(self, context, layout):
        layout.prop(self, "networked")


class BGNode_media_frame_setMediaFrameProperty(BGNetworked, BGNode, Node):
    bl_label = "Set Media Frame Property"
    node_type = "media_frame/setMediaFrameProperty"

    def init(self, context):
        super().init(context)
        self.inputs.new("BGHubsEntitySocket", "entity")
        from .sockets import BGFlowSocket
        BGFlowSocket.create(self.inputs, name="setActive")
        self.inputs.new("NodeSocketBool", "active")
        BGFlowSocket.create(self.inputs, name="setLocked")
        self.inputs.new("NodeSocketBool", "locked")
        BGFlowSocket.create(self.outputs)

    def draw_buttons(self, context, layout):
        layout.prop(self, "networked")


class BGNode_animation_createAnimationAction(BGNetworked, BGActionNode, BGNode, Node):
    bl_label = "Create AnimationAction"
    node_type = "animation/createAnimationAction"

    def init(self, context):
        super().init(context)
        self.inputs.new("BGHubsEntitySocket", "entity")
        self.inputs.new("NodeSocketString", "clipName")
        self.inputs.new("NodeSocketBool", "loop")
        self.inputs.new("NodeSocketBool", "clampWhenFinished")
        self.inputs.new("NodeSocketFloat", "weight")
        self.inputs.new("NodeSocketFloat", "timeScale")
        self.inputs.new("NodeSocketBool", "additiveBlending")
        self.outputs.new("BGHubsAnimationActionSocket", "action")

    def draw_buttons(self, context, layout):
        layout.prop(self, "networked")

    def update_network_dependencies(self, ob, export_settings):
        if self.networked:
            target = get_input_entity(self, bpy.context, ob)
            if not target:
                raise Exception("Entity not set")
            if not object_exists(target):
                raise Exception(f"Entity {target.name} does not exist")
            from .utils import update_gltf_network_dependencies
            from .components import networked_animation
            update_gltf_network_dependencies(self, export_settings, target, networked_animation.NetworkedAnimation)


class BGNode_animation_play(BGNetworked, BGActionNode, BGNode, Node):
    bl_label = "Play Animation"
    node_type = "animation/play"

    def init(self, context):
        super().init(context)
        from .sockets import BGFlowSocket
        self.inputs.new("BGHubsAnimationActionSocket", "action")
        self.inputs.new("NodeSocketBool", "reset")
        BGFlowSocket.create(self.outputs, name="finished")
        BGFlowSocket.create(self.outputs, name="loop")
        BGFlowSocket.create(self.outputs, name="stopped")

    def draw_buttons(self, context, layout):
        layout.prop(self, "networked")


class BGNode_animation_stop(BGNetworked, BGActionNode, BGNode, Node):
    bl_label = "Stop Animation"
    node_type = "animation/stop"

    def init(self, context):
        super().init(context)
        self.inputs.new("BGHubsAnimationActionSocket", "action")

    def draw_buttons(self, context, layout):
        layout.prop(self, "networked")


class BGNode_animation_crossfadeTo(BGNetworked, BGActionNode, BGNode, Node):
    bl_label = "Crossfade To Animation"
    node_type = "animation/crossfadeTo"

    def init(self, context):
        super().init(context)
        self.inputs.new("BGHubsAnimationActionSocket", "action")
        self.inputs.new("BGHubsAnimationActionSocket", "toAction")
        self.inputs.new("NodeSocketFloat", "duration")

    def draw_buttons(self, context, layout):
        layout.prop(self, "networked")


class BGNode_three_animation_setTimescale(BGNetworked, BGActionNode, BGNode, Node):
    bl_label = "Set timeScale"
    node_type = "three/animation/setTimescale"

    def init(self, context):
        super().init(context)
        self.inputs.new("BGHubsAnimationActionSocket", "action")
        self.inputs.new("NodeSocketFloat", "timeScale")

    def draw_buttons(self, context, layout):
        layout.prop(self, "networked")
