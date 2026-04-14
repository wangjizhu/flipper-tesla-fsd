#include "app_scene_functions.h"

#define ADD_SCENE(prefix, name, id) prefix##_scene_##name##_on_enter,
void (*const can_tester_on_enter_handlers[])(void*) = {
#include "app_scene_config.h"
};
#undef ADD_SCENE

#define ADD_SCENE(prefix, name, id) prefix##_scene_##name##_on_event,
bool (*const can_tester_on_event_handlers[])(void* context, SceneManagerEvent event) = {
#include "app_scene_config.h"
};
#undef ADD_SCENE

#define ADD_SCENE(prefix, name, id) prefix##_scene_##name##_on_exit,
void (*const can_tester_on_exit_handlers[])(void* context) = {
#include "app_scene_config.h"
};
#undef ADD_SCENE

const SceneManagerHandlers can_tester_scene_handlers = {
    .on_enter_handlers = can_tester_on_enter_handlers,
    .on_event_handlers = can_tester_on_event_handlers,
    .on_exit_handlers = can_tester_on_exit_handlers,
    .scene_num = can_tester_scene_count,
};
