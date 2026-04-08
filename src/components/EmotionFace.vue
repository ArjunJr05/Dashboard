<template>
  <svg
    class="emotion-face"
    :class="'ef-' + emotionKey"
    viewBox="0 0 60 60"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- Glow ring (emotion-coloured aura) -->
    <circle class="ef-glow" cx="30" cy="30" r="29" fill="none" stroke-width="2" opacity="0.35" />

    <!-- Face background -->
    <circle class="ef-bg" cx="30" cy="30" r="26" />

    <!-- Shine highlight -->
    <ellipse cx="22" cy="18" rx="7" ry="4" fill="rgba(255,255,255,0.22)" tfransform="rotate(-20,22,18)" />

    <!-- ─── ECSTATIC ─────────────────────────── -->
    <g v-if="emotionKey === 'ecstatic'" class="ef-ecstatic-group">
      <!-- Closed happy eyes (squinting) -->
      <path class="ef-eye-line" d="M14,23 Q17.5,19 21,23" stroke-width="3" stroke-linecap="round" fill="none"/>
      <path class="ef-eye-line" d="M39,23 Q42.5,19 46,23" stroke-width="3" stroke-linecap="round" fill="none"/>
      <!-- Big grin -->
      <path class="ef-mouth-line" d="M13,34 Q30,52 47,34" stroke-width="3.5" stroke-linecap="round" fill="none"/>
      <!-- Rosy cheeks -->
      <circle cx="12" cy="35" r="5" fill="rgba(255,100,100,0.25)" />
      <circle cx="48" cy="35" r="5" fill="rgba(255,100,100,0.25)" />
      <!-- Sparkle stars -->
      <g class="ef-sparkle">
        <text x="2"  y="12" font-size="8" fill="#FFD700">✦</text>
        <text x="48" y="10" font-size="6" fill="#FFD700">✦</text>
        <text x="50" y="22" font-size="5" fill="#ffe580">✦</text>
      </g>
    </g>

    <!-- ─── HAPPY ───────────────────────────── -->
    <g v-if="emotionKey === 'happy'" class="ef-happy-group">
      <!-- Eyes with shine -->
      <circle cx="20" cy="24" r="4" class="ef-pupil"/>
      <circle cx="21.5" cy="22.5" r="1.2" fill="rgba(255,255,255,0.7)"/>
      <circle cx="39" cy="24" r="4" class="ef-pupil"/>
      <circle cx="40.5" cy="22.5" r="1.2" fill="rgba(255,255,255,0.7)"/>
      <!-- Smile -->
      <path class="ef-mouth-line" d="M17,36 Q30,47 43,36" stroke-width="3" stroke-linecap="round" fill="none"/>
      <!-- Rosy cheeks -->
      <circle cx="13" cy="36" r="4.5" fill="rgba(255,120,120,0.2)" />
      <circle cx="47" cy="36" r="4.5" fill="rgba(255,120,120,0.2)" />
    </g>

    <!-- ─── NEUTRAL ─────────────────────────── -->
    <g v-if="emotionKey === 'neutral'" class="ef-neutral-group">
      <!-- Normal eyes -->
      <circle cx="20" cy="24" r="3.5" class="ef-pupil"/>
      <circle cx="21.2" cy="22.8" r="1" fill="rgba(255,255,255,0.6)"/>
      <circle cx="39" cy="24" r="3.5" class="ef-pupil"/>
      <circle cx="40.2" cy="22.8" r="1" fill="rgba(255,255,255,0.6)"/>
      <!-- Flat mouth -->
      <line x1="19" y1="37" x2="41" y2="37" class="ef-mouth-line" stroke-width="3" stroke-linecap="round"/>
    </g>

    <!-- ─── FRUSTRATED ──────────────────────── -->
    <g v-if="emotionKey === 'frustrated'" class="ef-frustrated-group">
      <!-- Narrowed eyes -->
      <ellipse cx="20" cy="24" rx="4" ry="2.5" class="ef-pupil"/>
      <ellipse cx="39" cy="24" rx="4" ry="2.5" class="ef-pupil"/>
      <!-- Brows angled inward-down -->
      <path class="ef-brow" d="M13,17 Q20,21 24,18" stroke-width="2.5" stroke-linecap="round" fill="none"/>
      <path class="ef-brow" d="M47,17 Q40,21 36,18" stroke-width="2.5" stroke-linecap="round" fill="none"/>
      <!-- Downward curve mouth -->
      <path class="ef-mouth-line" d="M17,41 Q30,33 43,41" stroke-width="3" stroke-linecap="round" fill="none"/>
      <!-- Steam puffs above head -->
      <g class="ef-steam">
        <circle cx="24" cy="5"  r="2.5" fill="currentColor" opacity="0.4"/>
        <circle cx="30" cy="3"  r="3"   fill="currentColor" opacity="0.4"/>
        <circle cx="36" cy="5"  r="2.5" fill="currentColor" opacity="0.4"/>
      </g>
    </g>

    <!-- ─── ANGRY ───────────────────────────── -->
    <g v-if="emotionKey === 'angry'" class="ef-angry-group">
      <!-- Angry slanted eyes -->
      <ellipse cx="20" cy="25" rx="4.5" ry="2.8" class="ef-pupil"/>
      <ellipse cx="39" cy="25" rx="4.5" ry="2.8" class="ef-pupil"/>
      <!-- Strong inward brows -->
      <path class="ef-brow" d="M11,15 Q19,22 25,17" stroke-width="3" stroke-linecap="round" fill="none"/>
      <path class="ef-brow" d="M49,15 Q41,22 35,17" stroke-width="3" stroke-linecap="round" fill="none"/>
      <!-- Deep frown -->
      <path class="ef-mouth-line" d="M16,44 Q30,30 44,44" stroke-width="3.5" stroke-linecap="round" fill="none"/>
      <!-- Rage vein on forehead -->
      <path d="M27,9 L29,13 L26,16" class="ef-vein" stroke-width="1.5" stroke-linecap="round" fill="none"/>
    </g>
  </svg>
</template>

<script setup>
defineProps({ emotionKey: String })
</script>

<style scoped>
.emotion-face {
  width: 54px;
  height: 54px;
  filter: drop-shadow(0 4px 14px rgba(0,0,0,0.45));
  overflow: visible;
}

/* ── Background & shared colours per emotion ── */
.ef-ecstatic   { color: #FFD700; }
.ef-happy      { color: #1db954; }
.ef-neutral    { color: #7888cc; }
.ef-frustrated { color: #ff6b35; }
.ef-angry      { color: #ff2d78; }

.ef-bg      { fill: currentColor; }
.ef-glow    { stroke: currentColor; }
.ef-pupil   { fill: rgba(0,0,0,0.75); }
.ef-eye-line{ stroke: rgba(0,0,0,0.75); }
.ef-mouth-line { stroke: rgba(0,0,0,0.75); }
.ef-brow    { stroke: rgba(0,0,0,0.7); }
.ef-vein    { stroke: rgba(140,0,0,0.8); }

/* ── ECSTATIC animations ── */
.ef-ecstatic-group {
  animation: ecstatic-bounce 0.55s ease-in-out infinite alternate;
  transform-origin: 30px 30px;
  transform-box: fill-box;
}
@keyframes ecstatic-bounce {
  from { transform: translateY(0) scale(1); }
  to   { transform: translateY(-4px) scale(1.07); }
}
.ef-sparkle {
  animation: sparkle-spin 1.2s linear infinite;
  transform-origin: 30px 30px;
  transform-box: fill-box;
}
@keyframes sparkle-spin {
  0%   { opacity:0.4; transform: scale(0.8) rotate(0deg); }
  50%  { opacity:1;   transform: scale(1.2) rotate(15deg); }
  100% { opacity:0.4; transform: scale(0.8) rotate(0deg); }
}
/* Face glow pulse for ecstatic */
.ef-ecstatic .ef-glow {
  animation: glow-pulse 0.8s ease-in-out infinite alternate;
}
@keyframes glow-pulse {
  from { opacity: 0.2; r: 28; }
  to   { opacity: 0.7; r: 30; }
}

/* ── HAPPY animations ── */
.ef-happy-group {
  animation: happy-sway 2.5s ease-in-out infinite alternate;
  transform-origin: 30px 30px;
  transform-box: fill-box;
}
@keyframes happy-sway {
  from { transform: rotate(-3deg) scale(1); }
  to   { transform: rotate(3deg) scale(1.04); }
}
.ef-happy .ef-glow {
  animation: glow-gentle 2s ease-in-out infinite alternate;
}
@keyframes glow-gentle {
  from { opacity: 0.15; }
  to   { opacity: 0.45; }
}

/* ── NEUTRAL animations ── */
.ef-neutral-group {
  animation: neutral-float 3s ease-in-out infinite alternate;
  transform-origin: 30px 30px;
  transform-box: fill-box;
}
@keyframes neutral-float {
  from { transform: translateY(0); }
  to   { transform: translateY(3px); }
}
/* Blink */
.ef-neutral .ef-pupil:first-child,
.ef-neutral .ef-pupil:nth-child(3) {
  animation: eye-blink 4s ease-in-out infinite;
  transform-origin: center;
  transform-box: fill-box;
}
@keyframes eye-blink {
  0%, 88%, 100% { transform: scaleY(1); }
  92%            { transform: scaleY(0.08); }
}

/* ── FRUSTRATED animations ── */
.ef-frustrated-group {
  animation: frustrated-shake 0.35s ease-in-out infinite alternate;
  transform-origin: 30px 30px;
  transform-box: fill-box;
}
@keyframes frustrated-shake {
  from { transform: rotate(-4deg) translateX(-1px); }
  to   { transform: rotate(4deg)  translateX(1px); }
}
.ef-steam {
  animation: steam-rise 1s ease-in-out infinite alternate;
  transform-origin: 30px 6px;
  transform-box: fill-box;
}
@keyframes steam-rise {
  from { transform: translateY(0) scaleX(1); opacity: 0.4; }
  to   { transform: translateY(-4px) scaleX(1.2); opacity: 0.7; }
}

/* ── ANGRY animations ── */
.ef-angry-group {
  animation: angry-rage 0.18s ease-in-out infinite alternate;
  transform-origin: 30px 30px;
  transform-box: fill-box;
}
@keyframes angry-rage {
  from { transform: rotate(-5deg) scale(1.04); }
  to   { transform: rotate(5deg)  scale(1.04); }
}
.ef-angry .ef-glow {
  animation: rage-glow 0.3s ease-in-out infinite alternate;
}
@keyframes rage-glow {
  from { opacity: 0.4; stroke-width: 2; }
  to   { opacity: 0.9; stroke-width: 4; }
}
.ef-vein {
  animation: vein-pulse 0.5s ease-in-out infinite alternate;
}
@keyframes vein-pulse {
  from { opacity: 0.3; }
  to   { opacity: 1; }
}
</style>
