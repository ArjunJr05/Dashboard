<template>
  <!-- LOADING -->
  <div class="loading-screen" v-if="!appReady && !loadError">
    <div class="load-blob load-blob-1"></div>
    <div class="load-blob load-blob-2"></div>
    <div class="load-content">
      <img src="/arattai.png" style="height:120px;margin-bottom:24px;object-fit:contain;" />
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
          <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
            <path d="M 60 0 L 0 0 0 60" fill="none" stroke="rgba(255,255,255,0.03)" stroke-width="1"/>
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
        <img src="/arattai.png" alt="Arattai" style="height:120px;width:auto;object-fit:contain;margin-top:15px;" />
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

      <!-- SLIDE 1: APP STORE (SENTIMENT) -->
      <div class="slide" :class="{sin: cur===1, sout: exitSlide===1}">
        <div class="slide-inner sentiment-slide">
          <div class="ss-stage-area" :key="cur + '-' + iosSentimentIdx">
            <div class="ss-sentiment-float" :class="'sf-'+currentIosSentiment.key">
              <div class="sf-glow"></div>
              <EmotionFace :emotionKey="currentIosSentiment.key" class="ss-big-face" />
              <div class="sf-name">{{ currentIosSentiment.label }}</div>
            </div>
            <div class="ss-review-panel ss-stack-panel">
              <transition-group name="rev-stack">
                <div v-for="(rev, ridx) in (iosSentimentGroups[currentIosSentiment.key] || [])" 
                  :key="iosSentimentIdx + '-' + ridx"
                  v-show="Math.abs(ridx - iosRevIdxInGroup) <= 1"
                  class="ss-review-card stack-card" 
                  :class="[
                    'rc-'+getEmotion(rev), 
                    ridx === iosRevIdxInGroup ? 'is-active' : (ridx < iosRevIdxInGroup ? 'is-prev' : 'is-next')
                  ]">
                  <div class="ss-rc-author-row">
                    <div class="ss-rc-avatar">{{ (rev.author||'A')[0].toUpperCase() }}</div>
                    <div class="ss-rc-meta">
                      <div class="ss-rc-author">{{ rev.author || 'Anonymous' }}</div>
                      <div class="ss-rc-stars-inline">
                        <span v-for="si in 5" :key="si" class="ss-rc-star-sm" :class="getStarClass(rev.rating||0, si)"></span>
                      </div>
                    </div>
                  </div>
                  <div class="ss-rc-quote-wrap">
                    <span class="ss-rc-quote-mark" :style="{color: sentimentColor(getEmotion(rev))}">"</span>
                    <div class="ss-rc-text">{{ rev.body }}</div>
                  </div>
                </div>
              </transition-group>
            </div>
          </div>
          <div class="ss-group-tabs">
            <div v-for="(s,i) in activeIosSentiments" :key="s.key" class="ss-group-tab" :class="[('tab-'+s.key), i===iosSentimentIdx ? 'tab-on' : '']" @click="jumpIosSentiment(i)"></div>
          </div>
        </div>
      </div>

      <!-- SLIDE 2: PLAY STORE -->
      <div class="slide" :class="{sin: cur===2, sout: exitSlide===2}">
        <div class="slide-inner sentiment-slide">
          <div class="ss-stage-area" :key="cur + '-' + andSentimentIdx">
            <div class="ss-sentiment-float" :class="'sf-'+currentAndSentiment.key">
              <div class="sf-glow"></div>
              <EmotionFace :emotionKey="currentAndSentiment.key" class="ss-big-face" />
              <div class="sf-name">{{ currentAndSentiment.label }}</div>
            </div>
            <div class="ss-review-panel ss-stack-panel">
              <transition-group name="rev-stack">
                <div v-for="(rev, ridx) in (andSentimentGroups[currentAndSentiment.key] || [])" 
                  :key="andSentimentIdx + '-' + ridx"
                  v-show="Math.abs(ridx - andRevIdxInGroup) <= 1"
                  class="ss-review-card stack-card" 
                  :class="[
                    'rc-'+getEmotion(rev), 
                    ridx === andRevIdxInGroup ? 'is-active' : (ridx < andRevIdxInGroup ? 'is-prev' : 'is-next')
                  ]">
                  <div class="ss-rc-author-row">
                    <div class="ss-rc-avatar">{{ (rev.author||'A')[0].toUpperCase() }}</div>
                    <div class="ss-rc-meta">
                      <div class="ss-rc-author">{{ rev.author || 'Anonymous' }}</div>
                      <div class="ss-rc-stars-inline">
                        <span v-for="si in 5" :key="si" class="ss-rc-star-sm" :class="getStarClass(rev.rating||0, si)"></span>
                      </div>
                    </div>
                  </div>
                  <div class="ss-rc-quote-wrap">
                    <span class="ss-rc-quote-mark" :style="{color: sentimentColor(getEmotion(rev))}">"</span>
                    <div class="ss-rc-text">{{ rev.body }}</div>
                  </div>
                </div>
              </transition-group>
            </div>
          </div>
          <div class="ss-group-tabs">
            <div v-for="(s,i) in activeAndSentiments" :key="s.key" class="ss-group-tab" :class="[('tab-'+s.key), i===andSentimentIdx ? 'tab-on' : '']" @click="jumpAndSentiment(i)"></div>
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
      <div class="bb-left" @click="loadData" style="cursor:pointer;" title="Click to refresh">
        <img src="/arattai.png" style="height:18px;object-fit:contain;opacity:0.8;" />
        <span class="bb-sep">·</span>
        <span class="bb-sprint" :class="{'pulse-sync': isFetching}">SYNCED: {{ lastUpdated }} {{ isFetching ? '(Updating...)' : '' }}</span>
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

const appReady    = ref(false)
const loadError   = ref(false)
const isFetching  = ref(false)
const lastUpdated = ref('--:--')
const data        = ref({})
const clock       = ref('')
const cur         = ref(0)
const exitSlide = ref(-1)
const total     = 4
const navs      = ['Overview','App Store','Play Store','News']
const prog      = ref(0)
// Duration: 5s per review × 10 reviews = 50s per store slide, 18s for others
const getDuration = () => {
  if (cur.value === 1) return Math.max(18000, (ios.value.reviews?.length || 10) * 3000)
  if (cur.value === 2) return Math.max(18000, (android.value.reviews?.length || 10) * 3000)
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

const activeIosSentiments = computed(() => {
  return sentimentOrder.filter(s => (iosSentimentGroups.value[s.key] || []).length > 0)
})
const activeAndSentiments = computed(() => {
  return sentimentOrder.filter(s => (andSentimentGroups.value[s.key] || []).length > 0)
})

const currentIosSentiment = computed(() => {
  const list = activeIosSentiments.value
  return list[iosSentimentIdx.value] || list[0] || sentimentOrder[0]
})
const currentAndSentiment = computed(() => {
  const list = activeAndSentiments.value
  return list[andSentimentIdx.value] || list[0] || sentimentOrder[0]
})

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
    // Move to next ACTIVE sentiment group
    const list = activeIosSentiments.value
    if (list.length > 0) {
      iosSentimentIdx.value = (iosSentimentIdx.value + 1) % list.length
    }
    iosRevIdxInGroup.value = 0
  }
}

function scheduleIosReview() {
  clearTimeout(iosRevTimeout)
  if (cur.value !== 1) return

  const rev = currentIosReview.value
  if (!rev) return

  iosRevTimeout = setTimeout(() => {
    advanceIosReview()
    scheduleIosReview()
  }, 3000)
}

function advanceAndReview() {
  const g = andSentimentGroups.value[currentAndSentiment.value.key] || []
  if (andRevIdxInGroup.value < g.length - 1) {
    andRevIdxInGroup.value++
  } else {
    // Move to next ACTIVE sentiment group
    const list = activeAndSentiments.value
    if (list.length > 0) {
      andSentimentIdx.value = (andSentimentIdx.value + 1) % list.length
    }
    andRevIdxInGroup.value = 0
  }
}

function scheduleAndReview() {
  clearTimeout(andRevTimeout)
  if (cur.value !== 2) return

  const rev = currentAndReview.value
  if (!rev) return

  andRevTimeout = setTimeout(() => {
    advanceAndReview()
    scheduleAndReview()
  }, 3000)
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
  if (isFetching.value) return
  isFetching.value = true
  try {
    let r = null
    const proxyUrl = `/api/data?t=`+Date.now()
    
    // First Attempt: Standard Proxy
    console.log("[App] Trying proxy fetch:", proxyUrl)
    try {
      r = await fetch(proxyUrl)
    } catch (e) {
      console.warn("[App] Proxy fetch network error, skipping to direct attempt.")
    }

    // Second Attempt: Direct connection if proxy failed/errored
    if (!r || !r.ok) {
      const directUrl = `http://127.0.0.1:5050/data?t=`+Date.now()
      console.log("[App] Attempting direct connection to backend:", directUrl)
      try {
        r = await fetch(directUrl)
      } catch (e) {
        throw new Error("Direct connection failed: " + e.message)
      }
    }
    
    if (!r.ok) throw new Error("HTTP " + r.status)
    const json = await r.json()
    
    if (json && json.appstore) {
      data.value = json
      lastUpdated.value = new Date().toLocaleTimeString('en-IN', { hour12: false, hour: '2-digit', minute: '2-digit' })
      loadError.value = ""
      
      if (!appReady.value) {
        console.log("[App] Success! Data loaded and dashboard is live.")
        appReady.value = true
        startProg()
        slideTimer = setTimeout(() => go(1), getDuration())
      }
    }
  } catch (err) { 
    console.error("[App] Connection to backend definitively failed:", err)
    loadError.value = "Backend unreachable (Port 5050). Check if server.py is running."
    if (!appReady.value) {
      setTimeout(() => { if(!appReady.value) appReady.value = true }, 4000)
    }
  } finally {
    isFetching.value = false
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
@import url('https://fonts.zohostatic.com/puvi/regular/font.css');
@import url('https://fonts.zohostatic.com/puvi/bold/font.css');
@import url('https://fonts.zohostatic.com/puvi/semibold/font.css');
@import url('https://fonts.zohostatic.com/puvi/medium/font.css');
@import url('https://fonts.zohostatic.com/puvi/extrabold/font.css');

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body{width:100%;height:100%;overflow:hidden;background:#080b14;}

:root{
  --lime:#b5ff3e;--cyan:#00e5ff;--magenta:#ff2d78;--orange:#ff6b35;
  --gold:#FFD700;--green:#1db954;--purple:#9b5de5;--blue:#0066ff;
  --neutral-c:#7888cc;--bg:#080b14;
  --surface:rgba(255,255,255,0.04);--border:rgba(255,255,255,0.09);
  --text:#fff;--font-d:'Puvi', sans-serif;--font-b:'Puvi', sans-serif;
}

/* ── LOADING ── */
.loading-screen{position:fixed;inset:0;z-index:9999;background:var(--bg);display:flex;align-items:center;justify-content:center;overflow:hidden;}
.load-blob{position:absolute;border-radius:50%;filter:blur(100px);animation:ld-drift 5s ease-in-out infinite alternate;}
.load-blob-1{width:500px;height:500px;background:var(--purple);opacity:.45;top:-120px;left:-120px;}
.load-blob-2{width:400px;height:400px;background:var(--cyan);opacity:.3;bottom:-80px;right:-80px;animation-delay:-2.5s;}
@keyframes ld-drift{to{transform:translate(60px,40px) scale(1.15);}}
.load-content{position:relative;z-index:1;text-align:center;}
.load-title{font-family:var(--font-d);font-size:72px;font-weight:800;color:#fff;letter-spacing:-.02em;margin-bottom:6px;text-shadow:0 0 60px var(--cyan);}
.load-sub{font-family:var(--font-b);font-size:14px;color:rgba(255,255,255,.4);letter-spacing:.2em;text-transform:uppercase;margin-bottom:28px;}
.load-bar{width:220px;height:3px;background:rgba(255,255,255,.1);border-radius:2px;margin:0 auto;overflow:hidden;}
.load-bar-fill{height:100%;width:0%;background:linear-gradient(90deg,var(--purple),var(--cyan));border-radius:2px;animation:lb-fill 2.2s ease forwards;}
@keyframes lb-fill{to{width:100%;}}
.error-screen{position:fixed;inset:0;background:var(--bg);display:flex;align-items:center;justify-content:center;}
.error-inner{font-family:var(--font-b);font-size:14px;color:rgba(255,255,255,.4);padding:2rem;border:1px solid var(--border);border-radius:12px;}

/* ══════════════════════════════════════════════════════════════════
   SCENE BACKGROUND — RICH LAYERED SYSTEM
   Base floor → Aurora beams → Floating orbs → Mesh grid → Vignette → Grain
   ══════════════════════════════════════════════════════════════════ */
.scene-bg{
  position:fixed;inset:0;z-index:0;overflow:hidden;
  background:#05080f;
  transition:--c1 1.2s ease,--c2 1.2s ease;
}

/* ── LAYER 1: Base gradient floor ── */
.bg-floor{
  position:absolute;inset:0;
  transition:background 1.4s cubic-bezier(.4,0,.2,1);
  will-change:background;
}
.scene-0 .bg-floor{
  background:
    radial-gradient(ellipse 80% 60% at 15% 85%, rgba(100,20,180,.55) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 85% 15%, rgba(220,40,120,.38) 0%, transparent 55%),
    radial-gradient(ellipse 70% 70% at 50% 50%, rgba(30,10,60,.9) 0%, transparent 100%),
    linear-gradient(160deg,#0d0520 0%,#080b1a 40%,#0a0618 100%);
}
.scene-1 .bg-floor{
  background:
    radial-gradient(ellipse 80% 55% at 10% 80%, rgba(0,60,200,.5) 0%, transparent 60%),
    radial-gradient(ellipse 65% 50% at 90% 20%, rgba(0,200,255,.28) 0%, transparent 55%),
    radial-gradient(ellipse 50% 60% at 55% 50%, rgba(60,0,180,.4) 0%, transparent 70%),
    linear-gradient(160deg,#020d1f 0%,#050a18 40%,#030c1a 100%);
}
.scene-2 .bg-floor{
  background:
    radial-gradient(ellipse 75% 55% at 12% 75%, rgba(0,120,40,.5) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 88% 20%, rgba(255,140,0,.28) 0%, transparent 55%),
    radial-gradient(ellipse 55% 65% at 50% 55%, rgba(10,40,20,.85) 0%, transparent 70%),
    linear-gradient(160deg,#030e08 0%,#060c0a 40%,#040e06 100%);
}
.scene-3 .bg-floor{
  background:
    radial-gradient(ellipse 70% 55% at 15% 80%, rgba(0,180,200,.4) 0%, transparent 60%),
    radial-gradient(ellipse 65% 50% at 85% 15%, rgba(140,0,220,.35) 0%, transparent 55%),
    radial-gradient(ellipse 55% 60% at 50% 50%, rgba(0,60,80,.8) 0%, transparent 70%),
    linear-gradient(160deg,#020c10 0%,#040a12 40%,#050810 100%);
}

/* ── LAYER 2: Aurora beams ── */
.aurora{
  position:absolute;
  border-radius:50%;
  opacity:0;
  pointer-events:none;
  will-change:transform,opacity;
  transition:opacity 1.4s ease, background 1.4s ease;
}
.a1{
  width:110vw;height:35vh;
  top:-8vh;left:-5vw;
  filter:blur(55px);
  animation:aurora-drift-1 18s ease-in-out infinite alternate;
}
.a2{
  width:80vw;height:28vh;
  bottom:-5vh;right:-10vw;
  filter:blur(50px);
  animation:aurora-drift-2 14s ease-in-out infinite alternate;
}
.a3{
  width:60vw;height:22vh;
  top:30%;left:20%;
  filter:blur(70px);
  animation:aurora-drift-3 20s ease-in-out infinite alternate;
}
@keyframes aurora-drift-1{
  from{transform:translateX(0) skewX(0deg) scaleY(1);}
  to{transform:translateX(5vw) skewX(-4deg) scaleY(1.15);}
}
@keyframes aurora-drift-2{
  from{transform:translateX(0) skewX(0deg);}
  to{transform:translateX(-6vw) skewX(5deg);}
}
@keyframes aurora-drift-3{
  from{transform:translate(0,0) rotate(-3deg);}
  to{transform:translate(4vw,-2vh) rotate(3deg);}
}
/* Scene-specific aurora colours */
.scene-0 .a1{opacity:.35;background:linear-gradient(90deg,rgba(140,0,255,.7),rgba(255,40,140,.5),transparent);}
.scene-0 .a2{opacity:.25;background:linear-gradient(270deg,rgba(255,60,180,.6),rgba(80,0,200,.4),transparent);}
.scene-0 .a3{opacity:.2;background:radial-gradient(ellipse,rgba(200,60,255,.5),transparent 70%);}
.scene-1 .a1{opacity:.3;background:linear-gradient(90deg,rgba(0,80,255,.7),rgba(0,200,255,.5),transparent);}
.scene-1 .a2{opacity:.22;background:linear-gradient(270deg,rgba(0,220,255,.5),rgba(60,0,200,.4),transparent);}
.scene-1 .a3{opacity:.18;background:radial-gradient(ellipse,rgba(0,160,255,.45),transparent 70%);}
.scene-2 .a1{opacity:.28;background:linear-gradient(90deg,rgba(0,160,60,.65),rgba(60,220,100,.4),transparent);}
.scene-2 .a2{opacity:.22;background:linear-gradient(270deg,rgba(255,160,0,.5),rgba(0,140,50,.4),transparent);}
.scene-2 .a3{opacity:.18;background:radial-gradient(ellipse,rgba(80,220,120,.4),transparent 70%);}
.scene-3 .a1{opacity:.28;background:linear-gradient(90deg,rgba(0,200,220,.6),rgba(100,0,255,.4),transparent);}
.scene-3 .a2{opacity:.22;background:linear-gradient(270deg,rgba(120,0,255,.5),rgba(0,200,200,.4),transparent);}
.scene-3 .a3{opacity:.18;background:radial-gradient(ellipse,rgba(0,240,200,.35),transparent 70%);}

/* ── LAYER 3: Floating orbs ── */
.orb{
  position:absolute;border-radius:50%;
  opacity:0;pointer-events:none;
  transition:opacity 1.2s ease, background 1.2s ease;
  will-change:transform;
}
.o1{width:500px;height:500px;top:-180px;left:-140px;filter:blur(90px);animation:orb-f1 16s ease-in-out infinite alternate;}
.o2{width:420px;height:420px;bottom:-120px;right:-100px;filter:blur(80px);animation:orb-f2 12s ease-in-out infinite alternate;}
.o3{width:300px;height:300px;top:40%;right:10%;filter:blur(70px);animation:orb-f3 19s ease-in-out infinite alternate;}
.o4{width:220px;height:220px;top:20%;left:40%;filter:blur(60px);animation:orb-f4 11s ease-in-out infinite alternate;}
@keyframes orb-f1{from{transform:translate(0,0) scale(1);}to{transform:translate(60px,40px) scale(1.1);}}
@keyframes orb-f2{from{transform:translate(0,0);}to{transform:translate(-50px,-30px) scale(1.08);}}
@keyframes orb-f3{from{transform:translate(0,0) scale(1);}to{transform:translate(-30px,50px) scale(1.12);}}
@keyframes orb-f4{from{transform:translate(0,0);}to{transform:translate(40px,-40px) scale(1.15);}}
/* Orb colours per scene */
.scene-0 .o1{opacity:.45;background:radial-gradient(circle,rgba(130,0,255,.8),rgba(80,0,160,.2));}
.scene-0 .o2{opacity:.35;background:radial-gradient(circle,rgba(255,30,130,.7),rgba(160,0,80,.2));}
.scene-0 .o3{opacity:.25;background:radial-gradient(circle,rgba(255,100,0,.6),rgba(120,0,60,.1));}
.scene-0 .o4{opacity:.3;background:radial-gradient(circle,rgba(180,0,255,.7),transparent);}
.scene-1 .o1{opacity:.4;background:radial-gradient(circle,rgba(0,60,220,.8),rgba(0,20,120,.2));}
.scene-1 .o2{opacity:.35;background:radial-gradient(circle,rgba(0,200,255,.6),rgba(0,80,180,.2));}
.scene-1 .o3{opacity:.22;background:radial-gradient(circle,rgba(80,0,255,.55),rgba(30,0,140,.1));}
.scene-1 .o4{opacity:.28;background:radial-gradient(circle,rgba(0,160,255,.65),transparent);}
.scene-2 .o1{opacity:.38;background:radial-gradient(circle,rgba(0,140,40,.75),rgba(0,60,20,.2));}
.scene-2 .o2{opacity:.32;background:radial-gradient(circle,rgba(255,140,0,.6),rgba(140,60,0,.2));}
.scene-2 .o3{opacity:.2;background:radial-gradient(circle,rgba(0,200,80,.5),rgba(0,80,30,.1));}
.scene-2 .o4{opacity:.25;background:radial-gradient(circle,rgba(200,220,0,.55),transparent);}
.scene-3 .o1{opacity:.38;background:radial-gradient(circle,rgba(0,180,200,.7),rgba(0,80,100,.2));}
.scene-3 .o2{opacity:.3;background:radial-gradient(circle,rgba(120,0,240,.6),rgba(60,0,140,.2));}
.scene-3 .o3{opacity:.22;background:radial-gradient(circle,rgba(0,240,180,.5),transparent);}
.scene-3 .o4{opacity:.26;background:radial-gradient(circle,rgba(60,0,255,.55),transparent);}

/* ── LAYER 4: SVG mesh grid ── */
.mesh-grid{
  position:absolute;inset:0;
  opacity:1;
  pointer-events:none;
  animation:grid-pan 60s linear infinite;
}
@keyframes grid-pan{
  from{transform:translate(0,0);}
  to{transform:translate(60px,60px);}
}

/* ── LAYER 5: Radial vignette ── */
.bg-vignette{
  position:absolute;inset:0;
  background:radial-gradient(ellipse 85% 85% at 50% 50%, transparent 40%, rgba(0,0,0,.75) 100%);
  pointer-events:none;
}

/* ── LAYER 6: Film grain ── */
.noise-layer{
  position:absolute;inset:0;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E");
  opacity:.04;
  mix-blend-mode:overlay;
  pointer-events:none;
}

/* ── TOPBAR ── */
.topbar{position:relative;z-index:100;display:flex;align-items:center;height:140px;padding:0 3rem;gap:1.5rem;background:linear-gradient(180deg, rgba(8,11,20,0.8) 0%, transparent 100%);border-bottom:none;flex-shrink:0;}
.logo-area{display:flex;align-items:center;gap:12px;background:none;border:none;}
.logo-text{font-family:var(--font-d);font-size:20px;font-weight:800;color:#fff;letter-spacing:.04em;}
.nav-pills{flex:1;display:flex;justify-content:center;gap:6px;}
.nav-pill{padding:6px 20px;border-radius:100px;font-family:var(--font-b);font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:rgba(255,255,255,.45);cursor:pointer;transition:all .2s;border:1px solid transparent;}
.nav-pill:hover{color:rgba(255,255,255,.8);border-color:var(--border);}
.pill-on{background:#fff;color:#000 !important;font-weight:700;border-color:#fff !important;}
.topbar-right{display:flex;align-items:center;gap:16px;}
.live-badge{display:flex;align-items:center;gap:5px;font-family:var(--font-d);font-size:11px;font-weight:700;letter-spacing:.12em;color:var(--green);}
.ld{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);animation:pulse 1.4s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
.clk{font-family:var(--font-d);font-size:13px;color:rgba(255,255,255,.5);letter-spacing:.04em;}

/* ── STAGE ── */
.stage{flex:1;position:relative;overflow:hidden;z-index:10;}
.slide{position:absolute;inset:0;opacity:0;pointer-events:none;transform:translateY(24px) scale(.97);transition:opacity .5s cubic-bezier(.22,1,.36,1),transform .5s cubic-bezier(.22,1,.36,1);}
.slide.sin{opacity:1;transform:translateY(0) scale(1);pointer-events:all;}
.slide.sout{opacity:0;transform:translateY(-20px) scale(1.03);transition:opacity .3s ease,transform .3s ease;}
.slide-inner{width:100%;height:100%;padding:1.5rem 2.5rem;display:flex;flex-direction:column;}

/* ── OVERVIEW ── */
.overview-slide{justify-content:center;gap:1.2rem;}
.ov-headline{margin-bottom:.5rem;}
.ov-eye{font-family:var(--font-b);font-size:12px;letter-spacing:.25em;text-transform:uppercase;color:rgba(255,255,255,.4);margin-bottom:4px;}
.ov-big{font-family:var(--font-d);font-size:clamp(52px,6.5vw,88px);font-weight:800;color:#fff;line-height:.88;letter-spacing:-.03em;}
.ov-outline{-webkit-text-stroke:2px rgba(255,255,255,.6);color:transparent;}
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}
.stat-card{border-radius:24px;padding:2rem 1.6rem;position:relative;overflow:hidden;animation:card-rise .65s cubic-bezier(.22,1,.36,1) both;animation-delay:var(--d,0s);cursor:default;transition:transform .3s ease,box-shadow .3s ease;}
.stat-card:hover{transform:translateY(-8px);box-shadow:0 24px 60px rgba(0,0,0,.55);}
@keyframes card-rise{from{opacity:0;transform:translateY(40px) scale(.95);}to{opacity:1;transform:translateY(0) scale(1);}}
.sc-ios{background:linear-gradient(145deg,#0a3977,#1a6fd4);border:1px solid rgba(100,180,255,.2);}
.sc-and{background:linear-gradient(145deg,#0a3d1a,#1a9c3d);border:1px solid rgba(100,255,140,.2);}
.sc-news{background:linear-gradient(145deg,#3d0a3a,#9b2d9b);border:1px solid rgba(200,100,240,.2);}
.sc-total{background:linear-gradient(145deg,#3d2000,#c06000);border:1px solid rgba(255,160,60,.2);}
.sc-icon{margin-bottom:12px;}
.sc-big-icon{font-size:40px;margin-bottom:12px;display:block;}
.sc-num{font-family:var(--font-d);font-size:clamp(40px,4.5vw,64px);font-weight:800;color:#fff;line-height:1;margin-bottom:6px;}
.sc-lbl{font-family:var(--font-d);font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:rgba(255,255,255,.7);}
.sc-stars-row{display:flex;gap:3px;margin:8px 0 4px;}
.sc-star{width:16px;height:16px;background:rgba(255,255,255,.25);clip-path:polygon(50% 0%,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%);}
.sc-star.star-full{background:#FFD700;}.sc-star.star-half{background:linear-gradient(90deg,#FFD700 50%,rgba(255,255,255,.25) 50%);}
.sc-count{font-family:var(--font-b);font-size:12px;color:rgba(255,255,255,.45);margin-top:4px;}

/* ══════════════════════════════════════════════════════════
   SENTIMENT SLIDE — BOLD REDESIGN
   Palette-per-emotion, floating particles, kinetic layout
   ══════════════════════════════════════════════════════════ */

/* Slide wrapper */
.sentiment-slide{
  height: 100%;
  justify-content: center;
  align-items: center;
  gap:0;
  padding:0 3rem;
  position:relative;
  overflow:hidden;
}

/* Floating particle bubbles — pure CSS, emotion-colored */
.sentiment-slide::before,
.sentiment-slide::after{
  content:'';
  position:absolute;
  border-radius:50%;
  pointer-events:none;
  z-index:0;
  opacity:.13;
  animation:part-drift 12s ease-in-out infinite alternate;
}
.sentiment-slide::before{
  width:420px;height:420px;
  top:-80px;right:-120px;
  background:radial-gradient(circle, currentColor 0%, transparent 70%);
  animation-duration:10s;
}
.sentiment-slide::after{
  width:280px;height:280px;
  bottom:30px;left:-60px;
  background:radial-gradient(circle, currentColor 0%, transparent 70%);
  animation-duration:14s;animation-delay:-5s;
}
@keyframes part-drift{
  from{transform:translate(0,0) scale(1);}
  to{transform:translate(40px,-30px) scale(1.15);}
}

/* ── HEADER ── */
.ss-header{
  display:flex;align-items:center;gap:16px;
  padding-bottom:0.85rem;
  border-bottom:1px solid rgba(255,255,255,.08);
  flex-shrink:0;flex-wrap:wrap;
  position:relative;z-index:2;
}
.ss-platform-badge{
  display:flex;align-items:center;gap:12px;
  padding:10px 20px;
  border-radius:60px;
  border:1.5px solid rgba(255,255,255,.12);
  background:rgba(255,255,255,.05);
  backdrop-filter:blur(12px);
  box-shadow:0 4px 20px rgba(0,0,0,.3);
}
.ios-badge{
  border-color:rgba(0,122,255,.4);
  background:linear-gradient(135deg,rgba(0,80,200,.15),rgba(0,200,255,.08));
  box-shadow:0 4px 20px rgba(0,122,255,.15);
}
.and-badge{
  border-color:rgba(52,211,100,.4);
  background:linear-gradient(135deg,rgba(20,120,40,.18),rgba(80,220,120,.08));
  box-shadow:0 4px 20px rgba(52,211,100,.15);
}
.ss-badge-img{width:36px;height:36px;object-fit:contain;}
.ss-badge-name{font-family:var(--font-d);font-size:13px;font-weight:700;letter-spacing:.04em;}
.ss-badge-stars{display:flex;align-items:center;gap:3px;margin-top:4px;}
.ss-star{
  width:12px;height:12px;
  background:rgba(255,255,255,.18);
  clip-path:polygon(50% 0%,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%);
}
.ss-star.star-full{background:#FFD700;filter:drop-shadow(0 0 3px #FFD70088);}
.ss-star.star-half{background:linear-gradient(90deg,#FFD700 50%,rgba(255,255,255,.18) 50%);}
.ss-rating{font-size:13px;font-weight:800;margin-left:6px;color:#FFD700;text-shadow:0 0 12px #FFD700aa;}
.ss-title-block{flex:1;}
.ss-eyebrow{
  font-family:var(--font-b);font-size:10px;letter-spacing:.22em;text-transform:uppercase;
  color:rgba(255,255,255,.32);margin-bottom:3px;
}
.ss-big-title{
  font-family:var(--font-d);font-size:clamp(20px,2.6vw,36px);font-weight:800;
  color:#fff;line-height:1;
  text-shadow:0 2px 20px rgba(255,255,255,.15);
}

/* ── MAIN STAGE AREA ── */
.ss-stage-area{
  flex:1;
  display:grid;
  grid-template-columns:220px 1fr;
  gap:0;
  min-height:0;
  width:100%;
  position:relative;z-index:2;
  align-items: center; /* Center items vertically */
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
  filter:blur(65px);
  opacity:.4;
  top:50%;left:50%;
  transform:translate(-50%,-52%);
  pointer-events:none;
  transition:background .6s ease;
  animation:sf-orb-pulse 3s ease-in-out infinite alternate;
}
@keyframes sf-orb-pulse{
  from{opacity:.28;transform:translate(-50%,-52%) scale(1);}
  to{opacity:.55;transform:translate(-50%,-52%) scale(1.22);}
}
.sf-neutral .sf-glow{background:radial-gradient(circle,#7888cc,#3344aa);}
.sf-happy .sf-glow{background:radial-gradient(circle,#1db954,#0a5c28);}
.sf-ecstatic .sf-glow{background:radial-gradient(circle,#FFD700,#ff9500);}
.sf-frustrated .sf-glow{background:radial-gradient(circle,#ff6b35,#cc2200);}
.sf-angry .sf-glow{background:radial-gradient(circle,#ff2d78,#8b0000);}

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

/* Emotion name — big, bold, gradient text */
.sf-name{
  font-family:var(--font-d);
  font-size:28px;
  font-weight:800;
  letter-spacing:-.01em;
  line-height:1;
  position:relative;z-index:1;
  background:linear-gradient(135deg,#fff 40%,rgba(255,255,255,.55));
  -webkit-background-clip:text;
  -webkit-text-fill-color:transparent;
  background-clip:text;
  text-align:center;
  width:100%;
}
/* Tint the emotion name per sentiment */
.sf-neutral .sf-name{background:linear-gradient(135deg,#a0b4ff,#7888cc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.sf-happy .sf-name{background:linear-gradient(135deg,#7affa0,#1db954);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.sf-ecstatic .sf-name{background:linear-gradient(135deg,#ffe97a,#FFD700);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.sf-frustrated .sf-name{background:linear-gradient(135deg,#ffb07a,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.sf-angry .sf-name{background:linear-gradient(135deg,#ff8ab0,#ff2d78);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}

.sf-count{
  font-family:var(--font-b);font-size:11px;
  color:rgba(255,255,255,.35);
  letter-spacing:.12em;text-transform:uppercase;
  position:relative;z-index:1;
  background:rgba(255,255,255,.06);
  border:1px solid rgba(255,255,255,.1);
  border-radius:20px;
  padding:4px 12px;
}

/* Sentiment progress dots */
.ss-progress-dots{display:flex;gap:5px;margin-top:6px;position:relative;z-index:1;justify-content:center;}
.ss-sdot{
  width:6px;height:6px;border-radius:50%;
  background:rgba(255,255,255,.15);
  transition:all .35s cubic-bezier(.34,1.56,.64,1);
}
.sdot-on{background:#fff !important;width:20px !important;border-radius:4px !important;box-shadow:0 0 8px rgba(255,255,255,.5);}

/* ── RIGHT: REVIEW CARD PANEL ── */
.ss-review-panel{
  flex:1;
  display:flex;
  flex-direction:column;
  gap:1rem;
  margin-left:1.6rem;
  min-height:260px;
  position:relative;
  overflow:hidden;
}
/* The main review card — universal centered size */
.ss-review-card{
  width:100%;
  max-width:900px;
  margin:auto;
  border-radius:32px;
  padding:2rem 2.8rem;
  border:1.5px solid rgba(255,255,255,.09);
  background:rgba(18, 22, 33, 0.82);
  backdrop-filter: blur(12px);
  display:flex;
  flex-direction:column;
  gap:1rem;
  position:relative;
  overflow:hidden;
  box-shadow:0 12px 40px rgba(0,0,0,.35);
  will-change:transform;
  animation:card-levitate 5s ease-in-out infinite;
}

.ss-sentiment-float{
  width:220px;
  flex-shrink:0;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:12px;
  position:relative;
  text-align:center;
  padding:1rem 0;
  animation:sentiment-spotlight 1.4s cubic-bezier(.22,1,.36,1) forwards;
  z-index: 10;
}
@keyframes sentiment-spotlight{
  0%{transform:translateX(calc(50vw - 110px)) scale(.4);opacity:0;}
  30%{transform:translateX(calc(50vw - 110px)) scale(1.6);opacity:1;}
  60%{transform:translateX(calc(50vw - 110px)) scale(1.2);opacity:1;}
  100%{transform:translateX(0) scale(1);opacity:1;}
}
.ss-review-panel{
  flex:1;
  height: 100%;
  display:flex;
  flex-direction:column;
  gap:1rem;
  margin-left:1.6rem;
  position:relative;
  overflow:visible; /* Show the stack ghost cards */
  animation:panel-entrance 0.6s ease 0.9s both;
}
@keyframes panel-entrance{
  from{opacity:0;transform:translateY(20px);}
  to{opacity:1;transform:translateY(0);}
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
  border-color:rgba(120,136,204,.45);
  box-shadow:0 0 0 1px rgba(120,136,204,.1), inset 0 0 60px rgba(120,136,204,.04);
}
.rc-neutral::before{background:linear-gradient(90deg,transparent,#7888cc,#a0b4ff,transparent);}
.rc-neutral::after{background:#7888cc;}

.rc-happy{
  border-color:rgba(29,185,84,.45);
  box-shadow:0 0 0 1px rgba(29,185,84,.1), inset 0 0 60px rgba(29,185,84,.04);
}
.rc-happy::before{background:linear-gradient(90deg,transparent,#1db954,#7affa0,transparent);}
.rc-happy::after{background:#1db954;}

.rc-ecstatic{
  border-color:rgba(255,215,0,.55);
  box-shadow:0 0 0 1px rgba(255,215,0,.12), inset 0 0 60px rgba(255,215,0,.05);
}
.rc-ecstatic::before{background:linear-gradient(90deg,transparent,#ff9500,#FFD700,#ffe97a,transparent);}
.rc-ecstatic::after{background:#FFD700;}

.rc-frustrated{
  border-color:rgba(255,107,53,.48);
  box-shadow:0 0 0 1px rgba(255,107,53,.1), inset 0 0 60px rgba(255,107,53,.04);
}
.rc-frustrated::before{background:linear-gradient(90deg,transparent,#ff6b35,#ffb07a,transparent);}
.rc-frustrated::after{background:#ff6b35;}

.rc-angry{
  border-color:rgba(255,45,120,.55);
  box-shadow:0 0 0 1px rgba(255,45,120,.12), inset 0 0 60px rgba(255,45,120,.05);
}
.rc-angry::before{background:linear-gradient(90deg,transparent,#ff2d78,#ff8ab0,transparent);}
.rc-angry::after{background:#ff2d78;}

/* ── AUTHOR ROW ── */
.ss-rc-author-row{
  display:flex;align-items:center;gap:14px;
  flex-shrink:0;
  padding-bottom:.85rem;
  border-bottom:1px solid rgba(255,255,255,.07);
}
.ss-rc-avatar{
  width:50px;height:50px;
  border-radius:50%;
  border:2px solid rgba(255,255,255,.18);
  display:flex;align-items:center;justify-content:center;
  font-family:var(--font-d);font-size:19px;font-weight:800;
  flex-shrink:0;
  position:relative;
  overflow:hidden;
  transition:box-shadow .4s;
}
/* Emotion-tinted avatar per sentiment (applied via parent .rc-* class cascade via custom prop) */
.rc-neutral .ss-rc-avatar{background:linear-gradient(135deg,#7888cc,#3344aa);box-shadow:0 0 16px rgba(120,136,204,.4);}
.rc-happy .ss-rc-avatar{background:linear-gradient(135deg,#1db954,#0a5c28);box-shadow:0 0 16px rgba(29,185,84,.4);}
.rc-ecstatic .ss-rc-avatar{background:linear-gradient(135deg,#FFD700,#ff9500);box-shadow:0 0 16px rgba(255,215,0,.4);}
.rc-frustrated .ss-rc-avatar{background:linear-gradient(135deg,#ff6b35,#aa2200);box-shadow:0 0 16px rgba(255,107,53,.4);}
.rc-angry .ss-rc-avatar{background:linear-gradient(135deg,#ff2d78,#8b0000);box-shadow:0 0 16px rgba(255,45,120,.4);}

.ss-rc-meta{flex:1;display:flex;flex-direction:column;gap:5px;}
.ss-rc-author{
  font-family:var(--font-d);font-size:17px;font-weight:700;color:#fff;line-height:1.2;
  letter-spacing:-.01em;
}
.ss-rc-stars-inline{display:flex;align-items:center;gap:3px;}
.ss-rc-star-sm{
  display:inline-block;width:14px;height:14px;
  background:rgba(255,255,255,.15);
  clip-path:polygon(50% 0%,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%);
  flex-shrink:0;
}
.ss-rc-star-sm.star-full{background:#FFD700;filter:drop-shadow(0 0 3px #FFD70077);}
.ss-rc-star-sm.star-half{background:linear-gradient(90deg,#FFD700 50%,rgba(255,255,255,.15) 50%);}
.ss-rc-date{margin-left:7px;font-family:var(--font-b);font-size:11px;color:rgba(255,255,255,.28);}

/* Review counter — big & prominent */
.ss-rev-indicator{
  margin-left:auto;
  font-family:var(--font-d);font-size:22px;font-weight:800;
  color:#fff;line-height:1;white-space:nowrap;
  background:rgba(255,255,255,.08);
  border:1px solid rgba(255,255,255,.1);
  border-radius:12px;
  padding:6px 12px;
}
.rev-ind-total{font-size:12px;font-weight:500;color:rgba(255,255,255,.28);}

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

/* Giant decorative quote mark — opacity-only animation, no filter repaint */
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
  from{opacity:.6;}
  to{opacity:.95;}
}

/* Review text — large, readable at TV distance */
.ss-rc-text{
  font-family:var(--font-b);
  font-size:clamp(18px,2.2vw,28px);
  line-height:1.65;
  color:rgba(255,255,255,.92);
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
  color:rgba(255,255,255,.22);
  text-align:center;
  letter-spacing:.08em;
}

/* Progress bar at bottom of panel */
.ss-rev-progress-bar{
  height:4px;
  background:rgba(255,255,255,.07);
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

/* Active state per sentiment — dot becomes accent-colored */
.tab-neutral.tab-on{
  background:#7888cc;
  border-color:#7888cc;
  box-shadow:0 0 8px rgba(120,136,204,.7);
}
.tab-happy.tab-on{
  background:#1db954;
  border-color:#1db954;
  box-shadow:0 0 8px rgba(29,185,84,.7);
}
.tab-ecstatic.tab-on{
  background:#FFD700;
  border-color:#FFD700;
  box-shadow:0 0 8px rgba(255,215,0,.7);
}
.tab-frustrated.tab-on{
  background:#ff6b35;
  border-color:#ff6b35;
  box-shadow:0 0 8px rgba(255,107,53,.7);
}
.tab-angry.tab-on{
  background:#ff2d78;
  border-color:#ff2d78;
  box-shadow:0 0 8px rgba(255,45,120,.7);
}

/* ══════════════════════════════════
   3D VERTICAL STACK TRANSITION
   ══════════════════════════════════ */
.ss-stack-panel {
  perspective: 1200px;
}
.stack-card {
  position: absolute;
  left: 0; right: 0;
  top: 46%; /* Lifted higher */
  margin: 0 auto;
  transition: all 0.75s cubic-bezier(0.16, 1, 0.3, 1);
  pointer-events: none;
}

.is-active {
  z-index: 10;
  opacity: 1;
  transform: translateY(-50%) scale(1);
  pointer-events: all;
  box-shadow: 0 30px 60px rgba(0,0,0,0.5);
}
.is-prev {
  z-index: 5;
  opacity: 0.35;
  transform: translateY(-130%) scale(0.85);
  filter: blur(2px);
}
.is-next {
  z-index: 5;
  opacity: 0.35;
  transform: translateY(30%) scale(0.85);
  filter: blur(2px);
}

/* Transition Group Hooks */
.rev-stack-enter-from {
  opacity: 0;
  transform: translateY(80%) scale(0.8);
}
.rev-stack-leave-to {
  opacity: 0;
  transform: translateY(-160%) scale(0.8);
}

/* Hide tab label text — emoji only */
.ss-tab-lbl{display:none;}

/* ── NEWS SLIDE ── */
.news-slide{flex-direction:row;gap:3.5rem;align-items:center;padding:0 3vw;height:100%;justify-content:flex-start;}
.news-left{width:200px;flex-shrink:0;}
.nl-eyebrow{font-family:var(--font-b);font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:rgba(255,255,255,.4);margin-bottom:8px;}
.nl-big{font-family:var(--font-d);font-size:clamp(44px,5.5vw,72px);font-weight:800;color:#fff;line-height:.88;letter-spacing:-.04em;margin-bottom:2rem;}
.news-count-pill{display:inline-flex;align-items:center;gap:8px;background:linear-gradient(90deg,var(--purple),var(--cyan));border-radius:100px;padding:7px 18px;}
.ncp-num{font-family:var(--font-d);font-size:24px;font-weight:800;color:#fff;}
.ncp-txt{font-family:var(--font-b);font-size:11px;color:rgba(255,255,255,.7);text-transform:uppercase;letter-spacing:.1em;}
.news-frame{flex:1;height:84vh;background:var(--surface);border:1px solid var(--border);border-radius:3vh;position:relative;overflow:hidden;box-shadow:0 32px 64px rgba(0,0,0,.55);}
.ns-poster{width:100%;height:100%;position:relative;display:flex;align-items:flex-end;overflow:hidden;}
.ns-hero{position:absolute;inset:0;z-index:0;}
.ns-hero-img{width:100%;height:100%;object-fit:cover;animation:kb 40s ease-in-out infinite alternate;}
@keyframes kb{0%{transform:scale(1);}100%{transform:scale(1.15) translate(20px,10px);}}
.ns-hero-overlay{position:absolute;inset:0;background:linear-gradient(0deg,#080b14 10%,rgba(8,11,20,.5) 60%,transparent 100%);}
.ns-content{position:relative;z-index:2;padding:5vh;width:100%;}
.ns-source-badge{display:inline-flex;align-items:center;gap:10px;padding:7px 20px;border-radius:100px;background:rgba(255,255,255,.1);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.12);margin-bottom:3vh;}
.ns-source{font-family:var(--font-d);font-weight:800;color:var(--cyan);font-size:13px;letter-spacing:.08em;}
.ns-sep{color:rgba(255,255,255,.3);}
.ns-date{font-family:var(--font-b);font-size:13px;color:rgba(255,255,255,.55);}
.ns-title{font-family:var(--font-d);font-size:clamp(30px,5vh,64px);font-weight:800;color:#fff;line-height:1.08;margin-bottom:5vh;text-shadow:0 8px 32px rgba(0,0,0,.5);}
.ns-footer{display:flex;align-items:center;justify-content:space-between;}
.ns-qr-wrap{display:flex;align-items:center;gap:16px;}
.ns-qr{width:9vh;height:9vh;border:2px solid #fff;border-radius:10px;background:#fff;}
.ns-qr-lbl{font-family:var(--font-d);font-size:13px;font-weight:800;color:var(--cyan);letter-spacing:.1em;}
.ns-pagination{display:flex;gap:7px;}
.ns-dot{width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,.25);transition:all .3s;cursor:pointer;}
.ns-dot-on{width:22px !important;border-radius:4px !important;background:#fff !important;}
.slide-next-enter-active,.slide-prev-enter-active{transition:all .5s cubic-bezier(.16,1,.3,1);}
.slide-next-leave-active,.slide-prev-leave-active{transition:all .3s ease;}
.slide-next-enter-from{opacity:0;transform:translateX(40px);}
.slide-next-leave-to{opacity:0;transform:translateX(-30px);}
.slide-prev-enter-from{opacity:0;transform:translateX(-40px);}
.slide-prev-leave-to{opacity:0;transform:translateX(30px);}

/* ── BOTTOM BAR ── */
.bottom-bar{position:relative;z-index:100;height:50px;display:flex;align-items:center;padding:0 2.4rem;gap:1rem;background:rgba(8,11,20,.8);backdrop-filter:blur(20px);border-top:1px solid var(--border);flex-shrink:0;}
.progress-rail{position:absolute;bottom:0;left:0;right:0;height:3px;background:rgba(255,255,255,.07);}
.progress-fill{height:100%;background:linear-gradient(90deg,var(--purple),var(--cyan));transition:none;box-shadow:0 0 10px var(--cyan);}
.bb-left{display:flex;align-items:center;gap:8px;}
.bb-brand{font-family:var(--font-d);font-size:13px;font-weight:800;color:#fff;}
.bb-sep{color:rgba(255,255,255,.25);}
.bb-sprint{font-family:var(--font-b);font-size:11px;color:rgba(255,255,255,.28);letter-spacing:.06em;}
.bb-center{flex:1;display:flex;align-items:center;justify-content:center;gap:8px;}
.bb-pip{width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,.2);cursor:pointer;transition:all .25s;}
.bb-pip:hover{background:rgba(255,255,255,.5);}
.pipa{width:26px !important;border-radius:4px !important;background:#fff !important;}
.bb-right{display:flex;align-items:center;gap:12px;}
.bb-counter{font-family:var(--font-d);font-size:12px;color:rgba(255,255,255,.3);}
.bb-keys{font-size:10px;color:rgba(255,255,255,.15);letter-spacing:.06em;}

#app{width:100vw;height:100vh;display:flex;flex-direction:column;overflow:hidden;position:relative;font-family:'Puvi', sans-serif;}
</style>
