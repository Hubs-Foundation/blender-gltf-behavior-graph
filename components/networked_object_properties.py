from io_hubs_addon.components.hubs_component import HubsComponent
from io_hubs_addon.components.types import Category, NodeType, PanelType
from ..utils import do_register, do_unregister
import bpy


class NetworkedTObjectProperties(HubsComponent):
    _definition = {
        'name': 'networked-object-properties',
        'display_name': 'BG Networked Object Properties',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'EMPTY_AXIS',
        'version': (1, 0, 0),
        'deps': ['networked']
    }

    visible: bpy.props.BoolProperty(
        name="Visibility", description="Visibility object state", default=False)

    transform: bpy.props.BoolProperty(
        name="Transform", description="Object transform", default=False)


def register():
    do_register(NetworkedTObjectProperties)


def unregister():
    do_unregister(NetworkedTObjectProperties)
