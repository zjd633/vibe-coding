#ifndef SNAKE_GAME_HIGH_SCORE_H
#define SNAKE_GAME_HIGH_SCORE_H

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

int snake_high_score_load_or_zero(const char *path);
bool snake_high_score_save(const char *path, int score);
bool snake_high_score_save_if_greater(const char *path, int candidate_score, int *stored_score);

#ifdef __cplusplus
}
#endif

#endif
