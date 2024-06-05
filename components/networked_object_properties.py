from io_hubs_addon.components.hubs_component import HubsComponent
from io_hubs_addon.components.types import NodeType, PanelType
from ..utils import do_register, do_unregister
import bpy


class NetworkedObjectProperties(HubsComponent):
    _definition = {
        'name': 'networked-object-properties',
        'display_name': 'Networked Object',
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'EMPTY_AXIS',
        'version': (1, 0, 0)
    }

    visible: bpy.props.BoolProperty(
        name="Visibility", description="Visibility object state", default=False)

    transform: bpy.props.BoolProperty(
        name="Transform", description="Object transform", default=False)


def register():
    do_register(NetworkedObjectProperties)


def unregister():
    do_unregister(NetworkedObjectProperties)
