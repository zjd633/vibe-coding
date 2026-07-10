#include "snake_game/snake_list.h"

#include <stdlib.h>

static bool directions_are_opposite(SnakeDirection a, SnakeDirection b)
{
    return (a == SNAKE_DIRECTION_UP && b == SNAKE_DIRECTION_DOWN)
        || (a == SNAKE_DIRECTION_DOWN && b == SNAKE_DIRECTION_UP)
        || (a == SNAKE_DIRECTION_LEFT && b == SNAKE_DIRECTION_RIGHT)
        || (a == SNAKE_DIRECTION_RIGHT && b == SNAKE_DIRECTION_LEFT);
}

static bool direction_is_valid(SnakeDirection direction)
{
    return direction == SNAKE_DIRECTION_UP
        || direction == SNAKE_DIRECTION_RIGHT
        || direction == SNAKE_DIRECTION_DOWN
        || direction == SNAKE_DIRECTION_LEFT;
}

static SnakePoint point_after_move(SnakePoint point, SnakeDirection direction)
{
    switch (direction) {
    case SNAKE_DIRECTION_UP:
        point.y -= 1;
        break;
    case SNAKE_DIRECTION_RIGHT:
        point.x += 1;
        break;
    case SNAKE_DIRECTION_DOWN:
        point.y += 1;
        break;
    case SNAKE_DIRECTION_LEFT:
        point.x -= 1;
        break;
    }

    return point;
}

static bool points_equal(SnakePoint a, SnakePoint b)
{
    return a.x == b.x && a.y == b.y;
}

static bool point_is_inside_board(SnakePoint point, int board_width, int board_height)
{
    return point.x >= 0
        && point.y >= 0
        && point.x < board_width
        && point.y < board_height;
}

static SnakeNode *create_node(SnakePoint position)
{
    SnakeNode *node = (SnakeNode *)calloc(1, sizeof(SnakeNode));
    if (node == NULL) {
        return NULL;
    }

    node->position = position;
    node->prev = node;
    node->next = node;
    return node;
}

static bool append_tail(SnakeList *snake, SnakePoint position)
{
    SnakeNode *node = create_node(position);
    if (node == NULL) {
        return false;
    }

    if (snake->head == NULL) {
        snake->head = node;
        snake->tail = node;
    } else {
        /*
         * 在尾部追加节点时，要一次性补齐四条连接：
         * 旧 tail -> 新节点、新节点 -> head、head -> 新节点、 新节点 -> 旧 tail。
         * 这样追加完成后链表仍然保持双向循环。
         */
        node->prev = snake->tail;
        node->next = snake->head;
        snake->tail->next = node;
        snake->head->prev = node;
        snake->tail = node;
    }

    snake->length += 1;
    return true;
}

static bool push_head(SnakeList *snake, SnakePoint position)
{
    SnakeNode *node = create_node(position);
    if (node == NULL) {
        return false;
    }

    if (snake->head == NULL) {
        snake->head = node;
        snake->tail = node;
    } else {
        /*
         * 贪吃蛇移动时采用“新增头节点”的模型：
         * 新节点放到 head 前面，并把它接入 tail 和旧 head 之间。
         */
        node->prev = snake->tail;
        node->next = snake->head;
        snake->head->prev = node;
        snake->tail->next = node;
        snake->head = node;
    }

    snake->length += 1;
    return true;
}

static void remove_tail(SnakeList *snake)
{
    SnakeNode *old_tail = snake->tail;
    if (old_tail == NULL) {
        return;
    }

    if (snake->length == 1) {
        snake->head = NULL;
        snake->tail = NULL;
        snake->length = 0;
        free(old_tail);
        return;
    }

    /*
     * 未吃到食物时删除尾节点，让蛇身总长度保持不变。
     * 删除后要把新 tail 接回 head，循环链表才不会断。
     */
    snake->tail = old_tail->prev;
    snake->tail->next = snake->head;
    snake->head->prev = snake->tail;
    snake->length -= 1;
    free(old_tail);
}

static bool next_position_hits_body(const SnakeList *snake, SnakePoint next_position, bool grow)
{
    const SnakeNode *node = snake->head;
    for (size_t i = 0; i < snake->length; ++i) {
        /*
         * 尾格安全规则：
         * 如果本帧没有增长，tail 会在同一步被删除，所以允许蛇头进入当前 tail 的格子。
         */
        if (!grow && node == snake->tail) {
            node = node->next;
            continue;
        }

        if (points_equal(node->position, next_position)) {
            return true;
        }

        node = node->next;
    }

    return false;
}

bool snake_list_init_centered(SnakeList *snake, int board_width, int board_height)
{
    if (snake == NULL || board_width < 3 || board_height < 1) {
        return false;
    }

    const int center_x = board_width / 2;
    const int center_y = board_height / 2;
    const SnakePoint points[] = {
        { center_x + 1, center_y },
        { center_x, center_y },
        { center_x - 1, center_y }
    };

    return snake_list_init_from_points(
        snake,
        board_width,
        board_height,
        points,
        sizeof(points) / sizeof(points[0]),
        SNAKE_DIRECTION_RIGHT
    );
}

bool snake_list_init_from_points(
    SnakeList *snake,
    int board_width,
    int board_height,
    const SnakePoint *points,
    size_t count,
    SnakeDirection direction
)
{
    if (snake == NULL
        || points == NULL
        || count == 0
        || board_width <= 0
        || board_height <= 0
        || !direction_is_valid(direction)) {
        return false;
    }

    snake->head = NULL;
    snake->tail = NULL;
    snake->length = 0;
    snake->board_width = board_width;
    snake->board_height = board_height;
    snake->direction = direction;
    snake->queued_direction = direction;

    for (size_t i = 0; i < count; ++i) {
        if (!point_is_inside_board(points[i], board_width, board_height)) {
            snake_list_destroy(snake);
            return false;
        }

        for (size_t j = 0; j < i; ++j) {
            if (points_equal(points[i], points[j])) {
                snake_list_destroy(snake);
                return false;
            }
        }

        if (!append_tail(snake, points[i])) {
            snake_list_destroy(snake);
            return false;
        }
    }

    return true;
}

void snake_list_destroy(SnakeList *snake)
{
    if (snake == NULL) {
        return;
    }

    while (snake->length > 0) {
        remove_tail(snake);
    }

    snake->head = NULL;
    snake->tail = NULL;
    snake->length = 0;
}

bool snake_list_request_direction(SnakeList *snake, SnakeDirection direction)
{
    if (snake == NULL || !direction_is_valid(direction)) {
        return false;
    }

    /*
     * 是否反向只和“当前正在移动的方向”比较。
     * 因此在一次移动间隔内，上、下这类连续合法输入可以由最后一次输入覆盖，
     * 但从右直接按左仍会被忽略。
     */
    if (directions_are_opposite(snake->direction, direction)) {
        return false;
    }

    snake->queued_direction = direction;
    return true;
}

SnakeStepResult snake_list_step(SnakeList *snake, bool grow)
{
    if (snake == NULL || snake->head == NULL) {
        return SNAKE_STEP_HIT_SELF;
    }

    snake->direction = snake->queued_direction;
    const SnakePoint next_position = point_after_move(snake->head->position, snake->direction);

    if (!point_is_inside_board(next_position, snake->board_width, snake->board_height)) {
        return SNAKE_STEP_HIT_WALL;
    }

    if (next_position_hits_body(snake, next_position, grow)) {
        return SNAKE_STEP_HIT_SELF;
    }

    if (!push_head(snake, next_position)) {
        return SNAKE_STEP_HIT_SELF;
    }

    if (!grow) {
        remove_tail(snake);
        return SNAKE_STEP_MOVED;
    }

    return SNAKE_STEP_GREW;
}

bool snake_list_contains(const SnakeList *snake, SnakePoint point)
{
    if (snake == NULL || snake->head == NULL) {
        return false;
    }

    const SnakeNode *node = snake->head;
    for (size_t i = 0; i < snake->length; ++i) {
        if (points_equal(node->position, point)) {
            return true;
        }

        node = node->next;
    }

    return false;
}
