from . import custom_tags, networked_behavior, networked_animation, networked_material, networked_object_material, networked_object_properties


def register():
    custom_tags.register()
    networked_behavior.register()
    networked_animation.register()
    networked_material.register()
    networked_object_material.register()
    networked_object_properties.register()


def unregister():
    networked_behavior.unregister()
    networked_animation.unregister()
    networked_material.unregister()
    networked_object_material.unregister()
    custom_tags.unregister()
    networked_object_properties.unregister()
