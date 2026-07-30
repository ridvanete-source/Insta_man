(function () {
  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');

  const scoreEl = document.getElementById('score');
  const bestEl = document.getElementById('best');
  const startScreen = document.getElementById('start-screen');
  const gameoverScreen = document.getElementById('gameover-screen');
  const startBtn = document.getElementById('start-btn');
  const retryBtn = document.getElementById('retry-btn');
  const finalScoreEl = document.getElementById('final-score');
  const finalBestEl = document.getElementById('final-best');

  const STORAGE_KEY = 'zipla-kac-best-score';

  let width, height, groundY, dpr;

  function resize() {
    dpr = window.devicePixelRatio || 1;
    width = canvas.clientWidth;
    height = canvas.clientHeight;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    groundY = height * 0.78;
  }
  window.addEventListener('resize', resize);

  const GRAVITY = 2200;
  const JUMP_VELOCITY = -820;
  const PLAYER_SIZE = 40;

  let player, obstacles, particles;
  let speed, spawnTimer, spawnInterval, elapsed, score, best;
  let running = false;
  let started = false;

  function loadBest() {
    return Number(localStorage.getItem(STORAGE_KEY) || 0);
  }
  function saveBest(v) {
    localStorage.setItem(STORAGE_KEY, String(v));
  }

  function resetState() {
    player = {
      x: width * 0.18,
      y: groundY - PLAYER_SIZE,
      vy: 0,
      onGround: true,
      rotation: 0,
    };
    obstacles = [];
    particles = [];
    speed = 380;
    spawnTimer = 0;
    spawnInterval = 1.3;
    elapsed = 0;
    score = 0;
    best = loadBest();
    scoreEl.textContent = '0';
    bestEl.textContent = 'En iyi: ' + best;
  }

  function jump() {
    if (!running) return;
    if (player.onGround) {
      player.vy = JUMP_VELOCITY;
      player.onGround = false;
    }
  }

  function spawnObstacle() {
    const isTall = Math.random() < 0.35;
    const w = isTall ? 26 : 32 + Math.random() * 18;
    const h = isTall ? 60 + Math.random() * 20 : 30 + Math.random() * 16;
    obstacles.push({
      x: width + w,
      y: groundY - h,
      w, h,
      passed: false,
    });
  }

  function update(dt) {
    elapsed += dt;
    speed += dt * 14;
    spawnInterval = Math.max(0.7, 1.3 - elapsed * 0.01);

    // player physics
    player.vy += GRAVITY * dt;
    player.y += player.vy * dt;
    if (player.y >= groundY - PLAYER_SIZE) {
      player.y = groundY - PLAYER_SIZE;
      player.vy = 0;
      player.onGround = true;
    }
    if (!player.onGround) {
      player.rotation += dt * 8;
    } else {
      player.rotation = 0;
    }

    // spawn obstacles
    spawnTimer += dt;
    if (spawnTimer >= spawnInterval) {
      spawnTimer = 0;
      spawnObstacle();
    }

    // move obstacles
    for (const o of obstacles) {
      o.x -= speed * dt;
      if (!o.passed && o.x + o.w < player.x) {
        o.passed = true;
        score += 1;
        scoreEl.textContent = String(score);
      }
    }
    obstacles = obstacles.filter(o => o.x + o.w > -10);

    // collision (slightly forgiving hitbox)
    const pad = 8;
    const px = player.x + pad, py = player.y + pad;
    const pw = PLAYER_SIZE - pad * 2, ph = PLAYER_SIZE - pad * 2;
    for (const o of obstacles) {
      if (
        px < o.x + o.w &&
        px + pw > o.x &&
        py < o.y + o.h &&
        py + ph > o.y
      ) {
        gameOver();
        return;
      }
    }

    // dust particles while running on ground
    if (player.onGround && Math.random() < 0.4) {
      particles.push({
        x: player.x + PLAYER_SIZE * 0.3,
        y: groundY - 2,
        vx: -speed * 0.4 - Math.random() * 40,
        vy: -20 - Math.random() * 30,
        life: 0.4,
        age: 0,
      });
    }
    for (const p of particles) {
      p.age += dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
    }
    particles = particles.filter(p => p.age < p.life);
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);

    // ground
    ctx.fillStyle = '#3f6b3f';
    ctx.fillRect(0, groundY, width, height - groundY);
    ctx.fillStyle = '#2f5230';
    ctx.fillRect(0, groundY, width, 4);

    // particles
    ctx.fillStyle = 'rgba(255,255,255,0.6)';
    for (const p of particles) {
      const alpha = 1 - p.age / p.life;
      ctx.globalAlpha = alpha;
      ctx.fillRect(p.x, p.y, 4, 4);
    }
    ctx.globalAlpha = 1;

    // obstacles
    ctx.fillStyle = '#c0392b';
    for (const o of obstacles) {
      ctx.fillRect(o.x, o.y, o.w, o.h);
    }

    // player
    ctx.save();
    ctx.translate(player.x + PLAYER_SIZE / 2, player.y + PLAYER_SIZE / 2);
    ctx.rotate(player.rotation);
    ctx.fillStyle = '#ffcf3f';
    ctx.fillRect(-PLAYER_SIZE / 2, -PLAYER_SIZE / 2, PLAYER_SIZE, PLAYER_SIZE);
    ctx.fillStyle = '#1e2a3a';
    ctx.fillRect(-PLAYER_SIZE / 2 + 24, -PLAYER_SIZE / 2 + 8, 6, 6);
    ctx.restore();
  }

  let lastTime = null;
  function loop(ts) {
    if (!running) return;
    if (lastTime === null) lastTime = ts;
    let dt = (ts - lastTime) / 1000;
    lastTime = ts;
    dt = Math.min(dt, 0.033);

    update(dt);
    draw();

    requestAnimationFrame(loop);
  }

  function startGame() {
    resize();
    resetState();
    running = true;
    started = true;
    lastTime = null;
    startScreen.classList.add('hidden');
    gameoverScreen.classList.add('hidden');
    requestAnimationFrame(loop);
  }

  function gameOver() {
    running = false;
    if (score > best) {
      best = score;
      saveBest(best);
    }
    finalScoreEl.textContent = 'Skor: ' + score;
    finalBestEl.textContent = 'En iyi: ' + best;
    bestEl.textContent = 'En iyi: ' + best;
    gameoverScreen.classList.remove('hidden');
  }

  function handleInput(e) {
    if (e.type === 'keydown' && e.code !== 'Space' && e.code !== 'ArrowUp') return;
    if (e.type === 'keydown') e.preventDefault();
    jump();
  }

  canvas.addEventListener('pointerdown', jump);
  window.addEventListener('keydown', handleInput);

  startBtn.addEventListener('click', startGame);
  retryBtn.addEventListener('click', startGame);

  resize();
  bestEl.textContent = 'En iyi: ' + loadBest();
})();
