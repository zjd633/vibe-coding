#include <gtest/gtest.h>

extern "C" {
#include "snake_game/app_ui.h"
}

TEST(AppUi, StartButtonHitboxMatchesDrawnButton)
{
    EXPECT_TRUE(snake_ui_is_start_button_hit(480, 359));
    EXPECT_TRUE(snake_ui_is_start_button_hit(378, 330));
    EXPECT_TRUE(snake_ui_is_start_button_hit(581, 387));

    EXPECT_FALSE(snake_ui_is_start_button_hit(377, 359));
    EXPECT_FALSE(snake_ui_is_start_button_hit(480, 329));
    EXPECT_FALSE(snake_ui_is_start_button_hit(582, 388));
    EXPECT_FALSE(snake_ui_is_start_button_hit(480, 389));
}

TEST(AppUi, ResumeButtonHitboxMatchesDrawnButton)
{
    EXPECT_TRUE(snake_ui_is_resume_button_hit(480, 404));
    EXPECT_FALSE(snake_ui_is_resume_button_hit(391, 404));
    EXPECT_FALSE(snake_ui_is_resume_button_hit(480, 429));
}

TEST(AppUi, RestartButtonHitboxMatchesDrawnButton)
{
    EXPECT_TRUE(snake_ui_is_restart_button_hit(480, 497));
    EXPECT_FALSE(snake_ui_is_restart_button_hit(353, 497));
    EXPECT_FALSE(snake_ui_is_restart_button_hit(480, 527));
}

TEST(AppUi, DebugNodeRoleNamesHeadTailAndBody)
{
    EXPECT_STREQ(snake_ui_debug_node_role(0, 4), "Head");
    EXPECT_STREQ(snake_ui_debug_node_role(1, 4), "Node");
    EXPECT_STREQ(snake_ui_debug_node_role(2, 4), "Node");
    EXPECT_STREQ(snake_ui_debug_node_role(3, 4), "Tail");
}

TEST(AppUi, DebugNodeRoleHandlesSingleNodeAsHead)
{
    EXPECT_STREQ(snake_ui_debug_node_role(0, 1), "Head");
    EXPECT_STREQ(snake_ui_debug_node_role(1, 1), "Node");
}
