#include <gtest/gtest.h>

#include <cstdio>
#include <fstream>
#include <string>

extern "C" {
#include "snake_game/high_score.h"
}

namespace {

std::string TempScorePath(const char *name)
{
    return std::string(name);
}

void RemoveFile(const std::string &path)
{
    std::remove(path.c_str());
}

}  // namespace

TEST(HighScore, MissingFileLoadsZero)
{
    const std::string path = TempScorePath("missing_high_score.txt");
    RemoveFile(path);

    EXPECT_EQ(snake_high_score_load_or_zero(path.c_str()), 0);
}

TEST(HighScore, SavesAndLoadsScore)
{
    const std::string path = TempScorePath("save_load_high_score.txt");
    RemoveFile(path);

    ASSERT_TRUE(snake_high_score_save(path.c_str(), 120));
    EXPECT_EQ(snake_high_score_load_or_zero(path.c_str()), 120);

    RemoveFile(path);
}

TEST(HighScore, InvalidFileLoadsZero)
{
    const std::string path = TempScorePath("invalid_high_score.txt");
    {
        std::ofstream file(path);
        file << "not-a-number";
    }

    EXPECT_EQ(snake_high_score_load_or_zero(path.c_str()), 0);

    RemoveFile(path);
}

TEST(HighScore, SaveIfGreaterOnlyOverwritesWhenScoreImproves)
{
    const std::string path = TempScorePath("greater_high_score.txt");
    RemoveFile(path);

    int stored_score = -1;
    ASSERT_TRUE(snake_high_score_save(path.c_str(), 100));
    EXPECT_TRUE(snake_high_score_save_if_greater(path.c_str(), 80, &stored_score));
    EXPECT_EQ(stored_score, 100);
    EXPECT_EQ(snake_high_score_load_or_zero(path.c_str()), 100);

    EXPECT_TRUE(snake_high_score_save_if_greater(path.c_str(), 140, &stored_score));
    EXPECT_EQ(stored_score, 140);
    EXPECT_EQ(snake_high_score_load_or_zero(path.c_str()), 140);

    RemoveFile(path);
}
