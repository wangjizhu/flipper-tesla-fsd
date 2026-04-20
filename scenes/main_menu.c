#include "../can_tester_app.h"
#include "../scenes_config/app_scene_functions.h"

enum {
    MainMenuLoopback,
    MainMenuNormal,
    MainMenuAbout,
};

static void main_menu_callback(void* context, uint32_t index) {
    CanTesterApp* app = context;
    view_dispatcher_send_custom_event(app->view_dispatcher, index);
}

void can_tester_scene_main_menu_on_enter(void* context) {
    CanTesterApp* app = context;

    submenu_reset(app->submenu);
    submenu_set_header(app->submenu, "CAN Tester");
    submenu_add_item(app->submenu, "Loopback Self-Test", MainMenuLoopback, main_menu_callback, app);
    submenu_add_item(app->submenu, "Normal Mode (CAN Bus)", MainMenuNormal, main_menu_callback, app);
    submenu_add_item(app->submenu, "About", MainMenuAbout, main_menu_callback, app);

    view_dispatcher_switch_to_view(app->view_dispatcher, CanTesterViewSubmenu);
}

bool can_tester_scene_main_menu_on_event(void* context, SceneManagerEvent event) {
    CanTesterApp* app = context;
    bool consumed = false;

    if(event.type == SceneManagerEventTypeCustom) {
        switch(event.event) {
        case MainMenuLoopback:
            app->test_mode = 0; // loopback
            scene_manager_next_scene(app->scene_manager, can_tester_scene_can_test);
            consumed = true;
            break;
        case MainMenuNormal:
            app->test_mode = 1; // normal
            scene_manager_next_scene(app->scene_manager, can_tester_scene_can_test);
            consumed = true;
            break;
        case MainMenuAbout:
            scene_manager_next_scene(app->scene_manager, can_tester_scene_about);
            consumed = true;
            break;
        }
    }
    return consumed;
}

void can_tester_scene_main_menu_on_exit(void* context) {
    CanTesterApp* app = context;
    submenu_reset(app->submenu);
}
