#ifndef SNAKE_GAME_APP_UI_H
#define SNAKE_GAME_APP_UI_H

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct SnakeUiRect {
    int x;
    int y;
    int width;
    int height;
} SnakeUiRect;

SnakeUiRect snake_ui_start_button_rect(void);
SnakeUiRect snake_ui_resume_button_rect(void);
SnakeUiRect snake_ui_restart_button_rect(void);

bool snake_ui_rect_contains(SnakeUiRect rect, int x, int y);
bool snake_ui_is_start_button_hit(int x, int y);
bool snake_ui_is_resume_button_hit(int x, int y);
bool snake_ui_is_restart_button_hit(int x, int y);
const char *snake_ui_debug_node_role(unsigned int node_index, unsigned int node_count);

#ifdef __cplusplus
}
#endif

#endif
