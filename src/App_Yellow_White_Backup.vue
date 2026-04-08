<template>
  <!-- LOADING -->
  <div class="loading-screen" v-if="!appReady && !loadError">
    <div class="load-blob load-blob-1"></div>
    <div class="load-blob load-blob-2"></div>
    <div class="load-content">
      <img src="/arattai.png" style="height:72px;margin-bottom:24px;border-radius:16px;object-fit:contain;box-shadow:0 8px 32px rgba(0,0,0,0.6);" />
      <div class="load-title">ARATTAI</div>
      <div v-if="!loadError" class="conn-status">
        {{ appReady ? 'Launching...' : 'Connecting to Python Backend at 127.0.0.1:5050...' }}
      </div>
      <div class="load-bar"><div class="load-bar-fill"></div></div>
    </div>
  </div>

  <div class="error-screen" v-if="loadError">
    <div class="error-inner">⚠ Run the Python fetcher first, then refresh.</div>
  </div>

  <template v-if="appReady">
    <!-- ANIMATED BG -->
    <div class="scene-bg" :class="'scene-'+cur">
      <!-- Base gradient floor -->
      <div class="bg-floor"></div>
      <!-- Aurora beam layer -->
      <div class="aurora a1"></div>
      <div class="aurora a2"></div>
      <div class="aurora a3"></div>
      <!-- Floating orbs -->
      <div class="orb o1"></div>
      <div class="orb o2"></div>
      <div class="orb o3"></div>
      <div class="orb o4"></div>
      <!-- SVG mesh grid -->
      <svg class="mesh-grid" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">
        <defs>
          <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
            <circle cx="24" cy="24" r="1.2" fill="rgba(180,130,0,0.12)"/>
          </pattern>
          <radialGradient id="grid-fade" cx="50%" cy="50%" r="60%">
            <stop offset="0%" stop-color="white" stop-opacity="0"/>
            <stop offset="100%" stop-color="white" stop-opacity="1"/>
          </radialGradient>
          <mask id="grid-mask">
            <rect width="100%" height="100%" fill="white"/>
            <rect width="100%" height="100%" fill="url(#grid-fade)"/>
          </mask>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" mask="url(#grid-mask)"/>
      </svg>
      <!-- Vignette -->
      <div class="bg-vignette"></div>
      <!-- Film grain -->
      <div class="noise-layer"></div>
    </div>

    <!-- TOPBAR -->
    <div class="topbar">
      <div class="logo-area">
        <img src="/arattai.png" alt="Arattai" style="height:40px;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,0.4);" />
        <span class="logo-text">ARATTAI</span>
      </div>
      <div class="nav-pills">
        <div v-for="(n,i) in navs" :key="n" class="nav-pill" :class="{'pill-on': cur===i}" @click="go(i)">{{ n }}</div>
      </div>
      <div class="topbar-right">
        <span class="live-badge"><span class="ld"></span>LIVE</span>
        <span class="clk">{{ clock }}</span>
      </div>
    </div>

    <!-- SLIDES -->
    <div class="stage">

      <!-- SLIDE 0: OVERVIEW -->
      <div class="slide" :class="{sin: cur===0, sout: exitSlide===0}">
        <div class="slide-inner overview-slide">
          <div class="ov-headline">
            <div class="ov-eye">Arattai's</div>
            <div class="ov-big">TODAY IN</div>
            <div class="ov-big ov-outline">REVIEW</div>
          </div>
          <div class="stat-grid">
            <div class="stat-card sc-ios" style="--d:0s">
              <div class="sc-icon"><img src="/ios.png" style="height:36px;object-fit:contain;" /></div>
              <div class="sc-num">{{ ios.rating || '4.7' }}</div>
              <div class="sc-lbl">App Store</div>
              <div class="sc-stars-row">
                <span v-for="i in 5" :key="i" class="sc-star" :class="getStarClass(ios.rating||4.7,i)"></span>
              </div>
              <div class="sc-count">{{ fmtNum(ios.rating_count||19401) }} ratings</div>
            </div>
            <div class="stat-card sc-and" style="--d:.08s">
              <div class="sc-icon"><img src="/android.png" style="height:36px;object-fit:contain;" /></div>
              <div class="sc-num">{{ android.rating || '4.6' }}</div>
              <div class="sc-lbl">Play Store</div>
              <div class="sc-stars-row">
                <span v-for="i in 5" :key="i" class="sc-star" :class="getStarClass(android.rating||4.6,i)"></span>
              </div>
              <div class="sc-count">{{ fmtNum(android.rating_count||111857) }} ratings</div>
            </div>
            <div class="stat-card sc-news" style="--d:.16s">
              <div class="sc-big-icon">📰</div>
              <div class="sc-num">{{ gnews.posts?.length || 0 }}</div>
              <div class="sc-lbl">News Hits</div>
              <div class="sc-count">This Sprint</div>
            </div>
            <div class="stat-card sc-total" style="--d:.24s">
              <div class="sc-big-icon">💬</div>
              <div class="sc-num">{{ allRevs.length }}</div>
              <div class="sc-lbl">Total Reviews</div>
              <div class="sc-count">All Platforms</div>
            </div>
          </div>
        </div>
      </div>

      <!-- SLIDE 1: APP STORE — sentiment-grouped, one review at a time -->
      <div class="slide" :class="{sin: cur===1, sout: exitSlide===1}">
        <div class="slide-inner sentiment-slide">
          <div class="ss-header">
            <div class="ss-platform-badge ios-badge">
              <img src="/ios.png" class="ss-badge-img" />
              <div>
                <div class="ss-badge-name">App Store</div>
                <div class="ss-badge-stars">
                  <span v-for="i in 5" :key="i" class="ss-star" :class="getStarClass(ios.rating||4.7,i)"></span>
                  <span class="ss-rating">{{ ios.rating || '4.7' }}</span>
                </div>
              </div>
            </div>
            <div class="ss-title-block">
              <div class="ss-eyebrow">AI Sentiment Analysis · iOS</div>
              <div class="ss-big-title">App Store Reviews</div>
            </div>
          </div>

          <div class="ss-stage-area">
            <!-- LEFT: floating emotion identity (no box) -->
            <div class="ss-sentiment-float" :class="'sf-'+currentIosSentiment.key">
              <div class="sf-glow"></div>
              <EmotionFace :key="'ios-face-'+currentIosSentiment.key" :emotionKey="currentIosSentiment.key" class="ss-big-face" />
              <div class="sf-name">{{ currentIosSentiment.label }}</div>
              <div class="sf-count">{{ iosSentimentGroups[currentIosSentiment.key]?.length || 0 }} reviews</div>
              <div class="ss-progress-dots">
                <span v-for="(s,i) in sentimentOrder" :key="s.key" class="ss-sdot" :class="i===iosSentimentIdx ? 'sdot-on' : ''"></span>
              </div>
            </div>

            <!-- RIGHT: single review -->
            <div class="ss-review-panel">
              <transition name="rev-fade">
                <div v-if="currentIosReview" :key="iosRevKey" 
                  class="ss-review-card" 
                  :class="['rc-'+getEmotion(currentIosReview), 'sz-'+(currentIosReview.container_size || 'medium')]">
                  <div class="ss-rc-author-row">
                    <div class="ss-rc-avatar">{{ (currentIosReview.author||'A')[0].toUpperCase() }}</div>
                    <div class="ss-rc-meta">
                      <div class="ss-rc-author">{{ currentIosReview.author || 'Anonymous' }}</div>
                      <div class="ss-rc-stars-inline">
                        <span v-for="si in 5" :key="si" class="ss-rc-star-sm" :class="getStarClass(currentIosReview.rating||0, si)"></span>
                        <span class="ss-rc-date">· {{ currentIosReview.date || 'Recently' }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="ss-rc-quote-wrap">
                    <span class="ss-rc-quote-mark" :style="{color: sentimentColor(getEmotion(currentIosReview))}">"</span>
                    <div class="ss-rc-text">{{ currentIosReview.body }}</div>
                  </div>
                </div>
                <div v-else :key="'empty-ios'" class="ss-review-card ss-empty-card">
                  <div class="ss-empty-msg">No {{ currentIosSentiment.label }} reviews yet</div>
                </div>
              </transition>
              <div class="ss-rev-progress-bar">
                <div class="ss-rev-progress-fill" :style="{ width: iosRevProgressPct + '%', background: sentimentColor(currentIosSentiment.key) }"></div>
              </div>
            </div>
          </div>

          <!-- Sentiment group tabs bottom — emoji + count only, no repeated label -->
          <div class="ss-group-tabs">
            <div
              v-for="(s,i) in sentimentOrder" :key="s.key"
              class="ss-group-tab"
              :class="[('tab-'+s.key), i===iosSentimentIdx ? 'tab-on' : '']"
              @click="jumpIosSentiment(i)"
            >
              <span class="ss-tab-emoji">{{ s.emoji }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- SLIDE 2: PLAY STORE — same structure -->
      <div class="slide" :class="{sin: cur===2, sout: exitSlide===2}">
        <div class="slide-inner sentiment-slide">
          <div class="ss-header">
            <div class="ss-platform-badge and-badge">
              <img src="/android.png" class="ss-badge-img" />
              <div>
                <div class="ss-badge-name">Play Store</div>
                <div class="ss-badge-stars">
                  <span v-for="i in 5" :key="i" class="ss-star" :class="getStarClass(android.rating||4.6,i)"></span>
                  <span class="ss-rating">{{ android.rating || '4.6' }}</span>
                </div>
              </div>
            </div>
            <div class="ss-title-block">
              <div class="ss-eyebrow">AI Sentiment Analysis · Android</div>
              <div class="ss-big-title">Play Store Reviews</div>
            </div>
          </div>

          <div class="ss-stage-area">
            <!-- LEFT: floating emotion identity (no box) -->
            <div class="ss-sentiment-float" :class="'sf-'+currentAndSentiment.key">
              <div class="sf-glow"></div>
              <EmotionFace :key="'and-face-'+currentAndSentiment.key" :emotionKey="currentAndSentiment.key" class="ss-big-face" />
              <div class="sf-name">{{ currentAndSentiment.label }}</div>
              <div class="sf-count">{{ andSentimentGroups[currentAndSentiment.key]?.length || 0 }} reviews</div>
              <div class="ss-progress-dots">
                <span v-for="(s,i) in sentimentOrder" :key="s.key" class="ss-sdot" :class="i===andSentimentIdx ? 'sdot-on' : ''"></span>
              </div>
            </div>

            <div class="ss-review-panel">
              <transition name="rev-fade">
                <div v-if="currentAndReview" :key="andRevKey" 
                  class="ss-review-card" 
                  :class="['rc-'+getEmotion(currentAndReview), 'sz-'+(currentAndReview.container_size || 'medium')]">
                  <div class="ss-rc-author-row">
                    <div class="ss-rc-avatar">{{ (currentAndReview.author||'A')[0].toUpperCase() }}</div>
                    <div class="ss-rc-meta">
                      <div class="ss-rc-author">{{ currentAndReview.author || 'Anonymous' }}</div>
                      <div class="ss-rc-stars-inline">
                        <span v-for="si in 5" :key="si" class="ss-rc-star-sm" :class="getStarClass(currentAndReview.rating||0, si)"></span>
                        <span class="ss-rc-date">· {{ currentAndReview.date || 'Recently' }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="ss-rc-quote-wrap">
                    <span class="ss-rc-quote-mark" :style="{color: sentimentColor(getEmotion(currentAndReview))}">"</span>
                    <div class="ss-rc-text">{{ currentAndReview.body }}</div>
                  </div>
                </div>
                <div v-else :key="'empty-and'" class="ss-review-card ss-empty-card">
                  <div class="ss-empty-msg">No {{ currentAndSentiment.label }} reviews yet</div>
                </div>
              </transition>
              <div class="ss-rev-progress-bar">
                <div class="ss-rev-progress-fill" :style="{ width: andRevProgressPct + '%', background: sentimentColor(currentAndSentiment.key) }"></div>
              </div>
            </div>
          </div>

          <div class="ss-group-tabs">
            <div
              v-for="(s,i) in sentimentOrder" :key="s.key"
              class="ss-group-tab"
              :class="[('tab-'+s.key), i===andSentimentIdx ? 'tab-on' : '']"
              @click="jumpAndSentiment(i)"
            >
              <span class="ss-tab-emoji">{{ s.emoji }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- SLIDE 3: NEWS -->
      <div class="slide" :class="{sin: cur===3, sout: exitSlide===3}">
        <div class="slide-inner news-slide">
          <div class="news-left">
            <div class="nl-eyebrow">📰 Press Coverage</div>
            <div class="nl-big">IN THE<br>HEAD<br>LINES</div>
            <div class="news-count-pill">
              <span class="ncp-num">{{ gnews.posts?.length || 0 }}</span>
              <span class="ncp-txt">articles this sprint</span>
            </div>
          </div>
          <div class="news-frame">
            <transition :name="newsTransDir" mode="out-in">
              <div v-if="currentNews" :key="newsIndex" class="ns-poster">
                <div v-if="currentNews.image" class="ns-hero">
                  <img :src="currentNews.image" class="ns-hero-img" alt="" />
                  <div class="ns-hero-overlay"></div>
                </div>
                <div class="ns-content">
                  <div class="ns-source-badge">
                    <span class="ns-source">{{ currentNews.source }}</span>
                    <span class="ns-sep">·</span>
                    <span class="ns-date">{{ currentNews.date }}</span>
                  </div>
                  <h1 class="ns-title">{{ currentNews.title }}</h1>
                  <div class="ns-footer">
                    <div class="ns-qr-wrap">
                      <img
                        :src="'https://api.qrserver.com/v1/create-qr-code/?size=300x300&format=svg&data='+encodeURIComponent(currentNews.resolved_url||currentNews.url)"
                        class="ns-qr" alt="QR"
                      />
                      <span class="ns-qr-lbl">SCAN FOR FULL STORY</span>
                    </div>
                    <div class="ns-pagination">
                      <span
                        v-for="(p,pi) in (gnews.posts||[])" :key="pi"
                        class="ns-dot"
                        :class="pi===newsIndex ? 'ns-dot-on' : ''"
                      ></span>
                    </div>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </div>

    </div><!-- stage -->

    <!-- BOTTOM BAR -->
    <div class="bottom-bar">
      <div class="progress-rail"><div class="progress-fill" :style="{width:prog+'%'}"></div></div>
      <div class="bb-left">
        <span class="bb-brand">ARATTAI</span>
        <span class="bb-sep">·</span>
        <span class="bb-sprint">SPRINT 24 · Q2 2026</span>
      </div>
      <div class="bb-center">
        <div v-for="(_,i) in total" :key="i" class="bb-pip" :class="cur===i ? 'pipa' : ''" @click="go(i)"></div>
      </div>
      <div class="bb-right">
        <span class="bb-counter">{{ cur+1 }} / {{ total }}</span>
        <span class="bb-keys">← →</span>
      </div>
    </div>

  </template>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import EmotionFace from './components/EmotionFace.vue'

const API_BASE = ''  // Use Vite proxy — requests go to same origin and proxy forwards to Flask on :5050

const appReady  = ref(false)
const loadError = ref(false)
const data      = ref({})
const clock     = ref('')
const cur       = ref(0)
const exitSlide = ref(-1)
const total     = 4
const navs      = ['Overview','App Store','Play Store','News']
const prog      = ref(0)
// Duration: 5s per review × 10 reviews = 50s per store slide, 18s for others
const getDuration = () => {
  if (cur.value === 1) return Math.max(18000, (ios.value.reviews?.length || 10) * 5000)
  if (cur.value === 2) return Math.max(18000, (android.value.reviews?.length || 10) * 5000)
  return 18000
}

// Sentiment order: NEUTRAL first
const sentimentOrder = [
  { key: 'neutral',    label: 'Neutral',    emoji: '😐', color: '#7888cc' },
  { key: 'happy',      label: 'Happy',      emoji: '😊', color: '#1db954' },
  { key: 'ecstatic',   label: 'Ecstatic',   emoji: '🤩', color: '#FFD700' },
  { key: 'frustrated', label: 'Frustrated', emoji: '😤', color: '#ff6b35' },
  { key: 'angry',      label: 'Angry',      emoji: '😡', color: '#ff2d78' },
]

function sentimentColor(key) {
  return sentimentOrder.find(s => s.key === key)?.color || '#fff'
}

let iosRevTimeout = null
const iosSentimentIdx  = ref(0)
const iosRevIdxInGroup = ref(0)

const andSentimentIdx  = ref(0)
const andRevIdxInGroup = ref(0)
let andRevTimeout = null

const newsIndex    = ref(0)
const newsTransDir = ref('slide-next')
let newsLoopTimeout = null
let slideTimer = null, progRaf = null, progStart = null
let clockInt = null, dataInt = null

function tick() {
  clock.value = new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',second:'2-digit'})
}

const ios     = computed(() => data.value.appstore    || {})
const android = computed(() => data.value.playstore   || {})
const gnews   = computed(() => data.value.google_news || {})
const allRevs = computed(() => [...(ios.value.reviews||[]),...(android.value.reviews||[])])

function getEmotion(rev) {
  // Use LLM-classified sentiment if present (set by enrich_reviews.py)
  const llmSentiment = (rev.sentiment || '').toLowerCase()
  const validKeys = ['neutral', 'happy', 'ecstatic', 'frustrated', 'angry']
  if (validKeys.includes(llmSentiment)) return llmSentiment

  // Fallback: heuristic from star rating
  const r = Number(rev.rating) || 3
  if (r >= 5) return 'ecstatic'
  if (r >= 4) return 'happy'
  if (r === 3) return 'neutral'
  if (r === 2) return 'frustrated'
  return 'angry'
}

const iosSentimentGroups = computed(() => {
  const revs = ios.value.reviews || []
  const groups = {}
  sentimentOrder.forEach(s => { groups[s.key] = [] })
  revs.forEach(r => { const e = getEmotion(r); if (groups[e]) groups[e].push(r) })
  return groups
})

const andSentimentGroups = computed(() => {
  const revs = android.value.reviews || []
  const groups = {}
  sentimentOrder.forEach(s => { groups[s.key] = [] })
  revs.forEach(r => { const e = getEmotion(r); if (groups[e]) groups[e].push(r) })
  return groups
})

const currentIosSentiment = computed(() => sentimentOrder[iosSentimentIdx.value])
const currentAndSentiment = computed(() => sentimentOrder[andSentimentIdx.value])

const currentIosReview = computed(() => {
  const g = iosSentimentGroups.value[currentIosSentiment.value.key] || []
  return g[iosRevIdxInGroup.value] || null
})
const currentAndReview = computed(() => {
  const g = andSentimentGroups.value[currentAndSentiment.value.key] || []
  return g[andRevIdxInGroup.value] || null
})

const iosRevKey = computed(() => `ios-${iosSentimentIdx.value}-${iosRevIdxInGroup.value}`)
const andRevKey = computed(() => `and-${andSentimentIdx.value}-${andRevIdxInGroup.value}`)

const allIosRevCount = computed(() => (ios.value.reviews||[]).length)
const allAndRevCount = computed(() => (android.value.reviews||[]).length)

const iosRevProgressPct = computed(() => {
  const g = iosSentimentGroups.value[currentIosSentiment.value.key] || []
  if (!g.length) return 0
  return ((iosRevIdxInGroup.value + 1) / g.length) * 100
})
const andRevProgressPct = computed(() => {
  const g = andSentimentGroups.value[currentAndSentiment.value.key] || []
  if (!g.length) return 0
  return ((andRevIdxInGroup.value + 1) / g.length) * 100
})

function advanceIosReview() {
  const g = iosSentimentGroups.value[currentIosSentiment.value.key] || []
  if (iosRevIdxInGroup.value < g.length - 1) {
    iosRevIdxInGroup.value++
  } else {
    // Move to next sentiment group that has reviews
    let nextIdx = (iosSentimentIdx.value + 1) % sentimentOrder.length
    let looped = 0
    while (looped < sentimentOrder.length) {
      const nextG = iosSentimentGroups.value[sentimentOrder[nextIdx].key] || []
      if (nextG.length > 0) break
      nextIdx = (nextIdx + 1) % sentimentOrder.length
      looped++
    }
    iosSentimentIdx.value = nextIdx
    iosRevIdxInGroup.value = 0
  }
}

function scheduleIosReview() {
  clearTimeout(iosRevTimeout)
  if (cur.value !== 1) return

  const rev = currentIosReview.value
  if (!rev) return

  const seconds = rev.timing || 5
  
  iosRevTimeout = setTimeout(() => {
    advanceIosReview()
    scheduleIosReview()
  }, seconds * 1000)
}

function advanceAndReview() {
  const g = andSentimentGroups.value[currentAndSentiment.value.key] || []
  if (andRevIdxInGroup.value < g.length - 1) {
    andRevIdxInGroup.value++
  } else {
    // Move to next sentiment group that has reviews
    let nextIdx = (andSentimentIdx.value + 1) % sentimentOrder.length
    let looped = 0
    while (looped < sentimentOrder.length) {
      const nextG = andSentimentGroups.value[sentimentOrder[nextIdx].key] || []
      if (nextG.length > 0) break
      nextIdx = (nextIdx + 1) % sentimentOrder.length
      looped++
    }
    andSentimentIdx.value = nextIdx
    andRevIdxInGroup.value = 0
  }
}

function scheduleAndReview() {
  clearTimeout(andRevTimeout)
  if (cur.value !== 2) return

  const rev = currentAndReview.value
  if (!rev) return

  const seconds = rev.timing || 5
  
  andRevTimeout = setTimeout(() => {
    advanceAndReview()
    scheduleAndReview()
  }, seconds * 1000)
}

function jumpIosSentiment(i) { iosSentimentIdx.value = i; iosRevIdxInGroup.value = 0 }
function jumpAndSentiment(i) { andSentimentIdx.value = i; andRevIdxInGroup.value = 0 }

function startProg() {
  cancelAnimationFrame(progRaf); prog.value = 0; progStart = performance.now()
  const d = getDuration()
  function step(now) {
    prog.value = Math.min(100, ((now - progStart) / d) * 100)
    if (prog.value < 100) progRaf = requestAnimationFrame(step)
  }
  progRaf = requestAnimationFrame(step)
}

function go(n) {
  if (n === cur.value) return
  exitSlide.value = cur.value
  setTimeout(() => { exitSlide.value = -1 }, 600)
  cur.value = n
  clearTimeout(slideTimer); startProg()
  slideTimer = setTimeout(() => go((cur.value + 1) % total), getDuration())
}

watch(cur, (n) => {
  clearTimeout(iosRevTimeout); clearTimeout(andRevTimeout); clearTimeout(newsLoopTimeout)
  if (n === 1) {
    iosSentimentIdx.value = 0; iosRevIdxInGroup.value = 0
    scheduleIosReview()
  }
  if (n === 2) {
    andSentimentIdx.value = 0; andRevIdxInGroup.value = 0
    scheduleAndReview()
  }
  if (n === 3) scheduleNextNews()
})

const currentNews = computed(() => (gnews.value.posts||[])[newsIndex.value]||null)

function scheduleNextNews() {
  clearTimeout(newsLoopTimeout)
  newsLoopTimeout = setTimeout(() => {
    const posts = gnews.value.posts || []
    if (!posts.length) return
    newsTransDir.value = 'slide-next'
    newsIndex.value = (newsIndex.value + 1) % posts.length
    scheduleNextNews()
  }, 9000)
}

function getStarClass(rating, index) {
  const diff = rating - (index - 1)
  if (diff >= 0.75) return 'star-full'
  if (diff >= 0.25) return 'star-half'
  return 'star-empty'
}
function fmtNum(n) { return new Intl.NumberFormat('en-IN').format(n) }
function starsFull(n) {
  if (!n) return '☆☆☆'
  const c = Math.min(5, Math.max(0, Number(n)))
  return '★'.repeat(c) + '☆'.repeat(5-c)
}

function onKey(e) {
  if (e.key==='ArrowRight'||e.key==='ArrowDown') go((cur.value+1)%total)
  if (e.key==='ArrowLeft' ||e.key==='ArrowUp')   go((cur.value-1+total)%total)
}

async function loadData() {
  try {
    const r = await fetch(`/api/data?t=`+Date.now())
    if (!r.ok) throw new Error("HTTP " + r.status)
    const json = await r.json()
    
    // Eagerly set data
    if (json) data.value = json
    
    // Force launch dashboard if we got any response
    if (!appReady.value) {
      console.log("[App] Data received, launching.")
      appReady.value = true
      startProg()
      slideTimer = setTimeout(() => go(1), getDuration())
    }
  } catch (err) { 
    console.error("[App] Connection failed:", err)
    // If it's been a while, just show the dashboard with whatever we have (cache/defaults)
    setTimeout(() => { if(!appReady.value) appReady.value = true }, 2000)
  }
}

onMounted(() => {
  tick(); clockInt = setInterval(tick, 1000)
  document.addEventListener('keydown', onKey)
  
  // Initial load
  loadData(); 
  dataInt = setInterval(loadData, 60000) // Refresh every 1 min while dev testing

  // SUPER-EAGER FALLBACK: If we are still loading after 4 seconds, just show the dashboard.
  setTimeout(() => {
    if (!appReady.value) {
      console.warn("[App] Safety trigger: showing dashboard now.");
      appReady.value = true;
      startProg();
      slideTimer = setTimeout(() => go(1), getDuration());
    }
  }, 4000);
})
onUnmounted(() => {
  clearInterval(clockInt); clearInterval(dataInt)
  clearTimeout(iosRevTimeout); clearTimeout(andRevTimeout)
  clearTimeout(slideTimer); cancelAnimationFrame(progRaf)
  clearTimeout(newsLoopTimeout)
  document.removeEventListener('keydown', onKey)
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Clash+Display:wght@400;500;600;700&family=Syne:wght@400;600;700;800&family=Manrope:wght@400;500;600;700&display=swap');

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body{width:100%;height:100%;overflow:hidden;background:#FFFDF5;}

:root{
  /* ── YELLOW PALETTE ── */
  --y1:#FFD700;   /* pure gold */
  --y2:#FFC200;   /* amber */
  --y3:#FFB300;   /* deep amber */
  --y4:#FF9500;   /* burnt orange-yellow */
  --y5:#FFF176;   /* pale lemon */
  --y6:#FFFDE7;   /* cream white */
  /* ── NEUTRAL ── */
  --ink:#1A1400;  /* near-black warm */
  --ink2:#3D3000; /* dark brown */
  --ink3:#6B5800; /* mid brown */
  --paper:#FFFDF5;
  --paper2:#FFF9E0;
  --paper3:#FFF3C0;
  --border-y:rgba(255,180,0,.22);
  --border-ys:rgba(255,215,0,.5);
  --shadow-y:rgba(180,120,0,.18);
  /* Legacy mapped for shared components */
  --gold:#FFD700;--green:#22a84a;--purple:#9b5de5;--cyan:#00c4d4;--magenta:#ff2d78;--orange:#ff6b35;
  --neutral-c:#B8A020;
  --bg:var(--paper);
  --surface:rgba(255,215,0,.06);
  --border:rgba(255,180,0,.18);
  --text:var(--ink);
  --font-d:'Syne',sans-serif;
  --font-b:'Manrope',sans-serif;
}

/* ── LOADING ── */
.loading-screen{
  position:fixed;inset:0;z-index:9999;
  background:var(--paper);
  display:flex;align-items:center;justify-content:center;overflow:hidden;
}
.load-blob{
  position:absolute;border-radius:50%;filter:blur(80px);
  animation:ld-drift 5s ease-in-out infinite alternate;
}
.load-blob-1{width:500px;height:500px;background:var(--y1);opacity:.25;top:-160px;left:-160px;}
.load-blob-2{width:400px;height:400px;background:var(--y3);opacity:.2;bottom:-100px;right:-100px;animation-delay:-2.5s;}
@keyframes ld-drift{to{transform:translate(60px,40px) scale(1.15);}}
.load-content{position:relative;z-index:1;text-align:center;}
.load-title{
  font-family:var(--font-d);font-size:72px;font-weight:800;
  color:var(--ink);letter-spacing:-.02em;margin-bottom:6px;
}
.load-sub{font-family:var(--font-b);font-size:14px;color:var(--ink3);letter-spacing:.2em;text-transform:uppercase;margin-bottom:28px;}
.conn-status{font-family:var(--font-b);font-size:13px;color:var(--ink3);margin-bottom:20px;}
.load-bar{width:220px;height:3px;background:var(--paper3);border-radius:2px;margin:0 auto;overflow:hidden;}
.load-bar-fill{height:100%;width:0%;background:linear-gradient(90deg,var(--y3),var(--y1));border-radius:2px;animation:lb-fill 2.2s ease forwards;}
@keyframes lb-fill{to{width:100%;}}
.error-screen{position:fixed;inset:0;background:var(--paper);display:flex;align-items:center;justify-content:center;}
.error-inner{font-family:var(--font-b);font-size:14px;color:var(--ink3);padding:2rem;border:1px solid var(--border-y);border-radius:12px;background:var(--paper2);}

/* ══════════════════════════════════════════════════════
   SCENE BACKGROUND — WHITE & YELLOW LIGHT THEME
   Cream base + golden orbs + animated dot grid + shimmer
   ══════════════════════════════════════════════════════ */
.scene-bg{
  position:fixed;inset:0;z-index:0;overflow:hidden;
  background:var(--paper);
}

/* ── LAYER 1: Warm gradient wash ── */
.bg-floor{
  position:absolute;inset:0;
  transition:background 1.2s ease;
}
.scene-0 .bg-floor{
  background:
    radial-gradient(ellipse 70% 55% at 8% 90%, rgba(255,200,0,.18) 0%, transparent 60%),
    radial-gradient(ellipse 55% 45% at 92% 10%, rgba(255,220,80,.14) 0%, transparent 55%),
    radial-gradient(ellipse 80% 80% at 50% 50%, rgba(255,249,220,.6) 0%, transparent 100%),
    linear-gradient(160deg,#FFFEF8 0%,#FFFBEA 50%,#FFF8D6 100%);
}
.scene-1 .bg-floor{
  background:
    radial-gradient(ellipse 65% 55% at 5% 85%, rgba(255,210,0,.2) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 95% 15%, rgba(255,230,100,.15) 0%, transparent 55%),
    radial-gradient(ellipse 70% 70% at 50% 50%, rgba(255,252,230,.5) 0%, transparent 100%),
    linear-gradient(150deg,#FFFEF0 0%,#FFFCEA 50%,#FFF9D8 100%);
}
.scene-2 .bg-floor{
  background:
    radial-gradient(ellipse 70% 50% at 10% 80%, rgba(255,195,0,.22) 0%, transparent 60%),
    radial-gradient(ellipse 55% 50% at 90% 20%, rgba(255,215,60,.15) 0%, transparent 55%),
    radial-gradient(ellipse 75% 75% at 50% 55%, rgba(255,250,215,.55) 0%, transparent 100%),
    linear-gradient(155deg,#FFFEF5 0%,#FFFBDE 50%,#FFF6C8 100%);
}
.scene-3 .bg-floor{
  background:
    radial-gradient(ellipse 60% 55% at 12% 88%, rgba(255,205,0,.18) 0%, transparent 60%),
    radial-gradient(ellipse 65% 45% at 88% 12%, rgba(255,225,80,.12) 0%, transparent 55%),
    radial-gradient(ellipse 80% 80% at 50% 50%, rgba(255,251,225,.5) 0%, transparent 100%),
    linear-gradient(160deg,#FFFEF8 0%,#FFFCEA 50%,#FFF9D5 100%);
}

/* ── LAYER 2: Golden aurora glow bands ── */
.aurora{
  position:absolute;border-radius:50%;
  pointer-events:none;will-change:transform;
}
.a1{
  width:100vw;height:40vh;top:-12vh;left:-5vw;
  background:linear-gradient(180deg,rgba(255,215,0,.12) 0%,transparent 100%);
  filter:blur(40px);
  animation:aurora-drift-1 20s ease-in-out infinite alternate;
}
.a2{
  width:80vw;height:30vh;bottom:-8vh;right:-8vw;
  background:linear-gradient(0deg,rgba(255,190,0,.1) 0%,transparent 100%);
  filter:blur(35px);
  animation:aurora-drift-2 16s ease-in-out infinite alternate;
}
.a3{
  width:50vw;height:25vh;top:35%;left:25%;
  background:radial-gradient(ellipse,rgba(255,230,80,.08),transparent 70%);
  filter:blur(50px);
  animation:aurora-drift-3 22s ease-in-out infinite alternate;
}
@keyframes aurora-drift-1{from{transform:translateX(0) scaleY(1);}to{transform:translateX(4vw) scaleY(1.2);}}
@keyframes aurora-drift-2{from{transform:translateX(0);}to{transform:translateX(-5vw) scaleY(1.15);}}
@keyframes aurora-drift-3{from{transform:translate(0,0) rotate(-2deg);}to{transform:translate(3vw,-3vh) rotate(2deg);}}

/* ── LAYER 3: Golden floating orbs ── */
.orb{
  position:absolute;border-radius:50%;
  pointer-events:none;will-change:transform;
}
.o1{width:600px;height:600px;top:-220px;left:-180px;filter:blur(100px);
  background:radial-gradient(circle,rgba(255,210,0,.22),rgba(255,180,0,.06));
  animation:orb-f1 18s ease-in-out infinite alternate;}
.o2{width:500px;height:500px;bottom:-150px;right:-140px;filter:blur(90px);
  background:radial-gradient(circle,rgba(255,200,0,.18),rgba(255,160,0,.05));
  animation:orb-f2 14s ease-in-out infinite alternate;}
.o3{width:360px;height:360px;top:38%;right:8%;filter:blur(80px);
  background:radial-gradient(circle,rgba(255,220,50,.15),transparent);
  animation:orb-f3 21s ease-in-out infinite alternate;}
.o4{width:260px;height:260px;top:18%;left:38%;filter:blur(70px);
  background:radial-gradient(circle,rgba(255,240,100,.18),transparent);
  animation:orb-f4 13s ease-in-out infinite alternate;}
@keyframes orb-f1{from{transform:translate(0,0);}to{transform:translate(50px,35px) scale(1.08);}}
@keyframes orb-f2{from{transform:translate(0,0);}to{transform:translate(-40px,-25px) scale(1.06);}}
@keyframes orb-f3{from{transform:translate(0,0);}to{transform:translate(-25px,40px) scale(1.1);}}
@keyframes orb-f4{from{transform:translate(0,0);}to{transform:translate(35px,-35px) scale(1.12);}}

/* ── LAYER 4: Animated dot grid (3JS-style) ── */
.mesh-grid{
  position:absolute;inset:0;
  pointer-events:none;
  animation:grid-pan 80s linear infinite;
  opacity:1;
}
@keyframes grid-pan{from{transform:translate(0,0);}to{transform:translate(48px,48px);}}

/* ── LAYER 5: Soft edge vignette ── */
.bg-vignette{
  position:absolute;inset:0;
  background:radial-gradient(ellipse 90% 90% at 50% 50%,transparent 50%,rgba(255,230,100,.15) 100%);
  pointer-events:none;
}

/* ── LAYER 6: Subtle paper texture ── */
.noise-layer{
  position:absolute;inset:0;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E");
  opacity:.025;
  mix-blend-mode:multiply;
  pointer-events:none;
}

/* ── TOPBAR ── */
.topbar{
  position:relative;z-index:100;
  display:flex;align-items:center;height:64px;
  padding:0 2.4rem;gap:1.5rem;
  background:rgba(255,253,240,.88);
  border-bottom:1.5px solid rgba(255,190,0,.2);
  flex-shrink:0;
  box-shadow:0 2px 24px rgba(180,130,0,.08);
}
.logo-area{display:flex;align-items:center;gap:12px;}
.logo-text{
  font-family:var(--font-d);font-size:20px;font-weight:800;
  color:var(--ink);letter-spacing:.04em;
}
.nav-pills{flex:1;display:flex;justify-content:center;gap:6px;}
.nav-pill{
  padding:7px 22px;border-radius:100px;
  font-family:var(--font-b);font-size:12px;font-weight:600;
  letter-spacing:.06em;text-transform:uppercase;
  color:var(--ink3);cursor:pointer;
  transition:all .2s;border:1.5px solid transparent;
}
.nav-pill:hover{color:var(--ink2);border-color:var(--border-y);background:rgba(255,215,0,.08);}
.pill-on{
  background:var(--y1) !important;
  color:var(--ink) !important;
  font-weight:700;
  border-color:var(--y2) !important;
  box-shadow:0 4px 16px rgba(255,180,0,.35);
}
.topbar-right{display:flex;align-items:center;gap:16px;}
.live-badge{display:flex;align-items:center;gap:5px;font-family:var(--font-d);font-size:11px;font-weight:700;letter-spacing:.12em;color:#22a84a;}
.ld{width:7px;height:7px;border-radius:50%;background:#22a84a;box-shadow:0 0 8px #22a84a;animation:pulse 1.4s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
.clk{font-family:var(--font-d);font-size:13px;color:var(--ink3);letter-spacing:.04em;}

/* ── STAGE ── */
.stage{flex:1;position:relative;overflow:hidden;z-index:10;}
.slide{position:absolute;inset:0;opacity:0;pointer-events:none;transform:translateY(24px) scale(.97);transition:opacity .5s cubic-bezier(.22,1,.36,1),transform .5s cubic-bezier(.22,1,.36,1);}
.slide.sin{opacity:1;transform:translateY(0) scale(1);pointer-events:all;}
.slide.sout{opacity:0;transform:translateY(-20px) scale(1.03);transition:opacity .3s ease,transform .3s ease;}
.slide-inner{width:100%;height:100%;padding:1.5rem 2.5rem;display:flex;flex-direction:column;color:var(--ink);}

/* ── OVERVIEW ── */
.overview-slide{justify-content:center;gap:1.4rem;}
.ov-headline{margin-bottom:.5rem;}
.ov-eye{
  font-family:var(--font-b);font-size:12px;letter-spacing:.25em;
  text-transform:uppercase;color:var(--ink3);margin-bottom:6px;
}
.ov-big{
  font-family:var(--font-d);
  font-size:clamp(52px,6.5vw,88px);
  font-weight:800;color:var(--ink);line-height:.88;letter-spacing:-.03em;
}
.ov-outline{
  -webkit-text-stroke:2.5px var(--y2);
  color:transparent;
}
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;}
.stat-card{
  border-radius:28px;
  padding:2rem 1.8rem;
  position:relative;overflow:hidden;
  animation:card-rise .65s cubic-bezier(.22,1,.36,1) both;
  animation-delay:var(--d,0s);
  cursor:default;
  transition:transform .3s ease,box-shadow .3s ease;
  border:1.5px solid var(--border-y);
}
.stat-card:hover{transform:translateY(-8px);box-shadow:0 24px 60px var(--shadow-y);}
@keyframes card-rise{from{opacity:0;transform:translateY(40px) scale(.95);}to{opacity:1;transform:translateY(0) scale(1);}}

/* Each card gets a unique yellow-family gradient */
.sc-ios{
  background:linear-gradient(145deg,#FFF8D0,#FFF0A0);
  box-shadow:0 8px 32px rgba(200,150,0,.12);
}
.sc-and{
  background:linear-gradient(145deg,#FFF5C0,#FFE880);
  box-shadow:0 8px 32px rgba(180,130,0,.13);
}
.sc-news{
  background:linear-gradient(145deg,#FFE8A0,#FFD040);
  box-shadow:0 8px 32px rgba(160,110,0,.14);
}
.sc-total{
  background:linear-gradient(145deg,#FFD840,#FFC000);
  box-shadow:0 8px 32px rgba(140,90,0,.16);
}
.sc-icon{margin-bottom:12px;}
.sc-big-icon{font-size:40px;margin-bottom:12px;display:block;}
.sc-num{
  font-family:var(--font-d);font-size:clamp(40px,4.5vw,64px);
  font-weight:800;color:var(--ink);line-height:1;margin-bottom:6px;
}
.sc-lbl{
  font-family:var(--font-d);font-size:13px;font-weight:700;
  letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);
}
.sc-stars-row{display:flex;gap:3px;margin:8px 0 4px;}
.sc-star{
  width:16px;height:16px;
  background:rgba(0,0,0,.1);
  clip-path:polygon(50% 0%,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%);
}
.sc-star.star-full{background:var(--y3);}
.sc-star.star-half{background:linear-gradient(90deg,var(--y3) 50%,rgba(0,0,0,.1) 50%);}
.sc-count{font-family:var(--font-b);font-size:12px;color:var(--ink3);margin-top:4px;}

/* ══════════════════════════════════════════════════════════
   SENTIMENT SLIDE — BOLD REDESIGN
   Palette-per-emotion, floating particles, kinetic layout
   ══════════════════════════════════════════════════════════ */

/* Slide wrapper */
.sentiment-slide{
  justify-content:flex-start;
  gap:0;
  padding:1rem 2rem 0.6rem;
  position:relative;
  overflow:hidden;
}

/* Floating accent circles */
.sentiment-slide::before{
  content:'';
  position:absolute;
  width:360px;height:360px;
  top:-80px;right:-100px;
  border-radius:50%;
  pointer-events:none;
  z-index:0;
  background:radial-gradient(circle,rgba(255,215,0,.12) 0%,transparent 70%);
  animation:part-drift 12s ease-in-out infinite alternate;
}
.sentiment-slide::after{
  content:'';
  position:absolute;
  width:240px;height:240px;
  bottom:20px;left:-60px;
  border-radius:50%;
  pointer-events:none;
  z-index:0;
  background:radial-gradient(circle,rgba(255,190,0,.1) 0%,transparent 70%);
  animation:part-drift 16s ease-in-out infinite alternate;
  animation-delay:-6s;
}
@keyframes part-drift{
  from{transform:translate(0,0) scale(1);}
  to{transform:translate(30px,-25px) scale(1.12);}
}

/* ── HEADER ── */
.ss-header{
  display:flex;align-items:center;gap:16px;
  padding-bottom:0.85rem;
  border-bottom:1.5px solid rgba(180,130,0,.15);
  flex-shrink:0;flex-wrap:wrap;
  position:relative;z-index:2;
}
.ss-platform-badge{
  display:flex;align-items:center;gap:12px;
  padding:10px 22px;
  border-radius:60px;
  border:1.5px solid rgba(180,130,0,.2);
  background:rgba(255,220,0,.08);
  box-shadow:0 4px 16px rgba(180,130,0,.08);
}
.ios-badge{
  border-color:rgba(0,90,200,.25);
  background:linear-gradient(135deg,rgba(0,80,200,.06),rgba(0,180,255,.04));
}
.and-badge{
  border-color:rgba(30,140,50,.25);
  background:linear-gradient(135deg,rgba(20,120,40,.06),rgba(60,200,100,.04));
}
.ss-badge-img{width:36px;height:36px;object-fit:contain;}
.ss-badge-name{font-family:var(--font-d);font-size:13px;font-weight:700;letter-spacing:.04em;color:var(--ink);}
.ss-badge-stars{display:flex;align-items:center;gap:3px;margin-top:4px;}
.ss-star{
  width:12px;height:12px;
  background:rgba(0,0,0,.1);
  clip-path:polygon(50% 0%,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%);
}
.ss-star.star-full{background:var(--y3);}
.ss-star.star-half{background:linear-gradient(90deg,var(--y3) 50%,rgba(0,0,0,.1) 50%);}
.ss-rating{font-size:13px;font-weight:800;margin-left:6px;color:var(--ink2);}
.ss-title-block{flex:1;}
.ss-eyebrow{
  font-family:var(--font-b);font-size:10px;letter-spacing:.22em;text-transform:uppercase;
  color:var(--ink3);margin-bottom:3px;
}
.ss-big-title{
  font-family:var(--font-d);font-size:clamp(20px,2.6vw,36px);font-weight:800;
  color:var(--ink);line-height:1;
}

/* ── MAIN STAGE AREA ── */
.ss-stage-area{
  flex:1;
  display:grid;
  grid-template-columns:220px 1fr;
  gap:0;
  min-height:0;
  margin:.8rem 0;
  position:relative;z-index:2;
}

/* ── LEFT: EMOTION IDENTITY PANEL ── */
.ss-sentiment-float{
  width:220px;
  flex-shrink:0;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:8px;
  position:relative;
  text-align:center;
  padding:1rem 0;
}

/* Glowing emotion orb behind the face */
.sf-glow{
  position:absolute;
  width:220px;height:220px;
  border-radius:50%;
  filter:blur(55px);
  opacity:.35;
  top:50%;left:50%;
  transform:translate(-50%,-52%);
  pointer-events:none;
  transition:background .6s ease;
  animation:sf-orb-pulse 3s ease-in-out infinite alternate;
}
@keyframes sf-orb-pulse{
  from{opacity:.22;transform:translate(-50%,-52%) scale(1);}
  to{opacity:.45;transform:translate(-50%,-52%) scale(1.2);}
}
.sf-neutral .sf-glow{background:radial-gradient(circle,rgba(120,136,204,.7),rgba(80,100,200,.2));}
.sf-happy .sf-glow{background:radial-gradient(circle,rgba(30,185,84,.65),rgba(10,100,40,.2));}
.sf-ecstatic .sf-glow{background:radial-gradient(circle,rgba(255,215,0,.8),rgba(255,150,0,.3));}
.sf-frustrated .sf-glow{background:radial-gradient(circle,rgba(255,107,53,.7),rgba(200,40,0,.2));}
.sf-angry .sf-glow{background:radial-gradient(circle,rgba(255,45,120,.7),rgba(140,0,0,.2));}

/* The animated face icon */
.ss-big-face{
  width:118px !important;
  height:118px !important;
  position:relative;z-index:1;
  filter:drop-shadow(0 8px 24px rgba(0,0,0,.5));
  animation:face-pop .55s cubic-bezier(.34,1.56,.64,1) both;
}
@keyframes face-pop{
  from{opacity:0;transform:scale(.6) rotate(-8deg);}
  to{opacity:1;transform:scale(1) rotate(0deg);}
}

/* Emotion name */
.sf-name{
  font-family:var(--font-d);
  font-size:28px;
  font-weight:800;
  letter-spacing:-.01em;
  line-height:1;
  position:relative;z-index:1;
  color:var(--ink);
  text-align:center;
  width:100%;
}
.sf-neutral .sf-name{color:#4455aa;}
.sf-happy .sf-name{color:#0d7a32;}
.sf-ecstatic .sf-name{color:#8a6000;}
.sf-frustrated .sf-name{color:#b04400;}
.sf-angry .sf-name{color:#aa0040;}

.sf-count{
  font-family:var(--font-b);font-size:11px;
  color:var(--ink3);
  letter-spacing:.12em;text-transform:uppercase;
  position:relative;z-index:1;
  background:rgba(180,130,0,.08);
  border:1px solid var(--border-y);
  border-radius:20px;
  padding:4px 12px;
}

/* Sentiment progress dots */
.ss-progress-dots{display:flex;gap:5px;margin-top:6px;position:relative;z-index:1;justify-content:center;}
.ss-sdot{
  width:6px;height:6px;border-radius:50%;
  background:rgba(0,0,0,.1);
  transition:all .35s cubic-bezier(.34,1.56,.64,1);
}
.sdot-on{background:var(--y2) !important;width:20px !important;border-radius:4px !important;box-shadow:0 0 8px rgba(255,200,0,.4);}

/* ── RIGHT: REVIEW CARD PANEL ── */
.ss-review-panel{
  flex:1;
  display:flex;
  flex-direction:column;
  gap:1rem;
  margin-left:1.6rem;
  min-height:0;
  position:relative;
}
.ss-review-panel.is-dual {
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
}
.ss-review-panel.is-dual .ss-review-card {
  flex: 1 1 45%;
  min-width: 440px;
  height: fit-content;
  position: relative; /* Allow natural flow */
  margin: 0 auto;
}

/* The main review card */
.ss-review-card{
  flex:1;
  border-radius:28px;
  padding:1.8rem 2.2rem;
  border:1.5px solid rgba(180,130,0,.18);
  background:rgba(255,253,235,.92);
  display:flex;
  flex-direction:column;
  gap:1rem;
  position:relative;
  overflow:hidden;
  transition:border-color .4s;
  min-height:0;
  box-shadow:0 8px 40px rgba(180,130,0,.1), 0 2px 8px rgba(0,0,0,.04);
  will-change:transform;
  animation:card-levitate 5s ease-in-out infinite;
}

/* Dynamic Sizes */
.ss-review-card.sz-small {
  flex: 0 0 auto;
  align-self: center;
  max-width: 820px;
  margin: auto 0;
  padding: 3rem 4rem;
}
.ss-review-card.sz-small .ss-rc-text {
  font-size: clamp(24px, 3.2vw, 42px);
  text-align: center;
}
.ss-review-card.sz-small .ss-rc-quote-wrap {
  justify-content: center;
}

.ss-review-card.sz-medium {
  flex: 0 0 auto;
  align-self: center;
  max-width: 1000px;
  margin: auto 0;
}

.ss-review-card.sz-large {
  flex: 1;
}

@keyframes card-levitate{
  0%,100%{transform:translateY(0);}
  50%{transform:translateY(-6px);}
}

/* Shimmering top edge — uses transform instead of left/right to avoid layout */
.ss-review-card::before{
  content:'';
  position:absolute;top:0;left:0;right:0;height:2px;
  border-radius:2px;
  animation:shimmer-edge 3s ease-in-out infinite alternate;
  will-change:opacity;
}
@keyframes shimmer-edge{
  from{opacity:.5;}
  to{opacity:1;}
}

/* Decorative corner ornament */
.ss-review-card::after{
  content:'';
  position:absolute;
  top:-60px;right:-60px;
  width:160px;height:160px;
  border-radius:50%;
  opacity:.07;
  pointer-events:none;
  transition:background .5s;
}

.rc-neutral{
  border-color:rgba(100,120,220,.3);
  box-shadow:0 8px 32px rgba(100,120,220,.08);
}
.rc-neutral::before{background:linear-gradient(90deg,transparent,rgba(120,136,204,.6),rgba(160,180,255,.8),transparent);}
.rc-neutral::after{background:#7888cc;}

.rc-happy{
  border-color:rgba(29,185,84,.3);
  box-shadow:0 8px 32px rgba(29,185,84,.08);
}
.rc-happy::before{background:linear-gradient(90deg,transparent,rgba(29,185,84,.6),rgba(120,255,160,.8),transparent);}
.rc-happy::after{background:#1db954;}

.rc-ecstatic{
  border-color:rgba(200,150,0,.4);
  box-shadow:0 8px 32px rgba(200,150,0,.12);
}
.rc-ecstatic::before{background:linear-gradient(90deg,transparent,rgba(200,140,0,.7),rgba(255,215,0,.9),rgba(255,240,120,.8),transparent);}
.rc-ecstatic::after{background:var(--y2);}

.rc-frustrated{
  border-color:rgba(220,90,30,.3);
  box-shadow:0 8px 32px rgba(220,90,30,.08);
}
.rc-frustrated::before{background:linear-gradient(90deg,transparent,rgba(255,107,53,.6),rgba(255,160,80,.8),transparent);}
.rc-frustrated::after{background:#ff6b35;}

.rc-angry{
  border-color:rgba(220,30,80,.3);
  box-shadow:0 8px 32px rgba(220,30,80,.08);
}
.rc-angry::before{background:linear-gradient(90deg,transparent,rgba(255,45,120,.6),rgba(255,120,160,.8),transparent);}
.rc-angry::after{background:#ff2d78;}

/* ── AUTHOR ROW ── */
.ss-rc-author-row{
  display:flex;align-items:center;gap:14px;
  flex-shrink:0;
  padding-bottom:.85rem;
  border-bottom:1px solid rgba(180,130,0,.12);
}
.ss-rc-avatar{
  width:50px;height:50px;
  border-radius:50%;
  border:2px solid rgba(180,130,0,.2);
  display:flex;align-items:center;justify-content:center;
  font-family:var(--font-d);font-size:19px;font-weight:800;
  color:#fff;
  flex-shrink:0;
  position:relative;
  overflow:hidden;
  transition:box-shadow .4s;
}
.rc-neutral .ss-rc-avatar{background:linear-gradient(135deg,#7888cc,#3344aa);}
.rc-happy .ss-rc-avatar{background:linear-gradient(135deg,#1db954,#0a5c28);}
.rc-ecstatic .ss-rc-avatar{background:linear-gradient(135deg,#d4a000,#a07000);}
.rc-frustrated .ss-rc-avatar{background:linear-gradient(135deg,#ff6b35,#aa2200);}
.rc-angry .ss-rc-avatar{background:linear-gradient(135deg,#ff2d78,#8b0000);}

.ss-rc-meta{flex:1;display:flex;flex-direction:column;gap:5px;}
.ss-rc-author{
  font-family:var(--font-d);font-size:17px;font-weight:700;
  color:var(--ink);line-height:1.2;letter-spacing:-.01em;
}
.ss-rc-stars-inline{display:flex;align-items:center;gap:3px;}
.ss-rc-star-sm{
  display:inline-block;width:14px;height:14px;
  background:rgba(0,0,0,.1);
  clip-path:polygon(50% 0%,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%);
  flex-shrink:0;
}
.ss-rc-star-sm.star-full{background:var(--y3);}
.ss-rc-star-sm.star-half{background:linear-gradient(90deg,var(--y3) 50%,rgba(0,0,0,.1) 50%);}
.ss-rc-date{margin-left:7px;font-family:var(--font-b);font-size:11px;color:var(--ink3);}

/* Review counter */
.ss-rev-indicator{
  margin-left:auto;
  font-family:var(--font-d);font-size:22px;font-weight:800;
  color:var(--ink);line-height:1;white-space:nowrap;
  background:rgba(180,130,0,.08);
  border:1.5px solid var(--border-y);
  border-radius:12px;
  padding:6px 12px;
}
.rev-ind-total{font-size:12px;font-weight:500;color:var(--ink3);}

/* ── QUOTE BLOCK ── */
.ss-rc-quote-wrap{
  flex:1;
  display:flex;
  gap:14px;
  align-items:flex-start;
  min-height:0;
  overflow:hidden;
  position:relative;
}

/* Giant decorative quote mark */
.ss-rc-quote-mark{
  font-family:Georgia,serif;
  font-size:clamp(80px,9vw,120px);
  line-height:.62;
  font-weight:900;
  flex-shrink:0;
  margin-top:4px;
  will-change:opacity;
  animation:quote-breathe 4s ease-in-out infinite alternate;
}
@keyframes quote-breathe{
  from{opacity:.4;}
  to{opacity:.75;}
}

/* Review text */
.ss-rc-text{
  font-family:var(--font-b);
  font-size:clamp(18px,2.2vw,28px);
  line-height:1.68;
  color:var(--ink);
  font-weight:500;
  flex:1;
  overflow:hidden;
  display:-webkit-box;
  -webkit-box-orient:vertical;
  -webkit-line-clamp:5;
  align-self:center;
  letter-spacing:.01em;
}

/* Empty state */
.ss-empty-card{justify-content:center;align-items:center;}
.ss-empty-msg{
  font-family:var(--font-b);font-size:18px;
  color:var(--ink3);
  text-align:center;
  letter-spacing:.08em;
}

/* Progress bar */
.ss-rev-progress-bar{
  height:4px;
  background:rgba(180,130,0,.12);
  border-radius:3px;
  overflow:hidden;
  flex-shrink:0;
  position:relative;
}
.ss-rev-progress-bar::before{
  content:'';
  position:absolute;inset:0;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.06),transparent);
  animation:bar-shimmer 2.5s linear infinite;
}
@keyframes bar-shimmer{
  from{transform:translateX(-100%);}
  to{transform:translateX(100%);}
}
.ss-rev-progress-fill{
  height:100%;
  border-radius:3px;
  transition:width .7s cubic-bezier(.4,0,.2,1);
  box-shadow:0 0 10px currentColor;
}

/* ══════════════════════════════════════════
   BOTTOM SENTIMENT TABS — Creative Pill Row
   ══════════════════════════════════════════ */
.ss-group-tabs{
  display:flex;
  gap:10px;
  flex-shrink:0;
  padding-top:.5rem;
  justify-content:center;
  position:relative;z-index:2;
}
.ss-group-tab{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  width:12px;
  height:12px;
  min-width:12px;
  min-height:12px;
  max-width:12px;
  max-height:12px;
  border-radius:50%;
  border:2px solid rgba(255,255,255,.18);
  background:rgba(255,255,255,.07);
  cursor:pointer;
  transition:border-color .2s, background .2s, box-shadow .2s;
  flex:0 0 12px;
  position:relative;
  box-sizing:border-box;
}
.ss-group-tab::before{display:none;}
.ss-group-tab:hover{
  border-color:rgba(255,255,255,.4);
  background:rgba(255,255,255,.14);
}
.ss-tab-emoji{display:none;}

/* Active dot per sentiment */
.tab-neutral.tab-on{background:#7888cc;border-color:#7888cc;box-shadow:0 0 6px rgba(120,136,204,.5);}
.tab-happy.tab-on{background:#1db954;border-color:#1db954;box-shadow:0 0 6px rgba(29,185,84,.5);}
.tab-ecstatic.tab-on{background:var(--y2);border-color:var(--y2);box-shadow:0 0 6px rgba(255,190,0,.5);}
.tab-frustrated.tab-on{background:#ff6b35;border-color:#ff6b35;box-shadow:0 0 6px rgba(255,107,53,.5);}
.tab-angry.tab-on{background:#ff2d78;border-color:#ff2d78;box-shadow:0 0 6px rgba(255,45,120,.5);}

/* ══════════════════════════════════
   REVIEW CARD TRANSITIONS
   No mode="out-in" — enter & leave run simultaneously
   ══════════════════════════════════ */
.rev-fade-enter-active{
  transition: opacity .35s ease, transform .35s ease;
  position: absolute; inset: 0;
}
.rev-fade-leave-active{
  transition: opacity .3s ease, transform .3s ease;
  position: absolute; inset: 0;
}
.rev-fade-enter-from{
  opacity:0;
  transform:translateX(20px);
}
.rev-fade-enter-to{
  opacity:1;
  transform:translateX(0);
}
.rev-fade-leave-from{opacity:1;}
.rev-fade-leave-to{opacity:0;}

/* Hide tab label text — emoji only */
.ss-tab-lbl{display:none;}

/* ── NEWS SLIDE ── */
.news-slide{flex-direction:row;gap:3.5rem;align-items:center;padding:0 3vw;height:100%;justify-content:flex-start;}
.news-left{width:200px;flex-shrink:0;}
.nl-eyebrow{font-family:var(--font-b);font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--ink3);margin-bottom:8px;}
.nl-big{font-family:var(--font-d);font-size:clamp(44px,5.5vw,72px);font-weight:800;color:var(--ink);line-height:.88;letter-spacing:-.04em;margin-bottom:2rem;}
.news-count-pill{
  display:inline-flex;align-items:center;gap:8px;
  background:linear-gradient(90deg,var(--y2),var(--y1));
  border-radius:100px;padding:7px 18px;
  box-shadow:0 4px 16px rgba(180,130,0,.25);
}
.ncp-num{font-family:var(--font-d);font-size:24px;font-weight:800;color:var(--ink);}
.ncp-txt{font-family:var(--font-b);font-size:11px;color:var(--ink2);text-transform:uppercase;letter-spacing:.1em;}
.news-frame{
  flex:1;height:84vh;
  background:var(--paper2);
  border:1.5px solid var(--border-y);
  border-radius:3vh;position:relative;overflow:hidden;
  box-shadow:0 24px 60px rgba(180,130,0,.12);
}
.ns-poster{width:100%;height:100%;position:relative;display:flex;align-items:flex-end;overflow:hidden;}
.ns-hero{position:absolute;inset:0;z-index:0;}
.ns-hero-img{width:100%;height:100%;object-fit:cover;animation:kb 40s ease-in-out infinite alternate;}
@keyframes kb{0%{transform:scale(1);}100%{transform:scale(1.15) translate(20px,10px);}}
.ns-hero-overlay{position:absolute;inset:0;background:linear-gradient(0deg,rgba(255,248,210,.95) 10%,rgba(255,248,210,.6) 55%,transparent 100%);}
.ns-content{position:relative;z-index:2;padding:5vh;width:100%;}
.ns-source-badge{
  display:inline-flex;align-items:center;gap:10px;
  padding:7px 20px;border-radius:100px;
  background:rgba(255,215,0,.15);
  border:1.5px solid var(--border-y);
  margin-bottom:3vh;
}
.ns-source{font-family:var(--font-d);font-weight:800;color:var(--ink2);font-size:13px;letter-spacing:.08em;}
.ns-sep{color:var(--ink3);}
.ns-date{font-family:var(--font-b);font-size:13px;color:var(--ink3);}
.ns-title{font-family:var(--font-d);font-size:clamp(30px,5vh,64px);font-weight:800;color:var(--ink);line-height:1.08;margin-bottom:5vh;}
.ns-footer{display:flex;align-items:center;justify-content:space-between;}
.ns-qr-wrap{display:flex;align-items:center;gap:16px;}
.ns-qr{width:9vh;height:9vh;border:2px solid var(--y2);border-radius:10px;background:#fff;}
.ns-qr-lbl{font-family:var(--font-d);font-size:13px;font-weight:800;color:var(--ink2);letter-spacing:.1em;}
.ns-pagination{display:flex;gap:7px;}
.ns-dot{width:7px;height:7px;border-radius:50%;background:rgba(0,0,0,.15);transition:all .3s;cursor:pointer;}
.ns-dot-on{width:22px !important;border-radius:4px !important;background:var(--y2) !important;}
.slide-next-enter-active,.slide-prev-enter-active{transition:all .5s cubic-bezier(.16,1,.3,1);}
.slide-next-leave-active,.slide-prev-leave-active{transition:all .3s ease;}
.slide-next-enter-from{opacity:0;transform:translateX(40px);}
.slide-next-leave-to{opacity:0;transform:translateX(-30px);}
.slide-prev-enter-from{opacity:0;transform:translateX(-40px);}
.slide-prev-leave-to{opacity:0;transform:translateX(30px);}

/* ── BOTTOM BAR ── */
.bottom-bar{
  position:relative;z-index:100;height:50px;
  display:flex;align-items:center;padding:0 2.4rem;gap:1rem;
  background:rgba(255,253,235,.92);
  border-top:1.5px solid rgba(180,130,0,.15);
  flex-shrink:0;
  box-shadow:0 -2px 16px rgba(180,130,0,.06);
}
.progress-rail{position:absolute;bottom:0;left:0;right:0;height:3px;background:rgba(180,130,0,.1);}
.progress-fill{
  height:100%;
  background:linear-gradient(90deg,var(--y3),var(--y1),var(--y5));
  transition:none;
  box-shadow:0 0 8px rgba(255,200,0,.4);
}
.bb-left{display:flex;align-items:center;gap:8px;}
.bb-brand{font-family:var(--font-d);font-size:13px;font-weight:800;color:var(--ink);}
.bb-sep{color:var(--ink3);}
.bb-sprint{font-family:var(--font-b);font-size:11px;color:var(--ink3);letter-spacing:.06em;}
.bb-center{flex:1;display:flex;align-items:center;justify-content:center;gap:8px;}
.bb-pip{width:7px;height:7px;border-radius:50%;background:rgba(0,0,0,.12);cursor:pointer;transition:all .25s;}
.bb-pip:hover{background:rgba(0,0,0,.3);}
.pipa{width:26px !important;border-radius:4px !important;background:var(--y2) !important;box-shadow:0 0 8px rgba(255,190,0,.4) !important;}
.bb-right{display:flex;align-items:center;gap:12px;}
.bb-counter{font-family:var(--font-d);font-size:12px;color:var(--ink3);}
.bb-keys{font-size:10px;color:var(--ink3);letter-spacing:.06em;}

#app{width:100vw;height:100vh;display:flex;flex-direction:column;overflow:hidden;position:relative;}
</style>
