#ifndef SNAKE_GAME_SNAKE_LIST_H
#define SNAKE_GAME_SNAKE_LIST_H

#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct SnakePoint {
    int x;
    int y;
} SnakePoint;

typedef enum SnakeDirection {
    SNAKE_DIRECTION_UP = 0,
    SNAKE_DIRECTION_RIGHT,
    SNAKE_DIRECTION_DOWN,
    SNAKE_DIRECTION_LEFT
} SnakeDirection;

typedef enum SnakeStepResult {
    SNAKE_STEP_MOVED = 0,
    SNAKE_STEP_GREW,
    SNAKE_STEP_HIT_WALL,
    SNAKE_STEP_HIT_SELF
} SnakeStepResult;

/*
 * 每一个 SnakeNode 都是一节蛇身。
 * prev/next 同时存在，且 head->prev 指向 tail、tail->next 指向 head，
 * 因此整个蛇身天然形成“双向循环链表”。
 */
typedef struct SnakeNode {
    SnakePoint position;
    struct SnakeNode *prev;
    struct SnakeNode *next;
} SnakeNode;

typedef struct SnakeList {
    SnakeNode *head;
    SnakeNode *tail;
    size_t length;
    int board_width;
    int board_height;
    SnakeDirection direction;
    SnakeDirection queued_direction;
} SnakeList;

bool snake_list_init_centered(SnakeList *snake, int board_width, int board_height);
bool snake_list_init_from_points(
    SnakeList *snake,
    int board_width,
    int board_height,
    const SnakePoint *points,
    size_t count,
    SnakeDirection direction
);
void snake_list_destroy(SnakeList *snake);

bool snake_list_request_direction(SnakeList *snake, SnakeDirection direction);
SnakeStepResult snake_list_step(SnakeList *snake, bool grow);
bool snake_list_contains(const SnakeList *snake, SnakePoint point);

#ifdef __cplusplus
}
#endif

#endif
