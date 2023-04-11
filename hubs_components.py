from bpy.props import BoolProperty, FloatProperty, EnumProperty, BoolVectorProperty, FloatVectorProperty
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

    mass: FloatProperty(
        name="Mass",
        description="Object's Mass",
        default=1)

    gravity: FloatVectorProperty(
        name="Gravity", description="Object's Gravity",
        unit="ACCELERATION",
        subtype="ACCELERATION",
        default=(0.0, -9.8, 0.0))

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

    def gather(self, export_settings, object):
        props = super().gather(export_settings, object)
        props['collisionMask'] = [value for i, (value, _label, _desc) in enumerate(collision_masks) if self.collisionMask[i]]
        props['gravity'] = [v for v in self.gravity] # prefer to store as an array for new components
        return props

    def draw(self, context, layout, panel):
        layout.prop(self, "type")
        layout.prop(self, "mass")
        layout.prop(self, "gravity")

        layout.prop(self, "disableCollision")
        layout.prop(self, "collisionGroup")
        if (self.disableCollision  and self.collisionGroup != "triggers") or (self.collisionGroup == "triggers" and not self.disableCollision):
            col = layout.column()
            # col.alert = True
            col.label(text="When making triggers you likely want 'Is Trigger' checked and collision group set to 'Triggers'", icon='INFO')

        layout.label(text="Collision Mask:")
        col = layout.column(align=True)
        for i, (_value, label, _desc) in enumerate(collision_masks):
            col.prop(self, "collisionMask", text=label, index=i, toggle=True)



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

def do_register(ComponentClass):
    register_component(ComponentClass)
    __components_registry[ComponentClass.get_name()] = ComponentClass

def do_unregister(ComponentClass):
    unregister_component(ComponentClass)
    __components_registry.pop(ComponentClass.get_name())

def register():
    do_register(Grabbable)
    do_register(RigidBody)
    do_register(PhysicsShape)

def unregister():
    do_unregister(Grabbable)
    do_unregister(RigidBody)
    do_unregister(PhysicsShape)
