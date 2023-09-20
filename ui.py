import bpy
from bpy.types import PropertyGroup, NodeTree
from bpy.props import PointerProperty, CollectionProperty, IntProperty, EnumProperty, StringProperty, FloatProperty, BoolProperty, FloatVectorProperty
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

        row = layout.row()
        row.label(text="Global Variables:")
        row = layout.row()
        row.template_list(BGGlobalVariablesList.bl_idname, "", context.object,
                          "bg_global_variables", context.object, "bg_active_global_variable_idx", rows=5)
        col = row.column(align=True)
        col.context_pointer_set('target', context.object)
        col.operator(BGGlobalVariableAdd.bl_idname, icon='ADD', text="")
        col.operator(BGGlobalVariableRemove.bl_idname, icon='REMOVE', text="")

        row = layout.row()
        row.label(text="Custom Events:")
        row = layout.row()
        row.template_list(BGCustomEventsList.bl_idname, "", context.object,
                          "bg_custom_events", context.object, "bg_active_custom_event_idx", rows=5)
        col = row.column(align=True)
        col.context_pointer_set('target', context.object)
        col.operator(BGCustomEventAdd.bl_idname, icon='ADD', text="")
        col.operator(BGCustomEventRemove.bl_idname, icon='REMOVE', text="")


GLOBAL_VARIABLES_TYPES = [
    ("boolean", "Boolean", "Boolean"),
    ("float", "Float", "Float"),
    ("integer", "Integer", "Integer"),
    ("string", "String", "String"),
    ("vec3", "Vector3", "Vector3"),
    ("animationAction", "Action", "Action"),
    ("entity", "Entity", "Entity"),
    ("color", "Color", "Color"),
]


def update_nodes(self, context):
    if hasattr(context.object, "bg_active_graph") and context.object.bg_active_graph != None:
        for node in context.object.bg_active_graph.nodes:
            if hasattr(node, "refresh") and callable(getattr(node, "refresh")):
                node.refresh()
    if hasattr(context.scene, "bg_active_graph") and context.scene.bg_active_graph != None:
        for node in context.scene.bg_active_graph.nodes:
            if hasattr(node, "refresh") and callable(getattr(node, "refresh")):
                node.refresh()


def update_graphs(self, context):
    if hasattr(context.object, "bg_active_graph") and context.object.bg_active_graph != None:
        context.object.bg_active_graph.update()
    if hasattr(context.scene, "bg_active_graph") and context.scene.bg_active_graph != None:
        context.scene.bg_active_graph.update()


class BGGlobalVariableType(PropertyGroup):
    name: StringProperty(
        name="Name",
        description="Name",
        update=update_nodes
    )

    type: EnumProperty(
        name="Type",
        description="Type",
        items=GLOBAL_VARIABLES_TYPES,
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

    defaultAnimationAction: StringProperty(
        name="default",
        description="Default Value",
        default=""
    )

    defaultColor: FloatVectorProperty(
        name="default",
        description="Default Value",
        subtype="COLOR_GAMMA",
        default=(1.0, 1.0, 1.0, 1.0),
        size=4,
        min=0,
        max=1
    )

    defaultEntity: PointerProperty(name="default", type=bpy.types.Object)


class BGGlobalVariableAdd(bpy.types.Operator):
    bl_idname = "ui.bg_add_global_variable"
    bl_label = "Add Global Variable"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target = context.target
        new_var = target.bg_global_variables.add()
        new_var.name = f"prop{len(target.bg_global_variables)}"
        new_var.type = "integer"

        update_nodes(self, context)

        return {'FINISHED'}


class BGGlobalVariableRemove(bpy.types.Operator):
    bl_idname = "ui.bg_remove_global_variable"
    bl_label = "Remove Global Variable"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target = context.target
        target.bg_global_variables.remove(target.bg_active_global_variable_idx)

        update_nodes(self, context)

        return {'FINISHED'}


class BGGlobalVariablesList(bpy.types.UIList):
    bl_idname = "BG_UL_GlobalVariables_list"
    bl_label = "Global Variables"

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
        elif item.type == "animationAction":
            split.prop(item, "defaultAnimationAction", text="", emboss=True, icon='NONE')
        elif item.type == "color":
            split.prop(item, "defaultColor", text="", emboss=True, icon='NONE')
        elif item.type == "entity":
            split.prop(item, "defaultEntity", text="", emboss=True, icon='NONE')


class BGCustomEventType(PropertyGroup):
    name: StringProperty(
        name="Name",
        description="Name",
        update=update_nodes
    )


class BGCustomEventAdd(bpy.types.Operator):
    bl_idname = "ui.bg_add_custom_event"
    bl_label = "Add Custom Event"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target = context.target
        new_event = target.bg_custom_events.add()
        new_event.name = f"prop{len(target.bg_custom_events)}"

        update_nodes(self, context)

        return {'FINISHED'}


class BGCustomEventRemove(bpy.types.Operator):
    bl_idname = "ui.bg_remove_custom_event"
    bl_label = "Remove Custom Event"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target = context.target
        target.bg_custom_events.remove(target.bg_active_custom_event_idx)

        update_nodes(self, context)

        return {'FINISHED'}


class BGCustomEventsList(bpy.types.UIList):
    bl_idname = "BG_UL_CustomEvents_list"
    bl_label = "Custom Events"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(align=True)
        split.prop(item, "name", text="", emboss=False, icon='NONE')


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

        row = layout.row()
        row.label(text="Global Variables:")
        row = layout.row()
        row.template_list(BGGlobalVariablesList.bl_idname, "", context.scene,
                          "bg_global_variables", context.scene, "bg_active_global_variable_idx", rows=5)
        col = row.column(align=True)
        col.context_pointer_set('target', context.scene)
        col.operator(BGGlobalVariableAdd.bl_idname, icon='ADD', text="")
        col.operator(BGGlobalVariableRemove.bl_idname, icon='REMOVE', text="")

        row = layout.row()
        row.label(text="Custom Events:")
        row = layout.row()
        row.template_list(BGCustomEventsList.bl_idname, "", context.scene,
                          "bg_custom_events", context.scene, "bg_active_custom_event_idx", rows=5)
        col = row.column(align=True)
        col.context_pointer_set('target', context.scene)
        col.operator(BGCustomEventAdd.bl_idname, icon='ADD', text="")
        col.operator(BGCustomEventRemove.bl_idname, icon='REMOVE', text="")


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
        new_slot.graph = self.bg_active_graph
        idx = indexForBGItem(self.bg_slots, self.bg_active_graph)
        self.bg_active_slot_idx = idx


class BGItem(PropertyGroup):
    graph: PointerProperty(type=NodeTree)


def register():
    bpy.utils.register_class(BGNew)
    bpy.utils.register_class(BGRemove)
    bpy.utils.register_class(BGAddSlot)
    bpy.utils.register_class(BGNodeTreeList)
    bpy.utils.register_class(BGObjectPanel)
    bpy.utils.register_class(BGScenePanel)
    bpy.utils.register_class(BGGlobalVariableType)
    bpy.utils.register_class(BGGlobalVariableAdd)
    bpy.utils.register_class(BGGlobalVariableRemove)
    bpy.utils.register_class(BGGlobalVariablesList)
    bpy.utils.register_class(BGCustomEventType)
    bpy.utils.register_class(BGCustomEventAdd)
    bpy.utils.register_class(BGCustomEventRemove)
    bpy.utils.register_class(BGCustomEventsList)

    bpy.utils.register_class(BGItem)
    bpy.types.Object.bg_slots = CollectionProperty(type=BGItem)
    bpy.types.Object.bg_active_graph = PointerProperty(type=NodeTree, update=bg_active_slot_update)
    bpy.types.Object.bg_active_slot_idx = IntProperty(
        name="Active BG index",
        description="Active BG index",
        update=bg_active_slot_idx_update,
        default=-1)
    bpy.types.Object.bg_global_variables = CollectionProperty(type=BGGlobalVariableType)
    bpy.types.Object.bg_active_global_variable_idx = IntProperty(
        name="Active Global Object Variable index",
        description="Active Global Object Variable index",
        default=-1)
    bpy.types.Object.bg_custom_events = CollectionProperty(type=BGCustomEventType)
    bpy.types.Object.bg_active_custom_event_idx = IntProperty(
        name="Active Custom Event index",
        description="Active Custom Event index",
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
    bpy.types.Scene.bg_global_variables = CollectionProperty(type=BGGlobalVariableType)
    bpy.types.Scene.bg_active_global_variable_idx = IntProperty(
        name="Active Global Variable index",
        description="Active Global Variable index",
        default=-1)
    bpy.types.Scene.bg_custom_events = CollectionProperty(type=BGCustomEventType)
    bpy.types.Scene.bg_active_custom_event_idx = IntProperty(
        name="Active Custom Event index",
        description="Active Custom Event index",
        default=-1)

    bpy.types.NODE_HT_header.draw = draw_header


def unregister():
    bpy.utils.unregister_class(BGNew)
    bpy.utils.unregister_class(BGRemove)
    bpy.utils.unregister_class(BGAddSlot)
    bpy.utils.unregister_class(BGObjectPanel)
    bpy.utils.unregister_class(BGScenePanel)
    bpy.utils.unregister_class(BGNodeTreeList)
    bpy.utils.unregister_class(BGGlobalVariableType)
    bpy.utils.unregister_class(BGGlobalVariableAdd)
    bpy.utils.unregister_class(BGGlobalVariableRemove)
    bpy.utils.unregister_class(BGGlobalVariablesList)
    bpy.utils.unregister_class(BGCustomEventType)
    bpy.utils.unregister_class(BGCustomEventAdd)
    bpy.utils.unregister_class(BGCustomEventRemove)
    bpy.utils.unregister_class(BGCustomEventsList)

    del bpy.types.Object.bg_slots
    del bpy.types.Object.bg_active_graph
    del bpy.types.Object.bg_active_slot_idx
    del bpy.types.Object.bg_global_variables
    del bpy.types.Object.bg_active_global_variable_idx
    del bpy.types.Scene.bg_slots
    del bpy.types.Scene.bg_active_graph
    del bpy.types.Scene.bg_active_slot_idx
    del bpy.types.Scene.bg_node_type
    del bpy.types.Scene.bg_global_variables
    del bpy.types.Scene.bg_active_global_variable_idx
    del bpy.types.Scene.bg_custom_events
    del bpy.types.Scene.bg_active_custom_event_idx
    bpy.utils.unregister_class(BGItem)

    bpy.types.NODE_HT_header.draw = original_NODE_HT_header_draw
