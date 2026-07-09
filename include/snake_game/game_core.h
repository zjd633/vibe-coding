#ifndef SNAKE_GAME_GAME_CORE_H
#define SNAKE_GAME_GAME_CORE_H

#include "snake_game/snake_list.h"

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum SnakeFoodType {
    SNAKE_FOOD_NORMAL = 0,
    SNAKE_FOOD_STAR,
    SNAKE_FOOD_ICE
} SnakeFoodType;

typedef enum SnakeDeathReason {
    SNAKE_DEATH_NONE = 0,
    SNAKE_DEATH_WALL,
    SNAKE_DEATH_SELF
} SnakeDeathReason;

typedef enum SnakeTickResult {
    SNAKE_TICK_MOVED = 0,
    SNAKE_TICK_ATE_FOOD,
    SNAKE_TICK_GAME_OVER
} SnakeTickResult;

#define SNAKE_GAME_MIN_FOOD_COUNT 5
#define SNAKE_GAME_FOOD_COUNT 10
#define SNAKE_GAME_FOOD_COLOR_COUNT 10

typedef struct SnakeFood {
    SnakePoint position;
    SnakeFoodType type;
    int color_index;
} SnakeFood;

typedef struct SnakeGame {
    SnakeList snake;
    SnakeFood foods[SNAKE_GAME_FOOD_COUNT];
    int food_count;
    int score;
    bool is_game_over;
    SnakeDeathReason death_reason;
    uint32_t rng_state;
    int normal_foods_since_special;
    int total_foods_eaten;
    SnakeFoodType next_special_food_type;
    float ice_slow_remaining_seconds;
    bool snake_has_food_color;
    SnakeFoodType snake_color_food_type;
    int snake_color_index;
} SnakeGame;

bool snake_game_init(SnakeGame *game, int board_width, int board_height, uint32_t seed);
void snake_game_destroy(SnakeGame *game);

bool snake_game_set_food(SnakeGame *game, SnakePoint position, SnakeFoodType type);
bool snake_game_set_food_at(SnakeGame *game, int food_index, SnakePoint position, SnakeFoodType type);
bool snake_game_request_direction(SnakeGame *game, SnakeDirection direction);
SnakeTickResult snake_game_tick(SnakeGame *game);
void snake_game_update_timers(SnakeGame *game, float delta_seconds, bool paused);
float snake_game_current_move_interval(const SnakeGame *game);

#ifdef __cplusplus
}
#endif

#endif
