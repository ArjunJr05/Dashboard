<template>
  <!-- LOADING -->
  <div class="loading-screen" v-if="!appReady && !loadError">
    <div class="load-blob load-blob-1"></div>
    <div class="load-blob load-blob-2"></div>
    <div class="load-blob load-blob-3"></div>
    <div class="load-content">
      <img src="/arattai.png" class="load-logo" />
      <div class="load-bar"><div class="load-bar-fill"></div></div>
    </div>
  </div>

  <div class="error-screen" v-if="loadError">
    <div class="error-inner">⚠ Run the Python fetcher first, then refresh.</div>
  </div>

  <template v-if="appReady">
    <div class="app-shell">
    <div class="scene-bg" :class="'scene-'+cur">
      <div class="bg-floor"></div>
      <svg class="mesh-grid" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">
        <defs>
          <pattern id="dots" width="40" height="40" patternUnits="userSpaceOnUse">
            <circle cx="20" cy="20" r="1.4" fill="rgba(255,255,255,0.05)"/>
          </pattern>
          <radialGradient id="dot-fade" cx="50%" cy="50%" r="55%">
            <stop offset="0%" stop-color="white" stop-opacity="0"/>
            <stop offset="100%" stop-color="white" stop-opacity="1"/>
          </radialGradient>
          <mask id="dot-mask">
            <rect width="100%" height="100%" fill="white"/>
            <rect width="100%" height="100%" fill="url(#dot-fade)"/>
          </mask>
        </defs>
        <rect width="100%" height="100%" fill="url(#dots)" mask="url(#dot-mask)"/>
      </svg>
      <div class="orb o1"></div>
      <div class="orb o2"></div>
      <div class="orb o3"></div>
    </div>

    <!-- TOPBAR -->
    <div class="topbar">
      <div class="tb-left">
        <img src="/arattai.png" alt="Arattai" class="topbar-logo" />
      </div>
      <div class="tb-right">
        <transition name="fade">
          <div v-if="cur===1 || cur===2" class="tb-meta-group">
            <div class="ss-platform-badge badge-top" :class="cur===1?'ios-badge':'and-badge'">
              <img :src="cur===1?'/ios.png':'/android.png'" class="ss-badge-img-sm" />
              <div class="ss-badge-name">{{ cur===1?'App Store':'Play Store' }} <span class="ss-rating-sm">{{ cur===1?ios.rating:android.rating }}</span></div>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!-- SLIDES -->
    <div class="stage">

      <!-- ══════════════ SLIDE 0: OVERVIEW DASHBOARD (REDESIGNED) ══════════════ -->
      <div v-if="isSlideEnabled(0)" class="slide" :class="{sin: cur===0, sout: exitSlide===0}">
        <div class="slide-inner overview-slide">

          <!-- Ambient background particles -->
          <div class="ov-ambient">
            <div class="ov-amb-orb ov-amb-1"></div>
            <div class="ov-amb-orb ov-amb-2"></div>
            <div class="ov-amb-orb ov-amb-3"></div>
            <div class="ov-amb-grid"></div>
          </div>

          <!-- ── LEFT COLUMN: Brand Hero ── -->
          <div class="ov-left-col">

            <!-- Brand block -->
            <div class="ov-brand-hero">
              <div class="ov-brand-eyebrow">
              </div>

              <div class="ov-brand-title">
                <div class="ov-title-line1">TODAY'S</div>
                <div class="ov-title-line2">
                  <span class="ov-title-outline-word">SNAPSHOTS</span>
                </div>
              </div>


              <!-- Signal total with lottie -->
              <div class="ov-signal-hero">
                <lottie-player
                  src="https://assets2.lottiefiles.com/packages/lf20_qp1q7mct.json"
                  background="transparent"
                  speed="1"
                  loop autoplay
                  class="ov-lottie-hero">
                </lottie-player>
                <div class="ov-signal-text">
                  <div class="ov-signal-num">{{ totalSignals }}</div>
                  <div class="ov-signal-label">TOTAL SIGNALS</div>
                  <div class="ov-signal-chips">
                    <span class="ov-chip ov-chip-rev">{{ allRevs.length }} Reviews</span>
                    <span class="ov-chip ov-chip-news">{{ gnews.posts?.length || 0 }} News</span>
                    <span class="ov-chip ov-chip-x">{{ twitter.recent_posts?.length || 0 }} X Posts</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Live ticker strip -->
            <div class="ov-ticker">
              <div class="ov-ticker-label">LIVE</div>
              <div class="ov-ticker-track">
                <div class="ov-ticker-inner">
                  <span>iOS Rating {{ ios.rating || '4.7' }} ★</span>
                  <span class="ov-tick-sep">◆</span>
                  <span>Android Rating {{ android.rating || '4.6' }} ★</span>
                  <span class="ov-tick-sep">◆</span>
                  <span>{{ ios.total_ratings ? fmtNum(ios.total_ratings) : '19.4k' }} App Store Reviews</span>
                  <span class="ov-tick-sep">◆</span>
                  <span>{{ android.total_ratings ? fmtNum(android.total_ratings) : '229k' }} Play Store Reviews</span>
                  <span class="ov-tick-sep">◆</span>
                  <span>{{ gnews.posts?.length || 0 }} Media Stories This Sprint</span>
                  <span class="ov-tick-sep">◆</span>
                  <span>iOS Rating {{ ios.rating || '4.7' }} ★</span>
                  <span class="ov-tick-sep">◆</span>
                  <span>Android Rating {{ android.rating || '4.6' }} ★</span>
                  <span class="ov-tick-sep">◆</span>
                  <span>{{ ios.total_ratings ? fmtNum(ios.total_ratings) : '19.4k' }} App Store Reviews</span>
                  <span class="ov-tick-sep">◆</span>
                  <span>{{ android.total_ratings ? fmtNum(android.total_ratings) : '229k' }} Play Store Reviews</span>
                </div>
              </div>
            </div>

          </div>

          <!-- ── RIGHT COLUMN: Metric Cards ── -->
          <div class="ov-right-col">

            <!-- Top row: iOS + Android -->
            <div class="ov-cards-row ov-row-platforms">

              <!-- iOS Card -->
              <div class="ov-card ov-card-ios" style="--d:0.08s">
                <div class="ov-card-shimmer"></div>
                <div class="ov-card-head">
                  <div class="ov-card-platform">
                    <img src="/ios.png" class="ov-plat-icon" alt="iOS" />
                    <div>
                      <div class="ov-plat-name">App Store</div>
                      <div class="ov-plat-sub">iOS</div>
                    </div>
                  </div>
                  <div class="ov-card-badge ov-badge-ios">WIDS</div>
                </div>

                <div class="ov-rating-block">
                  <div class="ov-ring-wrap">
                    <svg viewBox="0 0 100 100" class="ov-ring-svg">
                      <circle cx="50" cy="50" r="40" stroke="rgba(247,215,71,0.15)" stroke-width="9" fill="none"/>
                      <circle cx="50" cy="50" r="40" stroke="url(#ringGradient)" stroke-width="9" fill="none"
                        stroke-dasharray="251"
                        :stroke-dashoffset="251 - (251 * ((ios.rating||4.7)/5))"
                        stroke-linecap="round"
                        transform="rotate(-90 50 50)"
                        style="transition:stroke-dashoffset 1.4s cubic-bezier(.4,0,.2,1)"/>
                      <defs>
                        <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stop-color="#e8c200"/>
                          <stop offset="100%" stop-color="#f7d747"/>
                        </linearGradient>
                      </defs>
                    </svg>
                    <div class="ov-ring-center">
                      <div class="ov-ring-score">{{ ios.rating || '4.7' }}</div>
                      <div class="ov-ring-label">/ 5.0</div>
                    </div>
                  </div>
                  <div class="ov-rating-meta">
                    <div class="ov-rating-stars">
                      <span v-for="i in 5" :key="i" class="ov-star" :class="getStarClass(ios.rating||4.7, i)"></span>
                    </div>
                    <div class="ov-rating-count">{{ ios.total_ratings ? fmtNum(ios.total_ratings) : '19.4k' }}</div>
                    <div class="ov-rating-unit">Happy Users</div>
                  </div>
                </div>

                <div class="ov-card-footer-bar">
                  <div class="ov-footer-fill" style="width: 94%"></div>
                </div>
              </div>

              <!-- Android Card -->
              <div class="ov-card ov-card-and" style="--d:0.16s">
                <div class="ov-card-shimmer"></div>
                <div class="ov-card-head">
                  <div class="ov-card-platform">
                    <img src="/android.png" class="ov-plat-icon ov-plat-android" alt="Android" />
                    <div>
                      <div class="ov-plat-name">Play Store</div>
                      <div class="ov-plat-sub">Android</div>
                    </div>
                  </div>
                  <div class="ov-card-badge ov-badge-and">PLAY SENTO</div>
                </div>

                <div class="ov-rating-block">
                  <div class="ov-ring-wrap">
                    <svg viewBox="0 0 100 100" class="ov-ring-svg">
                      <circle cx="50" cy="50" r="40" stroke="rgba(247,215,71,0.15)" stroke-width="9" fill="none"/>
                      <circle cx="50" cy="50" r="40" stroke="url(#ringGradient2)" stroke-width="9" fill="none"
                        stroke-dasharray="251"
                        :stroke-dashoffset="251 - (251 * ((android.rating||4.6)/5))"
                        stroke-linecap="round"
                        transform="rotate(-90 50 50)"
                        style="transition:stroke-dashoffset 1.4s cubic-bezier(.4,0,.2,1)"/>
                      <defs>
                        <linearGradient id="ringGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stop-color="#c8a000"/>
                          <stop offset="100%" stop-color="#f7d747"/>
                        </linearGradient>
                      </defs>
                    </svg>
                    <div class="ov-ring-center">
                      <div class="ov-ring-score">{{ android.rating || '4.6' }}</div>
                      <div class="ov-ring-label">/ 5.0</div>
                    </div>
                  </div>
                  <div class="ov-rating-meta">
                    <div class="ov-rating-stars">
                      <span v-for="i in 5" :key="i" class="ov-star" :class="getStarClass(android.rating||4.6, i)"></span>
                    </div>
                    <div class="ov-rating-count">{{ android.total_ratings ? fmtNum(android.total_ratings) : '229k' }}</div>
                    <div class="ov-rating-unit">Android Voices</div>
                  </div>
                </div>

                <div class="ov-card-footer-bar">
                  <div class="ov-footer-fill" style="width: 92%"></div>
                </div>
              </div>

            </div>

            <!-- Bottom row: Buzz + Community -->
            <div class="ov-cards-row ov-row-bottom">

              <!-- Social Buzz Card -->
              <div class="ov-card ov-card-buzz" style="--d:0.24s">
                <div class="ov-card-shimmer"></div>
                <div class="ov-buzz-top">
                  <div class="ov-buzz-title-row">
                    <lottie-player
                      src="https://assets6.lottiefiles.com/packages/lf20_49rdyysj.json"
                      background="transparent"
                      speed="1"
                      loop autoplay
                      class="ov-lottie-buzz">
                    </lottie-player>
                    <span class="ov-buzz-heading">Social Pulse</span>
                  </div>
                  <div class="ov-buzz-tag-live">
                    <span class="ov-live-blink"></span> LIVE
                  </div>
                </div>

                <div class="ov-buzz-metrics">
                  <div class="ov-buzz-metric">
                    <div class="ov-buzz-icon-wrap ov-bi-news">
                      <span>📰</span>
                    </div>
                    <div class="ov-buzz-metric-body">
                      <div class="ov-buzz-num">{{ String(gnews.posts?.length || 3).padStart(2,'0') }}</div>
                      <div class="ov-buzz-desc">Media Stories</div>
                      <div class="ov-buzz-sprint">this sprint</div>
                    </div>
                  </div>

                  <div class="ov-buzz-divider-v"></div>

                  <div class="ov-buzz-metric">
                    <div class="ov-buzz-icon-wrap ov-bi-x">
                      <span style="font-size:15px;font-weight:900;font-family:sans-serif">𝕏</span>
                    </div>
                    <div class="ov-buzz-metric-body">
                      <div class="ov-buzz-num">{{ String(twitter.recent_posts?.length || 0).padStart(2,'0') }}</div>
                      <div class="ov-buzz-desc">X Posts</div>
                      <div class="ov-buzz-sprint">this sprint</div>
                    </div>
                  </div>

                  <div class="ov-buzz-divider-v"></div>

                  <div class="ov-buzz-metric">
                    <div class="ov-buzz-icon-wrap ov-bi-chat">
                      <span>💬</span>
                    </div>
                    <div class="ov-buzz-metric-body">
                      <div class="ov-buzz-num">{{ String(allRevs.length).padStart(2,'0') }}</div>
                      <div class="ov-buzz-desc">Reviews</div>
                      <div class="ov-buzz-sprint">total tracked</div>
                    </div>
                  </div>
                </div>

                <!-- Animated waveform -->
                <div class="ov-waveform">
                  <span v-for="b in 18" :key="b" class="ov-wave-bar" :style="{'--bi': b}"></span>
                </div>
              </div>

              <!-- Community Lottie Card -->
              <div class="ov-card ov-card-community" style="--d:0.32s">
                <div class="ov-card-shimmer"></div>
                <div class="ov-community-tag">X PROFILE</div>

                <div class="ov-community-lottie-wrap">
                  <lottie-player
                    src="https://assets4.lottiefiles.com/packages/lf20_myejiggj.json"
                    background="transparent"
                    speed="0.8"
                    loop autoplay
                    class="ov-lottie-community">
                  </lottie-player>
                </div>

                <div class="ov-community-footer">
                  <div class="ov-community-label">X Followers</div>
                  <div class="ov-community-sub">Live from @Arattai profile</div>
                  <div class="ov-community-num">{{ xFollowersText }}<span class="ov-community-num-label"> followers</span></div>
                </div>

                </div>
              </div>
            </div>
          </div>
        </div>

      <!-- ══════════════ SLIDE 1: APP STORE ══════════════ -->
      <div v-if="isSlideEnabled(1)" class="slide" :class="{sin: cur===1, sout: exitSlide===1}">
        <div class="slide-inner cluster-slide">
          <div class="ov-ambient">
            <div class="ov-amb-orb ov-amb-1" style="background:radial-gradient(circle,rgba(255,184,0,0.1),transparent 70%)"></div>
            <div class="ov-amb-orb ov-amb-2" style="background:radial-gradient(circle,rgba(255,255,255,0.05),transparent 70%)"></div>
          </div>

          <!-- BUBBLE GRID: 5 clusters, each with emoji hub + surrounding speech-bubble cards -->
          <div class="bubble-grid" :data-active="iosActiveCount">
            <template v-for="s in sentimentOrder" :key="'ios-node-'+s.key">
              <div
                v-if="(iosSentimentGroups[s.key] || []).length > 0"
                class="bc-cluster"
                :style="{'--sc': s.color}"
              >
                <div class="bc-sent-name">{{ s.label }}</div>
                <div class="bc-hub">
                  <div class="bc-hub-glow"></div>
                  <div class="bc-hub-ring"></div>
                  <EmotionFace :emotionKey="s.key" class="bc-emoji" />
                </div>
                <div class="bc-bubbles" :data-count="(iosSentimentGroups[s.key]||[]).length">
                  <div
                    v-for="(rev, bIdx) in (iosSentimentGroups[s.key]||[]).slice(0,5)"
                    :key="'ios-b-'+s.key+bIdx"
                    class="bc-bubble"
                  >
                    <div class="bcb-header">
                      <div class="bcb-avatar" :style="{'background': s.color}">{{ (rev.author||'U')[0].toUpperCase() }}</div>
                      <div class="bcb-header-meta">
                        <span class="bcb-author">{{ rev.author||'User' }}</span>
                        <span class="bcb-stars"><span v-for="i in 5" :key="i" class="bcb-star" :class="getStarClass(rev.rating||5,i)"></span></span>
                      </div>
                    </div>
                    <div class="bcb-text">{{ rev.body }}</div>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- ══════════════ SLIDE 2: PLAY STORE ══════════════ -->
      <div v-if="isSlideEnabled(2)" class="slide" :class="{sin: cur===2, sout: exitSlide===2}">
        <div class="slide-inner cluster-slide">
          <div class="ov-ambient">
            <div class="ov-amb-orb ov-amb-1" style="background:radial-gradient(circle,rgba(164,255,0,0.06),transparent 70%)"></div>
            <div class="ov-amb-orb ov-amb-2" style="background:radial-gradient(circle,rgba(255,255,255,0.05),transparent 70%)"></div>
          </div>

          <div class="bubble-grid" :data-active="andActiveCount">
            <template v-for="s in sentimentOrder" :key="'and-node-'+s.key">
              <div
                v-if="(andSentimentGroups[s.key] || []).length > 0"
                class="bc-cluster"
                :style="{'--sc': s.color}"
              >
                <div class="bc-sent-name">{{ s.label }}</div>
                <div class="bc-hub">
                  <div class="bc-hub-glow"></div>
                  <div class="bc-hub-ring"></div>
                  <EmotionFace :emotionKey="s.key" class="bc-emoji" />
                </div>
                <div class="bc-bubbles" :data-count="(andSentimentGroups[s.key]||[]).length">
                  <div
                    v-for="(rev, bIdx) in (andSentimentGroups[s.key]||[]).slice(0,5)"
                    :key="'and-b-'+s.key+bIdx"
                    class="bc-bubble"
                  >
                    <div class="bcb-header">
                      <div class="bcb-avatar" :style="{'background': s.color}">{{ (rev.author||'U')[0].toUpperCase() }}</div>
                      <div class="bcb-header-meta">
                        <span class="bcb-author">{{ rev.author||'User' }}</span>
                        <span class="bcb-stars"><span v-for="i in 5" :key="i" class="bcb-star" :class="getStarClass(rev.rating||5,i)"></span></span>
                      </div>
                    </div>
                    <div class="bcb-text">{{ rev.body }}</div>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- SLIDE 3: NEWS -->
      <div v-if="isSlideEnabled(3)" class="slide" :class="{sin: cur===3, sout: exitSlide===3}">
        <div class="slide-inner news-slide">
          <div class="news-left">
            <div class="nl-eyebrow">📰 Press Coverage</div>
            <div class="nl-big">IN THE<br><span class="nl-big-accent">HEAD</span><br>LINES</div>
            <div class="news-count-pill">
              <span class="ncp-num">{{ gnews.posts?.length || 0 }}</span>
              <span class="ncp-txt">articles this sprint</span>
            </div>
            <div class="ns-qr-wrap nl-qr-wrap" v-if="currentNews">
              <img :src="'https://api.qrserver.com/v1/create-qr-code/?size=300x300&format=svg&data='+encodeURIComponent(currentNews.resolved_url||currentNews.url)" class="ns-qr" alt="QR" />
              <span class="ns-qr-lbl">SCAN FOR FULL STORY</span>
            </div>
            <div class="news-deco-dots">
              <span></span><span></span><span></span>
              <span></span><span></span><span></span>
              <span></span><span></span><span></span>
            </div>
          </div>
          <div class="news-frame">
            <transition :name="newsTransDir" mode="out-in">
              <div v-if="currentNews" :key="newsIndex" class="ns-poster">
                <div v-if="currentNews.image" class="ns-hero">
                  <img :src="currentNews.image" class="ns-hero-img" alt="" @error="currentNews.image = ''" />
                  <div class="ns-hero-overlay"></div>
                </div>
                <div v-else class="ns-no-image"></div>
                <div class="ns-source-badge ns-source-banner">
                  <span class="ns-source">{{ currentNews.source }}</span>
                  <span class="ns-date">{{ currentNews.date }}</span>
                </div>
                <div class="ns-content">
                  <div class="ns-top">
                    <h1 class="ns-title">{{ currentNews.title }}</h1>
                  </div>
                  <div class="ns-footer">
                    <div class="ns-pagination">
                      <span v-for="(p,pi) in (gnews.posts||[])" :key="pi" class="ns-dot" :class="pi===newsIndex ? 'ns-dot-on' : ''"></span>
                    </div>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </div>

      <!-- ══════════════ SLIDE 4: X FEED ══════════════ -->
      <div v-if="isSlideEnabled(4)" class="slide" :class="{sin: cur===4, sout: exitSlide===4}">
        <div class="slide-inner xf-slide cluster-slide" :class="'xf-phase-'+xPhase">

          <!-- Left: post screenshot + dots — always visible -->
          <div class="xf-left-panel">
            <div class="xf-left-label">
              <div class="xf-left-eyebrow">LATEST POST</div>
              <div class="xf-left-handle">@Arattai</div>
              <div class="xf-left-date">{{ (twitter.recent_posts||[])[twitterIdx]?.date || '' }}</div>
            </div>
            <transition name="xf-pop" mode="out-in">
              <div class="xf-left-shot" :key="'left-'+twitterIdx">
                <img v-if="(twitter.recent_posts||[])[twitterIdx]?.screenshot_url && !xImageFallback"
                  :src="apiUrl((twitter.recent_posts||[])[twitterIdx].screenshot_url)"
                  class="xf-left-img" @error="xImageFallback=true" alt="tweet"/>
                <div v-else class="xf-left-text-block">
                  <div class="xf-left-text">{{ (twitter.recent_posts||[])[twitterIdx]?.body || '' }}</div>
                  
                  <!-- Fallback Live Preview if no screenshots/images -->
                  <div class="xf-fallback-preview">
                    <img :src="'https://image.thum.io/get/width/1200/noanimate/' + (twitter.recent_posts||[])[twitterIdx]?.url" 
                         class="xf-fallback-img" alt="live preview" />
                  </div>

                  <div v-if="((twitter.recent_posts||[])[twitterIdx]?.post_images||[]).length"
                    class="xf-post-images">
                    <img v-for="(imgUrl, imgIdx) in (twitter.recent_posts||[])[twitterIdx].post_images"
                      :key="'postimg-'+twitterIdx+'-'+imgIdx"
                      :src="apiUrl(imgUrl)"
                      class="xf-post-img"
                      alt="post image"
                      @error="$event.target.style.display='none'" />
                  </div>
                </div>
              </div>
            </transition>
            <div class="xf-dots">
              <span v-for="(p,pi) in (twitter.recent_posts||[])" :key="pi"
                class="xf-dot" :class="{active: pi===twitterIdx}" @click="twitterIdx=pi"></span>
            </div>
          </div>

          <!-- Right: sentiment cluster grid of comments -->
          <div class="xf-right-comments">
            <div class="xf-comments-header">
              <span class="xf-right-eyebrow">💬 COMMENTS</span>
              <span class="xf-right-count">{{ currentTwitterComments.length }} replies</span>
            </div>
            <div class="xf-comments-list">
              <div
                v-for="(comment, idx) in currentTwitterComments"
                :key="'xc-'+twitterIdx+'-'+idx"
                class="xf-comment-item"
              >
                <div class="xfc-avatar">{{ (comment.author||'U')[0].toUpperCase() }}</div>
                <div class="xfc-content">
                  <div class="xfc-author">{{ comment.author }}</div>
                  <div class="xfc-body">{{ comment.body }}</div>
                </div>
              </div>
              <div v-if="!currentTwitterComments.length" class="xf-no-comments">
                No comments yet
              </div>
            </div>
          </div>

        </div>
      </div>

    </div><!-- stage -->

    <!-- BOTTOM BAR -->
    <div class="bottom-bar">
      <div class="progress-rail"><div class="progress-fill" :style="{width:prog+'%'}"></div></div>
      <div class="bb-left" @click="loadData" style="cursor:pointer;" title="Refresh"></div>
      <div class="bb-center">
        <div v-for="s in slideDefs" :key="s.id" v-show="isSlideEnabled(s.id)" class="nav-pill nav-pill-sm" :class="{'pill-on': cur===s.id}" @click="go(s.id)">{{ s.name }}</div>
      </div>
      <div class="bb-right">
        <span class="bb-counter">{{ curDisplayIndex }} / {{ totalVisible }}</span>
      </div>
    </div>

    <!-- Bottom-right settings (UI flow controls only) -->
    <button class="slide-settings-btn" @click="showSlideSettings = !showSlideSettings" title="Slide Settings" aria-label="Slide Settings">
      ⚙
      <span v-if="!xSessionInfo.has_session" class="btn-status-dot"></span>
    </button>
    <div v-if="showSlideSettings" class="slide-settings-pop">
      <div class="ssp-head">Dashboard Flow</div>
      <div class="ssp-sub">Select slides to display</div>
      <label v-for="s in slideDefs" :key="'cfg-'+s.id" class="ssp-item" :class="{'ssp-item-locked': isLastEnabledSlide(s.id)}">
        <input
          type="checkbox"
          :checked="isSlideEnabled(s.id)"
          :disabled="isLastEnabledSlide(s.id)"
          @change="toggleSlide(s.id, $event.target.checked)" />
        <span>{{ s.name }}</span>
        <small v-if="isLastEnabledSlide(s.id)" class="ssp-lock">required</small>
      </label>

      
    </div>

    </div><!-- .app-shell -->
  </template>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import EmotionFace from './components/EmotionFace.vue'

const appReady    = ref(false)
const loadError   = ref(false)
const isFetching  = ref(false)
const lastUpdated = ref('--:--')
const data        = ref({})
const clock       = ref('')
const cur         = ref(0)
const exitSlide   = ref(-1)
const slideDefs   = [
  { id: 0, name: 'Overview' },
  { id: 1, name: 'App Store' },
  { id: 2, name: 'Play Store' },
  { id: 3, name: 'News' },
  { id: 4, name: 'X Feed' },
]
const total       = slideDefs.length
const prog        = ref(0)
const showSlideSettings = ref(false)
const slideEnabled = ref({ 0: true, 1: true, 2: true, 3: true, 4: true })
const SLIDE_CFG_KEY = 'dashboard_slide_enabled_v1'
const xSessionInfo = ref({ has_session: false, message: 'Checking...' })

const globalCycle = ref(0)
watch(cur, (n, oldV) => {
  if (n === 0 && oldV === 4) {
    globalCycle.value++
  }
})

const visibleSlideIds = computed(() => slideDefs.filter(s => !!slideEnabled.value[s.id]).map(s => s.id))
const totalVisible = computed(() => Math.max(1, visibleSlideIds.value.length))
const curDisplayIndex = computed(() => {
  const idx = visibleSlideIds.value.indexOf(cur.value)
  return idx >= 0 ? idx + 1 : 1
})

function isSlideEnabled(id) {
  return !!slideEnabled.value[id]
}

function isLastEnabledSlide(id) {
  return isSlideEnabled(id) && visibleSlideIds.value.length === 1
}

function nextEnabledSlide(fromId, step = 1) {
  const ids = visibleSlideIds.value
  if (!ids.length) return fromId
  const currentIdx = ids.indexOf(fromId)
  if (currentIdx === -1) return ids[0]
  const nextIdx = (currentIdx + step + ids.length) % ids.length
  return ids[nextIdx]
}

function persistSlideSettings() {
  try { localStorage.setItem(SLIDE_CFG_KEY, JSON.stringify(slideEnabled.value)) } catch (_) {}
}

function loadSlideSettings() {
  try {
    const raw = localStorage.getItem(SLIDE_CFG_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw)
    const merged = { ...slideEnabled.value }
    for (const s of slideDefs) {
      if (typeof parsed[s.id] === 'boolean') merged[s.id] = parsed[s.id]
    }
    if (!Object.values(merged).some(Boolean)) merged[0] = true
    slideEnabled.value = merged
  } catch (_) {}
}

function toggleSlide(id, enabled) {
  if (!enabled && isLastEnabledSlide(id)) return
  const next = { ...slideEnabled.value, [id]: enabled }
  if (!Object.values(next).some(Boolean)) return
  slideEnabled.value = next
  persistSlideSettings()
  if (!slideEnabled.value[cur.value]) cur.value = visibleSlideIds.value[0]
  scheduleAutoAdvance()
}

const getDuration = () => {
  if (cur.value === 1) {
    const all = visibleIosReviews.value
    if (!all.length) return 10000
    const totalReviewTime = all.reduce((sum, r) => sum + (r.timing || 5), 0)
    let usedSentimentCount = 0
    Object.keys(iosSentimentGroups.value).forEach(k => { if (iosSentimentGroups.value[k].length > 0) usedSentimentCount++ })
    return (totalReviewTime + (usedSentimentCount * 1.6)) * 1000
  }
  if (cur.value === 2) {
    const all = visibleAndReviews.value
    if (!all.length) return 10000
    const totalReviewTime = all.reduce((sum, r) => sum + (r.timing || 5), 0)
    let usedSentimentCount = 0
    Object.keys(andSentimentGroups.value).forEach(k => { if (andSentimentGroups.value[k].length > 0) usedSentimentCount++ })
    return (totalReviewTime + (usedSentimentCount * 1.6)) * 1000
  }
  if (cur.value === 3) return Math.max(12000, visibleNews.value.length * 9000)
  if (cur.value === 4) {
    const posts = twitter.value.recent_posts || []
    if (!posts.length) return 15000
    const totalTime = posts.reduce((sum, p) => {
      const comments = (p.comments || []).slice(0, 5)
      if (!comments.length) return sum + 9000
      return sum + comments.reduce((cSum, c) => cSum + ((c.timing || 3.5) * 1000), 0)
    }, 0)
    return Math.max(15000, totalTime)
  }
  return 10000
}

const sentimentOrder = [
  { key: 'neutral',    label: 'Neutral',    emoji: '😐', color: '#7888cc' },
  { key: 'happy',      label: 'Happy',      emoji: '😊', color: '#22a84a' },
  { key: 'ecstatic',   label: 'Ecstatic',   emoji: '🤩', color: '#d4a000' },
  { key: 'frustrated', label: 'Frustrated', emoji: '😤', color: '#e06020' },
  { key: 'angry',      label: 'Angry',      emoji: '😡', color: '#cc1050' },
]

function sentimentColor(key) { return sentimentOrder.find(s => s.key === key)?.color || '#1A1400' }

function getCarouselClass(ridx, activeIdx, total) {
  const diff = ridx - activeIdx
  if (diff === 0) return 'cc-active'
  if (diff === 1 || (activeIdx === total - 1 && ridx === 0)) return 'cc-next'
  if (diff === -1 || (activeIdx === 0 && ridx === total - 1)) return 'cc-prev'
  if (diff === 2) return 'cc-far-next'
  if (diff === -2) return 'cc-far-prev'
  return 'cc-hidden'
}
function getCarouselStyle(ridx, activeIdx, total, color) {
  const absDiff = Math.abs(ridx - activeIdx)
  if (absDiff === 0) return { '--cc-color': color, zIndex: 10 }
  if (absDiff === 1) return { '--cc-color': color, zIndex: 5 }
  if (absDiff === 2) return { '--cc-color': color, zIndex: 2 }
  return { '--cc-color': color, zIndex: 0 }
}
function getCommentClass(ridx, activeIdx, total) {
  const diff = ridx - activeIdx
  if (diff === 0) return 'xfc-active'
  if (diff === 1 || (activeIdx === total - 1 && ridx === 0)) return 'xfc-next'
  if (diff === -1 || (activeIdx === 0 && ridx === total - 1)) return 'xfc-prev'
  if (diff === 2) return 'xfc-far-next'
  if (diff === -2) return 'xfc-far-prev'
  return 'xfc-hidden'
}
function getCommentStyle(ridx, activeIdx, total) {
  const absDiff = Math.abs(ridx - activeIdx)
  if (absDiff === 0) return { zIndex: 10 }
  if (absDiff === 1) return { zIndex: 5 }
  if (absDiff === 2) return { zIndex: 2 }
  return { zIndex: 0 }
}

let iosRevTimeout = null
const iosSentimentIdx  = ref(0)
const iosRevIdxInGroup = ref(0)
const iosPhase         = ref('center')
const andSentimentIdx  = ref(0)
const andRevIdxInGroup = ref(0)
const andPhase         = ref('center')
const xPhase           = ref('center')
let andRevTimeout = null, iosPhaseTimeout = null, andPhaseTimeout = null, xPhaseTimeout = null

const iosCommCanvas = ref(null), andCommCanvas = ref(null)
const iosCeleCanvas = ref(null), andCeleCanvas = ref(null)

function runCelebrations(canvas) {
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  let w = canvas.width = window.innerWidth, h = canvas.height = window.innerHeight
  const colors = ['#f44336','#2196f3','#9c27b0','#ffeb3b','#4caf50','#00bcd4','#3f51b5','#e91e63']
  const particles = []
  for (let i = 0; i < 120; i++) {
    particles.push({ x: Math.random()*w, y: Math.random()*-h, r: Math.random()*4+4, d: Math.random()*120,
      color: colors[Math.floor(Math.random()*colors.length)], tilt: Math.floor(Math.random()*10)-10,
      tiltAngleInc: Math.random()*.07+.05, tiltAngle: 0, shape: ['rect','star','circle'][Math.floor(Math.random()*3)] })
  }
  function drawStar(x,y,r,p,m,color) {
    ctx.save();ctx.beginPath();ctx.translate(x,y);ctx.moveTo(0,0-r)
    for(let i=0;i<p;i++){ctx.rotate(Math.PI/p);ctx.lineTo(0,0-(r*m));ctx.rotate(Math.PI/p);ctx.lineTo(0,0-r)}
    ctx.fillStyle=color;ctx.fill();ctx.restore()
  }
  function draw() {
    if(canvas.offsetParent!==null){
      ctx.clearRect(0,0,w,h)
      particles.forEach(p=>{
        p.tiltAngle+=p.tiltAngleInc;p.y+=(Math.cos(p.tiltAngle)+3+p.r/2)/2;p.x+=Math.sin(p.tiltAngle);p.tilt=Math.sin(p.tiltAngle)*15
        if(p.shape==='rect'){ctx.beginPath();ctx.lineWidth=p.r;ctx.strokeStyle=p.color;ctx.moveTo(p.x+p.tilt+(p.r/2),p.y);ctx.lineTo(p.x+p.tilt,p.y+p.tilt+(p.r/2));ctx.stroke()}
        else if(p.shape==='star'){drawStar(p.x,p.y,p.r,5,.5,p.color)}
        else{ctx.beginPath();ctx.arc(p.x,p.y,p.r/2,0,Math.PI*2);ctx.fillStyle=p.color;ctx.fill()}
        if(p.x>w+5||p.x<-5||p.y>h){p.x=Math.random()*w;p.y=-20}
      })
    }
    requestAnimationFrame(draw)
  }
  window.addEventListener('resize',()=>{w=canvas.width=window.innerWidth;h=canvas.height=window.innerHeight})
  draw()
}

function runCommiserations(canvas) {
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  let w = canvas.width = window.innerWidth, h = canvas.height = window.innerHeight
  const drops = []
  for(let i=0;i<80;i++) drops.push({x:Math.random()*w,y:Math.random()*h,l:Math.random()*25+10,v:Math.random()*5+3,a:Math.random()*.4+.1})
  function draw(){
    if(canvas.offsetParent!==null){
      ctx.clearRect(0,0,w,h);ctx.strokeStyle='rgba(85,96,187,0.4)';ctx.lineWidth=1.5;ctx.lineCap='round'
      drops.forEach(d=>{ctx.beginPath();ctx.moveTo(d.x,d.y);ctx.lineTo(d.x,d.y+d.l);ctx.stroke();d.y+=d.v;if(d.y>h){d.y=-d.l;d.x=Math.random()*w}})
    }
    requestAnimationFrame(draw)
  }
  window.addEventListener('resize',()=>{w=canvas.width=window.innerWidth;h=canvas.height=window.innerHeight})
  draw()
}

function triggerIosPhase(){iosPhase.value='center';clearTimeout(iosPhaseTimeout);iosPhaseTimeout=setTimeout(()=>{iosPhase.value='split'},1600)}
function triggerAndPhase(){andPhase.value='center';clearTimeout(andPhaseTimeout);andPhaseTimeout=setTimeout(()=>{andPhase.value='split'},1600)}
function triggerXPhase(){xPhase.value='center';clearTimeout(xPhaseTimeout);xPhaseTimeout=setTimeout(()=>{xPhase.value='split'},1800)}

const newsIndex = ref(0), newsTransDir = ref('slide-next')
let newsLoopTimeout = null, slideTimer = null, progRaf = null, progStart = null, clockInt = null, dataInt = null

function tick(){clock.value=new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',second:'2-digit'})}

const ios     = computed(() => data.value.appstore    || {})
const android = computed(() => data.value.playstore   || {})
const gnews   = computed(() => data.value.google_news || {})
const twitter = computed(() => data.value.twitter     || { recent_posts: [] })
const allRevs = computed(() => [...(ios.value.reviews||[]),...(android.value.reviews||[])])
const totalSignals = computed(() => allRevs.value.length + (gnews.value.posts?.length || 0) + (twitter.value.recent_posts?.length || 0))
const API_BASE = import.meta.env.VITE_API_BASE || ''

const apiUrl = (p) => {
  if (!p) return ''
  if (p.startsWith('http')) return p
  return (p.startsWith('/') ? '' : '/') + p
}

const xFollowersText = computed(() => {
  const txt = (twitter.value.followers || '').toString().trim()
  if (txt) return txt
  const n = Number(twitter.value.followers_count || 0)
  if (!n) return '0'
  return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(n).toUpperCase()
})

const twitterIdx = ref(0), xCommentIdx = ref(0), xImageFallback = ref(false)
let twitterLoopTimeout = null, commentLoopTimeout = null

const currentTwitterComments = computed(() => {
  return ((twitter.value.recent_posts||[])[twitterIdx.value]?.comments) || []
})

watch(twitterIdx,()=>{xImageFallback.value=false;xCommentIdx.value=0})

function getEmotion(rev){
  const llmSentiment=(rev.sentiment||'').toLowerCase()
  const validKeys=['neutral','happy','ecstatic','frustrated','angry']
  if(validKeys.includes(llmSentiment))return llmSentiment
  const r=Number(rev.rating)||3
  if(r>=5)return 'ecstatic';if(r>=4)return 'happy';if(r===3)return 'neutral';if(r===2)return 'frustrated';return 'angry'
}

const visibleIosReviews = computed(() => {
  const revs = ios.value.reviews || []
  if (!revs.length) return []
  const round = globalCycle.value % Math.max(1, Math.ceil(revs.length / 5))
  const start = round * 5
  return revs.slice(start, start + 5)
})

const visibleAndReviews = computed(() => {
  const revs = android.value.reviews || []
  if (!revs.length) return []
  const round = globalCycle.value % Math.max(1, Math.ceil(revs.length / 5))
  const start = round * 5
  return revs.slice(start, start + 5)
})

const visibleNews = computed(() => {
  const posts = gnews.value.posts || []
  if (!posts.length) return []
  const round = globalCycle.value % Math.max(1, Math.ceil(posts.length / 5))
  const start = round * 5
  return posts.slice(start, start + 5)
})

const iosSentimentGroups=computed(()=>{
  const revs=visibleIosReviews.value;const groups={}
  sentimentOrder.forEach(s=>{groups[s.key]=[]});revs.forEach(r=>{const e=getEmotion(r);if(groups[e])groups[e].push(r)});return groups
})
const andSentimentGroups=computed(()=>{
  const revs=visibleAndReviews.value;const groups={}
  sentimentOrder.forEach(s=>{groups[s.key]=[]});revs.forEach(r=>{const e=getEmotion(r);if(groups[e])groups[e].push(r)});return groups
})
const iosActiveCount = computed(() => Object.values(iosSentimentGroups.value).filter(g => g.length > 0).length)
const andActiveCount = computed(() => Object.values(andSentimentGroups.value).filter(g => g.length > 0).length)
const getDynamicScale = (count) => {
  if (count <= 1) return 1.6;
  if (count === 2) return 1.4;
  if (count === 3) return 1.2;
  if (count === 4) return 1.05;
  return 0.95;
}
const currentIosSentiment=computed(()=>sentimentOrder[iosSentimentIdx.value])
const currentAndSentiment=computed(()=>sentimentOrder[andSentimentIdx.value])
const currentIosReview=computed(()=>{const g=iosSentimentGroups.value[currentIosSentiment.value.key]||[];return g[iosRevIdxInGroup.value]||null})
const currentAndReview=computed(()=>{const g=andSentimentGroups.value[currentAndSentiment.value.key]||[];return g[andRevIdxInGroup.value]||null})
const iosRevProgressPct=computed(()=>{const g=iosSentimentGroups.value[currentIosSentiment.value.key]||[];if(!g.length)return 0;return((iosRevIdxInGroup.value+1)/g.length)*100})
const andRevProgressPct=computed(()=>{const g=andSentimentGroups.value[currentAndSentiment.value.key]||[];if(!g.length)return 0;return((andRevIdxInGroup.value+1)/g.length)*100})

function advanceIosReview(){
  const g=iosSentimentGroups.value[currentIosSentiment.value.key]||[]
  if(iosRevIdxInGroup.value<g.length-1){iosRevIdxInGroup.value++}
  else{let nextIdx=(iosSentimentIdx.value+1)%sentimentOrder.length,looped=0;while(looped<sentimentOrder.length){const nextG=iosSentimentGroups.value[sentimentOrder[nextIdx].key]||[];if(nextG.length>0)break;nextIdx=(nextIdx+1)%sentimentOrder.length;looped++};iosSentimentIdx.value=nextIdx;iosRevIdxInGroup.value=0;triggerIosPhase()}
}
function scheduleIosReview(){clearTimeout(iosRevTimeout);if(cur.value!==1)return;const rev=currentIosReview.value;if(!rev)return;const seconds=rev.timing||5;const offset=(iosPhase.value==='center')?1.6:0;iosRevTimeout=setTimeout(()=>{advanceIosReview();scheduleIosReview()},(seconds+offset)*1000)}

function advanceAndReview(){
  const g=andSentimentGroups.value[currentAndSentiment.value.key]||[]
  if(andRevIdxInGroup.value<g.length-1){andRevIdxInGroup.value++}
  else{let nextIdx=(andSentimentIdx.value+1)%sentimentOrder.length,looped=0;while(looped<sentimentOrder.length){const nextG=andSentimentGroups.value[sentimentOrder[nextIdx].key]||[];if(nextG.length>0)break;nextIdx=(nextIdx+1)%sentimentOrder.length;looped++};andSentimentIdx.value=nextIdx;andRevIdxInGroup.value=0;triggerAndPhase()}
}
function scheduleAndReview(){clearTimeout(andRevTimeout);if(cur.value!==2)return;const rev=currentAndReview.value;if(!rev)return;const seconds=rev.timing||5;const offset=(andPhase.value==='center')?1.6:0;andRevTimeout=setTimeout(()=>{advanceAndReview();scheduleAndReview()},(seconds+offset)*1000)}

function jumpIosSentiment(i){iosSentimentIdx.value=i;iosRevIdxInGroup.value=0;triggerIosPhase()}
function jumpAndSentiment(i){andSentimentIdx.value=i;andRevIdxInGroup.value=0;triggerAndPhase()}

const currentNews=computed(()=>visibleNews.value[newsIndex.value]||null)

function startProg(){cancelAnimationFrame(progRaf);prog.value=0;progStart=performance.now();const d=getDuration();function step(now){prog.value=Math.min(100,((now-progStart)/d)*100);if(prog.value<100)progRaf=requestAnimationFrame(step)};progRaf=requestAnimationFrame(step)}

function scheduleAutoAdvance(){
  clearTimeout(slideTimer)
  const ids = visibleSlideIds.value
  if (!ids.length) return
  startProg()
  slideTimer = setTimeout(() => {
    const next = nextEnabledSlide(cur.value, 1)
    if (next === cur.value) {
      scheduleAutoAdvance()
      return
    }
    go(next)
  }, getDuration())
}

function go(n){
  if(!isSlideEnabled(n)) n = nextEnabledSlide(cur.value, 1)
  if(n===cur.value)return
  exitSlide.value=cur.value;setTimeout(()=>{exitSlide.value=-1},600)
  cur.value=n
  scheduleAutoAdvance()
}

watch(cur,(n)=>{
  clearTimeout(iosRevTimeout);clearTimeout(andRevTimeout);clearTimeout(twitterLoopTimeout);clearTimeout(commentLoopTimeout);clearTimeout(newsLoopTimeout)
  if(n===1){let first=0;for(let i=0;i<sentimentOrder.length;i++){if((iosSentimentGroups.value[sentimentOrder[i].key]||[]).length>0){first=i;break}};iosSentimentIdx.value=first;iosRevIdxInGroup.value=0;triggerIosPhase();scheduleIosReview()}
  if(n===2){let first=0;for(let i=0;i<sentimentOrder.length;i++){if((andSentimentGroups.value[sentimentOrder[i].key]||[]).length>0){first=i;break}};andSentimentIdx.value=first;andRevIdxInGroup.value=0;triggerAndPhase();scheduleAndReview()}
  if(n===3){newsIndex.value=0;scheduleNextNews()}
  if(n===4){twitterIdx.value=0;xCommentIdx.value=0;triggerXPhase();scheduleNextTwitter()}
})

function scheduleNextNews(){clearTimeout(newsLoopTimeout);const posts=visibleNews.value;if(!posts.length)return;newsLoopTimeout=setTimeout(()=>{newsTransDir.value='slide-next';newsIndex.value=(newsIndex.value+1)%posts.length;scheduleNextNews()},9000)}

function scheduleNextTwitter(){
  clearTimeout(twitterLoopTimeout);clearTimeout(commentLoopTimeout)
  const posts=twitter.value.recent_posts||[];if(!posts.length)return
  // Advance by post every ~12s (enough to read comments)
  twitterLoopTimeout=setTimeout(()=>{
    twitterIdx.value=(twitterIdx.value+1)%posts.length
    xCommentIdx.value=0;triggerXPhase();scheduleNextTwitter()
  },12000)
}

function getStarClass(rating,index){const diff=rating-(index-1);if(diff>=.75)return 'star-full';if(diff>=.25)return 'star-half';return 'star-empty'}
function fmtNum(n){return new Intl.NumberFormat('en-IN').format(n)}

function onKey(e){
  if(e.key==='ArrowRight'||e.key==='ArrowDown')go(nextEnabledSlide(cur.value,1))
  if(e.key==='ArrowLeft'||e.key==='ArrowUp')go(nextEnabledSlide(cur.value,-1))
}

async function loadData(){
  if(isFetching.value)return;isFetching.value=true
  try{
    let r=null
    try{r=await fetch(apiUrl(`/data.json?t=${Date.now()}`))}catch(e){}
    if(!r||!r.ok){try{r=await fetch(apiUrl(`/data?t=${Date.now()}`))}catch(e){throw new Error('unreachable')}}
    if(!r.ok)throw new Error('HTTP '+r.status)
    const json=await r.json()
    if(json){data.value=json;lastUpdated.value=new Date().toLocaleTimeString('en-IN',{hour12:false,hour:'2-digit',minute:'2-digit'});if(!appReady.value){appReady.value=true;scheduleAutoAdvance()}}
  }catch(err){if(!appReady.value)setTimeout(()=>{if(!appReady.value)appReady.value=true},2000)}
  finally{isFetching.value=false}
}

async function checkXSession() {
  try {
    const r = await fetch(apiUrl('/x-session/status'))
    if (r.ok) {
      xSessionInfo.value = await r.json()
    }
  } catch (e) {
    console.error('Failed to check X session:', e)
  }
}

function loginToX() {
  window.open(apiUrl('/x-session/login'), '_blank')
  // Periodically check if session becomes valid
  const interval = setInterval(async () => {
    await checkXSession()
    if (xSessionInfo.value.has_session) {
      clearInterval(interval)
    }
  }, 5000)
  // Stop checking after 4 mins
  setTimeout(() => clearInterval(interval), 240000)
}

function ensureLottiePlayerLoaded(){
  if(window.customElements && window.customElements.get('lottie-player')) return
  if(document.querySelector('script[data-lottie-player]')) return
  const s=document.createElement('script')
  s.src='https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js'
  s.defer=true
  s.setAttribute('data-lottie-player','1')
  document.head.appendChild(s)
}

onMounted(()=>{
  ensureLottiePlayerLoaded()
  loadSlideSettings()
  if(!isSlideEnabled(cur.value)) cur.value = visibleSlideIds.value[0]
  tick();clockInt=setInterval(tick,1000)
  document.addEventListener('keydown',onKey)
  loadData();dataInt=setInterval(loadData,60000)
  checkXSession();setInterval(checkXSession, 300000) // check every 5 min
  if(iosCommCanvas.value)runCommiserations(iosCommCanvas.value)
  if(andCommCanvas.value)runCommiserations(andCommCanvas.value)
  if(iosCeleCanvas.value)runCelebrations(iosCeleCanvas.value)
  if(andCeleCanvas.value)runCelebrations(andCeleCanvas.value)
  setTimeout(()=>{if(!appReady.value){appReady.value=true;scheduleAutoAdvance()}},4000)
})
onUnmounted(()=>{
  clearInterval(clockInt);clearInterval(dataInt)
  clearTimeout(iosRevTimeout);clearTimeout(andRevTimeout);clearTimeout(slideTimer);cancelAnimationFrame(progRaf)
  clearTimeout(newsLoopTimeout);clearTimeout(twitterLoopTimeout);clearTimeout(commentLoopTimeout)
  clearTimeout(iosPhaseTimeout);clearTimeout(andPhaseTimeout);clearTimeout(xPhaseTimeout)
  document.removeEventListener('keydown',onKey)
})
function getBubbleLayout(key, count, totalActive) {
  // kept for compatibility but no longer used
  return [];
}

function getCellStyle(color, activeCount) {
  // Each cell gets a subtle left border accent
  return { '--cell-accent': color };
}

function getHubStyle(activeCount) {
  // Hub size scales inversely with number of active sentiments
  // Optimised for 5 reviews each in a different sentiment (most common case)
  const sizes = { 1: '160px', 2: '130px', 3: '110px', 4: '88px', 5: '70px' };
  const sz = sizes[activeCount] || '70px';
  return { width: sz, height: sz, 'min-width': sz, 'flex-shrink': '0' };
}

function getReviewsStyle(activeCount, reviewCount) {
  // Always row: each review card sits side by side within its sentiment row
  return { 'flex-direction': 'row', 'flex-wrap': 'nowrap', 'align-items': 'stretch' };
}

function getCardScale(activeCount, reviewCount) {
  // Scale text proportionally — 5 sentiments × 1 card looks best at 1.0
  if (activeCount === 1) return reviewCount <= 2 ? 1.1 : 0.88;
  if (activeCount === 2) return reviewCount <= 2 ? 1.05 : 0.85;
  if (activeCount === 3) return reviewCount <= 2 ? 0.95 : 0.82;
  if (activeCount === 4) return reviewCount <= 1 ? 0.92 : 0.78;
  // 5 active sentiments: 1 card per row is the sweet spot
  return reviewCount <= 1 ? 1.0 : 0.72;
}
</script>

<style>
@import url('https://fonts.zohostatic.com/puvi/regular/font.css');
@import url('https://fonts.zohostatic.com/puvi/bold/font.css');
@import url('https://fonts.zohostatic.com/puvi/semibold/font.css');
@import url('https://fonts.zohostatic.com/puvi/medium/font.css');
@import url('https://fonts.zohostatic.com/puvi/extrabold/font.css');

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body{width:100%;height:100%;overflow:hidden;background:transparent;}

:root{
  --y-main:#f7d747;--y-deep:#e8c200;--y-soft:#fceea0;--y-pale:#fff9eb;--y-cream:#fffcf0;--y-warm:#fff3c0;
  --gx-main:#34a853; --gx-deep:#2d9147;
  --y-border:rgba(200,160,0,0.2);--y-shadow:rgba(160,120,0,0.14);
  --ink:#1A1400;--ink2:#3D3000;--ink3:#6B5800;--ink-light:rgba(26,20,0,0.45);
  --font-d:'Puvi','Segoe UI',sans-serif;--font-b:'Puvi','Segoe UI',sans-serif;
}

/* LOADING SCREEN - Beige hex background with container */
.loading-screen{
  position:fixed;inset:0;z-index:9999;
  background:#f5f1e8;
  display:flex;align-items:center;justify-content:center;overflow:hidden;
}
.loading-screen::before{
  content:'';position:absolute;inset:0;
  background-image:repeating-linear-gradient(0deg,transparent,transparent 50px,rgba(206,171,57,0.03) 50px,rgba(206,171,57,0.03) 51px),repeating-linear-gradient(60deg,transparent,transparent 50px,rgba(206,171,57,0.03) 50px,rgba(206,171,57,0.03) 51px),repeating-linear-gradient(120deg,transparent,transparent 50px,rgba(206,171,57,0.03) 50px,rgba(206,171,57,0.03) 51px);
  opacity:0.4;
}
.load-blob{position:absolute;border-radius:50%;filter:blur(80px);animation:ld-drift 5s ease-in-out infinite alternate;}
.load-blob-1{width:500px;height:500px;background:#e8c547;opacity:.15;top:-160px;left:-160px;}
.load-blob-2{width:400px;height:400px;background:#ceab39;opacity:.12;bottom:-100px;right:-100px;animation-delay:-2.5s;}
.load-blob-3{width:260px;height:260px;background:#f4e5b8;opacity:.2;top:40%;left:42%;animation-delay:-1.2s;}
@keyframes ld-drift{to{transform:translate(60px,40px) scale(1.15);}}
.load-content{
  position:relative;z-index:1;
  background:linear-gradient(160deg,rgba(255,255,255,0.95) 0%,rgba(255,250,235,0.92) 100%);
  border:2px solid rgba(206,171,57,0.2);
  border-radius:28px;
  padding:3rem 4rem;
  box-shadow:inset 0 2px 0 rgba(255,255,255,0.8),0 20px 60px rgba(160,120,0,0.12);
  backdrop-filter:blur(10px);
  display:flex;flex-direction:column;align-items:center;gap:1.5rem;
  min-width:420px;
}
.load-logo{height:90px;object-fit:contain;margin-bottom:8px;animation:logo-bob 2s ease-in-out infinite alternate;filter:drop-shadow(0 8px 24px rgba(200,160,0,0.3));}
@keyframes logo-bob{from{transform:translateY(0);}to{transform:translateY(-8px);}}
.load-bar{width:220px;height:3px;background:rgba(200,160,0,.15);border-radius:2px;overflow:hidden;margin-top:6px;}
.load-bar-fill{height:100%;width:0%;border-radius:2px;background:linear-gradient(90deg,var(--y-deep),var(--y-main),var(--y-soft));animation:lb-fill 2.4s ease forwards;box-shadow:0 0 8px rgba(200,160,0,.4);}
@keyframes lb-fill{to{width:100%;}}
.error-screen{position:fixed;inset:0;background:var(--y-pale);display:flex;align-items:center;justify-content:center;}
.error-inner{font-family:var(--font-b);font-size:14px;color:var(--ink3);padding:2rem;border:1.5px solid var(--y-border);border-radius:16px;background:var(--y-cream);}

/* SCENE BG */
.scene-bg{position:fixed;inset:0;z-index:0;overflow:hidden;background-color:#fff9eb;}
.bg-floor{position:absolute;inset:0;transition:background 1.2s ease;background:transparent;}
.orb{position:absolute;border-radius:50%;pointer-events:none;}
.o1{width:600px;height:600px;top:-220px;left:-180px;filter:blur(100px);background:radial-gradient(circle,rgba(255,255,255,.05),transparent);animation:orb-f1 18s ease-in-out infinite alternate;}
.o2{width:500px;height:500px;bottom:-150px;right:-140px;filter:blur(90px);background:radial-gradient(circle,rgba(255,255,255,.03),transparent);animation:orb-f2 14s ease-in-out infinite alternate;}
.o3{width:340px;height:340px;top:40%;right:10%;filter:blur(80px);background:radial-gradient(circle,rgba(255,255,255,.04),transparent);animation:orb-f3 21s ease-in-out infinite alternate;}
@keyframes orb-f1{from{transform:translate(0,0);}to{transform:translate(50px,35px) scale(1.08);}}
@keyframes orb-f2{from{transform:translate(0,0);}to{transform:translate(-40px,-25px) scale(1.06);}}
@keyframes orb-f3{from{transform:translate(0,0);}to{transform:translate(-25px,40px) scale(1.1);}}
.mesh-grid{position:absolute;inset:0;pointer-events:none;animation:grid-pan 80s linear infinite;}
@keyframes grid-pan{from{transform:translate(0,0);}to{transform:translate(40px,40px);}}

/* APP SHELL */
.app-shell{position:fixed;inset:0;z-index:1;display:flex;flex-direction:column;overflow:hidden;}
.topbar-logo{height:36px;width:auto;object-fit:contain;}

/* NAV */
.nav-pill{padding:7px 22px;border-radius:100px;font-family:var(--font-d);font-size:12px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--ink3);cursor:pointer;transition:all .2s;border:1.5px solid transparent;}
.nav-pill:hover{color:var(--ink2);border-color:rgba(200,160,0,.3);background:rgba(247,215,71,.12);}
.nav-pill-sm{padding:4px 16px;font-size:11px;}
.pill-on{background:var(--y-main)!important;color:var(--ink)!important;font-weight:800!important;border-color:var(--y-deep)!important;box-shadow:0 2px 10px rgba(200,160,0,.3);}

/* TOPBAR */
.topbar{position:relative;z-index:1000;display:flex;flex-direction:row;justify-content:space-between;align-items:center;height:80px;padding:0 2.5rem;background:transparent;flex-shrink:0;}
.tb-left{display:flex;align-items:center;}
.tb-right{display:flex;align-items:center;justify-content:flex-end;}
.tb-meta-group{display:flex;align-items:center;gap:20px;}
.tb-counter{border-radius:12px;padding:6px 14px;background:rgba(247,215,71,.15);border:1px solid rgba(247,215,71,.3);font-family:var(--font-d);font-weight:800;}

/* STAGE */
.stage{flex:1;position:relative;overflow:hidden;z-index:10;}
.slide{position:absolute;inset:0;opacity:0;pointer-events:none;transform:translateY(24px) scale(.97);transition:opacity .5s cubic-bezier(.22,1,.36,1),transform .5s cubic-bezier(.22,1,.36,1);}
.slide.sin{opacity:1;transform:translateY(0) scale(1);pointer-events:all;}
.slide.sout{opacity:0;transform:translateY(-20px) scale(1.03);transition:opacity .3s ease,transform .3s ease;}
.slide-inner{width:100%;height:100%;padding:0 2.5rem;display:flex;flex-direction:column;color:var(--ink);overflow:hidden;}

/* ════════════════════════════════════════════════════
   OVERVIEW — REDESIGNED  (two-column layout)
   ════════════════════════════════════════════════════ */

.overview-slide{
  flex-direction:row !important;
  padding:0 2rem 0 2rem !important;
  gap:2rem;
  align-items:stretch;
  position:relative;
  overflow:hidden;
}

/* ── Ambient layer ── */
.ov-ambient{position:absolute;inset:0;pointer-events:none;z-index:0;}
.ov-amb-orb{position:absolute;border-radius:50%;filter:blur(80px);}
.ov-amb-1{width:520px;height:520px;top:-180px;left:-120px;background:radial-gradient(circle,rgba(247,215,71,.18),transparent 70%);animation:amb-float1 16s ease-in-out infinite alternate;}
.ov-amb-2{width:400px;height:400px;bottom:-100px;right:30%;background:radial-gradient(circle,rgba(232,194,0,.12),transparent 70%);animation:amb-float2 12s ease-in-out infinite alternate;}
.ov-amb-3{width:300px;height:300px;top:30%;right:-60px;background:radial-gradient(circle,rgba(252,238,160,.2),transparent 70%);animation:amb-float3 18s ease-in-out infinite alternate;}
@keyframes amb-float1{from{transform:translate(0,0) scale(1);}to{transform:translate(40px,30px) scale(1.12);}}
@keyframes amb-float2{from{transform:translate(0,0) scale(1);}to{transform:translate(-30px,-20px) scale(1.08);}}
@keyframes amb-float3{from{transform:translate(0,0) scale(1);}to{transform:translate(-20px,35px) scale(1.1);}}
.ov-amb-grid{
  position:absolute;inset:0;
  background-image: radial-gradient(circle,rgba(200,160,0,.06) 1px, transparent 1px);
  background-size:38px 38px;
  animation:grid-drift 60s linear infinite;
}
@keyframes grid-drift{from{background-position:0 0;}to{background-position:38px 38px;}}

/* ── LEFT COLUMN ── */
.ov-left-col{
  flex-shrink:0;
  width:38%;
  display:flex;
  flex-direction:column;
  justify-content:center;
  gap:1.4rem;
  padding:1.2rem 0;
  position:relative;
  z-index:2;
}

/* Brand hero block */
.ov-brand-hero{display:flex;flex-direction:column;gap:.7rem;}

.ov-brand-eyebrow{
  display:flex;align-items:center;gap:8px;
  font-family:var(--font-b);font-size:10px;letter-spacing:.22em;text-transform:uppercase;
  color:var(--ink3);
}
.ov-pulse-dot{
  width:7px;height:7px;border-radius:50%;
  background:var(--y-deep);
  box-shadow:0 0 0 0 rgba(232,194,0,.5);
  animation:pulse-ring 1.8s cubic-bezier(.455,.03,.515,.955) infinite;
}
.ov-pd-right{animation-delay:.9s;}
@keyframes pulse-ring{
  0%{box-shadow:0 0 0 0 rgba(232,194,0,.5);}
  70%{box-shadow:0 0 0 8px rgba(232,194,0,0);}
  100%{box-shadow:0 0 0 0 rgba(232,194,0,0);}
}

.ov-brand-title{
  line-height:.88;
  filter:drop-shadow(0 6px 18px rgba(100,70,0,.15));
}
.ov-title-line1{
  font-family:var(--font-d);
  font-size:clamp(58px,7vw,100px);
  font-weight:900;color:var(--ink);
  letter-spacing:-.04em;
  animation:title-appear .8s cubic-bezier(.22,1,.36,1) both;
}
.ov-title-line2{
  font-family:var(--font-d);
  font-size:clamp(58px,7vw,100px);
  font-weight:900;color:var(--ink);
  letter-spacing:-.04em;
  display:flex;align-items:baseline;gap:.18em;
  animation:title-appear .8s .1s cubic-bezier(.22,1,.36,1) both;
}
@keyframes title-appear{from{opacity:0;transform:translateY(30px) skewX(-3deg);}to{opacity:1;transform:translateY(0) skewX(0deg);}}

.ov-title-outline-word{
  color:transparent;
  -webkit-text-stroke:2.5px var(--y-deep);
  animation:outline-shimmer 4s ease-in-out infinite alternate;
}
@keyframes outline-shimmer{
  0%{-webkit-text-stroke-color:var(--y-deep);filter:none;}
  50%{-webkit-text-stroke-color:#ffd000;filter:drop-shadow(0 0 14px rgba(247,215,71,.5));}
  100%{-webkit-text-stroke-color:#a07800;filter:none;}
}

.ov-brand-sub{
  font-family:var(--font-b);font-size:12px;font-weight:700;
  color:var(--ink3);letter-spacing:.14em;text-transform:uppercase;
  padding-left:2px;
  animation:title-appear .8s .2s cubic-bezier(.22,1,.36,1) both;
}

/* Signal hero */
.ov-signal-hero{
  display:flex;align-items:center;gap:1rem;
  background:linear-gradient(135deg,rgba(255,255,255,.85),rgba(255,248,200,.9));
  border:1.5px solid rgba(200,160,0,.25);
  border-radius:22px;
  padding:.9rem 1.1rem;
  box-shadow:0 8px 28px rgba(160,120,0,.1),inset 0 1px 0 rgba(255,255,255,.8);
  animation:card-rise .7s .3s cubic-bezier(.22,1,.36,1) both;
  position:relative;overflow:hidden;
}
.ov-signal-hero::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--y-deep),transparent);
  opacity:.6;
}
.ov-lottie-hero{width:80px;height:80px;flex-shrink:0;}
.ov-signal-text{display:flex;flex-direction:column;gap:4px;}
.ov-signal-num{
  font-family:var(--font-d);font-size:clamp(36px,4vw,54px);font-weight:900;
  color:var(--ink);line-height:1;letter-spacing:-.03em;
}
.ov-signal-label{
  font-family:var(--font-b);font-size:9px;font-weight:800;
  letter-spacing:.2em;text-transform:uppercase;color:var(--ink3);
}
.ov-signal-chips{display:flex;flex-wrap:wrap;gap:5px;margin-top:4px;}
.ov-chip{
  font-family:var(--font-b);font-size:9px;font-weight:700;
  border-radius:999px;padding:3px 9px;border:1px solid;
}
.ov-chip-rev{background:rgba(247,215,71,.2);border-color:rgba(200,160,0,.3);color:var(--ink2);}
.ov-chip-news{background:rgba(200,160,0,.12);border-color:rgba(200,160,0,.25);color:var(--ink2);}
.ov-chip-x{background:rgba(29,161,242,.08);border-color:rgba(29,161,242,.2);color:#1a5888;}

/* Live ticker */
.ov-ticker{
  display:flex;align-items:center;gap:0;
  background:var(--ink);border-radius:12px;
  overflow:hidden;height:34px;
  box-shadow:0 4px 14px rgba(0,0,0,.12);
  animation:card-rise .7s .5s cubic-bezier(.22,1,.36,1) both;
  flex-shrink:0;
}
.ov-ticker-label{
  flex-shrink:0;padding:0 12px;
  background:var(--y-deep);
  font-family:var(--font-d);font-size:9px;font-weight:900;
  letter-spacing:.18em;color:var(--ink);
  height:100%;display:flex;align-items:center;
  position:relative;
}
.ov-ticker-label::after{content:'';position:absolute;right:-8px;top:0;bottom:0;width:8px;background:linear-gradient(90deg,var(--y-deep),transparent);}
.ov-ticker-track{flex:1;overflow:hidden;height:100%;display:flex;align-items:center;}
.ov-ticker-inner{
  display:flex;align-items:center;gap:16px;
  white-space:nowrap;
  font-family:var(--font-b);font-size:10px;font-weight:600;color:rgba(255,255,255,.75);
  animation:ticker-scroll 25s linear infinite;
  padding-left:16px;
}
.ov-ticker-inner span{flex-shrink:0;}
.ov-tick-sep{color:var(--y-deep);font-size:6px;}
@keyframes ticker-scroll{from{transform:translateX(0);}to{transform:translateX(-50%);}}

/* ── RIGHT COLUMN ── */
.ov-right-col{
  flex:1;
  display:flex;flex-direction:column;
  gap:10px;
  padding:1.2rem 0;
  position:relative;z-index:2;
  min-width:0;
}

.ov-cards-row{display:flex;gap:10px;flex:1;min-height:0;}
.ov-row-platforms{flex:1.15;}
.ov-row-bottom{flex:1;}

/* ── Shared card base ── */
.ov-card{
  flex:1;border-radius:22px;
  position:relative;overflow:hidden;
  padding:1.1rem 1.3rem;
  background:linear-gradient(160deg,rgba(255,255,255,.92) 0%,rgba(255,246,200,.93) 100%);
  border:1.5px solid rgba(206,171,57,.22);
  box-shadow:inset 0 1.5px 0 rgba(255,255,255,.8),0 10px 28px rgba(160,120,0,.1);
  backdrop-filter:blur(8px);
  animation:card-rise .7s cubic-bezier(.22,1,.36,1) both;
  animation-delay:var(--d,0s);
  transition:transform .3s cubic-bezier(.22,1,.36,1),box-shadow .3s ease;
}
.ov-card:hover{transform:translateY(-6px) scale(1.01);box-shadow:0 20px 50px rgba(160,120,0,.16),inset 0 1.5px 0 rgba(255,255,255,.8);}
@keyframes card-rise{from{opacity:0;transform:translateY(40px) scale(.94);}to{opacity:1;transform:translateY(0) scale(1);}}

/* Shimmer sweep */
.ov-card-shimmer{
  position:absolute;inset:0;z-index:0;pointer-events:none;
  background:linear-gradient(105deg,transparent 40%,rgba(255,255,255,.55) 50%,transparent 60%);
  background-size:200% 100%;
  animation:shimmer-sweep 4s ease-in-out infinite;
}
@keyframes shimmer-sweep{0%,100%{background-position:-200% 0;}50%{background-position:200% 0;}}

/* Card internal top bar */
.ov-card-head{
  display:flex;align-items:center;justify-content:space-between;
  margin-bottom:.7rem;position:relative;z-index:1;
}
.ov-card-platform{display:flex;align-items:center;gap:9px;}
.ov-plat-icon{width:36px;height:36px;object-fit:contain;filter:drop-shadow(0 3px 8px rgba(0,0,0,.1));}
.ov-plat-android{width:28px;height:36px;}
.ov-plat-name{font-family:var(--font-d);font-size:14px;font-weight:800;color:var(--ink);line-height:1.1;}
.ov-plat-sub{font-family:var(--font-b);font-size:10px;font-weight:700;color:var(--ink3);letter-spacing:.06em;}

.ov-card-badge{
  font-family:var(--font-d);font-size:7.5px;font-weight:900;
  letter-spacing:.12em;text-transform:uppercase;
  border-radius:999px;padding:4px 9px;
  border:1px solid;
}
.ov-badge-ios{background:rgba(0,100,220,.07);border-color:rgba(0,100,220,.18);color:rgba(0,80,180,.7);}
.ov-badge-and{background:rgba(30,140,50,.07);border-color:rgba(30,140,50,.18);color:rgba(20,110,40,.7);}

/* Rating block */
.ov-rating-block{
  display:flex;align-items:center;gap:1rem;
  position:relative;z-index:1;
  flex:1;
}
.ov-ring-wrap{position:relative;width:90px;height:90px;flex-shrink:0;}
.ov-ring-svg{width:100%;height:100%;display:block;filter:drop-shadow(0 0 10px rgba(232,194,0,.3));}
.ov-ring-center{
  position:absolute;inset:0;display:flex;flex-direction:column;
  align-items:center;justify-content:center;
}
.ov-ring-score{font-family:var(--font-d);font-size:24px;font-weight:900;color:var(--ink);line-height:1;}
.ov-ring-label{font-family:var(--font-b);font-size:9px;font-weight:700;color:var(--ink3);}
.ov-rating-meta{display:flex;flex-direction:column;gap:3px;}
.ov-rating-stars{display:flex;gap:2px;margin-bottom:2px;}
.ov-star{
  display:inline-block;width:12px;height:12px;
  clip-path:polygon(50% 0%,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%);
  background:rgba(0,0,0,.1);
}
.ov-star.star-full{background:var(--y-deep);}
.ov-star.star-half{background:linear-gradient(90deg,var(--y-deep) 50%,rgba(0,0,0,.1) 50%);}
.ov-rating-count{font-family:var(--font-d);font-size:clamp(24px,2.5vw,34px);font-weight:900;color:var(--ink);line-height:1;letter-spacing:-.02em;}
.ov-rating-unit{font-family:var(--font-b);font-size:10px;font-weight:700;color:var(--ink3);letter-spacing:.05em;}

/* Card footer accent bar */
.ov-card-footer-bar{
  position:absolute;bottom:0;left:0;right:0;height:3px;
  background:rgba(200,160,0,.1);overflow:hidden;
}
.ov-footer-fill{
  height:100%;
  background:linear-gradient(90deg,var(--y-deep),var(--y-main));
  border-radius:0 2px 0 0;
  animation:bar-fill-in 1.4s cubic-bezier(.22,1,.36,1) both;
}
@keyframes bar-fill-in{from{width:0!important;}to{/* width set inline */}}

/* ── Social Buzz card ── */
.ov-card-buzz{display:flex;flex-direction:column;gap:.6rem;}
.ov-buzz-top{display:flex;align-items:center;justify-content:space-between;position:relative;z-index:1;}
.ov-buzz-title-row{display:flex;align-items:center;gap:6px;}
.ov-lottie-buzz{width:38px;height:38px;}
.ov-buzz-heading{font-family:var(--font-d);font-size:14px;font-weight:800;color:var(--ink);}
.ov-buzz-tag-live{
  display:flex;align-items:center;gap:5px;
  font-family:var(--font-b);font-size:8px;font-weight:900;
  letter-spacing:.18em;color:var(--ink3);
  background:rgba(200,160,0,.1);border:1px solid rgba(200,160,0,.22);
  border-radius:999px;padding:4px 9px;
}
.ov-live-blink{
  width:6px;height:6px;border-radius:50%;
  background:#e8c200;
  animation:live-blink .9s ease-in-out infinite alternate;
}
@keyframes live-blink{from{opacity:1;box-shadow:0 0 5px #e8c200;}to{opacity:.3;box-shadow:none;}}

.ov-buzz-metrics{
  display:flex;align-items:center;
  gap:0;flex:1;
  position:relative;z-index:1;
}
.ov-buzz-metric{flex:1;display:flex;align-items:center;gap:10px;padding:0 .5rem;}
.ov-buzz-divider-v{width:1px;height:50px;background:rgba(200,160,0,.2);flex-shrink:0;}
.ov-buzz-icon-wrap{
  width:36px;height:36px;border-radius:12px;
  display:flex;align-items:center;justify-content:center;
  font-size:16px;flex-shrink:0;
  border:1px solid rgba(200,160,0,.2);
}
.ov-bi-news{background:rgba(247,215,71,.2);}
.ov-bi-x{background:rgba(0,0,0,.06);}
.ov-bi-chat{background:rgba(200,160,0,.12);}
.ov-buzz-metric-body{display:flex;flex-direction:column;gap:1px;}
.ov-buzz-num{font-family:var(--font-d);font-size:clamp(22px,2.8vw,36px);font-weight:900;color:var(--ink);line-height:1;}
.ov-buzz-desc{font-family:var(--font-d);font-size:11px;font-weight:800;color:var(--ink2);}
.ov-buzz-sprint{font-family:var(--font-b);font-size:8px;color:var(--ink3);}

/* Audio waveform */
.ov-waveform{
  display:flex;align-items:flex-end;gap:3px;
  height:28px;padding-top:2px;
  position:relative;z-index:1;
}
.ov-wave-bar{
  flex:1;max-width:7px;border-radius:2px 2px 0 0;
  background:linear-gradient(180deg,var(--y-deep),rgba(232,194,0,.3));
  transform-origin:bottom;
  animation:wave-dance calc(0.6s + var(--bi) * 0.07s) ease-in-out infinite alternate;
  animation-delay:calc(var(--bi) * 0.06s);
  min-height:4px;
}
@keyframes wave-dance{
  from{height:4px;opacity:.4;}
  to{height:calc(8px + var(--bi) * 1.1px);opacity:.9;}
}

/* ── Community card ── */
.ov-card-community{
  display:flex;flex-direction:column;
  background:linear-gradient(160deg,#fffbe0 0%,#fff3a0 55%,#ffe870 100%);
  border-color:rgba(210,170,30,.35);
  box-shadow:0 14px 40px rgba(160,120,0,.18),inset 0 1.5px 0 rgba(255,255,255,.75);
  overflow:hidden;
  position:relative;
}
.ov-community-tag{
  position:absolute;top:10px;right:12px;z-index:5;
  font-family:var(--font-d);font-size:7.5px;font-weight:900;
  letter-spacing:.12em;text-transform:uppercase;
  color:rgba(100,70,0,.6);
  background:rgba(255,255,255,.4);border:1px solid rgba(200,160,0,.25);
  border-radius:999px;padding:3px 8px;
}
.ov-community-lottie-wrap{
  flex:1;display:flex;align-items:center;justify-content:center;
  position:relative;z-index:2;
  min-height:0;
}
.ov-lottie-community{width:110px;height:110px;}
.ov-community-footer{
  display:flex;flex-direction:column;gap:2px;
  position:relative;z-index:2;
}
.ov-community-label{font-family:var(--font-d);font-size:clamp(14px,1.6vw,20px);font-weight:800;color:rgba(26,20,0,.88);}
.ov-community-sub{font-family:var(--font-b);font-size:9px;font-weight:700;color:rgba(60,40,0,.55);letter-spacing:.08em;text-transform:uppercase;}
.ov-community-num{font-family:var(--font-d);font-size:clamp(28px,3.2vw,42px);font-weight:900;color:var(--ink);line-height:1;margin-top:2px;}
.ov-community-num-label{font-size:.38em;font-weight:700;color:var(--ink3);vertical-align:middle;margin-left:4px;}

/* Orbiting dots */
.ov-orbit{position:absolute;inset:0;pointer-events:none;z-index:1;}
.ov-orbit-ring{
  position:absolute;
  top:50%;left:50%;
  transform-origin:0 0;
  border-radius:50%;
}
.ov-orbit-1{
  width:120px;height:120px;
  margin-top:-60px;margin-left:-60px;
  animation:orbit-spin 8s linear infinite;
  border:1px dashed rgba(200,160,0,.2);
}
.ov-orbit-2{
  width:170px;height:170px;
  margin-top:-85px;margin-left:-85px;
  animation:orbit-spin 14s linear infinite reverse;
  border:1px dashed rgba(200,160,0,.15);
}
.ov-orbit-dot{
  position:absolute;top:-5px;left:50%;
  width:9px;height:9px;border-radius:50%;
  background:var(--y-deep);
  box-shadow:0 0 8px rgba(232,194,0,.6);
  transform:translateX(-50%);
  animation:orbit-dot-pulse 2s ease-in-out infinite alternate;
}
.ov-orbit-dot-2{
  background:rgba(232,194,0,.6);
  box-shadow:0 0 6px rgba(232,194,0,.4);
  width:6px;height:6px;top:-3px;
}
@keyframes orbit-spin{from{transform:rotate(0deg);}to{transform:rotate(360deg);}}
@keyframes orbit-dot-pulse{from{opacity:.6;transform:translateX(-50%) scale(.8);}to{opacity:1;transform:translateX(-50%) scale(1.2);}}

/* ════════════════════════════════════════════
   (all other slides unchanged below)
   ════════════════════════════════════════════ */

/* SENTIMENT SLIDE */
.sentiment-slide{flex:1;min-height:0;display:flex;flex-direction:column;gap:12px;padding:1.2rem 0 0.8rem;position:relative;overflow:hidden;}
.sentiment-slide::before{content:'';position:absolute;width:380px;height:380px;top:-80px;right:-100px;border-radius:50%;pointer-events:none;z-index:0;background:radial-gradient(circle,rgba(247,215,71,.15) 0%,transparent 70%);animation:blob-drift 14s ease-in-out infinite alternate;}
@keyframes blob-drift{from{transform:translate(0,0) scale(1);}to{transform:translate(30px,-20px) scale(1.1);}}
.ss-platform-badge{display:flex;align-items:center;gap:12px;padding:10px 20px;border-radius:60px;border:1.5px solid rgba(200,160,0,.22);background:rgba(247,215,71,.1);box-shadow:0 4px 14px rgba(160,120,0,.08);}
.ios-badge{border-color:rgba(0,100,220,.2);background:rgba(0,100,220,.05);}
.and-badge{border-color:rgba(30,140,50,.2);background:rgba(30,140,50,.05);}
.ss-badge-img-sm{width:24px;height:24px;object-fit:contain;}
.ss-rating-sm{font-weight:800;margin-left:6px;color:var(--y-deep);}
.badge-top{padding:6px 16px!important;}
.ss-badge-name{font-family:var(--font-d);font-size:15px;font-weight:700;color:var(--ink);}
.ss-slide-counter{display:flex;align-items:baseline;gap:4px;background:var(--y-main);border-radius:14px;padding:6px 16px;box-shadow:0 4px 12px rgba(200,160,0,.3);}
.ss-sc-cur{font-family:var(--font-d);font-size:22px;font-weight:800;color:var(--ink);line-height:1;}
.ss-sc-sep{font-family:var(--font-b);font-size:14px;color:var(--ink3);}
.ss-sc-tot{font-family:var(--font-b);font-size:14px;font-weight:600;color:var(--ink2);}
.ss-scene{flex:1;min-height:0;position:relative;overflow:hidden;display:grid;grid-template-columns:300px 1fr;grid-template-rows:1fr;}
.ss-wm-text{position:absolute;inset:0;z-index:0;pointer-events:none;user-select:none;display:flex;align-items:center;justify-content:center;font-family:var(--font-d);font-size:clamp(100px,16vw,210px);font-weight:800;letter-spacing:-.04em;white-space:nowrap;overflow:hidden;color:rgba(247,215,71,.12);transition:opacity .6s ease;}
.ss-phase-split .ss-wm-text{opacity:.04;}
.ss-face-stage{position:absolute;inset:0;z-index:5;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;opacity:1;transform:translateX(0) scale(1);transition:opacity .55s cubic-bezier(.4,0,.2,1),transform .65s cubic-bezier(.16,1,.3,1);}
.ss-phase-split .ss-face-stage{opacity:0;transform:translateX(-60px) scale(.85);pointer-events:none;}
.sf-ring{position:absolute;border-radius:50%;border:1.5px solid rgba(247,215,71,.5);pointer-events:none;animation:ring-expand 3s ease-out infinite;}
.sf-ring-1{width:220px;height:220px;animation-delay:0s;}
.sf-ring-2{width:300px;height:300px;animation-delay:1s;}
.sf-ring-3{width:380px;height:380px;animation-delay:2s;}
@keyframes ring-expand{0%{opacity:.55;transform:scale(.7);}100%{opacity:0;transform:scale(1.3);}}
.sf-glow{position:absolute;width:340px;height:340px;border-radius:50%;filter:blur(80px);top:50%;left:50%;transform:translate(-50%,-50%);animation:sf-pulse 3s ease-in-out infinite alternate;transition:background .6s;pointer-events:none;}
@keyframes sf-pulse{from{opacity:.22;transform:translate(-50%,-50%) scale(1);}to{opacity:.45;transform:translate(-50%,-50%) scale(1.2);}}
.sf-neutral .sf-glow{background:radial-gradient(circle,rgba(85,96,187,.8),transparent);}
.sf-happy .sf-glow{background:radial-gradient(circle,rgba(26,144,64,.8),transparent);}
.sf-ecstatic .sf-glow{background:radial-gradient(circle,rgba(200,144,0,.9),rgba(247,215,71,.4));}
.sf-frustrated .sf-glow{background:radial-gradient(circle,rgba(200,80,32,.8),transparent);}
.sf-angry .sf-glow{background:radial-gradient(circle,rgba(187,8,64,.8),transparent);}
.ss-hero-face{width:180px!important;height:180px!important;position:relative;z-index:2;filter:drop-shadow(0 12px 40px rgba(0,0,0,.35));animation:face-pop .6s cubic-bezier(.34,1.56,.64,1) both;}
@keyframes face-pop{from{opacity:0;transform:scale(.5) rotate(-12deg);}to{opacity:1;transform:scale(1) rotate(0deg);}}
.sf-label-wrap{display:flex;flex-direction:column;align-items:center;gap:6px;position:relative;z-index:2;animation:label-rise .5s .15s cubic-bezier(.22,1,.36,1) both;}
@keyframes label-rise{from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:translateY(0);}}
.sf-name{font-family:var(--font-d);font-size:clamp(32px,4vw,56px);font-weight:800;line-height:1;letter-spacing:-.02em;}
.sf-neutral .sf-name{color:#3344aa;}.sf-happy .sf-name{color:#0d7a32;}.sf-ecstatic .sf-name{color:#8a6000;}.sf-frustrated .sf-name{color:#a03a10;}.sf-angry .sf-name{color:#960030;}
.sf-count{font-family:var(--font-b);font-size:13px;color:var(--ink3);letter-spacing:.12em;text-transform:uppercase;background:rgba(200,160,0,.12);border:1px solid var(--y-border);border-radius:20px;padding:5px 16px;}
.ss-left-panel{grid-column:1;grid-row:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:1.5rem 1.2rem;position:relative;z-index:6;border-right:2px solid rgba(200,160,0,.18);opacity:0;transform:translateX(-80px);transition:opacity .55s cubic-bezier(.4,0,.2,1),transform .65s cubic-bezier(.16,1,.3,1);pointer-events:none;}
.ss-phase-split .ss-left-panel{opacity:1;transform:translateX(0);pointer-events:all;}
.slp-glow{position:absolute;width:260px;height:260px;border-radius:50%;filter:blur(70px);top:50%;left:50%;transform:translate(-50%,-50%);opacity:.2;pointer-events:none;animation:sf-pulse 4s ease-in-out infinite alternate;}
.sf-neutral{--sent-color:#5560bb;}.sf-happy{--sent-color:#1a9040;}.sf-ecstatic{--sent-color:#c89000;}.sf-frustrated{--sent-color:#c85020;}.sf-angry{--sent-color:#bb0840;}.sf-twitter{--sent-color:#1DA1F2;}
.sf-neutral .slp-glow{background:radial-gradient(circle,rgba(85,96,187,.9),transparent);}
.sf-happy .slp-glow{background:radial-gradient(circle,rgba(26,144,64,.9),transparent);}
.sf-ecstatic .slp-glow{background:radial-gradient(circle,rgba(200,144,0,.9),transparent);}
.sf-frustrated .slp-glow{background:radial-gradient(circle,rgba(200,80,32,.9),transparent);}
.sf-angry .slp-glow{background:radial-gradient(circle,rgba(187,8,64,.9),transparent);}
.sf-twitter .slp-glow{background:radial-gradient(circle,rgba(29,161,242,.6),transparent);}
.ss-panel-face,.ss-panel-logo{width:140px!important;height:140px!important;position:relative;z-index:2;filter:drop-shadow(0 8px 24px rgba(0,0,0,.15));flex-shrink:0;margin-top:1rem;object-fit:contain;}
.slp-as{font-size:.6em;vertical-align:middle;opacity:.7;margin-left:2px;}
.slp-title{font-family:var(--font-d);font-size:clamp(32px,4.5vw,56px);font-weight:900;line-height:.9;letter-spacing:-.04em;color:#1A1400;text-align:center;position:relative;z-index:2;text-transform:uppercase;}
.slp-accent{display:block;color:var(--ink);}
.slp-badge{display:flex;flex-direction:column;align-items:center;gap:2px;background:transparent;border:none;padding:0;position:relative;z-index:2;margin-top:1.2rem;}
.slp-sent-name{font-family:var(--font-d);font-size:32px;font-weight:900;color:transparent;-webkit-text-stroke:2px var(--sent-color,#f7d747);text-transform:uppercase;line-height:1.1;letter-spacing:.02em;}
.slp-rev-count{font-family:var(--font-b);font-size:12px;color:var(--ink);letter-spacing:.15em;text-transform:uppercase;font-weight:800;opacity:1;margin-top:2px;}
.ss-progress-dots{display:flex;gap:6px;position:relative;z-index:2;justify-content:center;}
.ss-sdot{width:7px;height:7px;border-radius:50%;background:rgba(0,0,0,.12);transition:all .35s cubic-bezier(.34,1.56,.64,1);}
.sdot-on{background:var(--y-deep)!important;width:22px!important;border-radius:4px!important;box-shadow:0 0 6px rgba(200,160,0,.45);}
.ss-carousel-panel{grid-column:2;grid-row:1;display:flex;flex-direction:column;height:100%;min-height:0;padding:1rem 1.5rem 1rem 0;opacity:0;transform:translateX(60px);transition:opacity .55s .15s cubic-bezier(.4,0,.2,1),transform .65s .15s cubic-bezier(.16,1,.3,1);pointer-events:none;}
.ss-phase-split .ss-carousel-panel{opacity:1;transform:translateX(0);pointer-events:all;}

/* 3D CAROUSEL */
.carousel-viewport{flex:1;min-height:0;position:relative;perspective:1400px;perspective-origin:50% 50%;overflow:visible;}
.carousel-track{position:absolute;inset:0;transform-style:preserve-3d;}
.carousel-card{position:absolute;top:50%;left:50%;height:500px;width:min(90%,900px);transform:translate(-50%,-50%);border-radius:24px;background:#ffffff;border:1.5px solid rgba(0,0,0,.07);padding:2.2rem 2.8rem;display:flex;flex-direction:column;gap:1.1rem;overflow:hidden;transition:transform .65s cubic-bezier(.16,1,.3,1),opacity .5s cubic-bezier(.16,1,.3,1),filter .5s ease,box-shadow .5s ease;will-change:transform,opacity;}
.cc-active{transform:translate(-50%,-50%) translateZ(0px) scale(1);opacity:1;filter:none;box-shadow:0 2px 0 rgba(255,255,255,.9) inset,0 28px 70px rgba(0,0,0,.13),0 6px 20px rgba(0,0,0,.07);z-index:10;border-color:rgba(0,0,0,.06);}
.cc-next{transform:translate(-20%,-50%) translateZ(-220px) rotateY(-22deg) scale(0.84);opacity:0.55;filter:brightness(0.82);z-index:5;}
.cc-prev{transform:translate(-80%,-50%) translateZ(-220px) rotateY(22deg) scale(0.84);opacity:0.55;filter:brightness(0.82);z-index:5;}
.cc-far-next{transform:translate(0%,-50%) translateZ(-420px) rotateY(-35deg) scale(0.65);opacity:0.25;filter:brightness(0.7);z-index:2;}
.cc-far-prev{transform:translate(-100%,-50%) translateZ(-420px) rotateY(35deg) scale(0.65);opacity:0.25;filter:brightness(0.7);z-index:2;}
.cc-hidden{opacity:0;pointer-events:none;z-index:0;transform:translate(-50%,-50%) translateZ(-700px) scale(0.3);}
.cc-deco-blob{position:absolute;width:110px;height:110px;border-radius:50%;top:-40px;right:-30px;opacity:0.09;pointer-events:none;}
.cc-author-row{display:flex;align-items:center;gap:12px;flex-shrink:0;padding-bottom:.7rem;border-bottom:1.5px solid rgba(200,160,0,.14);}
.cc-avatar{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:var(--font-d);font-size:18px;font-weight:800;flex-shrink:0;border:2px solid rgba(200,160,0,.18);}
.cc-meta{flex:1;display:flex;flex-direction:column;gap:4px;}
.cc-author{font-family:var(--font-d);font-size:18px;font-weight:700;color:var(--ink);line-height:1.2;}
.cc-stars{display:flex;align-items:center;gap:2px;}
.cc-star{display:inline-block;width:12px;height:12px;background:rgba(0,0,0,.1);clip-path:polygon(50% 0%,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%);flex-shrink:0;}
.cc-star.star-full{background:var(--y-deep);}
.cc-star.star-half{background:linear-gradient(90deg,var(--y-deep) 50%,rgba(0,0,0,.1) 50%);}
.cc-date{margin-left:6px;font-family:var(--font-b);font-size:11px;color:var(--ink3);}
.cc-quote{flex:1;display:flex;gap:8px;align-items:flex-start;min-height:0;overflow:hidden;}
.cc-qmark{font-family:Georgia,serif;font-size:clamp(52px,5.5vw,80px);line-height:.6;font-weight:900;flex-shrink:0;margin-top:2px;opacity:.45;}
.cc-body{font-family:var(--font-b);font-size:clamp(15px,1.8vw,22px);line-height:1.7;color:var(--ink);font-weight:500;flex:1;overflow:hidden;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:10;line-clamp:10;align-self:center;text-align:center;}
.cc-footer{display:flex;align-items:center;gap:10px;flex-shrink:0;padding-top:.6rem;border-top:1px solid rgba(0,0,0,.06);}
.cc-timing-bar{flex:1;height:3px;background:rgba(0,0,0,.08);border-radius:2px;overflow:hidden;}
.cc-timing-fill{height:100%;border-radius:2px;transition:width .7s cubic-bezier(.4,0,.2,1);opacity:.7;}

/* SENTIMENT TABS */
.ss-group-tabs{display:flex;gap:10px;flex-shrink:0;padding:4px 0;justify-content:center;position:relative;z-index:2;}
.ss-group-tab{width:36px;height:36px;border-radius:50%;border:2px solid rgba(200,160,0,.25);background:rgba(247,215,71,.1);cursor:pointer;transition:all .2s;display:flex;align-items:center;justify-content:center;}
.ss-group-tab:hover{background:rgba(247,215,71,.28);border-color:rgba(200,160,0,.5);transform:scale(1.1);}
.ss-tab-inner{font-size:18px;line-height:1;pointer-events:none;}
.tab-neutral.tab-on{background:#5560bb;border-color:#5560bb;box-shadow:0 0 10px rgba(85,96,187,.4);}
.tab-happy.tab-on{background:#1a9040;border-color:#1a9040;box-shadow:0 0 10px rgba(26,144,64,.4);}
.tab-ecstatic.tab-on{background:var(--y-deep);border-color:var(--y-deep);box-shadow:0 0 10px rgba(200,160,0,.5);}
.tab-frustrated.tab-on{background:#c85020;border-color:#c85020;box-shadow:0 0 10px rgba(200,80,32,.4);}
.tab-angry.tab-on{background:#bb0840;border-color:#bb0840;box-shadow:0 0 10px rgba(187,8,64,.4);}

/* CANVAS */
.commiseration-canvas,.celebration-canvas{position:fixed;inset:0;z-index:400;pointer-events:none;width:100vw;height:100vh;}

/* NEWS SLIDE */
.news-slide{flex-direction:row;gap:3.5rem;align-items:center;padding:0 3vw;height:100%;}
.news-left{width:210px;flex-shrink:0;}
.nl-eyebrow{font-family:var(--font-b);font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--ink3);margin-bottom:8px;}
.nl-big{font-family:var(--font-d);font-size:clamp(44px,5.5vw,72px);font-weight:800;color:var(--ink);line-height:.88;letter-spacing:-.04em;margin-bottom:2rem;}
.nl-big-accent{color:transparent;-webkit-text-stroke:2.5px var(--y-deep);}
.news-count-pill{display:inline-flex;align-items:center;gap:8px;background:var(--y-main);border-radius:100px;padding:8px 20px;box-shadow:0 6px 20px rgba(200,160,0,.35);border:1.5px solid var(--y-deep);}
.ncp-num{font-family:var(--font-d);font-size:24px;font-weight:800;color:var(--ink);}
.ncp-txt{font-family:var(--font-b);font-size:11px;color:var(--ink2);text-transform:uppercase;letter-spacing:.1em;}
.nl-qr-wrap{margin-top:1.4rem;align-items:flex-start;}
.news-deco-dots{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;width:fit-content;margin-top:2rem;}
.news-deco-dots span{width:8px;height:8px;border-radius:50%;background:rgba(200,160,0,.25);display:block;animation:dot-breathe 2s ease-in-out infinite alternate;}
.news-deco-dots span:nth-child(odd){animation-delay:.5s;}
.news-deco-dots span:nth-child(3n){animation-delay:1s;}
@keyframes dot-breathe{from{opacity:.3;transform:scale(1);}to{opacity:.7;transform:scale(1.3);}}
.news-frame{flex:1;height:84vh;background:var(--y-warm);border:2px solid rgba(200,160,0,.25);border-radius:3vh;position:relative;overflow:hidden;box-shadow:0 24px 60px rgba(160,120,0,.12);}
.ns-poster{width:100%;height:100%;position:relative;display:flex;align-items:flex-end;overflow:hidden;}
.ns-no-image{position:absolute;inset:0;background:linear-gradient(145deg,var(--y-soft),var(--y-main));}
.ns-hero{position:absolute;inset:0;z-index:0;}
.xf-fallback-preview {
  margin-top: 1.5rem;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  border: 1px solid rgba(255,255,255,0.2);
}
.xf-fallback-img {
  width: 100%;
  height: auto;
  display: block;
}
.ns-hero-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  animation: kb 40s ease-in-out infinite alternate;
}
@keyframes kb{0%{transform:scale(1);}100%{transform:scale(1.15) translate(20px,10px);}}
.ns-hero-overlay{position:absolute;inset:0;background:linear-gradient(0deg,rgba(255,252,225,.97) 10%,rgba(255,249,200,.55) 55%,transparent 100%);}
.ns-content{position:relative;z-index:2;padding:calc(5vh + 92px) 5vh 5vh;width:100%;height:100%;display:flex;flex-direction:column;justify-content:flex-end;}
.ns-top{max-width:100%;margin-bottom:3vh;}
.ns-source-badge{width:100%;display:flex;align-items:center;justify-content:space-between;gap:14px;padding:14px 24px;border-radius:calc(3vh - 2px) calc(3vh - 2px) 14px 14px;background:linear-gradient(180deg,#ff2a2a 0%,#e31313 100%);border-bottom:1.5px solid rgba(255,255,255,.35);border-left:0;border-right:0;border-top:0;margin-bottom:0;box-shadow:0 10px 24px rgba(170,20,20,.35);}
.ns-source-banner{position:absolute;top:0;left:0;right:0;z-index:3;}
.ns-source{font-family:var(--font-d);font-weight:900;color:#fff;font-size:clamp(26px,3.2vw,52px);letter-spacing:.03em;line-height:.95;text-transform:uppercase;}
.ns-date{font-family:var(--font-b);font-size:12px;color:rgba(255,255,255,.95);background:rgba(0,0,0,.22);border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:6px 10px;white-space:nowrap;}
.ns-title{font-family:var(--font-d);font-size:clamp(30px,5vh,64px);font-weight:800;color:var(--ink);line-height:1.08;margin-bottom:0;}
.ns-footer{display:flex;align-items:center;justify-content:flex-end;}
.ns-qr-wrap{display:flex;flex-direction:column;align-items:center;gap:8px;}
.ns-qr{width:9vh;height:9vh;border:2.5px solid var(--y-deep);border-radius:10px;background:#fff;}
.ns-qr-lbl{font-family:var(--font-d);font-size:11px;font-weight:800;color:var(--ink2);letter-spacing:.1em;text-align:center;}
.ns-pagination{display:flex;gap:7px;}
.ns-dot{width:7px;height:7px;border-radius:50%;background:rgba(0,0,0,.15);transition:all .3s;cursor:pointer;}
.ns-dot-on{width:22px!important;border-radius:4px!important;background:var(--y-deep)!important;}
.slide-next-enter-active,.slide-prev-enter-active{transition:all .5s cubic-bezier(.16,1,.3,1);}
.slide-next-leave-active,.slide-prev-leave-active{transition:all .3s ease;}
.slide-next-enter-from{opacity:0;transform:translateX(40px);}
.slide-next-leave-to{opacity:0;transform:translateX(-30px);}
.slide-prev-enter-from{opacity:0;transform:translateX(-40px);}
.slide-prev-leave-to{opacity:0;transform:translateX(30px);}

/* BOTTOM BAR */
.bottom-bar{position:relative;z-index:100;height:50px;display:flex;align-items:center;padding:0 2.4rem;gap:1rem;background:rgba(255,253,232,.94);border-top:1px solid rgba(0,0,0,.06);backdrop-filter:blur(15px);--ink3:rgba(26,20,0,.5);}
.progress-rail{position:absolute;bottom:0;left:0;right:0;height:3px;background:rgba(200,160,0,.12);}
.progress-fill{height:100%;background:linear-gradient(90deg,var(--y-deep),var(--y-main),var(--y-soft));box-shadow:0 0 8px rgba(200,160,0,.5);}
.bb-left{display:flex;align-items:center;gap:8px;}
.bb-center{flex:1;display:flex;align-items:center;justify-content:center;gap:8px;}
.bb-right{display:flex;align-items:center;gap:12px;}
.bb-counter{font-family:var(--font-d);font-size:12px;color:var(--ink3);}

.slide-settings-btn{
  position:fixed;
  right:18px;
  bottom:62px;
  z-index:1200;
  width:34px;
  height:34px;
  border-radius:50%;
  border:1.5px solid rgba(200,160,0,.34);
  background:rgba(255,253,232,.95);
  color:var(--ink2);
  font-size:16px;
  cursor:pointer;
  box-shadow:0 8px 20px rgba(120,90,0,.18);
  display:flex;align-items:center;justify-content:center;
}
.btn-status-dot{
  position:absolute;top:-2px;right:-2px;
  width:10px;height:10px;border-radius:50%;
  background:#ff1e1e;border:1.5px solid #fff;
  box-shadow:0 0 6px rgba(255,10,10,.5);
}
.slide-settings-pop{
  position:fixed;
  right:18px;
  bottom:102px;
  z-index:1200;
  width:210px;
  background:rgba(255,253,232,.98);
  border:1.5px solid rgba(200,160,0,.28);
  border-radius:14px;
  box-shadow:0 14px 36px rgba(120,90,0,.18);
  padding:10px 12px;
}
.ssp-head{font-family:var(--font-d);font-size:12px;font-weight:800;color:var(--ink);letter-spacing:.06em;text-transform:uppercase;}
.ssp-sub{font-family:var(--font-b);font-size:10px;color:var(--ink3);margin:.2rem 0 .5rem;}
.ssp-item{display:flex;align-items:center;gap:8px;font-family:var(--font-b);font-size:12px;color:var(--ink2);padding:5px 0;}
.ssp-item input{accent-color:var(--y-deep);}
.ssp-item-locked{opacity:.78;}
.ssp-lock{margin-left:auto;font-size:10px;color:var(--ink3);text-transform:uppercase;letter-spacing:.08em;}

.ssp-divider{height:1px;background:rgba(200,160,0,.15);margin:10px 0;}
.ssp-session-box{
  margin-top:8px;padding:10px;border-radius:10px;
  background:rgba(0,0,0,.03);border:1px solid rgba(0,0,0,.05);
  display:flex;flex-direction:column;gap:8px;
}
.ssp-session-box.session-ok{background:rgba(34,168,74,.06);border-color:rgba(34,168,74,.15);}
.ssp-status{display:flex;align-items:center;gap:6px;font-family:var(--font-d);font-size:11px;font-weight:800;color:var(--ink2);text-transform:uppercase;}
.status-dot{width:6px;height:6px;border-radius:50%;background:#ff4b4b;box-shadow:0 0 5px rgba(255,75,75,.4);}
.session-ok .status-dot{background:#22a84a;box-shadow:0 0 5px rgba(34,168,74,.4);}
.ssp-login-btn{
  width:100%;padding:8px;border-radius:8px;border:none;
  background:#1DA1F2;color:white;font-family:var(--font-d);
  font-size:11px;font-weight:800;cursor:pointer;
  transition:all .2s;box-shadow:0 4px 10px rgba(29,161,242,.2);
}
.ssp-login-btn:hover{background:#1a91da;transform:translateY(-1px);box-shadow:0 6px 14px rgba(29,161,242,.3);}
.ssp-refresh-btn{background:var(--ink2);box-shadow:0 4px 10px rgba(0,0,0,.1);}
.ssp-refresh-btn:hover{background:var(--ink);box-shadow:0 6px 14px rgba(0,0,0,.15);}

#app{width:100vw;height:100vh;display:flex;flex-direction:column;overflow:hidden;position:relative;font-family:var(--font-d);}

/* X FEED SLIDE — two-column: screenshot left, sentiment clusters right */
.xf-slide {
  flex-direction: row !important;
  align-items: stretch;
  padding: 0 !important;
  gap: 0;
}
.xf-left-panel {
  flex-shrink: 0;
  width: 480px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  gap: .8rem;
  padding: 1.2rem 1.2rem 1rem 1.8rem;
  position: relative;
  z-index: 6;
  border-right: 1.5px solid rgba(206,171,57,0.18);
  background: rgba(255,255,255,0.35);
  backdrop-filter: blur(4px);
}
.xf-right-comments {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 0;
  position: relative;
  z-index: 2;
  overflow: hidden;
}
.xf-comments-header {
  display: flex;
  align-items: baseline;
  gap: 14px;
  padding: 10px 18px 0;
  flex-shrink: 0;
}
/* bubble-grid inside xf-right-comments takes the rest of the height */
.xf-right-comments .bubble-grid {
  flex: 1;
  margin: 8px 10px 10px;
  width: auto;
  position: relative;
  inset: auto;
}
.xf-left-label{text-align:center;z-index:2;}
.xf-left-eyebrow{font-family:var(--font-b);font-size:10px;font-weight:800;letter-spacing:.22em;text-transform:uppercase;color:rgba(29,161,242,.7);margin-bottom:4px;}
.xf-left-handle{font-family:var(--font-d);font-size:clamp(22px,3vw,36px);font-weight:900;color:var(--ink);line-height:1;}
.xf-left-date{font-family:var(--font-b);font-size:12px;color:var(--ink3);margin-top:4px;}
.xf-left-shot{width:100%;max-width:100%;max-height:calc(100vh - 180px);border-radius:16px;overflow:hidden;background:#fff;display:flex;align-items:flex-start;justify-content:center;box-shadow:0 0 0 4px rgba(29,161,242,.1),0 16px 40px rgba(0,0,0,.15);}
.xf-left-img{width:100%;max-height:calc(100vh - 180px);height:auto;display:block;object-fit:contain;object-position:top center;}
.xf-left-text{padding:1.5rem;font-family:var(--font-b);font-size:clamp(14px,1.6vw,20px);line-height:1.6;color:var(--ink);background:#fff;min-height:80px;display:flex;align-items:flex-start;}
.xf-left-text-block{width:100%;display:flex;flex-direction:column;background:#fff;}
.xf-post-images{display:flex;flex-direction:column;gap:6px;padding:0 1rem 1rem;}
.xf-post-img{width:100%;border-radius:10px;object-fit:cover;max-height:180px;border:1px solid rgba(29,161,242,.12);box-shadow:0 4px 14px rgba(0,0,0,.08);}
.xf-dots{display:flex;gap:8px;justify-content:center;z-index:2;}
.xf-dot{width:8px;height:8px;border-radius:50%;background:rgba(0,0,0,.14);cursor:pointer;transition:all .3s cubic-bezier(.22,1,.36,1);}
.xf-dot.active{background:#1DA1F2;width:24px;border-radius:4px;box-shadow:0 0 8px rgba(29,161,242,.5);}
.xf-right-eyebrow{font-family:var(--font-d);font-size:11px;font-weight:900;letter-spacing:.2em;text-transform:uppercase;color:#1DA1F2;}
.xf-right-count{font-family:var(--font-b);font-size:12px;color:var(--ink3);}

/* Simple comment list (no sentiment clustering) */
.xf-comments-list {
  flex: 1;
  overflow: hidden;
  padding: 10px 18px 20px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(3, 1fr);
  gap: 15px;
}
/* If exactly 5 comments, make the 5th one span both columns to fill the gap */
.xf-comments-list > .xf-comment-item:nth-child(5):last-child {
  grid-column: span 2;
}
.xf-comment-item {
  display: flex;
  gap: 14px;
  padding: 1.2rem 1.4rem;
  background: #fff;
  border: 1px solid rgba(206,171,57,0.15);
  border-radius: 20px;
  transition: all 0.2s;
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
  height: 100%;
  align-items: center;
}
.xf-comment-item:hover {
  background: var(--y-cream);
  transform: translateX(4px);
  border-color: var(--y-main);
}
.xfc-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1DA1F2, #0A7BC5);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-d);
  font-size: 14px;
  font-weight: 900;
  flex-shrink: 0;
  box-shadow: 0 3px 8px rgba(29,161,242,0.22);
}
.xfc-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.xfc-author {
  font-family: var(--font-d);
  font-size: 16px;
  font-weight: 850;
  color: var(--ink);
  line-height: 1;
}
.xfc-body {
  font-family: var(--font-b);
  font-size: 15px;
  line-height: 1.4;
  color: var(--ink2);
  font-weight: 500;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.xf-no-comments {
  text-align: center;
  padding: 3rem;
  font-family: var(--font-b);
  font-size: 14px;
  color: rgba(255,255,255,0.3);
  font-style: italic;
}
/* ═══════════════════════════════════════════════════════════════
   BUBBLE CLUSTER LAYOUT  (Slides 1 & 2)
   Matches reference image: emoji hub centered, speech-bubble
   cards floating around it. 5 clusters tile the full viewport
   in a 3-column × 2-row grid. No overlap, no overflow.
   ═══════════════════════════════════════════════════════════════ */

/* Outer wrapper fills the slide */
.bubble-grid {
  position: absolute;
  inset: 0;
  display: grid;
  /* 1 active  → 1 col;  2 → 2;  3 → 3;  4 → 2×2;  5 → 3+2 */
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 10px;
  padding: 10px 14px 10px 14px;
  box-sizing: border-box;
  overflow: hidden;
}

/* 1–2 clusters: fewer columns */
.bubble-grid[data-active="1"] { grid-template-columns: 1fr; grid-template-rows: 1fr; }
.bubble-grid[data-active="2"] { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr; }
.bubble-grid[data-active="3"] { grid-template-columns: repeat(3, 1fr); grid-template-rows: 1fr; }
.bubble-grid[data-active="4"] { grid-template-columns: repeat(2, 1fr); grid-template-rows: repeat(2, 1fr); }
/* 5: first row 3 cols, second row 2 cols (centred via subgrid trick) */
.bubble-grid[data-active="5"] { grid-template-columns: repeat(6, 1fr); grid-template-rows: repeat(2, 1fr); }
.bubble-grid[data-active="5"] .bc-cluster:nth-child(1) { grid-column: span 2; }
.bubble-grid[data-active="5"] .bc-cluster:nth-child(2) { grid-column: span 2; }
.bubble-grid[data-active="5"] .bc-cluster:nth-child(3) { grid-column: span 2; }
.bubble-grid[data-active="5"] .bc-cluster:nth-child(4) { grid-column: 2 / span 2; }
.bubble-grid[data-active="5"] .bc-cluster:nth-child(5) { grid-column: 4 / span 2; }

/* ── Cluster card — warm cream style matching overview iOS/Android cards ── */
.bc-cluster {
  position: relative;
  display: grid;
  grid-template-rows: auto auto 1fr;
  grid-template-columns: 1fr;
  align-items: center;
  justify-items: center;
  gap: 0;
  padding: 12px 10px 10px;
  background: linear-gradient(160deg, rgba(255,255,255,0.92) 0%, rgba(255,246,200,0.93) 100%);
  border: 1.5px solid rgba(206,171,57,0.22);
  border-radius: 22px;
  box-shadow: inset 0 1.5px 0 rgba(255,255,255,0.85), 0 10px 28px rgba(160,120,0,0.12);
  overflow: hidden;
  backdrop-filter: blur(8px);
  transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
}
.bc-cluster::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 22px;
  background: linear-gradient(135deg, var(--sc), transparent);
  opacity: 0.04;
  pointer-events: none;
  z-index: 0;
}
/* Top shimmer line matching overview cards */
.bc-cluster::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2.5px;
  background: linear-gradient(90deg, transparent, var(--sc), transparent);
  opacity: 0.5;
  border-radius: 22px 22px 0 0;
  pointer-events: none;
  z-index: 1;
}
.bc-cluster:hover {
  transform: translateY(-5px) scale(1.01);
  box-shadow: 0 20px 50px rgba(160,120,0,0.16), inset 0 1.5px 0 rgba(255,255,255,0.85);
  border-color: rgba(206,171,57,0.45);
}

/* ── Sentiment label above hub ── */
.bc-sent-name {
  font-family: var(--font-d);
  font-size: clamp(14px, 1.6vw, 22px);
  font-weight: 950;
  color: var(--sc);
  letter-spacing: 0.04em;
  text-align: center;
  text-shadow: 0 1px 6px rgba(0,0,0,0.08);
  margin-bottom: 2px;
  z-index: 2;
  white-space: nowrap;
}

/* ── Emoji Hub ── */
.bc-hub {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: clamp(40px, 4.5vw, 65px);
  height: clamp(40px, 4.5vw, 65px);
  flex-shrink: 0;
  z-index: 2;
  margin-bottom: 4px;
}

.bc-hub-glow {
  position: absolute;
  inset: -12px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--sc, #aaa) 0%, transparent 70%);
  opacity: 0.35;
  filter: blur(14px);
  animation: bc-pulse 3s ease-in-out infinite alternate;
  pointer-events: none;
}
@keyframes bc-pulse {
  from { opacity: 0.22; transform: scale(0.88); }
  to   { opacity: 0.50; transform: scale(1.12); }
}

.bc-hub-ring {
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  border: 1.5px solid var(--sc, #aaa);
  opacity: 0.4;
  animation: bc-ring-spin 10s linear infinite;
  pointer-events: none;
}
@keyframes bc-ring-spin { to { transform: rotate(360deg); } }

.bc-emoji {
  width: 100% !important;
  height: 100% !important;
  position: relative;
  z-index: 2;
  filter: drop-shadow(0 4px 12px rgba(0,0,0,0.3));
}
.bc-emoji > div, .bc-emoji > div > * { width: 100% !important; height: 100% !important; }

/* ── Bubble cards area ── */
.bc-bubbles {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  justify-content: center;
  align-content: flex-start;
  overflow: hidden;
  max-height: none;
  padding-top: 6px;
}

/* ── Individual speech-bubble card — warm cream matching overview ── */
.bc-bubble {
  background: linear-gradient(160deg, rgba(255,255,255,0.97) 0%, rgba(255,252,232,0.98) 100%);
  border: 1.5px solid rgba(206,171,57,0.22);
  border-left: 4px solid var(--sc);
  border-radius: 16px;
  padding: 14px 16px;
  min-width: 0;
  flex: 1 1 calc(50% - 5px);
  max-width: calc(50% - 3px);
  box-shadow: 0 4px 18px rgba(160,120,0,0.1), inset 0 1.5px 0 rgba(255,255,255,0.95);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Single bubble: full width */
.bc-bubbles[data-count="1"] .bc-bubble { flex: 1 1 100%; max-width: 100%; }
/* 3 bubbles: first one full, next two half */
.bc-bubbles[data-count="3"] .bc-bubble:first-child { flex: 1 1 100%; max-width: 100%; }
/* 5 bubbles: first row 3, second row 2 — use 33%/50% split */
.bc-bubbles[data-count="5"] .bc-bubble { flex: 1 1 calc(33% - 5px); max-width: calc(33% - 3px); }
.bc-bubbles[data-count="5"] .bc-bubble:nth-child(4),
.bc-bubbles[data-count="5"] .bc-bubble:nth-child(5) { flex: 1 1 calc(50% - 5px); max-width: calc(50% - 3px); }

/* ── Bubble card header: avatar + author + stars ── */
.bcb-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(206,171,57,0.18);
  flex-shrink: 0;
}

.bcb-avatar {
  width: clamp(28px, 3vw, 40px);
  height: clamp(28px, 3vw, 40px);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-d);
  font-size: clamp(13px, 1.4vw, 18px);
  font-weight: 900;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 3px 10px rgba(0,0,0,0.15);
}

.bcb-header-meta {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.bcb-author {
  font-family: var(--font-d);
  font-size: clamp(12px, 1.2vw, 16px);
  font-weight: 800;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bcb-stars { display: flex; gap: 2px; align-items: center; }
.bcb-star {
  display: inline-block;
  width: clamp(10px, 1.1vw, 14px);
  height: clamp(10px, 1.1vw, 14px);
  background: rgba(0,0,0,0.1);
  clip-path: polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%);
  flex-shrink: 0;
}
.bcb-star.star-full  { background: var(--y-deep); }
.bcb-star.star-half  { background: linear-gradient(90deg, var(--y-deep) 50%, rgba(0,0,0,0.1) 50%); }

.bcb-text {
  font-family: var(--font-b);
  font-size: clamp(13px, 1.4vw, 19px);
  font-weight: 600;
  color: var(--ink);
  line-height: 1.4;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 5;
}

/* Warm scene bg for slides 1 & 2 — matches overview palette #fff9eb */
.cluster-slide {
  position: relative;
  width: 100%;
  height: 100%;
  padding: 0;
  box-sizing: border-box;
  overflow: hidden;
  background: #fff9eb;
}

/* Subtle ambient orbs using overview primary yellows */
.cluster-slide::before,
.cluster-slide::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  filter: blur(110px);
  opacity: 0.28;
  animation: blob-float 10s ease-in-out infinite alternate;
  pointer-events: none;
}
.cluster-slide::before {
  width: 520px; height: 520px;
  background: radial-gradient(circle, #f7d747, #e8c200);
  top: -180px; left: -160px;
  animation-delay: 0s;
}
.cluster-slide::after {
  width: 420px; height: 420px;
  background: radial-gradient(circle, #fceea0, #f7d747);
  bottom: -120px; right: -120px;
  animation-delay: -4s;
}
@keyframes blob-float {
  to { transform: translate(60px, 40px) scale(1.15); }
}

</style>
