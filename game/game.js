(function () {
  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');

  const scoreEl = document.getElementById('score');
  const bestValueEl = document.getElementById('best-value');
  const startScreen = document.getElementById('start-screen');
  const gameoverScreen = document.getElementById('gameover-screen');
  const startBtn = document.getElementById('start-btn');
  const retryBtn = document.getElementById('retry-btn');
  const continueBtn = document.getElementById('continue-btn');
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

  const THEME_STORAGE_KEY = 'zipla-kac-theme';

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
      skyStops: ['#241b3a', '#6a3f6b', '#f0895a'],
      orbStyle: 'sun', orbColor: '#ffe08a', orbGlow: 'rgba(255, 177, 92, 0.55)',
      decorFar: '#4a3358', decorNear: '#37243f',
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
      skyStops: ['#012636', '#0a5c73', '#3fc2d8'],
      orbStyle: 'sunbeam', orbColor: '#eafcff', orbGlow: 'rgba(180, 240, 255, 0.35)',
      topDecorStyle: 'shimmer', topDecorColor: '#bff3ff', topDecorColor2: 'rgba(180,240,255,0.28)',
      bottomDecorStyle: 'coral', bottomDecorColor: '#0a3540', bottomDecorColor2: '#0f4a55',
      particle: 'rgba(210, 245, 255, 0.6)', particleStyle: 'bubble',
      playerBody: '#ff8a3d', playerAccent: '#241b12', playerShape: 'fish',
      obstacleSet: [
        { shape: 'creature', body: '#5c7480', shade: '#374850' },
        { shape: 'orb', body: '#2b2038', shade: '#1a1424' },
      ],
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
      skyStops: ['#0f2c52', '#3f6fa8', '#a9d8f0'],
      orbStyle: 'sun', orbColor: '#fff6d8', orbGlow: 'rgba(255, 246, 216, 0.45)',
      topDecorStyle: 'cloud', topDecorColor: '#7fa3d6', topDecorColor2: '#9fbfe8',
      bottomDecorStyle: 'cloud', bottomDecorColor: '#3f6fa8', bottomDecorColor2: '#5583bd',
      particle: 'rgba(255, 255, 255, 0.75)', particleStyle: 'feather',
      playerBody: '#3fa7ff', playerAccent: '#0a2338', playerShape: 'bird',
      obstacleSet: [
        { shape: 'creature', body: '#5c3a28', shade: '#3a2417' },
        { shape: 'orb', body: '#8a8a8a', shade: '#4a4a4a' },
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
  const FREE_GRAVITY = 1300;
  const FREE_FLAP_VELOCITY = -420;
  const PLAYER_SIZE = 42;
  const BASE_SPEED = 380;
  const LEVEL_STEP = 25;

  let player, obstacles, particles;
  let speed, spawnTimer, spawnInterval, elapsed, score, best;
  let level, checkpoint, checkpointReady;
  let farScroll = 0, nearScroll = 0, groundScroll = 0, flapPhase = 0;
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
  let musicOn = localStorage.getItem('zipla-kac-muted') !== '1';
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
      nextNoteTime += 0.42;
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
    localStorage.setItem('zipla-kac-muted', musicOn ? '0' : '1');
    if (musicGain && audioCtx) {
      musicGain.gain.linearRampToValueAtTime(musicOn ? 0.16 : 0, audioCtx.currentTime + 0.1);
    }
    updateMuteIcon();
  }
  muteBtn.addEventListener('click', toggleMute);

  // ---- game state ----

  function bestKey() {
    return 'zipla-kac-best-' + themeId;
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
    spawnInterval = 1.3;
    elapsed = 0;
    flapPhase = 0;
    score = 0;
    level = 0;
    checkpoint = 0;
    checkpointReady = false;
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
      const size = 38 + Math.random() * 18;
      const usable = Math.max(14, (bandBottomPx - bandTopPx) - size);
      const y = bandTopPx + Math.random() * usable;
      const variant = theme.obstacleSet[Math.random() < 0.5 ? 0 : 1];
      obstacles.push({ x: width + size, y, w: size, h: size, passed: false, variant });
      return;
    }
    const tallChance = Math.min(0.65, 0.35 + level * 0.05);
    const isTall = Math.random() < tallChance;
    const w = isTall ? 26 : 32 + Math.random() * 18;
    const h = isTall ? 60 + Math.random() * 20 : 30 + Math.random() * 16;
    const variant = theme.obstacleSet[isTall ? 0 : 1];
    obstacles.push({ x: width + w, y: groundY - h, w, h, passed: false, variant });
  }

  function update(dt) {
    elapsed += dt;
    speed = BASE_SPEED + elapsed * 14 + level * 55;
    const minInterval = Math.max(0.38, 0.72 - level * 0.06);
    spawnInterval = Math.max(minInterval, 1.3 - elapsed * 0.01);
    farScroll += dt * 18;
    nearScroll += dt * 46;
    groundScroll += speed * dt;
    flapPhase += dt * (theme.playerShape === 'bird' ? 12 : theme.playerShape === 'fish' ? 8 : 0);

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
          checkpoint = level * LEVEL_STEP;
          checkpointReady = true;
          updateLevelBadge();
          showToast('🚩 ' + checkpoint + ' puan · Zorluk arttı!');
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
          vy: theme.particleStyle === 'bubble' ? -(30 + Math.random() * 40) : (Math.random() * 20 - 10),
          life: theme.particleStyle === 'bubble' ? 0.9 : 0.7,
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

  function ridgeY(x, offset, baseY, amp) {
    return baseY
      - amp * (0.55 + 0.45 * Math.sin((x + offset) * 0.0032))
      - amp * 0.35 * Math.sin((x + offset) * 0.009 + 1.7);
  }

  function drawRidge(offset, baseY, amp, color, bottomY) {
    ctx.beginPath();
    ctx.moveTo(0, bottomY);
    for (let x = 0; x <= width; x += 24) {
      ctx.lineTo(x, ridgeY(x, offset, baseY, amp));
    }
    ctx.lineTo(width, bottomY);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
  }

  function drawShimmerLine(offset, baseY, amp, color) {
    ctx.save();
    ctx.globalAlpha = 0.55;
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    for (let x = 0; x <= width; x += 20) {
      const yy = ridgeY(x, offset, baseY, amp);
      if (x === 0) ctx.moveTo(x, yy); else ctx.lineTo(x, yy);
    }
    ctx.stroke();
    ctx.restore();
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
    const ox = width * 0.76, oy = height * 0.2, r = Math.min(width, height) * 0.15;

    if (theme.orbStyle === 'sunbeam') {
      ctx.save();
      ctx.globalAlpha = 0.2;
      ctx.fillStyle = theme.orbColor;
      for (let i = -1; i <= 1; i++) {
        ctx.beginPath();
        ctx.moveTo(ox + i * r * 1.6 - 16, 0);
        ctx.lineTo(ox + i * r * 1.6 + 16, 0);
        ctx.lineTo(ox + i * r * 3.6 + 46, height);
        ctx.lineTo(ox + i * r * 3.6 - 46, height);
        ctx.closePath();
        ctx.fill();
      }
      ctx.restore();
      const glow = ctx.createRadialGradient(ox, 0, 0, ox, 0, r * 2.4);
      glow.addColorStop(0, theme.orbGlow);
      glow.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, width, height);
      return;
    }

    const glow = ctx.createRadialGradient(ox, oy, 0, ox, oy, r * 2.2);
    glow.addColorStop(0, theme.orbGlow);
    glow.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, width, height);
    ctx.beginPath();
    ctx.arc(ox, oy, r * 0.55, 0, Math.PI * 2);
    ctx.fillStyle = theme.orbColor;
    ctx.fill();
  }

  function drawCreatureObstacle(x, y, w, h, body, shade) {
    const cx = x + w / 2, cy = y + h / 2;
    ctx.beginPath();
    ctx.ellipse(cx, cy, w * 0.5, h * 0.32, 0, 0, Math.PI * 2);
    ctx.fillStyle = body;
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(cx - w * 0.06, cy - h * 0.26);
    ctx.lineTo(cx + w * 0.14, cy - h * 0.62);
    ctx.lineTo(cx + w * 0.3, cy - h * 0.2);
    ctx.closePath();
    ctx.fillStyle = shade;
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(cx - w * 0.46, cy);
    ctx.lineTo(cx - w * 0.72, cy - h * 0.3);
    ctx.lineTo(cx - w * 0.72, cy + h * 0.3);
    ctx.closePath();
    ctx.fillStyle = shade;
    ctx.fill();
  }

  function drawOrbObstacle(x, y, w, h, body, shade) {
    const cx = x + w / 2, cy = y + h / 2, r = Math.min(w, h) * 0.4;
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
      ctx.lineTo(cx + Math.cos(a) * (r + h * 0.3), cy + Math.sin(a) * (r + h * 0.3));
      ctx.stroke();
    }
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
    } else if (shape === 'spike') {
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
    } else if (shape === 'creature') {
      drawCreatureObstacle(x, y, w, h, body, shade);
    } else if (shape === 'orb') {
      drawOrbObstacle(x, y, w, h, body, shade);
    }
  }

  function drawPlayer() {
    ctx.save();
    ctx.translate(player.x + PLAYER_SIZE / 2, player.y + PLAYER_SIZE / 2);
    ctx.rotate(player.rotation);

    if (theme.playerShape === 'fish') {
      const tailWag = Math.sin(flapPhase) * 0.35;
      ctx.beginPath();
      ctx.ellipse(0, 0, PLAYER_SIZE * 0.5, PLAYER_SIZE * 0.36, 0, 0, Math.PI * 2);
      ctx.fillStyle = theme.playerBody;
      ctx.fill();
      ctx.save();
      ctx.translate(-PLAYER_SIZE * 0.46, 0);
      ctx.rotate(tailWag);
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(-PLAYER_SIZE * 0.32, -PLAYER_SIZE * 0.26);
      ctx.lineTo(-PLAYER_SIZE * 0.32, PLAYER_SIZE * 0.26);
      ctx.closePath();
      ctx.fillStyle = theme.playerBody;
      ctx.fill();
      ctx.restore();
      ctx.beginPath();
      ctx.moveTo(-PLAYER_SIZE * 0.05, -PLAYER_SIZE * 0.34);
      ctx.lineTo(PLAYER_SIZE * 0.12, -PLAYER_SIZE * 0.55);
      ctx.lineTo(PLAYER_SIZE * 0.22, -PLAYER_SIZE * 0.3);
      ctx.closePath();
      ctx.fillStyle = theme.playerBody;
      ctx.fill();
      ctx.fillStyle = theme.playerAccent;
      ctx.beginPath();
      ctx.arc(PLAYER_SIZE * 0.24, -PLAYER_SIZE * 0.08, 3.4, 0, Math.PI * 2);
      ctx.fill();
    } else if (theme.playerShape === 'bird') {
      const wingFlap = Math.sin(flapPhase) * 0.8;
      ctx.beginPath();
      ctx.ellipse(0, 0, PLAYER_SIZE * 0.42, PLAYER_SIZE * 0.36, 0, 0, Math.PI * 2);
      ctx.fillStyle = theme.playerBody;
      ctx.fill();
      ctx.save();
      ctx.translate(-PLAYER_SIZE * 0.05, 0);
      ctx.rotate(wingFlap);
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(-PLAYER_SIZE * 0.58, -PLAYER_SIZE * 0.3);
      ctx.lineTo(-PLAYER_SIZE * 0.14, PLAYER_SIZE * 0.24);
      ctx.closePath();
      ctx.fillStyle = theme.playerBody;
      ctx.fill();
      ctx.restore();
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

  function drawGroundScene() {
    const sky = ctx.createLinearGradient(0, 0, 0, groundY);
    sky.addColorStop(0, theme.skyStops[0]);
    sky.addColorStop(0.55, theme.skyStops[1]);
    sky.addColorStop(1, theme.skyStops[2]);
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, width, groundY);

    drawOrb();

    drawRidge(farScroll, groundY - height * 0.02, height * 0.16, theme.decorFar, groundY + 2);
    drawRidge(nearScroll, groundY, height * 0.1, theme.decorNear, groundY + 2);

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
      ctx.fillRect(p.x, p.y, 4, 4);
    }
    ctx.globalAlpha = 1;

    for (const o of obstacles) drawObstacle(o);
    drawPlayer();
  }

  function drawFreeScene() {
    const sky = ctx.createLinearGradient(0, 0, 0, height);
    sky.addColorStop(0, theme.skyStops[0]);
    sky.addColorStop(0.55, theme.skyStops[1]);
    sky.addColorStop(1, theme.skyStops[2]);
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, width, height);

    drawOrb();

    const bandTopPx = height * theme.bandTop;
    const bandBottomPx = height * theme.bandBottom;

    if (theme.topDecorStyle === 'cloud') {
      drawClouds(farScroll, bandTopPx * 0.55, height * 0.065, theme.topDecorColor);
      drawClouds(nearScroll, bandTopPx * 0.88, height * 0.05, theme.topDecorColor2);
    } else if (theme.topDecorStyle === 'shimmer') {
      const glow = ctx.createLinearGradient(0, 0, 0, bandTopPx);
      glow.addColorStop(0, theme.topDecorColor2);
      glow.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, width, bandTopPx);
      drawShimmerLine(farScroll, bandTopPx * 0.92, 6, theme.topDecorColor);
    }

    if (theme.bottomDecorStyle === 'cloud') {
      drawClouds(nearScroll, bandBottomPx + (height - bandBottomPx) * 0.3, height * 0.065, theme.bottomDecorColor);
      drawClouds(farScroll, bandBottomPx + (height - bandBottomPx) * 0.72, height * 0.05, theme.bottomDecorColor2);
    } else if (theme.bottomDecorStyle === 'coral') {
      drawRidge(nearScroll, height * 0.98, height * 0.1, theme.bottomDecorColor, height);
      drawRidge(farScroll, height * 0.92, height * 0.07, theme.bottomDecorColor2, height);
    }

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
      }
    }
    ctx.globalAlpha = 1;

    for (const o of obstacles) drawObstacle(o);
    drawPlayer();
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);
    if (theme.locomotion === 'free') {
      drawFreeScene();
    } else {
      drawGroundScene();
    }
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
    if (checkpointReady) {
      continueBtn.textContent = 'Devam Et (' + checkpoint + ' puan)';
      continueBtn.classList.remove('hidden');
    } else {
      continueBtn.classList.add('hidden');
    }
    gameoverScreen.classList.remove('hidden');
  }

  function continueFromCheckpoint() {
    if (!checkpointReady) return;
    checkpointReady = false;
    score = checkpoint;
    level = Math.floor(checkpoint / LEVEL_STEP);
    elapsed = 0;
    flapPhase = 0;
    obstacles = [];
    particles = [];
    spawnTimer = 0;
    spawnInterval = 1.3;
    const isFree = theme.locomotion === 'free';
    player.x = width * 0.18;
    player.y = isFree ? freeStartY() : groundY - PLAYER_SIZE;
    player.vy = 0;
    player.onGround = !isFree;
    player.rotation = 0;
    scoreEl.textContent = String(score);
    updateLevelBadge();
    running = true;
    lastTime = null;
    startMusic();
    gameoverScreen.classList.add('hidden');
    requestAnimationFrame(loop);
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
  continueBtn.addEventListener('click', continueFromCheckpoint);
  changeThemeBtn.addEventListener('click', showStartScreen);

  resize();
  applyThemeChrome();
  resetState();
  draw();
})();
