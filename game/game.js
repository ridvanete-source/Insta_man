(function () {
  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');

  const scoreEl = document.getElementById('score');
  const bestValueEl = document.getElementById('best-value');
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
    groundY = height * 0.76;
  }
  window.addEventListener('resize', resize);

  const GRAVITY = 2200;
  const JUMP_VELOCITY = -820;
  const PLAYER_SIZE = 42;

  let player, obstacles, particles;
  let speed, spawnTimer, spawnInterval, elapsed, score, best;
  let farScroll = 0, nearScroll = 0, groundScroll = 0;
  let running = false;

  function loadBest() {
    return Number(localStorage.getItem(STORAGE_KEY) || 0);
  }
  function saveBest(v) {
    localStorage.setItem(STORAGE_KEY, String(v));
  }

  function resetState() {
    player = { x: width * 0.18, y: groundY - PLAYER_SIZE, vy: 0, onGround: true, rotation: 0 };
    obstacles = [];
    particles = [];
    speed = 380;
    spawnTimer = 0;
    spawnInterval = 1.3;
    elapsed = 0;
    score = 0;
    best = loadBest();
    scoreEl.textContent = '0';
    bestValueEl.textContent = String(best);
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
    obstacles.push({ x: width + w, y: groundY - h, w, h, passed: false });
  }

  function update(dt) {
    elapsed += dt;
    speed += dt * 14;
    spawnInterval = Math.max(0.7, 1.3 - elapsed * 0.01);
    farScroll += dt * 18;
    nearScroll += dt * 46;
    groundScroll += speed * dt;

    player.vy += GRAVITY * dt;
    player.y += player.vy * dt;
    if (player.y >= groundY - PLAYER_SIZE) {
      player.y = groundY - PLAYER_SIZE;
      player.vy = 0;
      player.onGround = true;
    }
    player.rotation = player.onGround ? 0 : player.rotation + dt * 8;

    spawnTimer += dt;
    if (spawnTimer >= spawnInterval) {
      spawnTimer = 0;
      spawnObstacle();
    }

    for (const o of obstacles) {
      o.x -= speed * dt;
      if (!o.passed && o.x + o.w < player.x) {
        o.passed = true;
        score += 1;
        scoreEl.textContent = String(score);
      }
    }
    obstacles = obstacles.filter(o => o.x + o.w > -10);

    const pad = 9;
    const px = player.x + pad, py = player.y + pad;
    const pw = PLAYER_SIZE - pad * 2, ph = PLAYER_SIZE - pad * 2;
    for (const o of obstacles) {
      if (px < o.x + o.w && px + pw > o.x && py < o.y + o.h && py + ph > o.y) {
        gameOver();
        return;
      }
    }

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

  function ridgeY(x, offset, baseY, amp) {
    return baseY
      - amp * (0.55 + 0.45 * Math.sin((x + offset) * 0.0032))
      - amp * 0.35 * Math.sin((x + offset) * 0.009 + 1.7);
  }

  function drawRidge(offset, baseY, amp, color) {
    ctx.beginPath();
    ctx.moveTo(0, groundY + 2);
    for (let x = 0; x <= width; x += 24) {
      ctx.lineTo(x, ridgeY(x, offset, baseY, amp));
    }
    ctx.lineTo(width, groundY + 2);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
  }

  function roundRectPath(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);

    const sky = ctx.createLinearGradient(0, 0, 0, groundY);
    sky.addColorStop(0, '#241b3a');
    sky.addColorStop(0.55, '#6a3f6b');
    sky.addColorStop(1, '#f0895a');
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, width, groundY);

    const sunX = width * 0.76, sunY = height * 0.22, sunR = Math.min(width, height) * 0.16;
    const glow = ctx.createRadialGradient(sunX, sunY, 0, sunX, sunY, sunR * 2.2);
    glow.addColorStop(0, 'rgba(255, 177, 92, 0.55)');
    glow.addColorStop(1, 'rgba(255, 177, 92, 0)');
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, width, groundY);
    ctx.beginPath();
    ctx.arc(sunX, sunY, sunR * 0.55, 0, Math.PI * 2);
    ctx.fillStyle = '#ffe08a';
    ctx.fill();

    drawRidge(farScroll, groundY - height * 0.02, height * 0.16, '#4a3358');
    drawRidge(nearScroll, groundY, height * 0.1, '#37243f');

    const groundGrad = ctx.createLinearGradient(0, groundY, 0, height);
    groundGrad.addColorStop(0, '#d9a066');
    groundGrad.addColorStop(1, '#a86b3f');
    ctx.fillStyle = groundGrad;
    ctx.fillRect(0, groundY, width, height - groundY);
    ctx.fillStyle = '#7a4a2a';
    ctx.fillRect(0, groundY, width, 3);

    ctx.strokeStyle = 'rgba(122, 74, 42, 0.5)';
    ctx.lineWidth = 3;
    const tickOffset = groundScroll % 46;
    ctx.beginPath();
    for (let x = -tickOffset; x < width; x += 46) {
      ctx.moveTo(x, groundY + 14);
      ctx.lineTo(x + 18, groundY + 14);
    }
    ctx.stroke();

    ctx.fillStyle = 'rgba(251, 234, 217, 0.65)';
    for (const p of particles) {
      ctx.globalAlpha = 1 - p.age / p.life;
      ctx.fillRect(p.x, p.y, 4, 4);
    }
    ctx.globalAlpha = 1;

    for (const o of obstacles) {
      roundRectPath(o.x, o.y, o.w, o.h, 6);
      ctx.fillStyle = '#4a3547';
      ctx.fill();
      ctx.fillStyle = '#33222f';
      ctx.fillRect(o.x, o.y + o.h - 5, o.w, 5);
    }

    ctx.save();
    ctx.translate(player.x + PLAYER_SIZE / 2, player.y + PLAYER_SIZE / 2);
    ctx.rotate(player.rotation);
    roundRectPath(-PLAYER_SIZE / 2, -PLAYER_SIZE / 2, PLAYER_SIZE, PLAYER_SIZE, 10);
    ctx.fillStyle = '#ffb545';
    ctx.fill();
    ctx.fillStyle = '#3a1f05';
    ctx.fillRect(-PLAYER_SIZE / 2 + 25, -PLAYER_SIZE / 2 + 9, 6, 6);
    ctx.restore();
  }

  let lastTime = null;
  function loop(ts) {
    if (!running) return;
    if (lastTime === null) lastTime = ts;
    let dt = Math.min((ts - lastTime) / 1000, 0.033);
    lastTime = ts;
    update(dt);
    draw();
    requestAnimationFrame(loop);
  }

  function startGame() {
    resize();
    resetState();
    running = true;
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
    finalScoreEl.textContent = String(score);
    finalBestEl.textContent = String(best);
    bestValueEl.textContent = String(best);
    gameoverScreen.classList.remove('hidden');
  }

  function handleInput(e) {
    if (e.type === 'keydown') {
      if (e.code !== 'Space' && e.code !== 'ArrowUp') return;
      e.preventDefault();
    }
    jump();
  }

  canvas.addEventListener('pointerdown', jump);
  window.addEventListener('keydown', handleInput);
  startBtn.addEventListener('click', startGame);
  retryBtn.addEventListener('click', startGame);

  resize();
  bestValueEl.textContent = String(loadBest());
  draw();
})();
