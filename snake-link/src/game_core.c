#include "snake_game/game_core.h"

static bool points_equal(SnakePoint a, SnakePoint b)
{
    return a.x == b.x && a.y == b.y;
}

static uint32_t next_random(SnakeGame *game)
{
    /*
     * 使用一个小型 LCG 生成可复现随机数。
     * 测试可以传固定 seed，界面层可以传时间 seed。
     */
    game->rng_state = game->rng_state * 1664525u + 1013904223u;
    return game->rng_state;
}

static SnakePoint next_head_position(const SnakeList *snake)
{
    SnakePoint point = snake->head->position;

    switch (snake->queued_direction) {
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

static bool point_is_inside_board(const SnakeGame *game, SnakePoint point)
{
    return point.x >= 0
        && point.y >= 0
        && point.x < game->snake.board_width
        && point.y < game->snake.board_height;
}

static bool food_type_is_valid(SnakeFoodType type)
{
    return type == SNAKE_FOOD_NORMAL
        || type == SNAKE_FOOD_STAR
        || type == SNAKE_FOOD_ICE;
}

static bool food_index_is_valid(int food_index)
{
    return food_index >= 0 && food_index < SNAKE_GAME_FOOD_COUNT;
}

static bool food_color_index_is_valid(int color_index)
{
    return color_index >= 0 && color_index < SNAKE_GAME_FOOD_COLOR_COUNT;
}

static bool point_overlaps_foods(const SnakeGame *game, SnakePoint point, int ignored_food_index)
{
    /*
     * 多食物模式下，蛇吃掉一个槽位后只刷新这个槽位。
     * 这里用 ignored_food_index 跳过“正在被重放置”的槽位，避免它和自己旧位置比较。
     */
    for (int i = 0; i < game->food_count; ++i) {
        if (i != ignored_food_index && points_equal(game->foods[i].position, point)) {
            return true;
        }
    }

    return false;
}

static bool color_overlaps_foods(const SnakeGame *game, int color_index, int ignored_food_index)
{
    for (int i = 0; i < game->food_count; ++i) {
        if (i != ignored_food_index && game->foods[i].color_index == color_index) {
            return true;
        }
    }

    return false;
}

static int food_index_at_position(const SnakeGame *game, SnakePoint position)
{
    for (int i = 0; i < game->food_count; ++i) {
        if (points_equal(game->foods[i].position, position)) {
            return i;
        }
    }

    return -1;
}

static int next_unused_food_color_index(SnakeGame *game, int ignored_food_index)
{
    /*
     * 食物最多 10 个，调色板也准备 10 种颜色。
     * 随机起点让颜色顺序不死板，再线性扫描确保最终能找到一个未使用颜色。
     */
    const int start = (int)(next_random(game) % (uint32_t)SNAKE_GAME_FOOD_COLOR_COUNT);
    for (int offset = 0; offset < SNAKE_GAME_FOOD_COLOR_COUNT; ++offset) {
        const int color_index = (start + offset) % SNAKE_GAME_FOOD_COLOR_COUNT;
        if (!color_overlaps_foods(game, color_index, ignored_food_index)) {
            return color_index;
        }
    }

    return 0;
}

static int random_food_count(SnakeGame *game)
{
    /*
     * 食物数量不是固定值：每次需要重建/调整食物列表时，
     * 都在 5 到 10 之间重新抽一个目标数量，让棋盘压力有轻微变化。
     */
    const int range = SNAKE_GAME_FOOD_COUNT - SNAKE_GAME_MIN_FOOD_COUNT + 1;
    return SNAKE_GAME_MIN_FOOD_COUNT + (int)(next_random(game) % (uint32_t)range);
}

static bool place_random_food(SnakeGame *game, int food_index, SnakeFoodType type)
{
    if (!food_index_is_valid(food_index)) {
        return false;
    }

    const int total_cells = game->snake.board_width * game->snake.board_height;
    const int other_food_count = food_index < game->food_count ? game->food_count - 1 : game->food_count;
    if (total_cells <= 0 || (int)game->snake.length + other_food_count >= total_cells) {
        return false;
    }

    /*
     * 先用随机位置尝试，避免每次都从左上角开始。
     * 如果随机命中蛇身或其他食物，就线性扫描全图，保证最终能找到一个空格。
     */
    int start = (int)(next_random(game) % (uint32_t)total_cells);
    for (int offset = 0; offset < total_cells; ++offset) {
        const int index = (start + offset) % total_cells;
        SnakePoint candidate = {
            index % game->snake.board_width,
            index / game->snake.board_width
        };

        if (!snake_list_contains(&game->snake, candidate)
            && !point_overlaps_foods(game, candidate, food_index)) {
            game->foods[food_index].position = candidate;
            game->foods[food_index].type = type;
            game->foods[food_index].color_index = next_unused_food_color_index(game, food_index);
            return true;
        }
    }

    return false;
}

static bool place_initial_foods(SnakeGame *game)
{
    const int target_food_count = random_food_count(game);

    for (int i = 0; i < target_food_count; ++i) {
        if (!place_random_food(game, i, SNAKE_FOOD_NORMAL)) {
            return false;
        }

        /*
         * food_count 表示已经生效的槽位数量。
         * 初始化时逐个增加，后续随机刷新会避开前面已经放好的食物。
         */
        game->food_count += 1;
    }

    return true;
}

static void append_kept_food(SnakeGame *game, SnakeFood food)
{
    if (game->food_count >= SNAKE_GAME_FOOD_COUNT) {
        return;
    }

    game->foods[game->food_count] = food;
    game->food_count += 1;
}

static bool append_random_food(SnakeGame *game, SnakeFoodType type)
{
    if (game->food_count >= SNAKE_GAME_FOOD_COUNT) {
        return false;
    }

    if (!place_random_food(game, game->food_count, type)) {
        return false;
    }

    game->food_count += 1;
    return true;
}

static void move_last_food_to_front(SnakeGame *game)
{
    if (game->food_count <= 1) {
        return;
    }

    /*
     * 新刷出的食物放到 0 号槽位，测试和调试时更容易观察“刚被替换”的食物。
     * 这只是数组槽位顺序变化，不影响棋盘坐标、碰撞规则或链表逻辑。
     */
    const SnakeFood newest_food = game->foods[game->food_count - 1];
    for (int i = game->food_count - 1; i > 0; --i) {
        game->foods[i] = game->foods[i - 1];
    }
    game->foods[0] = newest_food;
}

static void place_food_after_eating(SnakeGame *game, int eaten_food_index, SnakeFoodType eaten_type)
{
    SnakeFoodType next_type = SNAKE_FOOD_NORMAL;
    SnakeFood kept_foods[SNAKE_GAME_FOOD_COUNT];
    int kept_food_count = 0;

    for (int i = 0; i < game->food_count; ++i) {
        if (i != eaten_food_index) {
            kept_foods[kept_food_count] = game->foods[i];
            kept_food_count += 1;
        }
    }

    if (eaten_type == SNAKE_FOOD_NORMAL) {
        game->normal_foods_since_special += 1;

        if (game->normal_foods_since_special >= 5) {
            next_type = game->next_special_food_type;
            game->normal_foods_since_special = 0;
            game->next_special_food_type =
                game->next_special_food_type == SNAKE_FOOD_STAR ? SNAKE_FOOD_ICE : SNAKE_FOOD_STAR;
        }
    }

    /*
     * 特殊食物本身不计入“五个普通苹果”的计数。
     * 吃完星星或冰晶后，下一次新刷出的食物回到普通苹果。
     */
    const int target_food_count = random_food_count(game);
    const int kept_limit = target_food_count - 1;
    const int kept_to_copy = kept_food_count < kept_limit ? kept_food_count : kept_limit;

    game->food_count = 0;
    for (int i = 0; i < kept_to_copy; ++i) {
        append_kept_food(game, kept_foods[i]);
    }

    if (append_random_food(game, next_type)) {
        move_last_food_to_front(game);
    }

    while (game->food_count < target_food_count) {
        if (!append_random_food(game, SNAKE_FOOD_NORMAL)) {
            break;
        }
    }
}

static int score_for_food(SnakeFoodType type)
{
    switch (type) {
    case SNAKE_FOOD_NORMAL:
        return 10;
    case SNAKE_FOOD_STAR:
        return 50;
    case SNAKE_FOOD_ICE:
        return 20;
    }

    return 0;
}

bool snake_game_init(SnakeGame *game, int board_width, int board_height, uint32_t seed)
{
    if (game == NULL) {
        return false;
    }

    game->score = 0;
    game->is_game_over = false;
    game->death_reason = SNAKE_DEATH_NONE;
    game->rng_state = seed == 0u ? 1u : seed;
    game->food_count = 0;
    for (int i = 0; i < SNAKE_GAME_FOOD_COUNT; ++i) {
        game->foods[i].position = (SnakePoint) { 0, 0 };
        game->foods[i].type = SNAKE_FOOD_NORMAL;
        game->foods[i].color_index = 0;
    }
    game->normal_foods_since_special = 0;
    game->total_foods_eaten = 0;
    game->next_special_food_type = SNAKE_FOOD_STAR;
    game->ice_slow_remaining_seconds = 0.0f;
    game->snake_has_food_color = false;
    game->snake_color_food_type = SNAKE_FOOD_NORMAL;
    game->snake_color_index = 0;

    if (!snake_list_init_centered(&game->snake, board_width, board_height)) {
        return false;
    }

    if (!place_initial_foods(game)) {
        snake_list_destroy(&game->snake);
        return false;
    }

    return true;
}

void snake_game_destroy(SnakeGame *game)
{
    if (game == NULL) {
        return;
    }

    snake_list_destroy(&game->snake);
    game->score = 0;
    game->is_game_over = false;
    game->death_reason = SNAKE_DEATH_NONE;
    game->food_count = 0;
    for (int i = 0; i < SNAKE_GAME_FOOD_COUNT; ++i) {
        game->foods[i].position = (SnakePoint) { 0, 0 };
        game->foods[i].type = SNAKE_FOOD_NORMAL;
        game->foods[i].color_index = 0;
    }
    game->normal_foods_since_special = 0;
    game->total_foods_eaten = 0;
    game->next_special_food_type = SNAKE_FOOD_STAR;
    game->ice_slow_remaining_seconds = 0.0f;
    game->snake_has_food_color = false;
    game->snake_color_food_type = SNAKE_FOOD_NORMAL;
    game->snake_color_index = 0;
}

bool snake_game_set_food(SnakeGame *game, SnakePoint position, SnakeFoodType type)
{
    return snake_game_set_food_at(game, 0, position, type);
}

bool snake_game_set_food_at(SnakeGame *game, int food_index, SnakePoint position, SnakeFoodType type)
{
    if (game == NULL || !food_type_is_valid(type) || !point_is_inside_board(game, position)) {
        return false;
    }

    if (!food_index_is_valid(food_index) || food_index >= game->food_count) {
        return false;
    }

    if (snake_list_contains(&game->snake, position)) {
        return false;
    }

    if (point_overlaps_foods(game, position, food_index)) {
        return false;
    }

    game->foods[food_index].position = position;
    game->foods[food_index].type = type;
    if (!food_color_index_is_valid(game->foods[food_index].color_index)
        || color_overlaps_foods(game, game->foods[food_index].color_index, food_index)) {
        game->foods[food_index].color_index = next_unused_food_color_index(game, food_index);
    }
    return true;
}

bool snake_game_request_direction(SnakeGame *game, SnakeDirection direction)
{
    if (game == NULL || game->is_game_over) {
        return false;
    }

    return snake_list_request_direction(&game->snake, direction);
}

SnakeTickResult snake_game_tick(SnakeGame *game)
{
    if (game == NULL || game->is_game_over) {
        return SNAKE_TICK_GAME_OVER;
    }

    const SnakePoint next_position = next_head_position(&game->snake);
    const int eaten_food_index = food_index_at_position(game, next_position);
    const bool will_eat_food = eaten_food_index >= 0;
    const SnakeFoodType eaten_type = will_eat_food ? game->foods[eaten_food_index].type : SNAKE_FOOD_NORMAL;
    const int eaten_color_index = will_eat_food ? game->foods[eaten_food_index].color_index : 0;
    const SnakeStepResult step_result = snake_list_step(&game->snake, will_eat_food);

    switch (step_result) {
    case SNAKE_STEP_MOVED:
        return SNAKE_TICK_MOVED;
    case SNAKE_STEP_GREW:
        game->score += score_for_food(eaten_type);
        game->total_foods_eaten += 1;
        game->snake_has_food_color = true;
        game->snake_color_food_type = eaten_type;
        game->snake_color_index = eaten_color_index;
        if (eaten_type == SNAKE_FOOD_ICE) {
            game->ice_slow_remaining_seconds = 5.0f;
        }
        place_food_after_eating(game, eaten_food_index, eaten_type);
        return SNAKE_TICK_ATE_FOOD;
    case SNAKE_STEP_HIT_WALL:
        game->is_game_over = true;
        game->death_reason = SNAKE_DEATH_WALL;
        return SNAKE_TICK_GAME_OVER;
    case SNAKE_STEP_HIT_SELF:
        game->is_game_over = true;
        game->death_reason = SNAKE_DEATH_SELF;
        return SNAKE_TICK_GAME_OVER;
    }

    game->is_game_over = true;
    game->death_reason = SNAKE_DEATH_SELF;
    return SNAKE_TICK_GAME_OVER;
}

void snake_game_update_timers(SnakeGame *game, float delta_seconds, bool paused)
{
    if (game == NULL || paused || delta_seconds <= 0.0f) {
        return;
    }

    if (game->ice_slow_remaining_seconds > 0.0f) {
        game->ice_slow_remaining_seconds -= delta_seconds;
        if (game->ice_slow_remaining_seconds < 0.0f) {
            game->ice_slow_remaining_seconds = 0.0f;
        }
    }
}

float snake_game_current_move_interval(const SnakeGame *game)
{
    if (game == NULL) {
        return 0.18f;
    }

    /*
     * 速度曲线：初始 180ms/步，每吃 3 个食物快 10ms，最低 90ms/步。
     * 冰晶生效时仅临时把当前间隔放大 30%，5 秒后恢复到按进食数计算的速度。
     */
    const int speed_steps = game->total_foods_eaten / 3;
    float interval = 0.18f - (float)speed_steps * 0.01f;
    if (interval < 0.09f) {
        interval = 0.09f;
    }

    if (game->ice_slow_remaining_seconds > 0.0f) {
        interval *= 1.3f;
    }

    return interval;
}
