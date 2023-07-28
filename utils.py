from io_hubs_addon.components.components_registry import register_component, unregister_component, __components_registry


def redraw_area(context, area_id):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == area_id:
                area.tag_redraw()
                context.window_manager.update_tag()


def do_register(ComponentClass):
    register_component(ComponentClass)
    __components_registry[ComponentClass.get_name()] = ComponentClass


def do_unregister(ComponentClass):
    unregister_component(ComponentClass)
    __components_registry.pop(ComponentClass.get_name())
