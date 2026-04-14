#pragma once

#include <gui/scene_manager.h>

#define ADD_SCENE(prefix, name, id) can_tester_scene_##id,
typedef enum {
#include "app_scene_config.h"
    can_tester_scene_count,
} CanTesterSceneID;
#undef ADD_SCENE

extern const SceneManagerHandlers can_tester_scene_handlers;

#define ADD_SCENE(prefix, name, id) void prefix##_scene_##name##_on_enter(void*);
#include "app_scene_config.h"
#undef ADD_SCENE

#define ADD_SCENE(prefix, name, id) \
    bool prefix##_scene_##name##_on_event(void* context, SceneManagerEvent event);
#include "app_scene_config.h"
#undef ADD_SCENE

#define ADD_SCENE(prefix, name, id) void prefix##_scene_##name##_on_exit(void* context);
#include "app_scene_config.h"
#undef ADD_SCENE
