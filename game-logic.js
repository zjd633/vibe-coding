const GRID_SIZE = 20;
const INITIAL_LENGTH = 3;
const START_X = 10;
const START_Y = 10;
const BASE_SPEED = 180;
const SPEED_STEP = 15;
const SPEED_THRESHOLD = 5;
const MIN_SPEED = 75;

const DIRECTIONS = {
  ArrowUp: { x: 0, y: -1 },
  KeyW: { x: 0, y: -1 },
  ArrowDown: { x: 0, y: 1 },
  KeyS: { x: 0, y: 1 },
  ArrowLeft: { x: -1, y: 0 },
  KeyA: { x: -1, y: 0 },
  ArrowRight: { x: 1, y: 0 },
  KeyD: { x: 1, y: 0 },
};

function createInitialSnake() {
  return Array.from({ length: INITIAL_LENGTH }, (_, index) => ({
    x: START_X - index,
    y: START_Y,
  }));
}

function getRandomInt(max, randomFn = Math.random) {
  return Math.floor(randomFn() * max);
}

function createFood(snake, randomFn = Math.random) {
  let candidate;

  do {
    candidate = {
      x: getRandomInt(GRID_SIZE, randomFn),
      y: getRandomInt(GRID_SIZE, randomFn),
    };
  } while (snake.some((segment) => segment.x === candidate.x && segment.y === candidate.y));

  return candidate;
}

function createInitialState(randomFn = Math.random) {
  const snake = createInitialSnake();

  return {
    status: 'idle',
    snake,
    direction: { x: 1, y: 0 },
    nextDirection: { x: 1, y: 0 },
    food: createFood(snake, randomFn),
    score: 0,
  };
}

function isReverseDirection(currentDirection, nextDirection) {
  return (
    currentDirection.x + nextDirection.x === 0 &&
    currentDirection.y + nextDirection.y === 0
  );
}

function queueDirection(state, key) {
  const intendedDirection = DIRECTIONS[key];

  if (!intendedDirection) {
    return false;
  }

  if (isReverseDirection(state.direction, intendedDirection)) {
    return false;
  }

  state.nextDirection = intendedDirection;
  return true;
}

function hasCollision(head, snake) {
  const outsideBoard =
    head.x < 0 || head.x >= GRID_SIZE || head.y < 0 || head.y >= GRID_SIZE;

  if (outsideBoard) {
    return true;
  }

  return snake.some((segment) => segment.x === head.x && segment.y === head.y);
}

function advanceSnake(state, randomFn = Math.random) {
  state.direction = state.nextDirection;

  const head = {
    x: state.snake[0].x + state.direction.x,
    y: state.snake[0].y + state.direction.y,
  };

  const ateFood = head.x === state.food.x && head.y === state.food.y;
  const bodyToCheck = ateFood ? state.snake : state.snake.slice(0, -1);

  if (hasCollision(head, bodyToCheck)) {
    return {
      collided: true,
      ateFood: false,
    };
  }

  state.snake.unshift(head);

  if (ateFood) {
    state.score += 1;
    state.food = createFood(state.snake, randomFn);
  } else {
    state.snake.pop();
  }

  return {
    collided: false,
    ateFood,
  };
}

function getSpeedDelay(score) {
  const reduction = Math.floor(score / SPEED_THRESHOLD) * SPEED_STEP;
  return Math.max(MIN_SPEED, BASE_SPEED - reduction);
}

module.exports = {
  GRID_SIZE,
  DIRECTIONS,
  createInitialState,
  queueDirection,
  advanceSnake,
  createFood,
  getSpeedDelay,
};
