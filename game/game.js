(function () {
  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');

  const scoreEl = document.getElementById('score');
  const bestValueEl = document.getElementById('best-value');
  const startScreen = document.getElementById('start-screen');
  const gameoverScreen = document.getElementById('gameover-screen');
  const startBtn = document.getElementById('start-btn');
  const retryBtn = document.getElementById('retry-btn');
  const changeThemeBtn = document.getElementById('change-theme-btn');
  const finalScoreEl = document.getElementById('final-score');
  const finalBestEl = document.getElementById('final-best');
  const themeEyebrowEl = document.getElementById('theme-eyebrow');
  const themeDescEl = document.getElementById('theme-desc');
  const gameoverTitleEl = document.getElementById('gameover-title');
  const themePickerEl = document.getElementById('theme-picker');
  const root = document.documentElement;

  const THEME_STORAGE_KEY = 'zipla-kac-theme';

  const THEMES = {
    desert: {
      label: 'Çöl', emoji: '🏜️', eyebrow: 'Çöl Koşusu',
      desc: 'Ekrana dokun ya da <b>boşluk</b> tuşuna bas, kayalardan zıplayarak kaç.',
      loseTitle: 'Toza Yenildin',
      css: {
        accent: '#ffb545', accentLight: '#ffcf6e', accentDark: '#a85f1d',
        cream: '#fbead9', creamDim: '#e7cdb8',
        panel: 'rgba(36, 23, 51, 0.72)', panelBorder: 'rgba(255, 224, 138, 0.18)',
        btnInk: '#3a1f05',
      },
      skyStops: ['#241b3a', '#6a3f6b', '#f0895a'],
      orbStyle: 'sun', orbColor: '#ffe08a', orbGlow: 'rgba(255, 177, 92, 0.55)',
      decorStyle: 'ridge', decorFar: '#4a3358', decorNear: '#37243f',
      groundTop: '#d9a066', groundBottom: '#a86b3f', groundRim: '#7a4a2a',
      tick: 'rgba(122, 74, 42, 0.5)',
      particle: 'rgba(251, 234, 217, 0.65)', particleStyle: 'dust',
      playerBody: '#ffb545', playerAccent: '#3a1f05', playerShape: 'runner',
      obstacleSet: [
        { shape: 'boulder', body: '#4a3547', shade: '#33222f' },
        { shape: 'spike', body: '#4a3547', shade: '#33222f' },
      ],
    },
    ocean: {
      label: 'Deniz', emoji: '🐟', eyebrow: 'Mercan Resifi',
      desc: 'Ekrana dokun ya da <b>boşluk</b> tuşuna bas, köpekbalıklarından zıplayarak kaç.',
      loseTitle: 'Ağa Takıldın',
      css: {
        accent: '#4fd6e8', accentLight: '#8fe9f2', accentDark: '#0f7a8a',
        cream: '#eafcff', creamDim: '#bfe9ef',
        panel: 'rgba(6, 38, 48, 0.74)', panelBorder: 'rgba(150, 230, 240, 0.22)',
        btnInk: '#052a30',
      },
      skyStops: ['#012636', '#0a5c73', '#3fc2d8'],
      orbStyle: 'sunbeam', orbColor: '#eafcff', orbGlow: 'rgba(180, 240, 255, 0.35)',
      decorStyle: 'ridge', decorFar: '#0f4a55', decorNear: '#0a3540',
      groundTop: '#e4c98a', groundBottom: '#b89a5e', groundRim: '#7d6636',
      tick: 'rgba(125, 102, 54, 0.5)',
      particle: 'rgba(210, 245, 255, 0.6)', particleStyle: 'bubble',
      playerBody: '#ff8a3d', playerAccent: '#241b12', playerShape: 'fish',
      obstacleSet: [
        { shape: 'finrock', body: '#5c7480', shade: '#374850' },
        { shape: 'urchin', body: '#2b2038', shade: '#1a1424' },
      ],
    },
    air: {
      label: 'Gökyüzü', emoji: '🐦', eyebrow: 'Bulut Katmanları',
      desc: 'Ekrana dokun ya da <b>boşluk</b> tuşuna bas, avcılardan ve kapanlardan zıplayarak kaç.',
      loseTitle: 'Kapana Yakalandın',
      css: {
        accent: '#ffd166', accentLight: '#ffe29b', accentDark: '#b5860f',
        cream: '#f3f8ff', creamDim: '#cddcee',
        panel: 'rgba(13, 32, 56, 0.74)', panelBorder: 'rgba(255, 255, 255, 0.2)',
        btnInk: '#3a2705',
      },
      skyStops: ['#0f2c52', '#3f6fa8', '#a9d8f0'],
      orbStyle: 'sun', orbColor: '#fff6d8', orbGlow: 'rgba(255, 246, 216, 0.45)',
      decorStyle: 'cloud', decorFar: '#6f93c2', decorNear: '#3f6fa8',
      groundTop: '#5a8f4f', groundBottom: '#3d6636', groundRim: '#2a4a26',
      tick: 'rgba(42, 74, 38, 0.5)',
      particle: 'rgba(255, 255, 255, 0.75)', particleStyle: 'feather',
      playerBody: '#3fa7ff', playerAccent: '#0a2338', playerShape: 'bird',
      obstacleSet: [
        { shape: 'hawk', body: '#5c3a28', shade: '#3a2417' },
        { shape: 'trap', body: '#8a8a8a', shade: '#4a4a4a' },
      ],
    },
  };
  const THEME_ORDER = ['desert', 'ocean', 'air'];

  let themeId = localStorage.getItem(THEME_STORAGE_KEY) || 'desert';
  if (!THEMES[themeId]) themeId = 'desert';
  let theme = THEMES[themeId];

  function applyThemeChrome() {
    theme = THEMES[themeId];
    const c = theme.css;
    root.style.setProperty('--accent', c.accent);
    root.style.setProperty('--accent-light', c.accentLight);
    root.style.setProperty('--accent-dark', c.accentDark);
    root.style.setProperty('--cream', c.cream);
    root.style.setProperty('--cream-dim', c.creamDim);
    root.style.setProperty('--panel', c.panel);
    root.style.setProperty('--panel-border', c.panelBorder);
    root.style.setProperty('--btn-ink', c.btnInk);
    themeEyebrowEl.textContent = theme.eyebrow;
    themeDescEl.innerHTML = theme.desc;
    gameoverTitleEl.textContent = theme.loseTitle;
    bestValueEl.textContent = String(loadBest());
    renderThemePicker();
  }

  function renderThemePicker() {
    themePickerEl.innerHTML = '';
    for (const id of THEME_ORDER) {
      const t = THEMES[id];
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'theme-chip' + (id === themeId ? ' active' : '');
      chip.innerHTML = '<span class="chip-emoji">' + t.emoji + '</span><span class="chip-label">' + t.label + '</span>';
      chip.addEventListener('click', () => {
        if (themeId === id) return;
        themeId = id;
        localStorage.setItem(THEME_STORAGE_KEY, themeId);
        applyThemeChrome();
        resize();
        resetState();
        draw();
      });
      themePickerEl.appendChild(chip);
    }
  }

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
  window.addEventListener('resize', () => { resize(); if (!running) draw(); });

  const GRAVITY = 2200;
  const JUMP_VELOCITY = -820;
  const PLAYER_SIZE = 42;

  let player, obstacles, particles;
  let speed, spawnTimer, spawnInterval, elapsed, score, best;
  let farScroll = 0, nearScroll = 0, groundScroll = 0;
  let running = false;

  function bestKey() {
    return 'zipla-kac-best-' + themeId;
  }
  function loadBest() {
    return Number(localStorage.getItem(bestKey()) || 0);
  }
  function saveBest(v) {
    localStorage.setItem(bestKey(), String(v));
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
    const variant = theme.obstacleSet[isTall ? 0 : 1];
    obstacles.push({ x: width + w, y: groundY - h, w, h, passed: false, variant });
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

  function drawClouds(offset, baseY, amp, color) {
    ctx.fillStyle = color;
    const step = 74;
    const shift = offset % step;
    for (let x = -step * 2; x <= width + step; x += step) {
      const cx = x - shift;
      const cy = baseY + Math.sin((x + offset) * 0.01) * amp * 0.4;
      const r = amp * 0.55 + 8 * Math.sin((x + offset) * 0.02);
      const rad = Math.max(10, r);
      ctx.beginPath();
      ctx.arc(cx, cy, rad, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx + rad * 0.7, cy + rad * 0.2, rad * 0.7, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx - rad * 0.6, cy + rad * 0.25, rad * 0.55, 0, Math.PI * 2);
      ctx.fill();
    }
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

  function drawOrb() {
    const ox = width * 0.76, oy = height * 0.22, r = Math.min(width, height) * 0.16;

    if (theme.orbStyle === 'sunbeam') {
      ctx.save();
      ctx.globalAlpha = 0.22;
      ctx.fillStyle = theme.orbColor;
      for (let i = -1; i <= 1; i++) {
        ctx.beginPath();
        ctx.moveTo(ox + i * r * 1.6 - 16, 0);
        ctx.lineTo(ox + i * r * 1.6 + 16, 0);
        ctx.lineTo(ox + i * r * 3.6 + 46, groundY);
        ctx.lineTo(ox + i * r * 3.6 - 46, groundY);
        ctx.closePath();
        ctx.fill();
      }
      ctx.restore();
      const glow = ctx.createRadialGradient(ox, 0, 0, ox, 0, r * 2.4);
      glow.addColorStop(0, theme.orbGlow);
      glow.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, width, groundY);
      return;
    }

    const glow = ctx.createRadialGradient(ox, oy, 0, ox, oy, r * 2.2);
    glow.addColorStop(0, theme.orbGlow);
    glow.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, width, groundY);
    ctx.beginPath();
    ctx.arc(ox, oy, r * 0.55, 0, Math.PI * 2);
    ctx.fillStyle = theme.orbColor;
    ctx.fill();
  }

  function drawObstacle(o) {
    const { x, y, w, h } = o;
    const { shape, body, shade } = o.variant;

    if (shape === 'boulder') {
      roundRectPath(x, y, w, h, 6);
      ctx.fillStyle = body;
      ctx.fill();
      ctx.fillStyle = shade;
      ctx.fillRect(x, y + h - 5, w, 5);
    } else if (shape === 'spike' || shape === 'finrock' || shape === 'hawk') {
      ctx.beginPath();
      ctx.moveTo(x, y + h);
      ctx.lineTo(x + w * 0.18, y + h * 0.1);
      ctx.lineTo(x + w * 0.5, y + h * 0.5);
      ctx.lineTo(x + w * 0.82, y);
      ctx.lineTo(x + w, y + h);
      ctx.closePath();
      ctx.fillStyle = body;
      ctx.fill();
      ctx.fillStyle = shade;
      ctx.fillRect(x, y + h - 4, w, 4);
    } else if (shape === 'urchin' || shape === 'trap') {
      const cx = x + w / 2, cy = y + h * 0.6, r = Math.min(w, h) * 0.42;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fillStyle = body;
      ctx.fill();
      ctx.strokeStyle = shade;
      ctx.lineWidth = 3;
      const spikes = 8;
      for (let i = 0; i < spikes; i++) {
        const a = (i / spikes) * Math.PI * 2;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(a) * r * 0.7, cy + Math.sin(a) * r * 0.7);
        ctx.lineTo(cx + Math.cos(a) * (r + h * 0.32), cy + Math.sin(a) * (r + h * 0.32));
        ctx.stroke();
      }
    }
  }

  function drawPlayer() {
    ctx.save();
    ctx.translate(player.x + PLAYER_SIZE / 2, player.y + PLAYER_SIZE / 2);
    ctx.rotate(player.rotation);

    if (theme.playerShape === 'fish') {
      ctx.beginPath();
      ctx.ellipse(0, 0, PLAYER_SIZE * 0.5, PLAYER_SIZE * 0.36, 0, 0, Math.PI * 2);
      ctx.fillStyle = theme.playerBody;
      ctx.fill();
      ctx.beginPath();
      ctx.moveTo(-PLAYER_SIZE * 0.46, 0);
      ctx.lineTo(-PLAYER_SIZE * 0.78, -PLAYER_SIZE * 0.26);
      ctx.lineTo(-PLAYER_SIZE * 0.78, PLAYER_SIZE * 0.26);
      ctx.closePath();
      ctx.fill();
      ctx.beginPath();
      ctx.moveTo(-PLAYER_SIZE * 0.05, -PLAYER_SIZE * 0.34);
      ctx.lineTo(PLAYER_SIZE * 0.12, -PLAYER_SIZE * 0.55);
      ctx.lineTo(PLAYER_SIZE * 0.22, -PLAYER_SIZE * 0.3);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = theme.playerAccent;
      ctx.beginPath();
      ctx.arc(PLAYER_SIZE * 0.24, -PLAYER_SIZE * 0.08, 3.4, 0, Math.PI * 2);
      ctx.fill();
    } else if (theme.playerShape === 'bird') {
      ctx.beginPath();
      ctx.ellipse(0, 0, PLAYER_SIZE * 0.42, PLAYER_SIZE * 0.36, 0, 0, Math.PI * 2);
      ctx.fillStyle = theme.playerBody;
      ctx.fill();
      ctx.beginPath();
      ctx.moveTo(-PLAYER_SIZE * 0.05, PLAYER_SIZE * 0.02);
      ctx.lineTo(-PLAYER_SIZE * 0.62, -PLAYER_SIZE * 0.3);
      ctx.lineTo(-PLAYER_SIZE * 0.18, PLAYER_SIZE * 0.22);
      ctx.closePath();
      ctx.fill();
      ctx.beginPath();
      ctx.moveTo(PLAYER_SIZE * 0.38, -PLAYER_SIZE * 0.08);
      ctx.lineTo(PLAYER_SIZE * 0.62, 0);
      ctx.lineTo(PLAYER_SIZE * 0.38, PLAYER_SIZE * 0.1);
      ctx.closePath();
      ctx.fillStyle = theme.playerAccent;
      ctx.fill();
      ctx.fillStyle = '#fff';
      ctx.beginPath();
      ctx.arc(PLAYER_SIZE * 0.18, -PLAYER_SIZE * 0.1, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = theme.playerAccent;
      ctx.beginPath();
      ctx.arc(PLAYER_SIZE * 0.2, -PLAYER_SIZE * 0.1, 2, 0, Math.PI * 2);
      ctx.fill();
    } else {
      roundRectPath(-PLAYER_SIZE / 2, -PLAYER_SIZE / 2, PLAYER_SIZE, PLAYER_SIZE, 10);
      ctx.fillStyle = theme.playerBody;
      ctx.fill();
      ctx.fillStyle = theme.playerAccent;
      ctx.fillRect(PLAYER_SIZE / 2 - 17, -PLAYER_SIZE / 2 + 9, 6, 6);
    }

    ctx.restore();
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);

    const sky = ctx.createLinearGradient(0, 0, 0, groundY);
    sky.addColorStop(0, theme.skyStops[0]);
    sky.addColorStop(0.55, theme.skyStops[1]);
    sky.addColorStop(1, theme.skyStops[2]);
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, width, groundY);

    drawOrb();

    if (theme.decorStyle === 'cloud') {
      drawClouds(farScroll, groundY - height * 0.3, height * 0.08, theme.decorFar);
      drawClouds(nearScroll, groundY - height * 0.14, height * 0.065, theme.decorNear);
    } else {
      drawRidge(farScroll, groundY - height * 0.02, height * 0.16, theme.decorFar);
      drawRidge(nearScroll, groundY, height * 0.1, theme.decorNear);
    }

    const groundGrad = ctx.createLinearGradient(0, groundY, 0, height);
    groundGrad.addColorStop(0, theme.groundTop);
    groundGrad.addColorStop(1, theme.groundBottom);
    ctx.fillStyle = groundGrad;
    ctx.fillRect(0, groundY, width, height - groundY);
    ctx.fillStyle = theme.groundRim;
    ctx.fillRect(0, groundY, width, 3);

    ctx.strokeStyle = theme.tick;
    ctx.lineWidth = 3;
    const tickOffset = groundScroll % 46;
    ctx.beginPath();
    for (let x = -tickOffset; x < width; x += 46) {
      ctx.moveTo(x, groundY + 14);
      ctx.lineTo(x + 18, groundY + 14);
    }
    ctx.stroke();

    ctx.fillStyle = theme.particle;
    for (const p of particles) {
      ctx.globalAlpha = 1 - p.age / p.life;
      if (theme.particleStyle === 'bubble') {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
        ctx.fill();
      } else if (theme.particleStyle === 'feather') {
        ctx.beginPath();
        ctx.ellipse(p.x, p.y, 5, 2.4, p.age * 4, 0, Math.PI * 2);
        ctx.fill();
      } else {
        ctx.fillRect(p.x, p.y, 4, 4);
      }
    }
    ctx.globalAlpha = 1;

    for (const o of obstacles) drawObstacle(o);
    drawPlayer();
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

  function showStartScreen() {
    running = false;
    gameoverScreen.classList.add('hidden');
    startScreen.classList.remove('hidden');
    applyThemeChrome();
    resize();
    resetState();
    draw();
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
  changeThemeBtn.addEventListener('click', showStartScreen);

  resize();
  applyThemeChrome();
  resetState();
  draw();
})();
