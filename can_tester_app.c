#include "can_tester_app.h"
#include "scenes_config/app_scene_functions.h"

static bool can_tester_custom_event_callback(void* context, uint32_t event) {
    CanTesterApp* app = context;
    return scene_manager_handle_custom_event(app->scene_manager, event);
}

static bool can_tester_back_event_callback(void* context) {
    CanTesterApp* app = context;
    return scene_manager_handle_back_event(app->scene_manager);
}

CanTesterApp* can_tester_app_alloc(void) {
    CanTesterApp* app = malloc(sizeof(CanTesterApp));
    memset(app, 0, sizeof(CanTesterApp));

    app->mcp_can = mcp_alloc(MCP_NORMAL, MCP_16MHZ, MCP_500KBPS);

    app->gui = furi_record_open(RECORD_GUI);

    app->scene_manager = scene_manager_alloc(&can_tester_scene_handlers, app);

    app->view_dispatcher = view_dispatcher_alloc();
    view_dispatcher_set_event_callback_context(app->view_dispatcher, app);
    view_dispatcher_set_custom_event_callback(app->view_dispatcher, can_tester_custom_event_callback);
    view_dispatcher_set_navigation_event_callback(app->view_dispatcher, can_tester_back_event_callback);
    view_dispatcher_attach_to_gui(app->view_dispatcher, app->gui, ViewDispatcherTypeFullscreen);

    app->submenu = submenu_alloc();
    view_dispatcher_add_view(app->view_dispatcher, CanTesterViewSubmenu, submenu_get_view(app->submenu));

    app->widget = widget_alloc();
    view_dispatcher_add_view(app->view_dispatcher, CanTesterViewWidget, widget_get_view(app->widget));

    return app;
}

void can_tester_app_free(CanTesterApp* app) {
    view_dispatcher_remove_view(app->view_dispatcher, CanTesterViewSubmenu);
    view_dispatcher_remove_view(app->view_dispatcher, CanTesterViewWidget);

    submenu_free(app->submenu);
    widget_free(app->widget);

    scene_manager_free(app->scene_manager);
    view_dispatcher_free(app->view_dispatcher);

    furi_record_close(RECORD_GUI);

    free_mcp2515(app->mcp_can);
    free(app);
}

int32_t can_tester_main(void* p) {
    UNUSED(p);
    CanTesterApp* app = can_tester_app_alloc();

    scene_manager_next_scene(app->scene_manager, can_tester_scene_main_menu);
    view_dispatcher_run(app->view_dispatcher);

    can_tester_app_free(app);
    return 0;
}
