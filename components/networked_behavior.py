import bpy
from bpy.types import PropertyGroup
from bpy.props import EnumProperty, CollectionProperty, StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty
from io_hubs_addon.components.hubs_component import HubsComponent
from io_hubs_addon.components.types import NodeType, PanelType
from io_hubs_addon.io.utils import gather_vec_property
from ..utils import do_register, do_unregister, gather_object_property, update_nodes

NETWORKED_TYPES = [
    ("boolean", "Boolean", "Boolean"),
    ("float", "Float", "Float"),
    ("integer", "Integer", "Integer"),
    ("string", "String", "String"),
    ("vec3", "Vector3", "Vector3")
]


class NetworkedPropertyType(PropertyGroup):
    name: StringProperty(
        name="Name",
        description="Name",
        update=update_nodes
    )

    type: EnumProperty(
        name="Type",
        description="Type",
        items=NETWORKED_TYPES,
        update=update_nodes,
        default="integer"
    )

    defaultInt: IntProperty(
        name="default",
        description="Default Value",
        default=0
    )

    defaultFloat: FloatProperty(
        name="default",
        description="Default Value",
        default=0.0
    )

    defaultString: StringProperty(
        name="default",
        description="Default Value",
        default=""
    )

    defaultBoolean: BoolProperty(
        name="default",
        description="Default Value",
        default=False
    )

    defaultVec3: FloatVectorProperty(
        name="default",
        description="Default Value",
        subtype="XYZ",
        default=(0.0, 0.0, 0.0)
    )


class NetworkedBehaviorAddProp(bpy.types.Operator):
    bl_idname = "ui.bg_add_networked_behavior_prop"
    bl_label = "Add Networked Property"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        hubs_component = context.hubs_component
        new_prop = hubs_component.props_list.add()
        new_prop.name = f"prop{len(hubs_component.props_list)}"
        new_prop.type = "integer"

        return {'FINISHED'}


class NetworkedBehaviorRemoveProp(bpy.types.Operator):
    bl_idname = "ui.bg_remove_networked_behavior_prop"
    bl_label = "Remove Networked Property"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        hubs_component = context.hubs_component
        hubs_component.props_list.remove(hubs_component.active_prop_idx)

        return {'FINISHED'}


class NetworkedBehaviorPropList(bpy.types.UIList):
    bl_idname = "BG_UL_NetworkedBehavior_props_list"
    bl_label = "Networked Properties"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(align=True)
        split.prop(item, "name", text="", emboss=False, icon='NONE')
        split.prop(item, "type", text="", emboss=False, icon='NONE')
        if item.type == "integer":
            split.prop(item, "defaultInt", text="", emboss=True, slider=False, icon='NONE')
        elif item.type == "boolean":
            split.prop(item, "defaultBoolean", text="", toggle=True, emboss=True, icon='NONE')
        elif item.type == "float":
            split.prop(item, "defaultFloat", text="", emboss=True, slider=False, icon='NONE')
        elif item.type == "string":
            split.prop(item, "defaultString", text="", emboss=True, icon='NONE')
        elif item.type == "vec3":
            split.prop(item, "defaultVec3", text="", emboss=True, icon='NONE')


def get_value(prop, export_settings):
    value = None
    if prop.type == "integer":
        value = prop.defaultInt
    elif prop.type == "boolean":
        value = prop.defaultBoolean
    elif prop.type == "float":
        value = prop.defaultFloat
    elif prop.type == "string":
        value = prop.defaultString
    elif prop.type == "vec3":
        value = gather_vec_property(export_settings, prop, prop, "defaultVec3")
        if export_settings['gltf_yup']:
            copy = value.copy()
            value["y"] = copy["z"]
            value["z"] = copy["y"]
    elif prop.type == "entity":
        value = gather_object_property(export_settings, prop.defaultEntity)
    elif prop.type == "animationAction":
        value = prop.defaultAnimationAction

    return value


class NetworkedBehavior(HubsComponent):
    _definition = {
        'name': 'networked-behavior',
        'display_name': 'Networked Behavior',
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'NODETREE',
        'deps': ['networked'],
        'version': (1, 0, 0)
    }

    props_list: CollectionProperty(
        type=NetworkedPropertyType,
        options={"HIDDEN"}
    )

    active_prop_idx: IntProperty(
        name="Active property index",
        description="Active property index",
        default=-1,
        options={"HIDDEN"}
    )

    def draw(self, context, layout, panel):
        row = layout.row()
        row.label(text="Networked Properties:")
        row = layout.row()
        row.context_pointer_set('panel', panel)
        row.template_list(NetworkedBehaviorPropList.bl_idname, "", self,
                          "props_list", self, "active_prop_idx", rows=5)
        col = row.column(align=True)
        col.context_pointer_set('hubs_component', self)
        col.operator(NetworkedBehaviorAddProp.bl_idname, icon='ADD', text="")
        col.operator(NetworkedBehaviorRemoveProp.bl_idname, icon='REMOVE', text="")

    def gather(self, export_settings, object):
        variables = {}
        for prop in self.props_list:
            variables[prop.name] = {
                "type": prop.type,
                "value": get_value(prop, export_settings)
            }

        return variables


def register():
    bpy.utils.register_class(NetworkedPropertyType)
    bpy.utils.register_class(NetworkedBehaviorPropList)
    bpy.utils.register_class(NetworkedBehaviorAddProp)
    bpy.utils.register_class(NetworkedBehaviorRemoveProp)
    do_register(NetworkedBehavior)


def unregister():
    do_unregister(NetworkedBehavior)
    bpy.utils.unregister_class(NetworkedBehaviorRemoveProp)
    bpy.utils.unregister_class(NetworkedBehaviorAddProp)
    bpy.utils.unregister_class(NetworkedBehaviorPropList)
    bpy.utils.unregister_class(NetworkedPropertyType)
