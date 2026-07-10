#include <gtest/gtest.h>

extern "C" {
#include "snake_game/game_core.h"
}

namespace {

SnakePoint Point(int x, int y)
{
    return SnakePoint{ x, y };
}

bool PointsEqual(SnakePoint a, SnakePoint b)
{
    return a.x == b.x && a.y == b.y;
}

bool FoodPositionAlreadyUsed(const SnakeGame& game, int limit, SnakePoint position)
{
    for (int i = 0; i < limit; ++i) {
        if (PointsEqual(game.foods[i].position, position)) {
            return true;
        }
    }

    return false;
}

void ForceFoodAtSlotZero(SnakeGame& game, SnakePoint position, SnakeFoodType type)
{
    game.foods[0].position = position;
    game.foods[0].type = type;
    game.foods[0].color_index = 0;

    int candidate_index = 0;
    for (int i = 1; i < game.food_count; ++i) {
        game.foods[i].color_index = i;
        while (candidate_index < game.snake.board_width * game.snake.board_height) {
            SnakePoint candidate = Point(
                candidate_index % game.snake.board_width,
                candidate_index / game.snake.board_width
            );
            candidate_index += 1;

            if (!PointsEqual(candidate, position)
                && !snake_list_contains(&game.snake, candidate)
                && !FoodPositionAlreadyUsed(game, i, candidate)) {
                game.foods[i].position = candidate;
                break;
            }
        }
    }
}

void ExpectFoodsInsideBoardAndNotOverlappingSnake(const SnakeGame& game, int board_width, int board_height)
{
    EXPECT_GE(game.food_count, 5);
    EXPECT_LE(game.food_count, SNAKE_GAME_FOOD_COUNT);

    for (int i = 0; i < game.food_count; ++i) {
        EXPECT_GE(game.foods[i].position.x, 0);
        EXPECT_LT(game.foods[i].position.x, board_width);
        EXPECT_GE(game.foods[i].position.y, 0);
        EXPECT_LT(game.foods[i].position.y, board_height);
        EXPECT_FALSE(snake_list_contains(&game.snake, game.foods[i].position));
        EXPECT_GE(game.foods[i].color_index, 0);
        EXPECT_LT(game.foods[i].color_index, SNAKE_GAME_FOOD_COLOR_COUNT);

        for (int j = i + 1; j < game.food_count; ++j) {
            EXPECT_FALSE(game.foods[i].position.x == game.foods[j].position.x
                && game.foods[i].position.y == game.foods[j].position.y);
            EXPECT_NE(game.foods[i].color_index, game.foods[j].color_index);
        }
    }
}

}  // namespace

TEST(GameCore, InitializesWithNormalFoodOutsideSnake)
{
    SnakeGame game{};

    ASSERT_TRUE(snake_game_init(&game, 32, 24, 1234u));

    EXPECT_EQ(game.score, 0);
    EXPECT_FALSE(game.is_game_over);
    EXPECT_EQ(game.death_reason, SNAKE_DEATH_NONE);
    ExpectFoodsInsideBoardAndNotOverlappingSnake(game, 32, 24);
    for (int i = 0; i < game.food_count; ++i) {
        EXPECT_EQ(game.foods[i].type, SNAKE_FOOD_NORMAL);
    }

    snake_game_destroy(&game);
}

TEST(GameCore, FoodCountVariesAcrossSeeds)
{
    int first_count = -1;
    bool saw_different_count = false;

    for (uint32_t seed = 1u; seed <= 80u; ++seed) {
        SnakeGame game{};
        ASSERT_TRUE(snake_game_init(&game, 32, 24, seed));
        ExpectFoodsInsideBoardAndNotOverlappingSnake(game, 32, 24);

        if (first_count < 0) {
            first_count = game.food_count;
        } else if (game.food_count != first_count) {
            saw_different_count = true;
        }

        snake_game_destroy(&game);
    }

    EXPECT_TRUE(saw_different_count);
}

TEST(GameCore, EatingFoodRerollsActiveFoodCount)
{
    bool saw_count_change_after_eating = false;

    for (uint32_t seed = 1u; seed <= 120u; ++seed) {
        SnakeGame game{};
        ASSERT_TRUE(snake_game_init(&game, 32, 24, seed));
        ForceFoodAtSlotZero(game, Point(18, 12), SNAKE_FOOD_NORMAL);

        const int count_before_tick = game.food_count;
        EXPECT_EQ(snake_game_tick(&game), SNAKE_TICK_ATE_FOOD);
        ExpectFoodsInsideBoardAndNotOverlappingSnake(game, 32, 24);

        if (game.food_count != count_before_tick) {
            saw_count_change_after_eating = true;
        }

        snake_game_destroy(&game);
    }

    EXPECT_TRUE(saw_count_change_after_eating);
}

TEST(GameCore, EatingFoodKeepsFoodsValidAfterRandomRefresh)
{
    SnakeGame game{};
    ASSERT_TRUE(snake_game_init(&game, 32, 24, 1234u));
    ForceFoodAtSlotZero(game, Point(18, 12), SNAKE_FOOD_NORMAL);

    EXPECT_EQ(snake_game_tick(&game), SNAKE_TICK_ATE_FOOD);

    EXPECT_EQ(game.score, 10);
    EXPECT_EQ(game.snake.length, 4u);
    ExpectFoodsInsideBoardAndNotOverlappingSnake(game, 32, 24);

    snake_game_destroy(&game);
}

TEST(GameCore, SnakeColorFollowsEatenFoodDisplayColor)
{
    SnakeGame game{};
    ASSERT_TRUE(snake_game_init(&game, 32, 24, 1234u));
    ForceFoodAtSlotZero(game, Point(18, 12), SNAKE_FOOD_NORMAL);
    game.foods[0].color_index = 7;

    EXPECT_FALSE(game.snake_has_food_color);
    EXPECT_EQ(snake_game_tick(&game), SNAKE_TICK_ATE_FOOD);

    EXPECT_TRUE(game.snake_has_food_color);
    EXPECT_EQ(game.snake_color_index, 7);

    snake_game_destroy(&game);
}

TEST(GameCore, EatingNormalAppleScoresAndGrows)
{
    SnakeGame game{};
    ASSERT_TRUE(snake_game_init(&game, 32, 24, 1234u));
    ForceFoodAtSlotZero(game, Point(18, 12), SNAKE_FOOD_NORMAL);

    EXPECT_FALSE(game.snake_has_food_color);
    EXPECT_EQ(snake_game_tick(&game), SNAKE_TICK_ATE_FOOD);

    EXPECT_EQ(game.score, 10);
    EXPECT_EQ(game.snake.length, 4u);
    EXPECT_EQ(game.snake.head->position.x, 18);
    EXPECT_EQ(game.snake.head->position.y, 12);
    EXPECT_TRUE(game.snake_has_food_color);
    EXPECT_EQ(game.snake_color_food_type, SNAKE_FOOD_NORMAL);
    EXPECT_FALSE(snake_list_contains(&game.snake, game.foods[0].position));

    snake_game_destroy(&game);
}

TEST(GameCore, SnakeColorFollowsTheLastEatenFoodType)
{
    SnakeGame game{};
    ASSERT_TRUE(snake_game_init(&game, 32, 24, 1234u));

    ForceFoodAtSlotZero(game, Point(18, 12), SNAKE_FOOD_STAR);
    EXPECT_EQ(snake_game_tick(&game), SNAKE_TICK_ATE_FOOD);
    EXPECT_TRUE(game.snake_has_food_color);
    EXPECT_EQ(game.snake_color_food_type, SNAKE_FOOD_STAR);

    ForceFoodAtSlotZero(game, Point(19, 12), SNAKE_FOOD_ICE);
    EXPECT_EQ(snake_game_tick(&game), SNAKE_TICK_ATE_FOOD);
    EXPECT_TRUE(game.snake_has_food_color);
    EXPECT_EQ(game.snake_color_food_type, SNAKE_FOOD_ICE);

    snake_game_destroy(&game);
}

TEST(GameCore, EveryFiveNormalApplesSpawnsAlternatingSpecialFood)
{
    SnakeGame game{};
    ASSERT_TRUE(snake_game_init(&game, 32, 24, 1234u));

    for (int i = 0; i < 5; ++i) {
        ForceFoodAtSlotZero(game, Point(18 + i, 12), SNAKE_FOOD_NORMAL);
        EXPECT_EQ(snake_game_tick(&game), SNAKE_TICK_ATE_FOOD);
    }

    EXPECT_EQ(game.score, 50);
    EXPECT_EQ(game.snake.length, 8u);
    EXPECT_EQ(game.foods[0].type, SNAKE_FOOD_STAR);

    ForceFoodAtSlotZero(game, Point(23, 12), SNAKE_FOOD_STAR);
    EXPECT_EQ(snake_game_tick(&game), SNAKE_TICK_ATE_FOOD);
    EXPECT_EQ(game.score, 100);
    EXPECT_EQ(game.snake.length, 9u);
    EXPECT_EQ(game.foods[0].type, SNAKE_FOOD_NORMAL);

    for (int i = 0; i < 5; ++i) {
        ForceFoodAtSlotZero(game, Point(24 + i, 12), SNAKE_FOOD_NORMAL);
        EXPECT_EQ(snake_game_tick(&game), SNAKE_TICK_ATE_FOOD);
    }

    EXPECT_EQ(game.score, 150);
    EXPECT_EQ(game.foods[0].type, SNAKE_FOOD_ICE);

    snake_game_destroy(&game);
}

TEST(GameCore, IceFoodScoresGrowsAndSlowsForFiveSeconds)
{
    SnakeGame game{};
    ASSERT_TRUE(snake_game_init(&game, 32, 24, 1234u));
    ForceFoodAtSlotZero(game, Point(18, 12), SNAKE_FOOD_ICE);

    const float normal_interval = snake_game_current_move_interval(&game);
    EXPECT_EQ(snake_game_tick(&game), SNAKE_TICK_ATE_FOOD);

    EXPECT_EQ(game.score, 20);
    EXPECT_EQ(game.snake.length, 4u);
    EXPECT_FLOAT_EQ(game.ice_slow_remaining_seconds, 5.0f);
    EXPECT_NEAR(snake_game_current_move_interval(&game), normal_interval * 1.3f, 0.0001f);

    snake_game_update_timers(&game, 2.0f, false);
    EXPECT_FLOAT_EQ(game.ice_slow_remaining_seconds, 3.0f);
    EXPECT_NEAR(snake_game_current_move_interval(&game), normal_interval * 1.3f, 0.0001f);

    snake_game_update_timers(&game, 3.0f, false);
    EXPECT_FLOAT_EQ(game.ice_slow_remaining_seconds, 0.0f);
    EXPECT_NEAR(snake_game_current_move_interval(&game), normal_interval, 0.0001f);

    snake_game_destroy(&game);
}

TEST(GameCore, PauseFreezesIceSlowTimer)
{
    SnakeGame game{};
    ASSERT_TRUE(snake_game_init(&game, 32, 24, 1234u));
    ForceFoodAtSlotZero(game, Point(18, 12), SNAKE_FOOD_ICE);
    EXPECT_EQ(snake_game_tick(&game), SNAKE_TICK_ATE_FOOD);

    snake_game_update_timers(&game, 2.0f, true);
    EXPECT_FLOAT_EQ(game.ice_slow_remaining_seconds, 5.0f);

    snake_game_update_timers(&game, 2.0f, false);
    EXPECT_FLOAT_EQ(game.ice_slow_remaining_seconds, 3.0f);

    snake_game_destroy(&game);
}

TEST(GameCore, MoveIntervalAcceleratesWithFoodAndCapsAtNinetyMilliseconds)
{
    SnakeGame game{};
    ASSERT_TRUE(snake_game_init(&game, 32, 24, 1234u));

    EXPECT_NEAR(snake_game_current_move_interval(&game), 0.18f, 0.0001f);

    for (int i = 0; i < 3; ++i) {
        ForceFoodAtSlotZero(game, Point(18 + i, 12), SNAKE_FOOD_NORMAL);
        EXPECT_EQ(snake_game_tick(&game), SNAKE_TICK_ATE_FOOD);
    }
    EXPECT_NEAR(snake_game_current_move_interval(&game), 0.17f, 0.0001f);

    for (int i = 0; i < 27; ++i) {
        game.total_foods_eaten = i + 4;
    }
    EXPECT_NEAR(snake_game_current_move_interval(&game), 0.09f, 0.0001f);

    snake_game_destroy(&game);
}

TEST(GameCore, WallCollisionEndsGame)
{
    SnakeGame game{};
    ASSERT_TRUE(snake_game_init(&game, 32, 24, 1234u));

    const SnakePoint points[] = { Point(31, 0), Point(30, 0), Point(29, 0) };
    snake_list_destroy(&game.snake);
    ASSERT_TRUE(snake_list_init_from_points(&game.snake, 32, 24, points, 3, SNAKE_DIRECTION_RIGHT));
    ForceFoodAtSlotZero(game, Point(0, 0), SNAKE_FOOD_NORMAL);

    EXPECT_EQ(snake_game_tick(&game), SNAKE_TICK_GAME_OVER);
    EXPECT_TRUE(game.is_game_over);
    EXPECT_EQ(game.death_reason, SNAKE_DEATH_WALL);
    EXPECT_EQ(game.score, 0);

    snake_game_destroy(&game);
}

TEST(GameCore, SelfCollisionEndsGame)
{
    SnakeGame game{};
    ASSERT_TRUE(snake_game_init(&game, 4, 4, 1234u));

    const SnakePoint points[] = { Point(1, 1), Point(2, 1), Point(2, 2), Point(1, 2) };
    snake_list_destroy(&game.snake);
    ASSERT_TRUE(snake_list_init_from_points(&game.snake, 4, 4, points, 4, SNAKE_DIRECTION_RIGHT));
    ForceFoodAtSlotZero(game, Point(0, 0), SNAKE_FOOD_NORMAL);

    EXPECT_EQ(snake_game_tick(&game), SNAKE_TICK_GAME_OVER);
    EXPECT_TRUE(game.is_game_over);
    EXPECT_EQ(game.death_reason, SNAKE_DEATH_SELF);

    snake_game_destroy(&game);
}
