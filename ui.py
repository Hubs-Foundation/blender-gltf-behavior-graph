import bpy
from bpy.types import PropertyGroup, NodeTree
from bpy.props import PointerProperty, CollectionProperty, IntProperty, EnumProperty, StringProperty
import uuid
from bpy.app.handlers import persistent

original_NODE_HT_header_draw = bpy.types.NODE_HT_header.draw


def draw_header(self, context):
    layout = self.layout
    snode = context.space_data

    if snode.tree_type == 'BGTree':
        layout.template_header()

        bpy.types.NODE_MT_editor_menus.draw_collapsible(context, layout)
        layout.separator_spacer()

        if context.scene.bg_node_type == 'OBJECT':
            target = context.active_object
        else:
            target = context.scene

        layout.prop(context.scene, "bg_node_type", text="")

        if target:
            row = layout.row()
            row.context_pointer_set("target", target)
            row.template_ID(target, "bg_active_graph", new=BGNew.bl_idname, unlink=BGRemove.bl_idname)

        layout.separator_spacer()

        overlay = snode.overlay
        tool_settings = context.tool_settings

        # Snap
        row = layout.row(align=True)
        row.prop(tool_settings, "use_snap_node", text="")
        row.prop(tool_settings, "snap_node_element", icon_only=True)
        if tool_settings.snap_node_element != 'GRID':
            row.prop(tool_settings, "snap_target", text="")

        # Overlay toggle & popover
        row = layout.row(align=True)
        row.prop(overlay, "show_overlays", icon='OVERLAY', text="")
        sub = row.row(align=True)
        sub.active = overlay.show_overlays
        sub.popover(panel="NODE_PT_overlay", text="")

        new_graph = None
        if target and target.bg_active_graph:
            new_graph = target.bg_active_graph
        else:
            new_graph = None

        if snode.node_tree != new_graph:
            snode.node_tree = new_graph

    else:
        original_NODE_HT_header_draw(self, context)


class BGNew(bpy.types.Operator):
    bl_idname = "ui.bg_new"
    bl_label = "New Behavior Graph"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        graph = bpy.data.node_groups.new("Behavior Graph", "BGTree")
        if graph:
            target = context.target
            target.bg_active_graph = graph
            return {'FINISHED'}

        return {'CANCELLED'}


class BGRemove(bpy.types.Operator):
    bl_idname = "ui.bg_remove"
    bl_label = "Remove Behavior Graph"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if hasattr(context, "target"):
            target = context.target
            return target.bg_active_slot_idx >= 0
        return False

    def execute(self, context):
        target = context.target
        target.bg_slots.remove(target.bg_active_slot_idx)
        target.bg_active_slot_idx = len(target.bg_slots) - 1
        if target.bg_active_slot_idx != -1:
            target.bg_active_graph = target.bg_slots[target.bg_active_slot_idx].graph
        else:
            target.bg_active_graph = None

        return {'FINISHED'}


class BGNodeTreeList(bpy.types.UIList):
    bl_idname = "BG_UL_NodeTree_list"
    bl_label = "Behavior Graphs"

    empty: StringProperty()

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.90, align=False)
        if item.graph != None:
            split.prop(item.graph, "name", text="", emboss=False, icon='NODETREE')
        else:
            split.prop(self, "empty", text="", emboss=False, icon='NODETREE')


class BGAddSlot(bpy.types.Operator):
    bl_idname = "ui.bg_add_slot"
    bl_label = "Add Behavior Graph Slot"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target = context.target
        new_slot = target.bg_slots.add()
        new_slot.name = str(uuid.uuid1())
        target.bg_active_slot_idx = len(target.bg_slots) - 1

        return {'FINISHED'}


class BGObjectPanel(bpy.types.Panel):
    bl_label = "Behavior Graphs"
    bl_idname = "OBJECT_PT_BG"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.template_list(BGNodeTreeList.bl_idname, "", context.object,
                          "bg_slots", context.object, "bg_active_slot_idx", rows=5)
        col = row.column(align=True)
        col.context_pointer_set('target', context.object)
        col.operator(BGAddSlot.bl_idname, icon='ADD', text="")
        col.operator(BGRemove.bl_idname, icon='REMOVE', text="")
        row = layout.row()
        row.context_pointer_set("target", context.object)
        row.template_ID(context.object, "bg_active_graph", new=BGNew.bl_idname, unlink=BGRemove.bl_idname)


class BGScenePanel(bpy.types.Panel):
    bl_label = 'Behavior Graphs'
    bl_idname = "SCENE_PT_BG"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.template_list(BGNodeTreeList.bl_idname, "", context.scene,
                          "bg_slots", context.scene, "bg_active_slot_idx", rows=5)
        col = row.column(align=True)
        col.context_pointer_set('target', context.scene)
        col.operator(BGAddSlot.bl_idname, icon='ADD', text="")
        col.operator(BGRemove.bl_idname, icon='REMOVE', text="")
        row = layout.row()
        row.context_pointer_set("target", context.scene)
        row.template_ID(context.scene, "bg_active_graph", new=BGNew.bl_idname, unlink=BGRemove.bl_idname)


def indexForBGItem(slots, graph):
    slot = next(slot for slot in slots if slot.graph.name == graph.name)
    if slot:
        return list(slots).index(slot)
    return -1


def bg_active_slot_idx_update(self, context):
    if self.bg_active_slot_idx != -1:
        slot = self.bg_slots[self.bg_active_slot_idx]
        if slot and self.bg_active_graph != slot.graph:
            self.bg_active_graph = slot.graph
    else:
        self.bg_active_graph = None


def bg_active_slot_update(self, context):
    if self.bg_active_slot_idx != -1:
        slot = self.bg_slots[self.bg_active_slot_idx]
        if slot:
            self.bg_slots[self.bg_active_slot_idx].graph = self.bg_active_graph
    elif self.bg_active_graph:
        new_slot = self.bg_slots.add()
        new_slot.name = str(uuid.uuid1())
        new_slot.graph = self.bg_active_graph
        idx = indexForBGItem(self.bg_slots, self.bg_active_graph)
        self.bg_active_slot_idx = idx


class BGItem(PropertyGroup):
    graph: PointerProperty(type=NodeTree)


@persistent
def load_post(dummy):
    for scene in bpy.data.scenes:
        for slot in scene.bg_slots:
            slot.name = str(uuid.uuid1())
    for object in bpy.data.objects:
        for slot in object.bg_slots:
            slot.name = str(uuid.uuid1())


def register():
    bpy.utils.register_class(BGNew)
    bpy.utils.register_class(BGRemove)
    bpy.utils.register_class(BGAddSlot)
    bpy.utils.register_class(BGNodeTreeList)
    bpy.utils.register_class(BGObjectPanel)
    bpy.utils.register_class(BGScenePanel)

    bpy.utils.register_class(BGItem)
    bpy.types.Object.bg_slots = CollectionProperty(type=BGItem)
    bpy.types.Object.bg_active_graph = PointerProperty(type=NodeTree, update=bg_active_slot_update)
    bpy.types.Object.bg_active_slot_idx = IntProperty(
        name="Active BG index",
        description="Active BG index",
        update=bg_active_slot_idx_update,
        default=-1)
    bpy.types.Scene.bg_slots = CollectionProperty(type=BGItem)
    bpy.types.Scene.bg_active_graph = PointerProperty(type=NodeTree, update=bg_active_slot_update)
    bpy.types.Scene.bg_active_slot_idx = IntProperty(
        name="Active BG index",
        description="Active BG index",
        update=bg_active_slot_idx_update,
        default=-1)
    bpy.types.Scene.bg_node_type = EnumProperty(
        name="Node Type", description="Node Type",
        items=[("OBJECT", "Object", "Object"),
               ("SCENE", "Scene", "Scene")],
        default="SCENE")

    bpy.types.NODE_HT_header.draw = draw_header

    if load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_post)


def unregister():
    bpy.utils.unregister_class(BGNew)
    bpy.utils.unregister_class(BGRemove)
    bpy.utils.unregister_class(BGAddSlot)
    bpy.utils.unregister_class(BGObjectPanel)
    bpy.utils.unregister_class(BGScenePanel)
    bpy.utils.unregister_class(BGNodeTreeList)

    del bpy.types.Object.bg_slots
    del bpy.types.Object.bg_active_graph
    del bpy.types.Object.bg_active_slot_idx
    del bpy.types.Scene.bg_slots
    del bpy.types.Scene.bg_active_graph
    del bpy.types.Scene.bg_active_slot_idx
    del bpy.types.Scene.bg_node_type
    bpy.utils.unregister_class(BGItem)

    bpy.types.NODE_HT_header.draw = original_NODE_HT_header_draw

    if load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post)
