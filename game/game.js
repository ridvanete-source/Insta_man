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
  const levelBadgeEl = document.getElementById('level-badge');
  const toastEl = document.getElementById('toast');
  const muteBtn = document.getElementById('mute-btn');
  const finalScoreEl = document.getElementById('final-score');
  const finalBestEl = document.getElementById('final-best');
  const themeEyebrowEl = document.getElementById('theme-eyebrow');
  const themeDescEl = document.getElementById('theme-desc');
  const gameoverTitleEl = document.getElementById('gameover-title');
  const themePickerEl = document.getElementById('theme-picker');
  const root = document.documentElement;

  const THEME_STORAGE_KEY = 'hoopwave-theme';

  const THEMES = {
    desert: {
      label: 'Çöl', emoji: '🏜️', eyebrow: 'Çöl Koşusu',
      desc: 'Ekrana dokun ya da <b>boşluk</b> tuşuna bas, kayalardan zıplayarak kaç.',
      loseTitle: 'Toza Yenildin',
      locomotion: 'ground',
      css: {
        accent: '#ffb545', accentLight: '#ffcf6e', accentDark: '#a85f1d',
        cream: '#fbead9', creamDim: '#e7cdb8',
        panel: 'rgba(36, 23, 51, 0.72)', panelBorder: 'rgba(255, 224, 138, 0.18)',
        btnInk: '#3a1f05',
      },
    },
    ocean: {
      label: 'Deniz', emoji: '🐟', eyebrow: 'Mercan Resifi',
      desc: 'Ekrana dokun ya da <b>boşluk</b> tuşuna bas, yukarı yüz ve köpekbalıklarından kaç.',
      loseTitle: 'Ağa Takıldın',
      locomotion: 'free',
      bandTop: 0.14, bandBottom: 0.84,
      css: {
        accent: '#4fd6e8', accentLight: '#8fe9f2', accentDark: '#0f7a8a',
        cream: '#eafcff', creamDim: '#bfe9ef',
        panel: 'rgba(6, 38, 48, 0.74)', panelBorder: 'rgba(150, 230, 240, 0.22)',
        btnInk: '#052a30',
      },
    },
    air: {
      label: 'Gökyüzü', emoji: '🐦', eyebrow: 'Bulut Katmanları',
      desc: 'Ekrana dokun ya da <b>boşluk</b> tuşuna bas, kanat çırp ve avcılardan/kapanlardan kaç.',
      loseTitle: 'Kapana Yakalandın',
      locomotion: 'free',
      bandTop: 0.12, bandBottom: 0.86,
      css: {
        accent: '#ffd166', accentLight: '#ffe29b', accentDark: '#b5860f',
        cream: '#f3f8ff', creamDim: '#cddcee',
        panel: 'rgba(13, 32, 56, 0.74)', panelBorder: 'rgba(255, 255, 255, 0.2)',
        btnInk: '#3a2705',
      },
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
  const FREE_GRAVITY = 1300;
  const FREE_FLAP_VELOCITY = -420;
  const PLAYER_SIZE = 42;
  const BASE_SPEED = 380;
  const LEVEL_STEP = 25;
  const BEAT = 0.42; // matches the procedural music tempo below — obstacle cadence locks to it

  function beatsForLevel(lvl) {
    if (lvl >= 5) return 1;
    if (lvl >= 3) return 1.5;
    if (lvl >= 1) return 2;
    return 3;
  }

  let player, obstacles, particles;
  let speed, spawnTimer, spawnInterval, elapsed, score, best;
  let level;
  let farScroll = 0, groundScroll = 0;
  let running = false;
  let toastTimer = null;

  function showToast(text) {
    toastEl.textContent = text;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove('show'), 1700);
  }

  function updateLevelBadge() {
    levelBadgeEl.textContent = 'Seviye ' + (level + 1);
  }

  // ---- procedural background music (Web Audio, no external assets) ----
  const SCALES = {
    desert: [220.0, 261.63, 293.66, 329.63, 392.0],
    ocean: [196.0, 233.08, 261.63, 311.13, 349.23],
    air: [329.63, 392.0, 440.0, 523.25, 587.33],
  };
  let musicOn = localStorage.getItem('hoopwave-muted') !== '1';
  let audioCtx = null;
  let musicGain = null;
  let musicStarted = false;
  let nextNoteTime = 0;
  let noteIndex = 0;

  function updateMuteIcon() {
    muteBtn.textContent = musicOn ? '🔊' : '🔇';
  }
  updateMuteIcon();

  function ensureAudio() {
    if (audioCtx) return true;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return false;
    audioCtx = new AC();
    musicGain = audioCtx.createGain();
    musicGain.gain.value = musicOn ? 0.16 : 0;
    musicGain.connect(audioCtx.destination);
    return true;
  }

  function playNote(freq, time, dur, type) {
    const osc = audioCtx.createOscillator();
    const g = audioCtx.createGain();
    osc.type = type || 'sine';
    osc.frequency.value = freq;
    g.gain.setValueAtTime(0, time);
    g.gain.linearRampToValueAtTime(0.55, time + 0.02);
    g.gain.exponentialRampToValueAtTime(0.001, time + dur);
    osc.connect(g);
    g.connect(musicGain);
    osc.start(time);
    osc.stop(time + dur + 0.05);
  }

  function scheduleMusic() {
    if (!audioCtx) return;
    const scale = SCALES[themeId] || SCALES.desert;
    while (nextNoteTime < audioCtx.currentTime + 0.6) {
      const freq = scale[noteIndex % scale.length] * (Math.random() < 0.15 ? 2 : 1);
      playNote(freq, nextNoteTime, 0.9, 'sine');
      if (noteIndex % 3 === 0) playNote(freq / 2, nextNoteTime, 1.4, 'triangle');
      noteIndex++;
      nextNoteTime += BEAT;
    }
    setTimeout(scheduleMusic, 180);
  }

  function startMusic() {
    if (!ensureAudio()) return;
    if (audioCtx.state === 'suspended') audioCtx.resume();
    if (musicStarted) return;
    musicStarted = true;
    nextNoteTime = audioCtx.currentTime + 0.1;
    noteIndex = 0;
    scheduleMusic();
  }

  function toggleMute() {
    musicOn = !musicOn;
    localStorage.setItem('hoopwave-muted', musicOn ? '0' : '1');
    if (musicGain && audioCtx) {
      musicGain.gain.linearRampToValueAtTime(musicOn ? 0.16 : 0, audioCtx.currentTime + 0.1);
    }
    updateMuteIcon();
  }
  muteBtn.addEventListener('click', toggleMute);

  // beat-synced flash: peaks right on the beat, decays until the next one
  function beatPhase() {
    const t = audioCtx ? audioCtx.currentTime : elapsed;
    const ph = (t % BEAT) / BEAT;
    return Math.pow(1 - ph, 3);
  }

  // ---- game state ----

  function bestKey() {
    return 'hoopwave-best-' + themeId;
  }
  function loadBest() {
    return Number(localStorage.getItem(bestKey()) || 0);
  }
  function saveBest(v) {
    localStorage.setItem(bestKey(), String(v));
  }

  function freeStartY() {
    return height * (theme.bandTop + theme.bandBottom) / 2 - PLAYER_SIZE / 2;
  }

  function resetState() {
    const isFree = theme.locomotion === 'free';
    player = {
      x: width * 0.18,
      y: isFree ? freeStartY() : groundY - PLAYER_SIZE,
      vy: 0,
      onGround: !isFree,
      rotation: 0,
    };
    obstacles = [];
    particles = [];
    speed = BASE_SPEED;
    spawnTimer = 0;
    level = 0;
    spawnInterval = BEAT * beatsForLevel(level);
    elapsed = 0;
    score = 0;
    best = loadBest();
    scoreEl.textContent = '0';
    bestValueEl.textContent = String(best);
    updateLevelBadge();
  }

  function jump() {
    if (!running) return;
    if (theme.locomotion === 'free') {
      player.vy = FREE_FLAP_VELOCITY;
    } else if (player.onGround) {
      player.vy = JUMP_VELOCITY;
      player.onGround = false;
    }
  }

  function spawnObstacle() {
    if (theme.locomotion === 'free') {
      const bandTopPx = height * theme.bandTop;
      const bandBottomPx = height * theme.bandBottom;
      const size = 34 + Math.random() * 16;
      const usable = Math.max(14, (bandBottomPx - bandTopPx) - size);
      const y = bandTopPx + Math.random() * usable;
      const spike = Math.random() < 0.5;
      obstacles.push({ x: width + size, y, w: size, h: size, passed: false, spike });
      if (level >= 3 && Math.random() < 0.3) {
        const y2 = bandTopPx + Math.random() * usable;
        obstacles.push({ x: width + size + speed * BEAT * 0.5, y: y2, w: size, h: size, passed: false, spike: !spike });
      }
      return;
    }
    const isTall = Math.random() < Math.min(0.65, 0.3 + level * 0.06);
    const w = isTall ? 26 : 34 + Math.random() * 16;
    const h = isTall ? 56 + Math.random() * 18 : 30 + Math.random() * 14;
    obstacles.push({ x: width + w, y: groundY - h, w, h, passed: false, spike: isTall });
    if (level >= 3 && Math.random() < 0.3) {
      const w2 = 30, h2 = 34 + Math.random() * 14;
      obstacles.push({ x: width + w + speed * BEAT * 0.55, y: groundY - h2, w: w2, h: h2, passed: false, spike: false });
    }
  }

  function update(dt) {
    elapsed += dt;
    speed = BASE_SPEED + level * 70 + Math.min(elapsed * 6, 40);
    spawnInterval = BEAT * beatsForLevel(level);
    farScroll += dt * 18;
    groundScroll += speed * dt;

    const isFree = theme.locomotion === 'free';

    if (isFree) {
      player.vy += FREE_GRAVITY * dt;
      player.y += player.vy * dt;
      const bandTopPx = height * theme.bandTop;
      const bandBottomPx = height * theme.bandBottom - PLAYER_SIZE;
      if (player.y < bandTopPx) {
        player.y = bandTopPx;
        player.vy = Math.max(player.vy, 0);
      } else if (player.y > bandBottomPx) {
        player.y = bandBottomPx;
        player.vy = Math.min(player.vy, 0);
      }
      player.rotation = Math.max(-0.5, Math.min(0.6, player.vy / 900));
    } else {
      player.vy += GRAVITY * dt;
      player.y += player.vy * dt;
      if (player.y >= groundY - PLAYER_SIZE) {
        player.y = groundY - PLAYER_SIZE;
        player.vy = 0;
        player.onGround = true;
      }
      player.rotation = player.onGround ? 0 : player.rotation + dt * 8;
    }

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
        const newLevel = Math.floor(score / LEVEL_STEP);
        if (newLevel > level) {
          level = newLevel;
          updateLevelBadge();
          showToast('⚡ Zorluk arttı!');
        }
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

    if (isFree) {
      if (Math.random() < 0.5) {
        particles.push({
          x: player.x + PLAYER_SIZE * 0.2,
          y: player.y + PLAYER_SIZE * 0.5,
          vx: -speed * 0.3 - Math.random() * 30,
          vy: Math.random() * 20 - 10,
          life: 0.7,
          age: 0,
        });
      }
    } else if (player.onGround && Math.random() < 0.4) {
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

  function roundRectPath(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function drawNeonGrid(color, y0, y1, spacing, alpha, offset) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.globalAlpha = alpha;
    ctx.lineWidth = 2;
    const off = offset % spacing;
    ctx.beginPath();
    for (let x = -off; x <= width; x += spacing) {
      ctx.moveTo(x, y0);
      ctx.lineTo(x, y1);
    }
    ctx.stroke();
    ctx.restore();
  }

  function drawNeonLine(y, color, glow) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.shadowColor = color;
    ctx.shadowBlur = glow;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
    ctx.restore();
  }

  function drawBackground() {
    ctx.fillStyle = '#05060b';
    ctx.fillRect(0, 0, width, height);

    const pulse = beatPhase();
    ctx.save();
    ctx.globalAlpha = 0.05 + pulse * 0.09;
    ctx.fillStyle = theme.css.accent;
    ctx.fillRect(0, 0, width, height);
    ctx.restore();

    const isFree = theme.locomotion === 'free';
    const topY = isFree ? height * theme.bandTop : groundY;
    const botY = isFree ? height * theme.bandBottom : height;

    drawNeonGrid(theme.css.accentDark, topY, botY, 130, 0.12, farScroll);
    drawNeonGrid(theme.css.accent, topY, botY, 60, 0.16, groundScroll);

    drawNeonLine(topY, theme.css.accent, 8 + pulse * 16);
    if (isFree) drawNeonLine(botY, theme.css.accent, 8 + pulse * 16);
  }

  function drawParticles() {
    ctx.save();
    ctx.fillStyle = theme.css.accentLight;
    for (const p of particles) {
      ctx.globalAlpha = (1 - p.age / p.life) * 0.8;
      ctx.fillRect(p.x - 2, p.y - 2, 4, 4);
    }
    ctx.restore();
  }

  function drawObstacleNeon(o) {
    const { x, y, w, h, spike } = o;
    ctx.save();
    ctx.shadowColor = theme.css.accent;
    ctx.shadowBlur = 14;
    ctx.fillStyle = theme.css.accent;
    ctx.globalAlpha = 0.22;
    if (spike) {
      ctx.beginPath();
      ctx.moveTo(x, y + h);
      ctx.lineTo(x + w / 2, y);
      ctx.lineTo(x + w, y + h);
      ctx.closePath();
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.strokeStyle = theme.css.accentLight;
      ctx.lineWidth = 2.5;
      ctx.stroke();
    } else {
      roundRectPath(x, y, w, h, 4);
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.strokeStyle = theme.css.accentLight;
      ctx.lineWidth = 2.5;
      roundRectPath(x, y, w, h, 4);
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawPlayer() {
    ctx.save();
    ctx.translate(player.x + PLAYER_SIZE / 2, player.y + PLAYER_SIZE / 2);
    ctx.rotate(player.rotation);
    ctx.shadowColor = theme.css.accentLight;
    ctx.shadowBlur = 18;
    ctx.fillStyle = theme.css.accent;
    roundRectPath(-PLAYER_SIZE / 2, -PLAYER_SIZE / 2, PLAYER_SIZE, PLAYER_SIZE, 8);
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.strokeStyle = theme.css.cream;
    ctx.lineWidth = 2;
    roundRectPath(-PLAYER_SIZE / 2, -PLAYER_SIZE / 2, PLAYER_SIZE, PLAYER_SIZE, 8);
    ctx.stroke();
    ctx.fillStyle = theme.css.btnInk;
    ctx.fillRect(PLAYER_SIZE / 2 - 15, -PLAYER_SIZE / 2 + 8, 6, 6);
    ctx.restore();
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);
    drawBackground();
    drawParticles();
    for (const o of obstacles) drawObstacleNeon(o);
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
    startMusic();
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
