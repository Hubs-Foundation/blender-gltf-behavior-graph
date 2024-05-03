import bpy
from bpy.props import CollectionProperty, StringProperty, IntProperty
from io_hubs_addon.components.hubs_component import HubsComponent
from io_hubs_addon.components.types import Category, NodeType, PanelType
from ..utils import do_register, do_unregister


class CustomTagItem(bpy.types.PropertyGroup):
    def _set_unique_tag(self, context):
        tags = self.id_data.hubs_component_custom_tags.tags
        for tag in tags:
            if tag != self and tag.tag == self.tag:
                self.tag = f"{self.tag}_1"
                return

    tag: StringProperty(name="tag", update=_set_unique_tag)


class CUSTOM_TAGS_UL_tags_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "tag", text="", emboss=False, icon_value=icon)


def get_host(context):
    if context.active_object.type == 'ARMATURE' and (context.mode == 'EDIT_ARMATURE' or context.mode == 'POSE'):
        return context.active_bone
    else:
        return context.active_object


class CUSTOM_TAGS_OT_add_tag(bpy.types.Operator):
    bl_idname = "custom_tags.tag_add"
    bl_label = "Add Custom Tag"
    bl_description = "Add a new unique custom tag"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        host = get_host(context)
        tags = host.hubs_component_custom_tags.tags

        new_tag = tags.add()
        new_tag.tag = "New Tag"

        return {'FINISHED'}


class CUSTOM_TAGS_OT_remove_tag(bpy.types.Operator):
    bl_idname = "custom_tags.tag_remove"
    bl_label = "Remove Custom Tag"
    bl_description = "Remove the selected custom tag"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        host = get_host(context)
        tags = host.hubs_component_custom_tags.tags
        index = host.hubs_component_custom_tags.active_tag_index

        if 0 <= index < len(tags):
            tags.remove(index)
        else:
            self.report({'INFO'}, "No tag to remove.")
            return {'CANCELLED'}

        return {'FINISHED'}


class CustomTags(HubsComponent):
    _definition = {
        'name': 'custom-tags',
        'display_name': 'Custom Tags',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'COPY_ID',
        'version': (1, 0, 0)
    }

    tags: CollectionProperty(type=CustomTagItem)
    active_tag_index: IntProperty(name="Active Tag Index", default=0)

    def draw(self, context, layout, panel):
        layout.template_list("CUSTOM_TAGS_UL_tags_list",
                             "", self, "tags", self, "active_tag_index")
        row = layout.row(align=True)
        row.operator("custom_tags.tag_add", text="", icon="ADD")
        row.operator("custom_tags.tag_remove", text="", icon="REMOVE")

    def gather(self, export_settings, object):
        return {
            "tags": [tag.tag for tag in self.tags]
        }


def register():
    bpy.utils.register_class(CustomTagItem)
    bpy.utils.register_class(CUSTOM_TAGS_UL_tags_list)
    bpy.utils.register_class(CUSTOM_TAGS_OT_add_tag)
    bpy.utils.register_class(CUSTOM_TAGS_OT_remove_tag)
    do_register(CustomTags)


def unregister():
    bpy.utils.unregister_class(CustomTagItem)
    bpy.utils.unregister_class(CUSTOM_TAGS_UL_tags_list)
    bpy.utils.unregister_class(CUSTOM_TAGS_OT_add_tag)
    bpy.utils.unregister_class(CUSTOM_TAGS_OT_remove_tag)
    do_unregister(CustomTags)
