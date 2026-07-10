#include "snake_game/app_ui.h"

SnakeUiRect snake_ui_start_button_rect(void)
{
    return (SnakeUiRect) { 378, 330, 204, 58 };
}

SnakeUiRect snake_ui_resume_button_rect(void)
{
    return (SnakeUiRect) { 392, 380, 176, 48 };
}

SnakeUiRect snake_ui_restart_button_rect(void)
{
    return (SnakeUiRect) { 354, 468, 252, 58 };
}

bool snake_ui_rect_contains(SnakeUiRect rect, int x, int y)
{
    /*
     * UI 坐标使用左闭右开区间：
     * 左上角像素算命中，右/下边界外一像素不算命中。
     * 这样相邻按钮不会共享同一个边界像素。
     */
    return x >= rect.x
        && y >= rect.y
        && x < rect.x + rect.width
        && y < rect.y + rect.height;
}

bool snake_ui_is_start_button_hit(int x, int y)
{
    return snake_ui_rect_contains(snake_ui_start_button_rect(), x, y);
}

bool snake_ui_is_resume_button_hit(int x, int y)
{
    return snake_ui_rect_contains(snake_ui_resume_button_rect(), x, y);
}

bool snake_ui_is_restart_button_hit(int x, int y)
{
    return snake_ui_rect_contains(snake_ui_restart_button_rect(), x, y);
}

const char *snake_ui_debug_node_role(unsigned int node_index, unsigned int node_count)
{
    if (node_index == 0u && node_count > 0u) {
        return "Head";
    }

    if (node_count > 1u && node_index + 1u == node_count) {
        return "Tail";
    }

    return "Node";
}
