#pragma once

#include <furi.h>
#include <gui/gui.h>
#include <gui/scene_manager.h>
#include <gui/view_dispatcher.h>
#include <gui/modules/widget.h>
#include <gui/modules/submenu.h>

#include "libraries/mcp_can_2515.h"

#define CAN_TESTER_VERSION "1.0.0"

typedef enum {
    CanTesterViewSubmenu,
    CanTesterViewWidget,
} CanTesterView;

typedef enum {
    WorkerFlagStop = (1 << 0),
} WorkerFlag;

typedef struct {
    Gui* gui;
    SceneManager* scene_manager;
    ViewDispatcher* view_dispatcher;
    Widget* widget;
    Submenu* submenu;

    MCP2515* mcp_can;

    FuriThread* worker_thread;
} CanTesterApp;

CanTesterApp* can_tester_app_alloc(void);
void can_tester_app_free(CanTesterApp* app);
int32_t can_tester_main(void* p);
