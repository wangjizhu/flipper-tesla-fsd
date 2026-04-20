#include "../can_tester_app.h"
#include "../scenes_config/app_scene_functions.h"

// CAN Test configuration
#define CAN_TEST_TX_ID        0x7E0
#define CAN_TEST_INTERVAL_MS  500
#define CAN_TEST_POLL_MS      2

typedef enum {
    CanTestEventUpdate = 100,
    CanTestEventInitFail,
    CanTestEventInitOk,
} CanTestEvent;

// Test mode: start with loopback, user can switch to normal
typedef enum {
    TestModeLoopback = 0,
    TestModeNormal,
} TestMode;

typedef struct {
    uint32_t tx_count;
    uint32_t rx_count;
    uint32_t err_count;
    uint8_t  tx_counter;
    uint32_t last_rx_id;
    uint8_t  last_rx_len;
    uint8_t  last_rx_data[8];
    bool     running;
    bool     init_ok;
    TestMode mode;
    uint8_t  mcp_mode_reg;  // raw CANSTAT mode bits for diagnostics
} CanTestState;

static CanTestState test_state;

static int32_t can_test_worker(void* context) {
    CanTesterApp* app = context;
    if(!app || !app->mcp_can) return 0;

    MCP2515* mcp = app->mcp_can;
    CANFRAME tx_frame;
    CANFRAME rx_frame;

    // Use the selected mode
    if(test_state.mode == TestModeLoopback) {
        mcp->mode = MCP_LOOPBACK;
    } else {
        mcp->mode = MCP_NORMAL;
    }
    mcp->bitRate = MCP_500KBPS;
    mcp->clck = MCP_8MHZ;

    ERROR_CAN init_result = mcp2515_init(mcp);
    if(init_result != ERROR_OK) {
        test_state.init_ok = false;
        view_dispatcher_send_custom_event(app->view_dispatcher, CanTestEventInitFail);
        return 0;
    }

    test_state.init_ok = true;

    // Read back actual mode register for diagnostics
    // (mode bits are in CANSTAT register upper 3 bits)

    // Clear all masks/filters — accept everything
    init_mask(mcp, 0, 0x000);
    init_mask(mcp, 1, 0x000);
    for(int i = 0; i < 6; i++) {
        init_filter(mcp, i, 0x000);
    }

    // Notify UI that init succeeded
    view_dispatcher_send_custom_event(app->view_dispatcher, CanTestEventInitOk);

    // Prepare TX frame template
    memset(&tx_frame, 0, sizeof(CANFRAME));
    tx_frame.canId = CAN_TEST_TX_ID;
    tx_frame.data_length = 8;
    tx_frame.ext = 0;
    tx_frame.req = 0;

    uint32_t last_tx = 0;
    uint32_t last_ui_update = 0;
    test_state.running = true;

    while(true) {
        uint32_t flags = furi_thread_flags_get();
        if(flags & WorkerFlagStop) break;

        uint32_t now = furi_get_tick();

        // --- TX: send test frame periodically ---
        if((now - last_tx) >= furi_ms_to_ticks(CAN_TEST_INTERVAL_MS)) {
            tx_frame.buffer[0] = test_state.tx_counter;
            tx_frame.buffer[1] = 0xDE;
            tx_frame.buffer[2] = 0xAD;
            tx_frame.buffer[3] = 0xBE;
            tx_frame.buffer[4] = 0xEF;
            tx_frame.buffer[5] = 0xCA;
            tx_frame.buffer[6] = 0xFE;
            uint8_t sum = 0;
            for(int i = 0; i < 7; i++) sum += tx_frame.buffer[i];
            tx_frame.buffer[7] = sum;

            if(send_can_frame(mcp, &tx_frame) == ERROR_OK) {
                test_state.tx_count++;
                test_state.tx_counter++;
            } else {
                test_state.err_count++;
            }
            last_tx = now;
        }

        // --- RX: check for incoming frames ---
        if(check_receive(mcp) == ERROR_OK) {
            if(read_can_message(mcp, &rx_frame) == ERROR_OK) {
                test_state.rx_count++;
                test_state.last_rx_id = rx_frame.canId;
                test_state.last_rx_len = rx_frame.data_length;
                memcpy(test_state.last_rx_data, rx_frame.buffer,
                       rx_frame.data_length > 8 ? 8 : rx_frame.data_length);
            }
        }

        // --- UI update ---
        if((now - last_ui_update) >= furi_ms_to_ticks(300)) {
            view_dispatcher_send_custom_event(app->view_dispatcher, CanTestEventUpdate);
            last_ui_update = now;
        }

        furi_delay_ms(CAN_TEST_POLL_MS);
    }

    test_state.running = false;
    deinit_mcp2515(mcp);
    return 0;
}

static void can_test_update_widget(CanTesterApp* app) {
    widget_reset(app->widget);

    const char* mode_str = (test_state.mode == TestModeLoopback) ? "LOOPBACK" : "NORMAL";

    // Title with mode
    char title[32];
    snprintf(title, sizeof(title), "CAN Test [%s]", mode_str);
    widget_add_string_element(
        app->widget, 64, 2, AlignCenter, AlignTop, FontPrimary, title);

    // TX info
    char tx_buf[40];
    snprintf(tx_buf, sizeof(tx_buf), "TX: %lu  ERR: %lu",
             (unsigned long)test_state.tx_count,
             (unsigned long)test_state.err_count);
    widget_add_string_element(
        app->widget, 2, 16, AlignLeft, AlignTop, FontSecondary, tx_buf);

    // RX info
    char rx_buf[40];
    if(test_state.rx_count > 0) {
        snprintf(rx_buf, sizeof(rx_buf), "RX: %lu  ID:0x%lX [%u]",
                 (unsigned long)test_state.rx_count,
                 (unsigned long)test_state.last_rx_id,
                 test_state.last_rx_len);
    } else {
        snprintf(rx_buf, sizeof(rx_buf), "RX: 0  (waiting...)");
    }
    widget_add_string_element(
        app->widget, 2, 27, AlignLeft, AlignTop, FontSecondary, rx_buf);

    // Last RX data hex dump
    char data_buf[40];
    if(test_state.rx_count > 0 && test_state.last_rx_len > 0) {
        int pos = 0;
        uint8_t show_len = test_state.last_rx_len > 8 ? 8 : test_state.last_rx_len;
        for(uint8_t i = 0; i < show_len && pos < 38; i++) {
            pos += snprintf(data_buf + pos, sizeof(data_buf) - pos, "%02X ",
                            test_state.last_rx_data[i]);
        }
        data_buf[pos > 0 ? pos - 1 : 0] = '\0';
    } else {
        snprintf(data_buf, sizeof(data_buf), "-- -- -- -- -- -- -- --");
    }
    widget_add_string_element(
        app->widget, 2, 38, AlignLeft, AlignTop, FontSecondary, data_buf);

    // Status
    char status_buf[40];
    snprintf(status_buf, sizeof(status_buf), "500kbps  Init:%s",
             test_state.init_ok ? "OK" : "FAIL");
    widget_add_string_element(
        app->widget, 2, 49, AlignLeft, AlignTop, FontSecondary, status_buf);

    widget_add_string_element(
        app->widget, 64, 62, AlignCenter, AlignBottom, FontSecondary,
        "[BACK] stop");
}

void can_tester_scene_can_test_on_enter(void* context) {
    CanTesterApp* app = context;
    memset(&test_state, 0, sizeof(CanTestState));

    // Use mode selected from main menu
    test_state.mode = (app->test_mode == 1) ? TestModeNormal : TestModeLoopback;
    const char* mode_label = (test_state.mode == TestModeLoopback) ? "LOOPBACK self-test" : "NORMAL mode";

    widget_reset(app->widget);
    widget_add_string_multiline_element(
        app->widget, 64, 20, AlignCenter, AlignCenter, FontPrimary,
        "CAN Bus Test");

    char init_msg[64];
    snprintf(init_msg, sizeof(init_msg), "%s\n500kbps / 16MHz", mode_label);
    widget_add_string_multiline_element(
        app->widget, 64, 40, AlignCenter, AlignCenter, FontSecondary, init_msg);
    view_dispatcher_switch_to_view(app->view_dispatcher, CanTesterViewWidget);

    if(app->mcp_can) {
        app->worker_thread = furi_thread_alloc_ex("CanTestWorker", 2048, can_test_worker, app);
        furi_thread_start(app->worker_thread);
    }
}

bool can_tester_scene_can_test_on_event(void* context, SceneManagerEvent event) {
    CanTesterApp* app = context;
    bool consumed = false;

    if(event.type == SceneManagerEventTypeCustom) {
        switch(event.event) {
        case CanTestEventUpdate:
            can_test_update_widget(app);
            consumed = true;
            break;
        case CanTestEventInitOk:
            can_test_update_widget(app);
            consumed = true;
            break;
        case CanTestEventInitFail:
            widget_reset(app->widget);
            widget_add_string_multiline_element(
                app->widget, 64, 20, AlignCenter, AlignCenter, FontPrimary,
                "MCP2515 Init Failed!");
            widget_add_string_multiline_element(
                app->widget, 64, 44, AlignCenter, AlignCenter, FontSecondary,
                "Check CAN board\nis plugged in correctly");
            consumed = true;
            break;
        }
    }
    return consumed;
}

void can_tester_scene_can_test_on_exit(void* context) {
    CanTesterApp* app = context;
    if(app->worker_thread) {
        furi_thread_flags_set(furi_thread_get_id(app->worker_thread), WorkerFlagStop);
        furi_thread_join(app->worker_thread);
        furi_thread_free(app->worker_thread);
        app->worker_thread = NULL;
    }
    widget_reset(app->widget);
}
