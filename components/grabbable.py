from bpy.props import BoolProperty
from io_hubs_addon.components.hubs_component import HubsComponent
from io_hubs_addon.components.types import Category, NodeType, PanelType
from ..utils import do_register, do_unregister


class Grabbable(HubsComponent):
    _definition = {
        'name': 'grabbable',
        'display_name': 'BG Grabbable',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'VIEW_PAN',
        'deps': ['rigidbody', 'networked-transform'],
        'version': (1, 0, 0)
    }

    cursor: BoolProperty(
        name="By Cursor", description="Can be grabbed by a cursor", default=True)

    hand: BoolProperty(
        name="By Hand", description="Can be grabbed by VR hands", default=True)


def register():
    do_register(Grabbable)


def unregister():
    do_unregister(Grabbable)
