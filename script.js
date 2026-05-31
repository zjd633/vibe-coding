(function () {
  const GRID_SIZE = 20;
  const CELL_SIZE = 26;
  const STORAGE_KEY = 'neon-snake-high-score';
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

  const canvas = document.getElementById('game-canvas');
  const context = canvas.getContext('2d');
  const scoreElement = document.getElementById('score');
  const highScoreElement = document.getElementById('high-score');
  const statusElement = document.getElementById('status-text');
  const toggleButton = document.getElementById('toggle-button');
  const restartButton = document.getElementById('restart-button');

  let state = createInitialState();
  let loopId = null;

  function createInitialSnake() {
    return [
      { x: 10, y: 10 },
      { x: 9, y: 10 },
      { x: 8, y: 10 },
    ];
  }

  function createFood(snake) {
    let food;

    do {
      food = {
        x: Math.floor(Math.random() * GRID_SIZE),
        y: Math.floor(Math.random() * GRID_SIZE),
      };
    } while (snake.some((segment) => segment.x === food.x && segment.y === food.y));

    return food;
  }

  function createInitialState() {
    const snake = createInitialSnake();

    return {
      status: 'idle',
      snake,
      direction: { x: 1, y: 0 },
      nextDirection: { x: 1, y: 0 },
      food: createFood(snake),
      score: 0,
      highScore: loadHighScore(),
      speedDelay: BASE_SPEED,
    };
  }

  function loadHighScore() {
    const savedScore = window.localStorage.getItem(STORAGE_KEY);
    const parsedScore = Number(savedScore);

    return Number.isFinite(parsedScore) && parsedScore >= 0 ? parsedScore : 0;
  }

  function saveHighScore(score) {
    window.localStorage.setItem(STORAGE_KEY, String(score));
  }

  function getSpeedDelay(score) {
    const reduction = Math.floor(score / SPEED_THRESHOLD) * SPEED_STEP;
    return Math.max(MIN_SPEED, BASE_SPEED - reduction);
  }

  function isReverseDirection(currentDirection, nextDirection) {
    return (
      currentDirection.x + nextDirection.x === 0 &&
      currentDirection.y + nextDirection.y === 0
    );
  }

  function queueDirection(code) {
    const nextDirection = DIRECTIONS[code];

    if (!nextDirection || state.status === 'gameover') {
      return;
    }

    if (isReverseDirection(state.direction, nextDirection)) {
      return;
    }

    state.nextDirection = nextDirection;
  }

  function startLoop() {
    clearLoop();
    loopId = window.setInterval(runTick, state.speedDelay);
  }

  function clearLoop() {
    if (loopId !== null) {
      window.clearInterval(loopId);
      loopId = null;
    }
  }

  function updateHUD() {
    scoreElement.textContent = String(state.score);
    highScoreElement.textContent = String(state.highScore);

    if (state.status === 'idle') {
      statusElement.textContent = '点击“开始游戏”进入棋盘';
      toggleButton.textContent = '开始游戏';
    } else if (state.status === 'running') {
      statusElement.textContent = '正在穿越电子网格，空格键可暂停';
      toggleButton.textContent = '暂停游戏';
    } else if (state.status === 'paused') {
      statusElement.textContent = '游戏已暂停，按空格或按钮继续';
      toggleButton.textContent = '继续游戏';
    } else {
      statusElement.textContent = '碰撞发生，点击“重新开始”再来一局';
      toggleButton.textContent = '再玩一次';
    }
  }

  function drawBoard() {
    context.clearRect(0, 0, canvas.width, canvas.height);

    const gradient = context.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, '#061323');
    gradient.addColorStop(1, '#0b1c34');
    context.fillStyle = gradient;
    context.fillRect(0, 0, canvas.width, canvas.height);

    context.strokeStyle = 'rgba(139, 247, 196, 0.08)';
    context.lineWidth = 1;

    for (let index = 0; index <= GRID_SIZE; index += 1) {
      const offset = index * CELL_SIZE;

      context.beginPath();
      context.moveTo(offset + 0.5, 0);
      context.lineTo(offset + 0.5, canvas.height);
      context.stroke();

      context.beginPath();
      context.moveTo(0, offset + 0.5);
      context.lineTo(canvas.width, offset + 0.5);
      context.stroke();
    }
  }

  function drawFood() {
    const centerX = state.food.x * CELL_SIZE + CELL_SIZE / 2;
    const centerY = state.food.y * CELL_SIZE + CELL_SIZE / 2;
    const radius = CELL_SIZE * 0.28;

    context.save();
    context.fillStyle = '#ffe269';
    context.shadowColor = 'rgba(255, 226, 105, 0.75)';
    context.shadowBlur = 18;
    context.beginPath();
    context.arc(centerX, centerY, radius, 0, Math.PI * 2);
    context.fill();
    context.restore();
  }

  function drawSnake() {
    state.snake.forEach((segment, index) => {
      const inset = 2.5;
      const x = segment.x * CELL_SIZE + inset;
      const y = segment.y * CELL_SIZE + inset;
      const size = CELL_SIZE - inset * 2;

      context.save();
      context.fillStyle = index === 0 ? '#8bf7c4' : '#5fe7ff';
      context.shadowColor = index === 0 ? 'rgba(139, 247, 196, 0.45)' : 'rgba(95, 231, 255, 0.24)';
      context.shadowBlur = index === 0 ? 16 : 10;
      drawRoundedRect(x, y, size, size, 7);
      context.fill();
      context.restore();

      if (index === 0) {
        drawSnakeEyes(segment);
      }
    });
  }

  function drawSnakeEyes(head) {
    const baseX = head.x * CELL_SIZE;
    const baseY = head.y * CELL_SIZE;
    const eyeOffset = 7;
    const eyeSize = 3;
    let eyes;

    if (state.direction.x === 1) {
      eyes = [
        { x: baseX + 18, y: baseY + 8 },
        { x: baseX + 18, y: baseY + 18 },
      ];
    } else if (state.direction.x === -1) {
      eyes = [
        { x: baseX + 8, y: baseY + 8 },
        { x: baseX + 8, y: baseY + 18 },
      ];
    } else if (state.direction.y === -1) {
      eyes = [
        { x: baseX + 8, y: baseY + 8 },
        { x: baseX + 18, y: baseY + 8 },
      ];
    } else {
      eyes = [
        { x: baseX + 8, y: baseY + 18 },
        { x: baseX + 18, y: baseY + 18 },
      ];
    }

    context.fillStyle = '#04111a';
    eyes.forEach((eye) => {
      context.beginPath();
      context.arc(eye.x, eye.y, eyeSize, 0, Math.PI * 2);
      context.fill();
    });
  }

  function drawOverlay() {
    if (state.status === 'running') {
      return;
    }

    context.save();
    context.fillStyle = 'rgba(4, 10, 20, 0.58)';
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.textAlign = 'center';
    context.fillStyle = '#f2f7ff';
    context.font = '700 30px Trebuchet MS';

    if (state.status === 'idle') {
      context.fillText('准备进入网格', canvas.width / 2, canvas.height / 2 - 10);
      context.font = '18px Trebuchet MS';
      context.fillStyle = '#98a9c9';
      context.fillText('点击开始或按空格键启动', canvas.width / 2, canvas.height / 2 + 26);
    } else if (state.status === 'paused') {
      context.fillText('已暂停', canvas.width / 2, canvas.height / 2 - 10);
      context.font = '18px Trebuchet MS';
      context.fillStyle = '#98a9c9';
      context.fillText('按空格或点击按钮继续', canvas.width / 2, canvas.height / 2 + 26);
    } else {
      context.fillStyle = '#ff7d7d';
      context.fillText('游戏结束', canvas.width / 2, canvas.height / 2 - 14);
      context.font = '18px Trebuchet MS';
      context.fillStyle = '#f2f7ff';
      context.fillText(`最终分数 ${state.score}`, canvas.width / 2, canvas.height / 2 + 18);
      context.fillStyle = '#98a9c9';
      context.fillText('点击重新开始挑战新纪录', canvas.width / 2, canvas.height / 2 + 48);
    }

    context.restore();
  }

  function drawRoundedRect(x, y, width, height, radius) {
    context.beginPath();
    context.moveTo(x + radius, y);
    context.arcTo(x + width, y, x + width, y + height, radius);
    context.arcTo(x + width, y + height, x, y + height, radius);
    context.arcTo(x, y + height, x, y, radius);
    context.arcTo(x, y, x + width, y, radius);
    context.closePath();
  }

  function render() {
    drawBoard();
    drawFood();
    drawSnake();
    drawOverlay();
  }

  function finishGame() {
    state.status = 'gameover';
    clearLoop();

    if (state.score > state.highScore) {
      state.highScore = state.score;
      saveHighScore(state.highScore);
    }

    updateHUD();
    render();
  }

  function runTick() {
    state.direction = state.nextDirection;

    const nextHead = {
      x: state.snake[0].x + state.direction.x,
      y: state.snake[0].y + state.direction.y,
    };

    const ateFood = nextHead.x === state.food.x && nextHead.y === state.food.y;
    const bodyToCheck = ateFood ? state.snake : state.snake.slice(0, -1);
    const collision =
      nextHead.x < 0 ||
      nextHead.x >= GRID_SIZE ||
      nextHead.y < 0 ||
      nextHead.y >= GRID_SIZE ||
      bodyToCheck.some(
        (segment) => segment.x === nextHead.x && segment.y === nextHead.y,
      );

    if (collision) {
      finishGame();
      return;
    }

    state.snake.unshift(nextHead);

    if (ateFood) {
      state.score += 1;
      state.food = createFood(state.snake);
      const nextSpeed = getSpeedDelay(state.score);

      if (nextSpeed !== state.speedDelay) {
        state.speedDelay = nextSpeed;
        startLoop();
      }
    } else {
      state.snake.pop();
    }

    if (state.score > state.highScore) {
      state.highScore = state.score;
      saveHighScore(state.highScore);
    }

    updateHUD();
    render();
  }

  function startGame() {
    if (state.status === 'running') {
      return;
    }

    if (state.status === 'gameover') {
      resetGame();
    }

    state.status = 'running';
    updateHUD();
    render();
    startLoop();
  }

  function pauseGame() {
    if (state.status !== 'running') {
      return;
    }

    state.status = 'paused';
    clearLoop();
    updateHUD();
    render();
  }

  function toggleGame() {
    if (state.status === 'running') {
      pauseGame();
      return;
    }

    startGame();
  }

  function resetGame() {
    const rememberedHighScore = state.highScore;
    state = createInitialState();
    state.highScore = rememberedHighScore;
    clearLoop();
    updateHUD();
    render();
  }

  function handleKeydown(event) {
    if (event.code === 'Space') {
      event.preventDefault();
      toggleGame();
      return;
    }

    if (Object.prototype.hasOwnProperty.call(DIRECTIONS, event.code)) {
      event.preventDefault();
      if (state.status === 'idle') {
        startGame();
      }
      queueDirection(event.code);
    }
  }

  toggleButton.addEventListener('click', toggleGame);
  restartButton.addEventListener('click', resetGame);
  window.addEventListener('keydown', handleKeydown);

  updateHUD();
  render();
})();
