import bpy
from bpy.types import PropertyGroup
from bpy.props import EnumProperty, CollectionProperty, StringProperty, IntProperty
from io_hubs_addon.components.hubs_component import HubsComponent
from io_hubs_addon.components.types import Category, NodeType, PanelType
from ..utils import do_register, do_unregister

NETWORKED_TYPES = [
    ("boolean", "Boolean", "Boolean"),
    ("float", "Float", "Float"),
    ("int", "Integer", "Integer"),
    ("string", "String", "String"),
    ("vec3", "Vector3", "Vector3")
]


def update_ui(self, context):
    if hasattr(context.object, "bg_active_graph"):
        context.object.bg_active_graph.update()


class NetworkedPropertyType(PropertyGroup):
    name: StringProperty(
        name="Name",
        description="Name",
        update=update_ui
    )

    type: EnumProperty(
        name="Type",
        description="Type",
        items=NETWORKED_TYPES,
        update=update_ui,
        default="int"
    )


class NetworkedBehaviorAddProp(bpy.types.Operator):
    bl_idname = "ui.bg_add_networked_behavior_prop"
    bl_label = "Add Networked Property"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        hubs_component = context.hubs_component
        new_prop = hubs_component.props_list.add()
        new_prop.name = f"prop{len(hubs_component.props_list)   }"
        new_prop.type = "int"

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


class NetworkedBehavior(HubsComponent):
    _definition = {
        'name': 'networked-behavior',
        'display_name': 'BG Networked Behavior',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'NODETREE',
        'version': (1, 0, 0),
        'deps': ['networked']
    }

    props_list: CollectionProperty(
        type=NetworkedPropertyType)

    active_prop_idx: IntProperty(
        name="Active property index",
        description="Active property index",
        default=-1
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
