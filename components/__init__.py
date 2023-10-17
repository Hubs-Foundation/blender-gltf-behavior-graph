from . import custom_tags, grabbable, rigid_body, physics_shape, networked_behavior, networked_transform, networked_animation, capturable, networked_material, networked_object_material, networked_object_properties


def register():
    custom_tags.register()
    grabbable.register()
    rigid_body.register()
    physics_shape.register()
    networked_behavior.register()
    networked_transform.register()
    networked_animation.register()
    networked_material.register()
    networked_object_material.register()
    networked_object_properties.register()
    capturable.register()


def unregister():
    capturable.unregister()
    networked_behavior.unregister()
    networked_transform.unregister()
    networked_animation.unregister()
    networked_material.unregister()
    networked_object_material.unregister()
    rigid_body.unregister()
    physics_shape.unregister()
    grabbable.unregister()
    custom_tags.unregister()
    networked_object_properties.unregister()
