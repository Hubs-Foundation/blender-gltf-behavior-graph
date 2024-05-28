import bpy
from bpy.props import StringProperty, PointerProperty
from bpy.types import NodeSocketStandard, NodeSocketString

if bpy.app.version < (4, 0, 0):
    from bpy.types import NodeSocketInterface as NodeSocket
else:
    from bpy.types import NodeSocket

from .utils import gather_object_property, filter_on_components, filter_entity_type, update_nodes, should_export_node_entity

class BGFlowSocket(NodeSocketStandard):
    bl_label = "Behavior Graph Flow"

    def draw(self, context, layout, node, text):
        if text == "flow":
            layout.label(text="▶")
        elif self.is_output:
            layout.label(text=text + " ▶")
        else:
            layout.label(text="▶ " + text)

    def draw_color(self, context, node):
        return (1.0, 1.0, 1.0, 1.0)

    @classmethod
    def create(cls, target, name="flow"):
        socket = target.new(cls.bl_rna.name, name)
        socket.display_shape = "DIAMOND"
        if socket.is_output:
            socket.link_limit = 1
        else:
            socket.link_limit = 0


class BGHubsEntitySocketInterface(NodeSocket):
    bl_idname = "BGHubsEntitySocketInterface"
    bl_socket_idname = "BGHubsEntitySocket"

    if bpy.app.version < (4, 0, 0):
        def draw(self, context, layout):
            pass
        def draw_color(self, context):
            return (0.2, 1.0, 0.2, 1.0)
    else:
        def draw(self, context, layout, node, text):
            pass
        def draw_color(self, context, node):
            return (0.2, 1.0, 0.2, 1.0)


def update_entity_socket(self, context):
    if self.refresh:
        update_nodes(self, context)


class BGHubsEntitySocket(NodeSocketStandard):
    bl_label = "Hubs Entity"

    target: PointerProperty(
        name="Target Entity",
        description="Target Entity",
        type=bpy.types.Object,
        poll=filter_on_components,
        update=update_entity_socket
    )

    entity_type: bpy.props.EnumProperty(
        name="Entity Type",
        description="Entity Type",
        items=filter_entity_type,
        options={'HIDDEN'},
        update=update_entity_socket,
        default=0
    )

    poll_components: bpy.props.StringProperty(
        name="Component",
        description="Component",
        options={'HIDDEN'},
        default=""
    )

    custom_type: bpy.props.EnumProperty(
        name="Custom Type", description="Custom Type",
        items=[("default", "Default", "Default"),
               ("event_variable", "Event/Variable", "Event/Variable")],
        options={'HIDDEN'},
        default=0)

    export: bpy.props.BoolProperty(default=True)

    refresh: bpy.props.BoolProperty(default=True)

    def draw(self, context, layout, node, text=None):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            col = layout.column()
            col.prop(self, "entity_type")
            is_var_event_node = self.node.bl_idname in ["BGNode_variable_get",
                                                        "BGNode_variable_set",
                                                        "BGNode_customEvent_trigger",
                                                        "BGNode_customEvent_onTriggered", "BGNode_networkedVariable_get",
                                                        "BGNode_networkedVariable_set"]
            if is_var_event_node:
                if self.entity_type == "other":
                    col.prop(self, "target", text=text)
            else:
                if self.entity_type != "self":
                    col.prop(self, "target", text=text)

    def draw_color(self, context, node):
        return (0.2, 1.0, 0.2, 1.0)

    def gather_parameters(self, ob, export_settings):
        if should_export_node_entity(self.node, ob) and self.export:
            if not self.entity_type:
                raise Exception('Entity type not correctly set')

            if self.entity_type == "self":
                return {
                    "value": gather_object_property(export_settings, ob)
                }
            elif self.entity_type == "other":
                if self.target:
                    if self.target.name not in bpy.context.view_layer.objects:
                        raise Exception(f"Entity {self.target.name} does not exist")
                    else:
                        return {
                            "value": gather_object_property(export_settings, self.target)
                        }
                else:
                    return {
                        "value": gather_object_property(export_settings, self.target)
                    }
            elif self.target:
                if self.target.name not in bpy.context.view_layer.objects:
                    raise Exception(f"Entity {self.target.name} does not exist")
                else:
                    return {
                        "value": gather_object_property(export_settings, self.target)
                    }
            else:
                if type(ob) is bpy.types.Scene:
                    raise Exception('Empty entity cannot be used for Scene objects in this context')
                else:
                    return {
                        "value": gather_object_property(export_settings, ob)
                    }


def get_choices(self, context):
    return [(choice.value, choice.text, "") for choice in self.choices]


class BGEnumSocketChoice(bpy.types.PropertyGroup):
    text: StringProperty()
    value: StringProperty()


class BGEnumSocket(NodeSocketStandard):
    bl_label = "String Choice"

    default_value: bpy.props.EnumProperty(
        name="",
        items=get_choices
    )

    choices: bpy.props.CollectionProperty(type=BGEnumSocketChoice)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (0.4, 0.7, 1.0, 1.0)


class BGHubsAnimationActionSocketInterface(NodeSocket):
    bl_idname = "BGHubsAnimationActionSocketInterface"
    bl_socket_idname = "BGHubsAnimationActionSocket"

    if bpy.app.version < (4, 0, 0):
        def draw(self, context, layout):
            pass
        def draw_color(self, context):
            return (0.2, 1.0, 0.2, 1.0)
    else:
        def draw(self, context, layout, node, text):
            pass

        def draw_color(self, context, node):
            return (0.2, 1.0, 1.0, 1.0)


class BGHubsAnimationActionSocket(NodeSocketStandard):
    bl_label = "Hubs AnimationAction"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (0.2, 1.0, 1.0, 1.0)


class BGHubsPlayerSocketInterface(NodeSocket):
    bl_idname = "BGHubsPlayerSocketInterface"
    bl_socket_idname = "BGHubsPlayerSocket"

    if bpy.app.version < (4, 0, 0):
        def draw(self, context, layout):
            pass
        def draw_color(self, context):
            return (0.2, 1.0, 0.2, 1.0)
    else:
        def draw(self, context, layout, node, text):
            pass
        def draw_color(self, context, node):
            return (1.00, 0.91, 0.34, 1.0)


class BGHubsPlayerSocket(NodeSocketStandard):
    bl_label = "Hubs Player"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1.00, 0.91, 0.34, 1.0)


class BGCustomEventSocketInterface(NodeSocketString):
    bl_idname = "BGCustomEventSocketInterface"
    bl_socket_idname = "BGCustomEventSocket"

    def draw(self, context, layout, node, text):
        pass
    def draw_color(self, context, node):
        return (0.2, 1.0, 0.2, 1.0)

class BGCustomEventSocket(NodeSocketString):
    bl_label = "Custom Event"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1.00, 0.91, 0.34, 1.0)