#include "snake_game/high_score.h"

#include <stdio.h>

int snake_high_score_load_or_zero(const char *path)
{
    if (path == NULL) {
        return 0;
    }

    FILE *file = fopen(path, "r");
    if (file == NULL) {
        return 0;
    }

    int score = 0;
    const int matched = fscanf(file, "%d", &score);
    fclose(file);

    if (matched != 1 || score < 0) {
        return 0;
    }

    return score;
}

bool snake_high_score_save(const char *path, int score)
{
    if (path == NULL || score < 0) {
        return false;
    }

    FILE *file = fopen(path, "w");
    if (file == NULL) {
        return false;
    }

    /*
     * 最高分文件只存一个整数。
     * 这种格式方便教学，也便于玩家手动检查本地保存结果。
     */
    const int written = fprintf(file, "%d\n", score);
    const int closed = fclose(file);
    return written > 0 && closed == 0;
}

bool snake_high_score_save_if_greater(const char *path, int candidate_score, int *stored_score)
{
    if (path == NULL || candidate_score < 0) {
        return false;
    }

    int current_score = snake_high_score_load_or_zero(path);
    if (candidate_score > current_score) {
        if (!snake_high_score_save(path, candidate_score)) {
            return false;
        }
        current_score = candidate_score;
    }

    if (stored_score != NULL) {
        *stored_score = current_score;
    }

    return true;
}
