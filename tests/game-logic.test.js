const test = require('node:test');
const assert = require('node:assert/strict');

const {
  GRID_SIZE,
  createInitialState,
  queueDirection,
  advanceSnake,
  createFood,
  getSpeedDelay,
} = require('../game-logic.js');

test('createInitialState sets up a centered snake and valid food state', () => {
  const state = createInitialState();

  assert.equal(state.status, 'idle');
  assert.equal(state.score, 0);
  assert.equal(state.snake.length, 3);
  assert.deepEqual(state.direction, { x: 1, y: 0 });
  assert.deepEqual(state.nextDirection, { x: 1, y: 0 });
  assert.ok(
    state.snake.every(
      (segment) =>
        segment.x >= 0 &&
        segment.x < GRID_SIZE &&
        segment.y >= 0 &&
        segment.y < GRID_SIZE,
    ),
  );
  assert.ok(
    state.food.x >= 0 &&
      state.food.x < GRID_SIZE &&
      state.food.y >= 0 &&
      state.food.y < GRID_SIZE,
  );
});

test('queueDirection ignores direct reverse turns and accepts valid turns', () => {
  const state = createInitialState();

  queueDirection(state, 'ArrowLeft');
  assert.deepEqual(state.nextDirection, { x: 1, y: 0 });

  queueDirection(state, 'ArrowUp');
  assert.deepEqual(state.nextDirection, { x: 0, y: -1 });
});

test('advanceSnake moves forward without food and keeps length stable', () => {
  const state = createInitialState();
  state.food = { x: 0, y: 0 };

  const result = advanceSnake(state);

  assert.equal(result.ateFood, false);
  assert.equal(result.collided, false);
  assert.equal(state.snake.length, 3);
  assert.deepEqual(state.snake[0], { x: 11, y: 10 });
  assert.deepEqual(state.snake[2], { x: 9, y: 10 });
});

test('advanceSnake grows the snake, increases score, and refreshes food when eaten', () => {
  const state = createInitialState();
  state.food = { x: 11, y: 10 };

  const result = advanceSnake(state, () => 0);

  assert.equal(result.ateFood, true);
  assert.equal(result.collided, false);
  assert.equal(state.score, 1);
  assert.equal(state.snake.length, 4);
  assert.notDeepEqual(state.food, { x: 11, y: 10 });
  assert.equal(
    state.snake.some(
      (segment) => segment.x === state.food.x && segment.y === state.food.y,
    ),
    false,
  );
});

test('advanceSnake reports collisions with walls and self', () => {
  const wallState = createInitialState();
  wallState.snake = [{ x: GRID_SIZE - 1, y: 4 }];
  wallState.direction = { x: 1, y: 0 };
  wallState.nextDirection = { x: 1, y: 0 };

  const wallResult = advanceSnake(wallState);
  assert.equal(wallResult.collided, true);

  const selfState = createInitialState();
  selfState.snake = [
    { x: 5, y: 5 },
    { x: 6, y: 5 },
    { x: 4, y: 6 },
    { x: 5, y: 6 },
  ];
  selfState.direction = { x: 1, y: 0 };
  selfState.nextDirection = { x: 1, y: 0 };

  const selfResult = advanceSnake(selfState);
  assert.equal(selfResult.collided, true);
});

test('createFood retries until it finds an empty cell', () => {
  const snake = [
    { x: 0, y: 0 },
    { x: 1, y: 0 },
  ];
  let calls = 0;
  const randomValues = [0, 0, 0.05, 0, 0.1, 0.05];

  const food = createFood(snake, () => randomValues[calls++]);

  assert.deepEqual(food, { x: 2, y: 1 });
  assert.equal(calls, 6);
});

test('getSpeedDelay ramps difficulty and respects the minimum speed cap', () => {
  assert.equal(getSpeedDelay(0), 180);
  assert.equal(getSpeedDelay(4), 180);
  assert.equal(getSpeedDelay(5), 165);
  assert.equal(getSpeedDelay(20), 120);
  assert.equal(getSpeedDelay(200), 75);
});
