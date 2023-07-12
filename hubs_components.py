import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty, BoolVectorProperty, FloatVectorProperty, CollectionProperty, StringProperty, IntProperty
from io_hubs_addon.components.hubs_component import HubsComponent
from io_hubs_addon.components.types import Category, NodeType, PanelType
from io_hubs_addon.components.components_registry import register_component, unregister_component, __components_registry

class Grabbable(HubsComponent):
    _definition = {
        'name': 'grabbable',
        'display_name': 'BG Grabbable',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'VIEW_PAN',
        'deps': ['rigidbody'],
        'version': (1, 0, 0)
    }

    cursor: BoolProperty(
        name="By Curosr", description="Can be grabbed by a cursor", default=True)

    hand: BoolProperty(
        name="By Hand", description="Can be grabbed by VR hands", default=True)

collision_masks = [
    ("objects", "Objects", "Interactive objects"),
    ("triggers", "Triggers", "Trigger Colliders"),
    ("environment", "Environment", "Environment geometry"),
    ("avatars", "Avatars", "Player Avatars")
]

class RigidBody(HubsComponent):
    _definition = {
        'name': 'rigidbody',
        'display_name': 'BG RigidBody',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'PHYSICS',
        'deps': ['physics-shape'],
        'version': (1, 0, 0)
    }

    type: EnumProperty(
        name="type",
        description="RigidBody Type",
        items=[("static", "Static", "Will not ever move."),
               ("dynamic", "Dynamic", "Effected by physics and gravity"),
               ("kinematic", "Kinematic", "Not effected by gravity or collisions, but can be moved.")],
        default="dynamic")


    disableCollision: BoolProperty(
        name="Is Trigger",
        description="Disable collision response, act as a trigger only",
        default=False)

    collisionGroup: EnumProperty(
        name="Collision Group",
        description="What collision group this object belongs to. This effects what objects will collide with it.",
        items=[g for g in collision_masks if g[0] != "avatars"],
        default="objects")

    collisionMask: BoolVectorProperty(
        name="Collision Mask",
        description="What collision groups this object will collide with. Note: the other object must also be set to collide with this object's group.",
        size=4,
        subtype='LAYER',
        options={'ANIMATABLE'},
        default=[value in ["objects", "triggers", "environment"] for (value, _label, _desc) in collision_masks])

    mass: FloatProperty(
        name="Mass",
        description="Object's Mass",
        default=1)

    linearDamping: FloatProperty(
        name="Linear Damping",
        description="Amount of linear damping",
        default=0,
        min=0.0,
        soft_max=1.0,
    )

    angularDamping: FloatProperty(
        name="Angular Damping",
        description="Amount of angular damping",
        default=0,
        min=0.0,
        soft_max=1.0,
    )

    linearSleepingThreshold: FloatProperty(
        name="Linear Sleeping Threshold",
        description="Linear velocity threshold below which the object starts to sleep",
        default=0.8,
        min=0.0,
        soft_max=10.0,
    )

    angularSleepingThreshold: FloatProperty(
        name="Angular Sleeping Threshold",
        description="Angular velocity threshold below which the object starts to sleep",
        default=1.0,
        min=0.0,
        soft_max=10.0,
    )

    angularFactor: FloatVectorProperty(
        name="Angular Factor",
        description="Influence of the object's rotation along the X, Y, and Z axes",
        size=3,
        subtype="XYZ",
        default=(1.0, 1.0, 1.0),
        min=0.0,
        soft_max=10.0,
    )

    gravity: FloatVectorProperty(
        name="Gravity", description="Object's Gravity",
        unit="ACCELERATION",
        subtype="ACCELERATION",
        default=(0.0, -9.8, 0.0))

    def gather(self, export_settings, object):
        props = super().gather(export_settings, object)
        props['collisionMask'] = [value for i, (value, _label, _desc) in enumerate(collision_masks) if self.collisionMask[i]]
        # prefer to store as an array for new components
        props['gravity'] = [v for v in self.gravity]
        props['angularFactor'] = [v for v in self.angularFactor]
        return props

    def draw(self, context, layout, panel):
        layout.prop(self, "type")

        if (self.disableCollision  and self.collisionGroup != "triggers") or (self.collisionGroup == "triggers" and not self.disableCollision):
            col = layout.column()
            # col.alert = True
            col.label(text="When making triggers you likely want 'Is Trigger' checked and collision group set to 'Triggers'", icon='INFO')
        layout.prop(self, "collisionGroup")
        layout.label(text="Collision Mask:")
        col = layout.column(align=True)
        for i, (_value, label, _desc) in enumerate(collision_masks):
            col.prop(self, "collisionMask", text=label, index=i, toggle=True)
        layout.prop(self, "disableCollision")

        layout.prop(self, "mass")
        layout.prop(self, "linearDamping")
        layout.prop(self, "angularDamping")
        layout.prop(self, "linearSleepingThreshold")
        layout.prop(self, "angularSleepingThreshold")
        layout.prop(self, "angularFactor")
        layout.prop(self, "gravity")



class PhysicsShape(HubsComponent):
    _definition = {
        'name': 'physics-shape',
        'display_name': 'BG Physics Shape',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'SCENE_DATA',
        'version': (1, 0, 0)
    }

    type: EnumProperty(
        name="Type", description="Type",
        items=[("box", "Box Collider", "A box-shaped primitive collision shape"),
               ("sphere", "Sphere Collider", "A primitive collision shape which represents a sphere"),
               ("hull", "Convex Hull",
                "A convex hull wrapped around the object's vertices. A good analogy for a convex hull is an elastic membrane or balloon under pressure which is placed around a given set of vertices. When released the membrane will assume the shape of the convex hull"),
               ("mesh", "Mesh Collider",
                "A shape made of the actual vertices of the object. This can be expensive for large meshes")],
        default="hull")

    fit: EnumProperty(
        name="Fit Mode",
        description="Shape fitting mode",
        items=[("all", "Automatic fit all", "Automatically match the shape to fit the object's vertices"),
               ("manual", "Manual", "Use the manually specified dimensions to define the shape, ignoring the object's vertices")],
        default="all")

    halfExtents: FloatVectorProperty(
        name="Half Extents",
        description="Half dimensions of the collider. (Only used when fit is set to \"manual\" and type is set to \"box\")",
        unit='LENGTH',
        subtype="XYZ",
        default=(0.5, 0.5, 0.5))

    minHalfExtent: FloatProperty(
        name="Min Half Extent",
        description="The minimum size to use when automatically generating half extents. (Only used when fit is set to \"all\" and type is set to \"box\")",
        unit="LENGTH",
        default=0.0)

    maxHalfExtent: FloatProperty(
        name="Max Half Extent",
        description="The maximum size to use when automatically generating half extents. (Only used when fit is set to \"all\" and type is set to \"box\")",
        unit="LENGTH",
        default=1000.0)

    sphereRadius: FloatProperty(
        name="Sphere Radius",
        description="Radius of the sphere collider. (Only used when fit is set to \"manual\" and type is set to \"sphere\")",
        unit="LENGTH", default=0.5)

    offset: FloatVectorProperty(
        name="Offset", description="An offset to apply to the collider relative to the object's origin",
        unit='LENGTH',
        subtype="XYZ",
        default=(0.0, 0.0, 0.0))

    includeInvisible: BoolProperty(
        name="Include Invisible",
        description="Include invisible objects when generating a collider. (Only used if \"fit\" is set to \"all\")",
        default=False)

    def draw(self, context, layout, panel):
        layout.prop(self, "type")
        layout.prop(self, "fit")
        if self.fit == "manual":
            if self.type == "box":
                layout.prop(self, "halfExtents")
            elif self.type == "sphere":
                layout.prop(self, "sphereRadius")
        else:
            if self.type == "box":
                layout.prop(self, "minHalfExtent")
                layout.prop(self, "maxHalfExtent")
            layout.prop(self, "includeInvisible")
        layout.prop(self, "offset")

        if self.fit == "manual" and (self.type == "mesh" or self.type == "hull"):
            col = layout.column()
            col.alert = True
            col.label(text="'Hull' and 'Mesh' do not support 'manual' fit mode", icon='ERROR')

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
    if context.object.type == 'ARMATURE' and (context.mode == 'EDIT_ARMATURE' or context.mode == 'POSE'):
        return context.active_bone
    else:
        return context.object

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
        'display_name': 'BG Custom Tags',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'COPY_ID',
        'version': (1, 0, 0)
    }

    tags: CollectionProperty(type=CustomTagItem)
    active_tag_index: IntProperty(name="Active Tag Index", default=0)

    def draw(self, context, layout, panel):
        layout.template_list("CUSTOM_TAGS_UL_tags_list", "", self, "tags", self, "active_tag_index")
        row = layout.row(align=True)
        row.operator("custom_tags.tag_add", text="", icon="ADD")
        row.operator("custom_tags.tag_remove", text="", icon="REMOVE")

    def gather(self, export_settings, object):
        return {
            "tags": [tag.tag for tag in self.tags]
        }

def do_register(ComponentClass):
    register_component(ComponentClass)
    __components_registry[ComponentClass.get_name()] = ComponentClass

def register():
    do_register(Grabbable)
    do_register(RigidBody)
    do_register(PhysicsShape)

    bpy.utils.register_class(CustomTagItem)
    bpy.utils.register_class(CUSTOM_TAGS_UL_tags_list)
    bpy.utils.register_class(CUSTOM_TAGS_OT_add_tag)
    bpy.utils.register_class(CUSTOM_TAGS_OT_remove_tag)
    do_register(CustomTags)


def unregister():
    # No need to unregister the Hubs components here, the registry will handle that.
    bpy.utils.unregister_class(CustomTagItem)
    bpy.utils.unregister_class(CUSTOM_TAGS_UL_tags_list)
    bpy.utils.unregister_class(CUSTOM_TAGS_OT_add_tag)
    bpy.utils.unregister_class(CUSTOM_TAGS_OT_remove_tag)
