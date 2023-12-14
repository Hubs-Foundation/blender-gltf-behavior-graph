# Nodes that are deprecated and are replaced with hardcoded nodes but we still load the nodes
# from the JSON as we want the to work for backwards compatibility but we don't want them to show in
# the categories
from .components import networked_animation, networked_behavior, networked_transform, rigid_body, physics_shape
from io_hubs_addon.components.definitions import text, video, audio, media_frame, visible
DEPRECATED_NODES = [
    "BGNode_hubs_material_set",
    "BGNode_hubs_material_getColor",
    "BGNode_hubs_material_setColor",
    "BGNode_hubs_material_getMap",
    "BGNode_hubs_material_setMap",
    "BGNode_hubs_material_getTransparent",
    "BGNode_hubs_material_setTransparent",
    "BGNode_hubs_material_getOpacity",
    "BGNode_hubs_material_setOpacity",
    "BGNode_hubs_material_getAlphaMap",
    "BGNode_hubs_material_setAlphaMap",
    "BGNode_hubs_material_getToneMapped",
    "BGNode_hubs_material_setToneMapped",
    "BGNode_hubs_material_getEmissive",
    "BGNode_hubs_material_setEmissive",
    "BGNode_hubs_material_getEmissiveMap",
    "BGNode_hubs_material_setEmissiveMap",
    "BGNode_hubs_material_getEmissiveIntensity",
    "BGNode_hubs_material_setEmissiveIntensity",
    "BGNode_hubs_material_getRoughness",
    "BGNode_hubs_material_setRoughness",
    "BGNode_hubs_material_getRoughnessMap",
    "BGNode_hubs_material_setRoughnessMap",
    "BGNode_hubs_material_getMetalness",
    "BGNode_hubs_material_setMetalness",
    "BGNode_hubs_material_getMetalnessMap",
    "BGNode_hubs_material_setMetalnessMap",
    "BGNode_hubs_material_getLightMap",
    "BGNode_hubs_material_setLightMap",
    "BGNode_hubs_material_getLightMapIntensity",
    "BGNode_hubs_material_setLightMapIntensity",
    "BGNode_hubs_material_getAOMap",
    "BGNode_hubs_material_setAOMap",
    "BGNode_hubs_material_getAOMapIntensity",
    "BGNode_hubs_material_setAOMapIntensity",
    "BGNode_hubs_material_getNormalMap",
    "BGNode_hubs_material_setNormalMap",
    "BGNode_hubs_material_getWireframe",
    "BGNode_hubs_material_setWireframe",
    "BGNode_hubs_material_getFlatShading",
    "BGNode_hubs_material_setFlatShading",
    "BGNode_hubs_material_getFog",
    "BGNode_hubs_material_setFog",
    "BGNode_hubs_material_getDepthWrite",
    "BGNode_hubs_material_setDepthWrite",
    "BGNode_hubs_material_getalphaTest",
    "BGNode_hubs_material_setalphaTest"
]

#  Nodes we want to be loaded from the JSON spec but we just want to change their categories
CUSTOM_CATEGORY_NODES = ["BGNode_hubs_onPlayerJoined",
                         "BGNode_hubs_onPlayerLeft",
                         "BGNode_lifecycle_onStart",
                         "BGNode_lifecycle_onEnd",
                         "BGNode_lifecycle_onTick",
                         "BGNode_hubs_entity_components_custom_tags_removeTag",
                         "BGNode_hubs_entity_components_custom_tags_addTag",
                         "BGNode_hubs_entity_components_custom_tags_hasTag",
                         "BGNode_hubs_components_text_setText"]

# Categories that we don't want to load from the JSON because we are replacing them by hardcoded categories
FILTERED_CATEGORIES = ["Media", "Text",  "String Math",
                       "Bool Math", "Int Math", "Float Math", "Vec3 Math", "Euler Math", "Physics", "Media Frame"]

MATERIAL_PROPERTIES_ENUM = [
    ("color", "Color", "Color"),
    ("map", "Map", "Map"),
    ("transparent", "Transparent", "Transparent"),
    ("opacity", "Opacity", "Opacity"),
    ("alphaMap", "AlphaMap", "AlphaMap"),
    ("toneMapped", "ToneMapped", "ToneMapped"),
    ("emissive", "Emissive", "Emissive"),
    ("emissiveMap", "EmissiveMap", "EmissiveMap"),
    ("emissiveIntensity", "EmissiveIntensity", "EmissiveIntensity"),
    ("roughness", "Roughness", "Roughness"),
    ("roughnessMap", "RoughnessMap", "RoughnessMap"),
    ("metalness", "Metalness", "Metalness"),
    ("metalnessMap", "MetalnessMap", "MetalnessMap"),
    ("lightMap", "LightMap", "LightMap"),
    ("lightMapIntensity", "LightMapIntensity", "LightMapIntensity"),
    ("aoMap", "AOMap", "AOMap"),
    ("aoMapIntensity", "AOMapIntensity", "AOMapIntensity"),
    ("normalMap", "NormalMap", "NormalMap"),
    ("wireframe", "Wireframe", "Wireframe"),
    ("flatShading", "FlatShading", "FlatShading"),
    ("fog", "Fog", "Fog"),
    ("depthWrite", "DepthWrite", "DepthWrite"),
    ("alphaTest", "AlphaTest", "AlphaTest")
]

MATERIAL_PROPERTIES_TO_TYPES = {
    "color": "color",
    "map": "texture",
    "transparent": "boolean",
    "opacity": "float",
    "alphaMap": "texture",
    "toneMapped": "boolean",
    "emissive": "color",
    "emissiveMap": "texture",
    "emissiveIntensity": "float",
    "roughness": "float",
    "roughnessMap": "texture",
    "metalness": "float",
    "metalnessMap": "texture",
    "lightMap": "texture",
    "lightMapIntensity": "float",
    "aoMap": "texture",
    "aoMapIntensity": "float",
    "normalMap": "texture",
    "wireframe": "boolean",
    "flatShading": "boolean",
    "fog": "boolean",
    "depthWrite": "boolean",
    "alphaTest": "float"
}

CATEGORY_COLORS = {
    "Event":  (0.6, 0.2, 0.2),
    "Flow":  (0.2, 0.2, 0.2),
    "Time":  (0.3, 0.3, 0.3),
    "Action":  (0.2, 0.2, 0.6),
    "None": (0.6, 0.6, 0.2),
    "Networking": (0.0, 0.7, 0.7)
}


# Components that Get Entity Component support. Support for these need to be available in the Hubs client
SUPPORTED_COMPONENTS = [
    video.Video.get_name(),
    audio.Audio.get_name(),
    text.Text.get_name(),
    networked_animation.NetworkedAnimation.get_name(),
    rigid_body.RigidBody.get_name(),
    physics_shape.PhysicsShape.get_name(),
    networked_transform.NetworkedTransform.get_name(),
    networked_behavior.NetworkedBehavior.get_name(),
    media_frame.MediaFrame.get_name(),
    visible.Visible.get_name()
]

# Components that Set Component property support. Support for these need to be available in the Hubs client
SUPPORTED_PROPERTY_COMPONENTS = [
    video.Video.get_name(),
    audio.Audio.get_name(),
    text.Text.get_name(),
    rigid_body.RigidBody.get_name(),
    media_frame.MediaFrame.get_name(),
    visible.Visible.get_name(),
]

VARIABLES_TYPES = [
    ("boolean", "Boolean", "Boolean"),
    ("float", "Float", "Float"),
    ("integer", "Integer", "Integer"),
    ("string", "String", "String"),
    ("vec3", "Vector3", "Vector3"),
    ("animationAction", "Action", "Action"),
    ("entity", "Entity", "Entity"),
    ("color", "Color", "Color"),
    ("material", "Material", "Material")
]
