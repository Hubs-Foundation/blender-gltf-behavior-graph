import bpy
from bpy.props import StringProperty, PointerProperty
from bpy.types import NodeSocketStandard, NodeSocketInterface, NodeSocketString, NodeSocketInterfaceString
from .utils import gather_object_property, filter_on_components, filter_entity_type, ExportException


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


class BGHubsEntitySocketInterface(NodeSocketInterface):
    bl_idname = "BGHubsEntitySocketInterface"
    bl_socket_idname = "BGHubsEntitySocket"

    def draw(self, context, layout):
        pass

    def draw_color(self, context):
        return (0.2, 1.0, 0.2, 1.0)


class BGHubsEntitySocket(NodeSocketStandard):
    bl_label = "Hubs Entity"

    target: PointerProperty(
        name="Target",
        type=bpy.types.Object,
        poll=filter_on_components
    )

    entity_type: bpy.props.EnumProperty(
        name="",
        description="Target Entity",
        items=filter_entity_type,
        options={'HIDDEN'},
        default=0
    )

    poll_components: bpy.props.StringProperty(
        name="Component",
        description="Component",
        options={'HIDDEN'},
        default=""
    )

    custom_type: bpy.props.EnumProperty(
        name="",
        description="Target Entity",
        items=[("default", "Default", "Default"), ("event_variable", "Event/Variable", "Event/Variable")],
        options={'HIDDEN'},
        default=0
    )

    export: bpy.props.BoolProperty(default=True)

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            col = layout.column()
            col.prop(self, "entity_type")
            if not hasattr(self, "custom_type") or self.custom_type == "default":
                if self.entity_type != "self":
                    col.prop(self, "target", text=text)
            elif self.custom_type == "event_variable":
                if self.entity_type == "other":
                    col.prop(self, "target", text=text)

    def draw_color(self, context, node):
        return (0.2, 1.0, 0.2, 1.0)

    def gather_parameters(self, ob, export_settings):
        if not hasattr(self, "custom_type") or self.custom_type == "default":
            if not self.target:
                if type(ob) == bpy.types.Scene:
                    raise ExportException('Empty entity cannot be used for Scene objects in this context')
                else:
                    return {
                        "value": gather_object_property(export_settings, ob)
                    }
            else:
                return {
                    "value": gather_object_property(export_settings, self.target)
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


class BGHubsAnimationActionSocketInterface(NodeSocketInterface):
    bl_idname = "BGHubsAnimationActionSocketInterface"
    bl_socket_idname = "BGHubsAnimationActionSocket"

    def draw(self, context, layout):
        pass

    def draw_color(self, context):
        return (0.2, 1.0, 1.0, 1.0)


class BGHubsAnimationActionSocket(NodeSocketStandard):
    bl_label = "Hubs AnimationAction"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (0.2, 1.0, 1.0, 1.0)


class BGHubsPlayerSocketInterface(NodeSocketInterface):
    bl_idname = "BGHubsPlayerSocketInterface"
    bl_socket_idname = "BGHubsPlayerSocket"

    def draw(self, context, layout):
        pass

    def draw_color(self, context):
        return (1.00, 0.91, 0.34, 1.0)


class BGHubsPlayerSocket(NodeSocketStandard):
    bl_label = "Hubs Player"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1.00, 0.91, 0.34, 1.0)


class BGCustomEventSocketInterface(NodeSocketInterfaceString):
    bl_idname = "BGCustomEventSocketInterface"
    bl_socket_idname = "BGCustomEventSocket"

    def draw(self, context, layout):
        pass

    def draw_color(self, context):
        return (1.00, 0.91, 0.34, 1.0)


class BGCustomEventSocket(NodeSocketString):
    bl_label = "Custom Event"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1.00, 0.91, 0.34, 1.0)
