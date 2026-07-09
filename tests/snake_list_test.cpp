#include <gtest/gtest.h>

extern "C" {
#include "snake_game/snake_list.h"
}

namespace {

SnakePoint Point(int x, int y)
{
    return SnakePoint{ x, y };
}

void ExpectPoint(SnakePoint actual, int x, int y)
{
    EXPECT_EQ(actual.x, x);
    EXPECT_EQ(actual.y, y);
}

void ExpectListPositions(const SnakeList *snake, const SnakePoint *expected, size_t count)
{
    ASSERT_NE(snake->head, nullptr);
    ASSERT_EQ(snake->length, count);

    const SnakeNode *node = snake->head;
    for (size_t i = 0; i < count; ++i) {
        ASSERT_NE(node, nullptr);
        ExpectPoint(node->position, expected[i].x, expected[i].y);
        node = node->next;
    }

    EXPECT_EQ(node, snake->head);
}

}  // namespace

TEST(SnakeList, InitializesCenteredLengthThreeAndRight)
{
    SnakeList snake{};

    ASSERT_TRUE(snake_list_init_centered(&snake, 32, 24));

    EXPECT_EQ(snake.length, 3u);
    EXPECT_EQ(snake.direction, SNAKE_DIRECTION_RIGHT);
    EXPECT_EQ(snake.queued_direction, SNAKE_DIRECTION_RIGHT);
    ASSERT_NE(snake.head, nullptr);
    ASSERT_NE(snake.tail, nullptr);
    ExpectPoint(snake.head->position, 17, 12);
    ExpectPoint(snake.tail->position, 15, 12);

    snake_list_destroy(&snake);
}

TEST(SnakeList, MaintainsBidirectionalCircularLinks)
{
    SnakeList snake{};
    ASSERT_TRUE(snake_list_init_centered(&snake, 32, 24));

    ASSERT_EQ(snake.head->prev, snake.tail);
    ASSERT_EQ(snake.tail->next, snake.head);

    const SnakeNode *node = snake.head;
    for (size_t i = 0; i < snake.length; ++i) {
        ASSERT_NE(node->next, nullptr);
        ASSERT_NE(node->prev, nullptr);
        EXPECT_EQ(node->next->prev, node);
        EXPECT_EQ(node->prev->next, node);
        node = node->next;
    }
    EXPECT_EQ(node, snake.head);

    snake_list_destroy(&snake);
}

TEST(SnakeList, MoveWithoutGrowthAddsHeadAndDeletesTail)
{
    SnakeList snake{};
    ASSERT_TRUE(snake_list_init_centered(&snake, 32, 24));

    EXPECT_EQ(snake_list_step(&snake, false), SNAKE_STEP_MOVED);

    const SnakePoint expected[] = { Point(18, 12), Point(17, 12), Point(16, 12) };
    ExpectListPositions(&snake, expected, 3);
    EXPECT_FALSE(snake_list_contains(&snake, Point(15, 12)));

    snake_list_destroy(&snake);
}

TEST(SnakeList, MoveWithGrowthAddsHeadAndKeepsTail)
{
    SnakeList snake{};
    ASSERT_TRUE(snake_list_init_centered(&snake, 32, 24));

    EXPECT_EQ(snake_list_step(&snake, true), SNAKE_STEP_GREW);

    const SnakePoint expected[] = { Point(18, 12), Point(17, 12), Point(16, 12), Point(15, 12) };
    ExpectListPositions(&snake, expected, 4);

    snake_list_destroy(&snake);
}

TEST(SnakeList, RejectsImmediateOppositeDirection)
{
    SnakeList snake{};
    ASSERT_TRUE(snake_list_init_centered(&snake, 32, 24));

    EXPECT_FALSE(snake_list_request_direction(&snake, SNAKE_DIRECTION_LEFT));
    EXPECT_EQ(snake.queued_direction, SNAKE_DIRECTION_RIGHT);
    EXPECT_TRUE(snake_list_request_direction(&snake, SNAKE_DIRECTION_UP));

    EXPECT_EQ(snake_list_step(&snake, false), SNAKE_STEP_MOVED);
    EXPECT_EQ(snake.direction, SNAKE_DIRECTION_UP);
    ExpectPoint(snake.head->position, 17, 11);

    snake_list_destroy(&snake);
}

TEST(SnakeList, UsesLastLegalDirectionBeforeStep)
{
    SnakeList snake{};
    ASSERT_TRUE(snake_list_init_centered(&snake, 32, 24));

    EXPECT_TRUE(snake_list_request_direction(&snake, SNAKE_DIRECTION_UP));
    EXPECT_TRUE(snake_list_request_direction(&snake, SNAKE_DIRECTION_DOWN));

    EXPECT_EQ(snake_list_step(&snake, false), SNAKE_STEP_MOVED);
    EXPECT_EQ(snake.direction, SNAKE_DIRECTION_DOWN);
    ExpectPoint(snake.head->position, 17, 13);

    snake_list_destroy(&snake);
}

TEST(SnakeList, AllowsMovingIntoTailWhenTailWillLeave)
{
    const SnakePoint points[] = { Point(1, 1), Point(2, 1), Point(2, 2), Point(1, 2) };
    SnakeList snake{};
    ASSERT_TRUE(snake_list_init_from_points(&snake, 4, 4, points, 4, SNAKE_DIRECTION_DOWN));

    EXPECT_EQ(snake_list_step(&snake, false), SNAKE_STEP_MOVED);

    const SnakePoint expected[] = { Point(1, 2), Point(1, 1), Point(2, 1), Point(2, 2) };
    ExpectListPositions(&snake, expected, 4);

    snake_list_destroy(&snake);
}

TEST(SnakeList, HitsSelfWhenEnteringBodyThatIsNotTail)
{
    const SnakePoint points[] = { Point(1, 1), Point(2, 1), Point(2, 2), Point(1, 2) };
    SnakeList snake{};
    ASSERT_TRUE(snake_list_init_from_points(&snake, 4, 4, points, 4, SNAKE_DIRECTION_RIGHT));

    EXPECT_EQ(snake_list_step(&snake, false), SNAKE_STEP_HIT_SELF);
    EXPECT_EQ(snake.length, 4u);
    ExpectPoint(snake.head->position, 1, 1);

    snake_list_destroy(&snake);
}

TEST(SnakeList, HitsWallWhenLeavingBoard)
{
    const SnakePoint points[] = { Point(31, 0), Point(30, 0), Point(29, 0) };
    SnakeList snake{};
    ASSERT_TRUE(snake_list_init_from_points(&snake, 32, 24, points, 3, SNAKE_DIRECTION_RIGHT));

    EXPECT_EQ(snake_list_step(&snake, false), SNAKE_STEP_HIT_WALL);
    EXPECT_EQ(snake.length, 3u);
    ExpectPoint(snake.head->position, 31, 0);

    snake_list_destroy(&snake);
}

TEST(SnakeList, DestroyResetsStateAndIsIdempotent)
{
    SnakeList snake{};
    ASSERT_TRUE(snake_list_init_centered(&snake, 32, 24));

    snake_list_destroy(&snake);
    EXPECT_EQ(snake.head, nullptr);
    EXPECT_EQ(snake.tail, nullptr);
    EXPECT_EQ(snake.length, 0u);

    snake_list_destroy(&snake);
    EXPECT_EQ(snake.head, nullptr);
    EXPECT_EQ(snake.tail, nullptr);
    EXPECT_EQ(snake.length, 0u);
}
