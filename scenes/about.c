#include "../can_tester_app.h"
#include "../scenes_config/app_scene_functions.h"

void can_tester_scene_about_on_enter(void* context) {
    CanTesterApp* app = context;

    widget_reset(app->widget);
    widget_add_string_element(
        app->widget, 64, 5, AlignCenter, AlignTop, FontPrimary,
        "CAN Tester");
    widget_add_string_element(
        app->widget, 64, 18, AlignCenter, AlignTop, FontSecondary,
        "Version: " CAN_TESTER_VERSION);
    widget_add_string_multiline_element(
        app->widget, 64, 33, AlignCenter, AlignTop, FontSecondary,
        "MCP2515 CAN bus loopback\n"
        "tester for verifying\n"
        "wiring with USB-CAN\n"
        "analyzers (CANalyst-II)");

    view_dispatcher_switch_to_view(app->view_dispatcher, CanTesterViewWidget);
}

bool can_tester_scene_about_on_event(void* context, SceneManagerEvent event) {
    UNUSED(context);
    UNUSED(event);
    return false;
}

void can_tester_scene_about_on_exit(void* context) {
    CanTesterApp* app = context;
    widget_reset(app->widget);
}
