#include "snake_game/app_config.h"
#include "snake_game/app_ui.h"
#include "snake_game/game_core.h"
#include "snake_game/high_score.h"

#include "raylib.h"

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef enum ScreenState {
    SCREEN_START = 0,
    SCREEN_PLAYING,
    SCREEN_PAUSED,
    SCREEN_GAME_OVER
} ScreenState;

typedef struct AppSounds {
    Sound eat;
    Sound star;
    Sound ice;
    Sound game_over;
    Sound click;
    bool ready;
} AppSounds;

typedef struct AppState {
    ScreenState screen;
    SnakeGame game;
    bool game_ready;
    int high_score;
    float move_accumulator;
    float eat_flash_timer;
    float high_score_flash_timer;
    SnakeFoodType last_eaten_food;
    int last_eaten_color_index;
    bool debug_overlay_enabled;
    AppSounds sounds;
} AppState;

static const char *HIGH_SCORE_FILE_PATH = "snake_high_score.txt";
static const float EAT_FLASH_SECONDS = 0.18f;
static const float HIGH_SCORE_FLASH_SECONDS = 1.0f;

static const Color COLOR_BACKGROUND = { 13, 20, 28, 255 };
static const Color COLOR_PANEL = { 24, 35, 46, 255 };
static const Color COLOR_BOARD = { 17, 27, 36, 255 };
static const Color COLOR_BOARD_BORDER = { 71, 101, 113, 255 };
static const Color COLOR_GRID = { 38, 54, 66, 255 };
static const Color COLOR_TEXT = { 226, 238, 241, 255 };
static const Color COLOR_MUTED = { 130, 153, 160, 255 };
static const Color COLOR_GREEN_HEAD = { 70, 224, 157, 255 };
static const Color COLOR_GREEN_BODY = { 41, 185, 135, 255 };
static const Color COLOR_SHADOW = { 4, 9, 13, 150 };
static const Color COLOR_APPLE = { 235, 78, 86, 255 };
static const Color COLOR_STAR = { 255, 203, 82, 255 };
static const Color COLOR_ICE = { 81, 174, 255, 255 };
static const Color COLOR_FOOD_PALETTE[SNAKE_GAME_FOOD_COLOR_COUNT] = {
    { 235, 78, 86, 255 },
    { 255, 203, 82, 255 },
    { 81, 174, 255, 255 },
    { 118, 230, 126, 255 },
    { 248, 126, 255, 255 },
    { 255, 145, 83, 255 },
    { 101, 242, 223, 255 },
    { 190, 135, 255, 255 },
    { 245, 245, 112, 255 },
    { 255, 118, 170, 255 }
};

static Color ColorWithAlpha(Color color, unsigned char alpha)
{
    color.a = alpha;
    return color;
}

static Color BrightenColor(Color color, int amount)
{
    const int red = color.r + amount;
    const int green = color.g + amount;
    const int blue = color.b + amount;
    color.r = (unsigned char)(red > 255 ? 255 : red);
    color.g = (unsigned char)(green > 255 ? 255 : green);
    color.b = (unsigned char)(blue > 255 ? 255 : blue);
    return color;
}

static Color DarkenColor(Color color, float factor)
{
    color.r = (unsigned char)((float)color.r * factor);
    color.g = (unsigned char)((float)color.g * factor);
    color.b = (unsigned char)((float)color.b * factor);
    return color;
}

static Color FoodDisplayColor(int color_index)
{
    if (color_index < 0 || color_index >= SNAKE_GAME_FOOD_COLOR_COUNT) {
        return COLOR_APPLE;
    }

    return COLOR_FOOD_PALETTE[color_index];
}

static Color SnakeSegmentColor(const SnakeGame *game, bool is_head)
{
    if (game->snake_has_food_color) {
        return FoodDisplayColor(game->snake_color_index);
    }

    return is_head ? COLOR_GREEN_HEAD : COLOR_GREEN_BODY;
}

static Sound LoadToneSound(int frequency, int duration_ms, short amplitude)
{
    const unsigned int sample_rate = 22050;
    const unsigned int frame_count = (sample_rate * (unsigned int)duration_ms) / 1000u;
    short *samples = (short *)malloc(sizeof(short) * frame_count);
    if (samples == NULL) {
        return (Sound) { 0 };
    }

    for (unsigned int i = 0; i < frame_count; ++i) {
        const unsigned int phase = ((i * (unsigned int)frequency) / sample_rate) % 2u;
        const float fade = 1.0f - ((float)i / (float)frame_count);
        samples[i] = (short)((phase == 0u ? amplitude : -amplitude) * fade);
    }

    /*
     * 音效由代码生成，避免引入外部素材授权和路径问题。
     * LoadSoundFromWave 会把 Wave 数据送入音频缓冲，随后释放临时波形数据。
     */
    Wave wave = {
        .frameCount = frame_count,
        .sampleRate = sample_rate,
        .sampleSize = 16,
        .channels = 1,
        .data = samples
    };
    Sound sound = LoadSoundFromWave(wave);
    UnloadWave(wave);
    return sound;
}

static void InitAppSounds(AppState *app)
{
    InitAudioDevice();
    app->sounds.ready = IsAudioDeviceReady();
    if (!app->sounds.ready) {
        return;
    }

    app->sounds.eat = LoadToneSound(660, 70, 4500);
    app->sounds.star = LoadToneSound(880, 90, 5000);
    app->sounds.ice = LoadToneSound(440, 110, 4200);
    app->sounds.game_over = LoadToneSound(180, 180, 5000);
    app->sounds.click = LoadToneSound(520, 45, 3200);
}

static void UnloadAppSounds(AppState *app)
{
    if (!app->sounds.ready) {
        return;
    }

    UnloadSound(app->sounds.eat);
    UnloadSound(app->sounds.star);
    UnloadSound(app->sounds.ice);
    UnloadSound(app->sounds.game_over);
    UnloadSound(app->sounds.click);
    CloseAudioDevice();
    app->sounds.ready = false;
}

static void PlayAppSound(const AppState *app, Sound sound)
{
    if (app->sounds.ready) {
        PlaySound(sound);
    }
}

static void PlayFoodSound(const AppState *app, SnakeFoodType type)
{
    if (type == SNAKE_FOOD_STAR) {
        PlayAppSound(app, app->sounds.star);
    } else if (type == SNAKE_FOOD_ICE) {
        PlayAppSound(app, app->sounds.ice);
    } else {
        PlayAppSound(app, app->sounds.eat);
    }
}

static void DrawTextCentered(const char *text, int y, int font_size, Color color)
{
    const int width = MeasureText(text, font_size);
    DrawText(text, (SNAKE_WINDOW_WIDTH - width) / 2, y, font_size, color);
}

static void DrawTextInRectCentered(const char *text, Rectangle rect, int font_size, Color color)
{
    const int width = MeasureText(text, font_size);
    const int x = (int)(rect.x + (rect.width - (float)width) / 2.0f);
    const int y = (int)(rect.y + (rect.height - (float)font_size) / 2.0f - 1.0f);
    DrawText(text, x, y, font_size, color);
}

static void DrawArcadeButton(Rectangle rect, const char *label, int font_size, Color base_color, Color text_color)
{
    const bool hovered = CheckCollisionPointRec(GetMousePosition(), rect);
    const Color fill = hovered ? BrightenColor(base_color, 22) : base_color;
    const Rectangle shadow = { rect.x, rect.y + 6.0f, rect.width, rect.height };

    DrawRectangleRounded(shadow, 0.16f, 12, COLOR_SHADOW);
    DrawRectangleRounded(rect, 0.16f, 12, fill);
    DrawRectangleRounded(
        (Rectangle) { rect.x + 4.0f, rect.y + 4.0f, rect.width - 8.0f, 8.0f },
        0.45f,
        8,
        ColorWithAlpha(BrightenColor(fill, 42), 110)
    );
    DrawTextInRectCentered(label, rect, font_size, text_color);
}

static Rectangle CellRect(int column, int row)
{
    return (Rectangle) {
        (float)(SNAKE_BOARD_ORIGIN_X + column * SNAKE_CELL_SIZE),
        (float)(SNAKE_BOARD_ORIGIN_Y + row * SNAKE_CELL_SIZE),
        (float)SNAKE_CELL_SIZE,
        (float)SNAKE_CELL_SIZE
    };
}

static void DrawBoard(void)
{
    const Rectangle board = {
        (float)SNAKE_BOARD_ORIGIN_X,
        (float)SNAKE_BOARD_ORIGIN_Y,
        (float)SNAKE_BOARD_PIXEL_WIDTH,
        (float)SNAKE_BOARD_PIXEL_HEIGHT
    };

    DrawRectangleRounded(board, 0.02f, 8, COLOR_BOARD);
    DrawRectangleLinesEx(board, 2.0f, COLOR_BOARD_BORDER);
    DrawRectangle(
        SNAKE_BOARD_ORIGIN_X,
        SNAKE_BOARD_ORIGIN_Y,
        SNAKE_BOARD_PIXEL_WIDTH,
        3,
        ColorWithAlpha(BrightenColor(COLOR_BOARD_BORDER, 35), 140)
    );

    /*
     * 棋盘仍然只是渲染网格，真正的蛇身坐标来自纯 C 核心层。
     * 这样 raylib 不参与规则判断，gtest 可以独立覆盖游戏逻辑。
     */
    for (int column = 0; column <= SNAKE_BOARD_COLUMNS; ++column) {
        const int x = SNAKE_BOARD_ORIGIN_X + column * SNAKE_CELL_SIZE;
        DrawLine(x, SNAKE_BOARD_ORIGIN_Y, x, SNAKE_BOARD_ORIGIN_Y + SNAKE_BOARD_PIXEL_HEIGHT, COLOR_GRID);
    }

    for (int row = 0; row <= SNAKE_BOARD_ROWS; ++row) {
        const int y = SNAKE_BOARD_ORIGIN_Y + row * SNAKE_CELL_SIZE;
        DrawLine(SNAKE_BOARD_ORIGIN_X, y, SNAKE_BOARD_ORIGIN_X + SNAKE_BOARD_PIXEL_WIDTH, y, COLOR_GRID);
    }
}

static void DrawSnakeEyes(Rectangle head_rect, SnakeDirection direction)
{
    float eye_a_x = head_rect.x + 15.0f;
    float eye_a_y = head_rect.y + 9.0f;
    float eye_b_x = head_rect.x + 15.0f;
    float eye_b_y = head_rect.y + 16.0f;

    if (direction == SNAKE_DIRECTION_LEFT) {
        eye_a_x = head_rect.x + 9.0f;
        eye_b_x = head_rect.x + 9.0f;
    } else if (direction == SNAKE_DIRECTION_UP) {
        eye_a_x = head_rect.x + 9.0f;
        eye_a_y = head_rect.y + 9.0f;
        eye_b_x = head_rect.x + 16.0f;
        eye_b_y = head_rect.y + 9.0f;
    } else if (direction == SNAKE_DIRECTION_DOWN) {
        eye_a_x = head_rect.x + 9.0f;
        eye_a_y = head_rect.y + 16.0f;
        eye_b_x = head_rect.x + 16.0f;
        eye_b_y = head_rect.y + 16.0f;
    }

    DrawCircle((int)eye_a_x, (int)eye_a_y, 2.0f, COLOR_BACKGROUND);
    DrawCircle((int)eye_b_x, (int)eye_b_y, 2.0f, COLOR_BACKGROUND);
}

static void DrawSnake(const SnakeGame *game)
{
    if (game->snake.head == NULL) {
        return;
    }

    const SnakeNode *node = game->snake.head;
    for (size_t i = 0; i < game->snake.length; ++i) {
        const Rectangle cell = CellRect(node->position.x, node->position.y);
        const Rectangle segment = {
            cell.x + 3.0f,
            cell.y + 3.0f,
            cell.width - 6.0f,
            cell.height - 6.0f
        };
        const bool is_head = node == game->snake.head;
        const Rectangle shadow = {
            segment.x + 2.0f,
            segment.y + 2.0f,
            segment.width,
            segment.height
        };
        const Rectangle shine = {
            segment.x + 4.0f,
            segment.y + 4.0f,
            segment.width - 8.0f,
            5.0f
        };
        const Color segment_color = SnakeSegmentColor(game, is_head);

        DrawRectangleRounded(shadow, 0.35f, 8, COLOR_SHADOW);
        DrawRectangleRounded(segment, 0.35f, 8, DarkenColor(segment_color, 0.72f));
        DrawRectangleRounded(
            (Rectangle) { segment.x + 1.0f, segment.y + 1.0f, segment.width - 2.0f, segment.height - 2.0f },
            0.35f,
            8,
            segment_color
        );
        DrawRectangleRounded(shine, 0.45f, 8, ColorWithAlpha(BrightenColor(segment_color, 55), 70));
        if (is_head) {
            DrawSnakeEyes(cell, game->snake.direction);
        }

        node = node->next;
    }
}

static Vector2 CellCenter(SnakePoint point)
{
    const Rectangle cell = CellRect(point.x, point.y);
    return (Vector2) {
        cell.x + cell.width / 2.0f,
        cell.y + cell.height / 2.0f
    };
}

static void DrawDebugOverlay(const AppState *app)
{
    if (!app->debug_overlay_enabled || !app->game_ready || app->game.snake.head == NULL) {
        return;
    }

    const SnakeList *snake = &app->game.snake;
    const Color link_color = { 255, 203, 82, 150 };
    const Color tag_background = { 13, 20, 28, 230 };
    const Color tag_border = { 255, 203, 82, 230 };

    const SnakeNode *node = snake->head;
    for (size_t i = 0; i < snake->length; ++i) {
        const Vector2 from = CellCenter(node->position);
        const Vector2 to = CellCenter(node->next->position);
        DrawLineEx(from, to, 2.0f, link_color);
        node = node->next;
    }

    node = snake->head;
    for (size_t i = 0; i < snake->length; ++i) {
        const Rectangle cell = CellRect(node->position.x, node->position.y);
        const char *role = snake_ui_debug_node_role((unsigned int)i, (unsigned int)snake->length);
        char index_text[12];
        snprintf(index_text, sizeof(index_text), "%u", (unsigned int)i);

        DrawRectangleLinesEx((Rectangle) { cell.x + 2.0f, cell.y + 2.0f, cell.width - 4.0f, cell.height - 4.0f }, 2.0f, tag_border);
        DrawText(
            index_text,
            (int)(cell.x + (cell.width - MeasureText(index_text, 12)) / 2.0f),
            (int)(cell.y + 6.0f),
            12,
            COLOR_TEXT
        );

        if (role[0] != 'N') {
            const int label_width = MeasureText(role, 12) + 8;
            const int label_x = (int)(cell.x + (cell.width - (float)label_width) / 2.0f);
            const int label_y = role[0] == 'H' ? (int)cell.y - 16 : (int)cell.y + SNAKE_CELL_SIZE + 2;
            DrawRectangle(label_x, label_y, label_width, 14, tag_background);
            DrawRectangleLines(label_x, label_y, label_width, 14, tag_border);
            DrawText(role, label_x + 4, label_y + 1, 12, tag_border);
        }

        node = node->next;
    }

    DrawRectangle(36, 56, 430, 26, (Color) { 13, 20, 28, 220 });
    DrawText(
        TextFormat(
            "Linked List  Len %02d  Head (%02d,%02d)  Tail (%02d,%02d)",
            (int)snake->length,
            snake->head->position.x,
            snake->head->position.y,
            snake->tail->position.x,
            snake->tail->position.y
        ),
        48,
        60,
        16,
        tag_border
    );
}

static void DrawSingleFood(const SnakeFood *food_info)
{
    const Rectangle food = CellRect(food_info->position.x, food_info->position.y);
    const double time = GetTime();
    const float phase = (float)(time - (int)time);
    const float pulse = phase < 0.5f ? phase * 2.0f : (1.0f - phase) * 2.0f;
    const float radius = 8.0f + pulse * 2.0f;
    const Color food_color = FoodDisplayColor(food_info->color_index);
    const Color food_shadow = ColorWithAlpha(COLOR_SHADOW, 130);
    const Vector2 center = { food.x + food.width / 2.0f, food.y + food.height / 2.0f };
    const Vector2 shadow_center = { center.x + 2.0f, center.y + 2.0f };

    switch (food_info->type) {
    case SNAKE_FOOD_NORMAL:
        DrawCircleV(shadow_center, radius + 2.0f, food_shadow);
        DrawCircleV(center, radius + 1.0f, DarkenColor(food_color, 0.72f));
        DrawCircleV(center, radius, food_color);
        DrawCircleV((Vector2) { center.x - 4.0f, center.y - 4.0f }, 3.0f, ColorWithAlpha(BrightenColor(food_color, 70), 180));
        DrawRectangle((int)(food.x + food.width / 2.0f), (int)(food.y + 4.0f), 3, 5, COLOR_GREEN_BODY);
        break;
    case SNAKE_FOOD_STAR:
        DrawPoly(shadow_center, 5, radius + 4.0f, -18.0f, food_shadow);
        DrawPoly(
            center,
            5,
            radius + 2.0f,
            -18.0f,
            food_color
        );
        DrawPoly(center, 5, radius * 0.45f, -18.0f, ColorWithAlpha(BrightenColor(food_color, 60), 190));
        break;
    case SNAKE_FOOD_ICE:
        DrawPoly(shadow_center, 6, radius + 3.0f, 30.0f, food_shadow);
        DrawPoly(
            center,
            6,
            radius + 1.0f,
            30.0f,
            food_color
        );
        DrawPoly(center, 6, radius * 0.48f, 30.0f, ColorWithAlpha(BrightenColor(food_color, 65), 175));
        break;
    }
}

static void DrawFood(const SnakeGame *game)
{
    for (int i = 0; i < game->food_count; ++i) {
        DrawSingleFood(&game->foods[i]);
    }
}

static void DrawEatPulse(const AppState *app)
{
    if (!app->game_ready || app->eat_flash_timer <= 0.0f || app->game.snake.head == NULL) {
        return;
    }

    const Rectangle head = CellRect(app->game.snake.head->position.x, app->game.snake.head->position.y);
    const float progress = 1.0f - (app->eat_flash_timer / EAT_FLASH_SECONDS);
    const float radius = 9.0f + progress * 15.0f;
    Color color = FoodDisplayColor(app->last_eaten_color_index);
    color.a = (unsigned char)(180.0f * (1.0f - progress));

    DrawRing(
        (Vector2) { head.x + head.width / 2.0f, head.y + head.height / 2.0f },
        radius - 2.0f,
        radius,
        0.0f,
        360.0f,
        32,
        color
    );
}

static void DrawStartFoodIcons(void)
{
    DrawCircle(294, 496, 13.0f, COLOR_APPLE);
    DrawPoly((Vector2) { 480.0f, 496.0f }, 5, 15.0f, -18.0f, COLOR_STAR);
    DrawPoly((Vector2) { 666.0f, 496.0f }, 6, 15.0f, 30.0f, COLOR_ICE);
}

static void DrawTopBar(const AppState *app)
{
    const int score = app->game_ready ? app->game.score : 0;
    const int length = app->game_ready ? (int)app->game.snake.length : 0;
    const int food_count = app->game_ready ? app->game.food_count : 0;

    DrawRectangle(0, 0, SNAKE_WINDOW_WIDTH, 88, COLOR_PANEL);
    DrawText("SNAKE LINK", 48, 28, 26, COLOR_TEXT);
    DrawText(TextFormat("Score %04d", score), 286, 28, 22, COLOR_TEXT);
    DrawText(
        TextFormat("High %04d", app->high_score),
        448,
        28,
        22,
        app->high_score_flash_timer > 0.0f ? COLOR_STAR : COLOR_TEXT
    );
    DrawText(TextFormat("Length %02d", length), 608, 28, 22, COLOR_TEXT);
    DrawText(TextFormat("Food %02d", food_count), 760, 28, 22, COLOR_TEXT);

    if (app->game_ready && app->game.ice_slow_remaining_seconds > 0.0f) {
        DrawText(TextFormat("Ice %.1fs", app->game.ice_slow_remaining_seconds), 760, 58, 18, COLOR_ICE);
    } else if (app->debug_overlay_enabled) {
        DrawText("List Debug", 760, 58, 18, COLOR_STAR);
    }
}

static void DrawStartScreen(void)
{
    DrawTextCentered("SNAKE LINK", 168, 56, COLOR_TEXT);
    DrawTextCentered("DOUBLE CIRCULAR LIST EDITION", 236, 20, COLOR_MUTED);

    const SnakeUiRect start_hitbox = snake_ui_start_button_rect();
    const Rectangle start_button = {
        (float)start_hitbox.x,
        (float)start_hitbox.y,
        (float)start_hitbox.width,
        (float)start_hitbox.height
    };
    DrawArcadeButton(start_button, "START", 26, COLOR_GREEN_BODY, COLOR_BACKGROUND);

    DrawStartFoodIcons();
}

static void DrawPlayingScreen(const AppState *app)
{
    DrawTopBar(app);
    DrawBoard();

    if (app->game_ready) {
        DrawFood(&app->game);
        DrawSnake(&app->game);
        DrawEatPulse(app);
        DrawDebugOverlay(app);
    }
}

static void DrawPauseOverlay(void)
{
    const SnakeUiRect resume_hitbox = snake_ui_resume_button_rect();
    const Rectangle resume_button = {
        (float)resume_hitbox.x,
        (float)resume_hitbox.y,
        (float)resume_hitbox.width,
        (float)resume_hitbox.height
    };

    DrawRectangle(0, 0, SNAKE_WINDOW_WIDTH, SNAKE_WINDOW_HEIGHT, (Color) { 6, 10, 14, 170 });
    DrawTextCentered("PAUSED", 292, 50, COLOR_TEXT);
    DrawArcadeButton(resume_button, "RESUME", 22, COLOR_PANEL, COLOR_GREEN_HEAD);
}

static const char *DeathReasonText(SnakeDeathReason reason)
{
    if (reason == SNAKE_DEATH_WALL) {
        return "WALL COLLISION";
    }

    if (reason == SNAKE_DEATH_SELF) {
        return "BODY COLLISION";
    }

    return "GAME OVER";
}

static void DrawGameOverScreen(const AppState *app)
{
    const int score = app->game_ready ? app->game.score : 0;
    const SnakeDeathReason reason = app->game_ready ? app->game.death_reason : SNAKE_DEATH_NONE;
    const SnakeUiRect restart_hitbox = snake_ui_restart_button_rect();
    const Rectangle restart_button = {
        (float)restart_hitbox.x,
        (float)restart_hitbox.y,
        (float)restart_hitbox.width,
        (float)restart_hitbox.height
    };

    DrawTextCentered("GAME OVER", 192, 54, COLOR_TEXT);
    DrawTextCentered(DeathReasonText(reason), 260, 22, COLOR_APPLE);
    DrawTextCentered(TextFormat("Score %04d", score), 328, 28, COLOR_TEXT);
    DrawTextCentered(
        TextFormat("High %04d", app->high_score),
        368,
        28,
        app->high_score_flash_timer > 0.0f ? COLOR_STAR : COLOR_MUTED
    );

    DrawArcadeButton(restart_button, "RESTART", 25, COLOR_GREEN_BODY, COLOR_BACKGROUND);
}

static void StartNewGame(AppState *app)
{
    PlayAppSound(app, app->sounds.click);

    if (app->game_ready) {
        snake_game_destroy(&app->game);
        app->game_ready = false;
    }

    const uint32_t seed = (uint32_t)(GetTime() * 100000.0) + 1u;
    if (snake_game_init(&app->game, SNAKE_BOARD_COLUMNS, SNAKE_BOARD_ROWS, seed)) {
        app->game_ready = true;
        app->move_accumulator = 0.0f;
        app->eat_flash_timer = 0.0f;
        app->last_eaten_food = SNAKE_FOOD_NORMAL;
        app->last_eaten_color_index = 0;
        app->screen = SCREEN_PLAYING;
    }
}

static void ReturnToStart(AppState *app)
{
    PlayAppSound(app, app->sounds.click);
    app->screen = SCREEN_START;
    app->move_accumulator = 0.0f;
}

static void FinishGame(AppState *app)
{
    if (app->game_ready) {
        const int previous_high_score = app->high_score;
        int stored_score = app->high_score;
        if (snake_high_score_save_if_greater(HIGH_SCORE_FILE_PATH, app->game.score, &stored_score)) {
            app->high_score = stored_score;
        } else if (app->game.score > app->high_score) {
            app->high_score = app->game.score;
        }

        if (app->high_score > previous_high_score) {
            app->high_score_flash_timer = HIGH_SCORE_FLASH_SECONDS;
        }
    }

    PlayAppSound(app, app->sounds.game_over);
    app->screen = SCREEN_GAME_OVER;
}

static bool DirectionFromKey(int key, SnakeDirection *direction)
{
    if (key == KEY_UP || key == KEY_W) {
        *direction = SNAKE_DIRECTION_UP;
        return true;
    }

    if (key == KEY_RIGHT || key == KEY_D) {
        *direction = SNAKE_DIRECTION_RIGHT;
        return true;
    }

    if (key == KEY_DOWN || key == KEY_S) {
        *direction = SNAKE_DIRECTION_DOWN;
        return true;
    }

    if (key == KEY_LEFT || key == KEY_A) {
        *direction = SNAKE_DIRECTION_LEFT;
        return true;
    }

    return false;
}

static void HandleKey(AppState *app, int key)
{
    if (key == KEY_F1) {
        app->debug_overlay_enabled = !app->debug_overlay_enabled;
        PlayAppSound(app, app->sounds.click);
        return;
    }

    if (key == KEY_ESCAPE) {
        ReturnToStart(app);
        return;
    }

    switch (app->screen) {
    case SCREEN_START:
        if (key == KEY_ENTER) {
            StartNewGame(app);
        }
        break;
    case SCREEN_PLAYING:
        if (key == KEY_SPACE) {
            app->screen = SCREEN_PAUSED;
        } else {
            SnakeDirection direction = SNAKE_DIRECTION_RIGHT;
            if (DirectionFromKey(key, &direction)) {
                (void)snake_game_request_direction(&app->game, direction);
            }
        }
        break;
    case SCREEN_PAUSED:
        if (key == KEY_SPACE) {
            PlayAppSound(app, app->sounds.click);
            app->screen = SCREEN_PLAYING;
        }
        break;
    case SCREEN_GAME_OVER:
        if (key == KEY_ENTER) {
            StartNewGame(app);
        }
        break;
    }
}

static void HandleMouseClick(AppState *app, int x, int y)
{
    switch (app->screen) {
    case SCREEN_START:
        if (snake_ui_is_start_button_hit(x, y)) {
            StartNewGame(app);
        }
        break;
    case SCREEN_PLAYING:
        break;
    case SCREEN_PAUSED:
        if (snake_ui_is_resume_button_hit(x, y)) {
            PlayAppSound(app, app->sounds.click);
            app->screen = SCREEN_PLAYING;
        }
        break;
    case SCREEN_GAME_OVER:
        if (snake_ui_is_restart_button_hit(x, y)) {
            StartNewGame(app);
        }
        break;
    }
}

static void UpdateGameClock(AppState *app)
{
    if (app->screen != SCREEN_PLAYING || !app->game_ready) {
        return;
    }

    const float frame_time = GetFrameTime();
    snake_game_update_timers(&app->game, frame_time, false);
    if (app->eat_flash_timer > 0.0f) {
        app->eat_flash_timer -= frame_time;
        if (app->eat_flash_timer < 0.0f) {
            app->eat_flash_timer = 0.0f;
        }
    }
    if (app->high_score_flash_timer > 0.0f) {
        app->high_score_flash_timer -= frame_time;
        if (app->high_score_flash_timer < 0.0f) {
            app->high_score_flash_timer = 0.0f;
        }
    }
    app->move_accumulator += frame_time;

    while (app->move_accumulator >= snake_game_current_move_interval(&app->game) && app->screen == SCREEN_PLAYING) {
        const float interval = snake_game_current_move_interval(&app->game);
        const SnakeTickResult result = snake_game_tick(&app->game);
        app->move_accumulator -= interval;

        if (result == SNAKE_TICK_GAME_OVER) {
            FinishGame(app);
        } else if (result == SNAKE_TICK_ATE_FOOD) {
            app->last_eaten_food = app->game.snake_color_food_type;
            app->last_eaten_color_index = app->game.snake_color_index;
            app->eat_flash_timer = EAT_FLASH_SECONDS;
            PlayFoodSound(app, app->last_eaten_food);
        }
    }
}

static void UpdateApp(AppState *app)
{
    int key = GetKeyPressed();
    while (key != 0) {
        HandleKey(app, key);
        key = GetKeyPressed();
    }

    if (IsMouseButtonPressed(MOUSE_BUTTON_LEFT)) {
        const Vector2 mouse = GetMousePosition();
        HandleMouseClick(app, (int)mouse.x, (int)mouse.y);
    }

    UpdateGameClock(app);
}

static void DrawApp(const AppState *app)
{
    ClearBackground(COLOR_BACKGROUND);

    switch (app->screen) {
    case SCREEN_START:
        DrawStartScreen();
        break;
    case SCREEN_PLAYING:
        DrawPlayingScreen(app);
        break;
    case SCREEN_PAUSED:
        DrawPlayingScreen(app);
        DrawPauseOverlay();
        break;
    case SCREEN_GAME_OVER:
        DrawGameOverScreen(app);
        break;
    }
}

int main(void)
{
    AppState app = {
        .screen = SCREEN_START,
        .game_ready = false,
        .high_score = 0,
        .move_accumulator = 0.0f,
        .eat_flash_timer = 0.0f,
        .high_score_flash_timer = 0.0f,
        .last_eaten_food = SNAKE_FOOD_NORMAL,
        .last_eaten_color_index = 0,
        .debug_overlay_enabled = false,
        .sounds = { .ready = false }
    };

    InitWindow(SNAKE_WINDOW_WIDTH, SNAKE_WINDOW_HEIGHT, "Snake Link");
    app.high_score = snake_high_score_load_or_zero(HIGH_SCORE_FILE_PATH);
    InitAppSounds(&app);
    SetTargetFPS(60);

    while (!WindowShouldClose()) {
        UpdateApp(&app);

        BeginDrawing();
        DrawApp(&app);
        EndDrawing();
    }

    if (app.game_ready) {
        snake_game_destroy(&app.game);
    }
    UnloadAppSounds(&app);

    CloseWindow();
    return 0;
}
