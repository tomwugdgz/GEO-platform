<template>
  <div class="px-fade-in">
    <div class="px-page-title">
      <div class="px-page-title-icon">⚡</div>
      <h1>品牌诊断中心</h1>
      <span class="sub">BRAND DIAGNOSIS HUB // TEXT · MULTIMODAL · COMPETITOR INTELLIGENCE</span>
    </div>

    <!-- ═══ 三 Tab 切换 ═══ -->
    <div class="tab-switcher">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
        <span class="tab-sub">{{ tab.sub }}</span>
      </button>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Tab 1: 品牌 GEO 诊断（苍何诊断师 v4.1）
         ═══════════════════════════════════════════════════════════ -->
    <div v-show="activeTab === 'diagnosis'">
      <!-- 输入区 -->
      <div class="px-card diag-input-card" v-if="!diagnosing && !diagResult">
        <div class="px-card-title">▸ 品牌 GEO 诊断 — CANG-HE ENGINE v4.1</div>
        <div class="px-grid px-grid-2" style="margin-bottom:16px">
          <div>
            <label class="px-label">品牌名称 <span style="color:var(--px-neon-pink)">*</span></label>
            <input v-model="form.brandName" class="px-input" placeholder="如：亲邻科技" />
          </div>
          <div>
            <label class="px-label">产品类型 <span style="color:var(--px-neon-pink)">*</span></label>
            <input v-model="form.productType" class="px-input" placeholder="如：社区媒体" />
          </div>
        </div>
        <div style="margin-bottom:16px">
          <label class="px-label">官网域名（可选）</label>
          <input v-model="form.website" class="px-input" placeholder="如：qinlin.com" />
        </div>
        <div style="margin-bottom:16px">
          <label class="px-label">诊断 AI 平台（默认全选 8 个）</label>
          <div class="platform-select-grid">
            <label v-for="p in allPlatforms" :key="p.code" class="platform-checkbox"
              :class="{ active: form.platforms.includes(p.code) }">
              <input type="checkbox" :value="p.code" v-model="form.platforms" />
              <span class="platform-check-icon">{{ p.icon }}</span>
              <span>{{ p.name }}</span>
            </label>
          </div>
        </div>
        <div style="display:flex; gap:12px; align-items:center">
          <button class="px-btn px-btn-primary" @click="startDiagnosis">▶ 开始 AI 诊断</button>
          <span style="font-size:10px; color:var(--px-text-muted)">
            预计 6-8 分钟 · 4 阶段流水线 · AIVO 四维评分
          </span>
        </div>
      </div>

      <!-- 诊断进度 -->
      <div v-if="diagnosing" class="px-card">
        <div class="px-card-title">▸ 诊断进行中 — RUNNING</div>
        <div class="diag-progress-wrap">
          <div v-for="(stage, idx) in stages" :key="idx" class="diag-stage"
            :class="{ active: currentStage === idx, done: currentStage > idx, pending: currentStage < idx }">
            <div class="diag-stage-node">
              <span v-if="currentStage > idx">✓</span>
              <span v-else-if="currentStage === idx" class="px-loading"></span>
              <span v-else>{{ idx + 1 }}</span>
            </div>
            <div class="diag-stage-info">
              <div class="diag-stage-name">{{ stage.name }}</div>
              <div class="diag-stage-desc">{{ stage.desc }}</div>
            </div>
            <div class="diag-stage-status">
              <span v-if="currentStage > idx" class="px-tag px-tag-success">完成</span>
              <span v-else-if="currentStage === idx" class="px-tag">执行中</span>
              <span v-else class="px-tag" style="opacity:0.3">等待中</span>
            </div>
          </div>
          <div class="diag-progress-bar-wrap">
            <div class="px-progress">
              <div class="px-progress-bar" :style="{ width: progressPct + '%' }"></div>
            </div>
            <span style="font-family:'VT323',monospace; font-size:16px; color:var(--px-neon-cyan)">
              {{ progressPct }}%
            </span>
          </div>
        </div>
      </div>

      <!-- 诊断结果 -->
      <div v-if="diagResult">
        <div class="px-grid px-grid-4" style="margin-bottom:16px">
          <div class="px-stat aivo-card" v-for="dim in aivoDimensions" :key="dim.key">
            <div class="px-stat-label">{{ dim.label }}</div>
            <div class="aivo-score" :style="{ color: dim.color }">{{ dim.value }}</div>
            <div class="aivo-bar"><div class="aivo-bar-fill" :style="{ width: dim.value + '%', background: dim.color }"></div></div>
            <div class="aivo-weight">权重 25%</div>
          </div>
        </div>
        <div class="px-card total-score-card" style="margin-bottom:16px">
          <div class="total-score-left">
            <div class="total-score-label">AIVO 综合评分</div>
            <div class="total-score-value" :style="{ color: totalScoreColor }">{{ diagResult.totalScore }}</div>
            <div class="total-score-grade" :style="{ color: totalScoreColor }">{{ totalScoreGrade }}</div>
          </div>
          <div class="total-score-radar">
            <svg viewBox="0 0 200 200" class="radar-svg">
              <polygon :points="radarBg(80)" fill="none" stroke="rgba(0,240,255,0.1)" stroke-width="1" />
              <polygon :points="radarBg(60)" fill="none" stroke="rgba(0,240,255,0.08)" stroke-width="1" />
              <polygon :points="radarBg(40)" fill="none" stroke="rgba(0,240,255,0.05)" stroke-width="1" />
              <line v-for="i in 4" :key="'a'+i" x1="100" y1="100"
                :x2="100 + 80 * Math.cos(i * Math.PI/2 - Math.PI/2)"
                :y2="100 + 80 * Math.sin(i * Math.PI/2 - Math.PI/2)"
                stroke="rgba(0,240,255,0.06)" stroke-width="1" />
              <polygon :points="radarPoints" fill="rgba(0,240,255,0.15)" stroke="#00f0ff" stroke-width="2" />
              <circle v-for="(p, i) in radarDots" :key="i" :cx="p.x" :cy="p.y" r="4"
                :fill="aivoDimensions[i].color"
                :style="{ filter: 'drop-shadow(0 0 4px ' + aivoDimensions[i].color + ')' }" />
              <text v-for="(label, i) in radarLabels" :key="i"
                :x="label.x" :y="label.y"
                fill="var(--px-text-dim)" font-size="10" text-anchor="middle" font-family="JetBrains Mono">
                {{ label.text }}
              </text>
            </svg>
          </div>
        </div>
        <div class="px-card" style="margin-bottom:16px">
          <div class="px-card-title">▸ AI 平台出镜率 — PLATFORM MENTION RATE</div>
          <div class="platform-list">
            <div v-for="p in diagResult.platforms" :key="p.name" class="platform-row">
              <div class="platform-icon" :style="{ background: p.color, boxShadow: '0 0 8px ' + p.color }">{{ p.icon }}</div>
              <div class="platform-name">{{ p.name }}</div>
              <div class="platform-bar-wrap">
                <div class="px-progress" style="height:10px">
                  <div class="px-progress-bar" :style="{ width: p.rate + '%', background: `linear-gradient(90deg, ${p.color}, ${p.color}88)` }"></div>
                </div>
              </div>
              <div class="platform-rate" :style="{ color: p.color }">{{ p.rate }}%</div>
              <div class="platform-tag">
                <span :class="'px-tag px-tag-' + (p.rate >= 70 ? 'success' : p.rate >= 30 ? 'warn' : 'danger')">
                  {{ p.rate >= 70 ? '优秀' : p.rate >= 30 ? '一般' : '较低' }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div class="px-grid px-grid-2" style="margin-bottom:16px">
          <div class="px-card">
            <div class="px-card-title">▸ 品牌基建评估 — INFRASTRUCTURE</div>
            <div v-for="item in diagResult.infrastructure" :key="item.label" class="infra-row">
              <div class="infra-icon">{{ item.icon }}</div>
              <div class="infra-info">
                <div class="infra-label">{{ item.label }}</div>
                <div class="infra-detail">{{ item.detail }}</div>
              </div>
              <div class="infra-score" :style="{ color: item.score >= 80 ? '#39ff14' : item.score >= 60 ? '#fff200' : '#ff2e97' }">{{ item.score }}</div>
            </div>
          </div>
          <div class="px-card">
            <div class="px-card-title">▸ 舆情健康度 — SENTIMENT</div>
            <div class="sentiment-overview">
              <div class="sentiment-ring">
                <svg viewBox="0 0 120 120">
                  <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(0,240,255,0.1)" stroke-width="8" />
                  <circle cx="60" cy="60" r="50" fill="none"
                    :stroke="diagResult.sentiment.health >= 80 ? '#39ff14' : '#fff200'"
                    stroke-width="8" :stroke-dasharray="314.16"
                    :stroke-dashoffset="314.16 * (1 - diagResult.sentiment.health / 100)"
                    stroke-linecap="round" transform="rotate(-90 60 60)" />
                </svg>
                <div class="sentiment-ring-text"><span>{{ diagResult.sentiment.health }}</span></div>
              </div>
              <div class="sentiment-stats">
                <div class="sentiment-stat" v-for="s in diagResult.sentiment.breakdown" :key="s.label">
                  <span class="sentiment-dot" :style="{ background: s.color }"></span>
                  <span class="sentiment-label">{{ s.label }}</span>
                  <span class="sentiment-count">{{ s.count }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="px-card" style="margin-bottom:16px">
          <div class="px-card-title">▸ 竞品对标 — COMPETITOR BENCHMARK</div>
          <table class="px-table">
            <thead><tr><th>品牌</th><th>GEO 评分</th><th>市场份额</th><th>威胁等级</th><th>AI出镜率</th><th>定位</th></tr></thead>
            <tbody>
              <tr v-for="c in diagResult.competitors" :key="c.name"
                :style="{ background: c.isBrand ? 'rgba(0,240,255,0.08)' : '' }">
                <td><span v-if="c.isBrand" style="color:var(--px-neon-cyan)">★ </span>{{ c.name }}</td>
                <td><span style="font-family:'VT323',monospace; font-size:18px"
                  :style="{ color: c.geoScore >= 75 ? '#39ff14' : c.geoScore >= 60 ? '#fff200' : '#ff2e97' }">{{ c.geoScore }}</span></td>
                <td>{{ c.marketShare }}%</td>
                <td><span :class="'px-tag px-tag-' + (c.threatLevel === 'high' ? 'danger' : c.threatLevel === 'medium' ? 'warn' : '')">
                  {{ c.threatLevel === 'high' ? '高' : c.threatLevel === 'medium' ? '中' : '低' }}</span></td>
                <td>
                  <div class="mini-bar"><div class="mini-bar-fill" :style="{ width: c.aiMention + '%', background: c.isBrand ? '#00f0ff' : '#5a6888' }"></div></div>
                  <span style="font-size:10px; color:var(--px-text-muted)">{{ c.aiMention }}%</span>
                </td>
                <td style="color:var(--px-text-dim)">{{ c.position }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="px-card" style="margin-bottom:16px">
          <div class="px-card-title">▸ 优化建议 — OPTIMIZATION SUGGESTIONS</div>
          <div class="suggestion-grid">
            <div v-for="(s, idx) in diagResult.suggestions" :key="idx" class="suggestion-card"
              :style="{ borderLeftColor: s.priority === 'high' ? '#ff2e97' : s.priority === 'medium' ? '#fff200' : '#39ff14' }">
              <div class="suggestion-header">
                <span class="suggestion-num">{{ String(idx + 1).padStart(2, '0') }}</span>
                <span :class="'px-tag px-tag-' + (s.priority === 'high' ? 'danger' : s.priority === 'medium' ? 'warn' : 'success')">
                  {{ s.priority === 'high' ? '紧急' : s.priority === 'medium' ? '重要' : '建议' }}</span>
              </div>
              <div class="suggestion-title">{{ s.title }}</div>
              <div class="suggestion-desc">{{ s.desc }}</div>
              <div class="suggestion-impact">预期提升：<span style="color:var(--px-neon-green)">{{ s.impact }}</span></div>
            </div>
          </div>
        </div>
        <div style="display:flex; gap:12px; margin-top:20px; padding-top:16px; border-top:1px dashed var(--px-border)">
          <button class="px-btn" @click="resetDiagnosis">◀ 重新诊断</button>
          <button class="px-btn px-btn-ghost" @click="exportReport">⇗ 导出报告</button>
        </div>
      </div>

      <!-- 空状态说明 -->
      <div v-if="!diagnosing && !diagResult" class="px-card" style="margin-top:16px">
        <div class="px-card-title">▸ 诊断说明</div>
        <div class="diag-explain">
          <div class="diag-explain-item"><span class="diag-explain-icon" style="color:var(--px-neon-cyan)">◈</span>
            <div><div style="color:var(--px-text-primary); margin-bottom:4px">AIVO 四维评分</div>
              <div style="font-size:11px; color:var(--px-text-muted)">AI搜索可见性 × 基建完善度 × 竞争优势 × 舆情健康度，各 25% 等权重</div></div></div>
          <div class="diag-explain-item"><span class="diag-explain-icon" style="color:var(--px-neon-green)">◇</span>
            <div><div style="color:var(--px-text-primary); margin-bottom:4px">8 大 AI 平台检测</div>
              <div style="font-size:11px; color:var(--px-text-muted)">DeepSeek / 豆包 / 元宝 / 通义千问 / 文心一言 / 纳米搜索 / Kimi / 智谱清言</div></div></div>
          <div class="diag-explain-item"><span class="diag-explain-icon" style="color:var(--px-neon-purple)">◎</span>
            <div><div style="color:var(--px-text-primary); margin-bottom:4px">搜索增强 + 虚拟推理</div>
              <div style="font-size:11px; color:var(--px-text-muted)">优先真实搜索数据，搜索不足时 AI 推理补充，所有数据标注来源</div></div></div>
          <div class="diag-explain-item"><span class="diag-explain-icon" style="color:var(--px-neon-yellow)">▤</span>
            <div><div style="color:var(--px-text-primary); margin-bottom:4px">4 阶段流水线</div>
              <div style="font-size:11px; color:var(--px-text-muted)">基础调研 → 收录+可见性 → 舆情分析 → 评分建议，约 6-8 分钟完成</div></div></div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Tab 2: 多模态诊断
         ═══════════════════════════════════════════════════════════ -->
    <div v-show="activeTab === 'multimodal'">
      <div class="px-card" style="margin-bottom:16px">
        <div class="px-card-title">▸ 多模态分析引擎 — MULTIMODAL ANALYSIS ENGINE</div>
        <div style="font-size:11px; color:var(--px-text-dim); line-height:1.6; margin-bottom:16px">
          超越文本监测，对图像/视频/音频进行品牌可见性深度分析。建立视觉识别 + 语音转写 + 情感分析的多模态技术护城河。
        </div>
        <div class="capability-grid">
          <div v-for="cap in multimodalCapabilities" :key="cap.module" class="capability-card"
            :style="{ borderColor: cap.color }">
            <div class="capability-header">
              <span class="capability-icon" :style="{ color: cap.color }">{{ cap.icon }}</span>
              <div>
                <div class="capability-name">{{ cap.name }}</div>
                <div class="capability-status" :class="cap.status">{{ cap.statusLabel }}</div>
              </div>
            </div>
            <div class="capability-desc">{{ cap.description }}</div>
            <div class="capability-features">
              <span v-for="f in cap.features" :key="f" class="feature-tag">{{ f }}</span>
            </div>
            <button class="px-btn px-btn-sm" @click="openMultimodalForm(cap.module)"
              :style="{ borderColor: cap.color, color: cap.color }">
              ▶ 开始分析
            </button>
          </div>
        </div>
      </div>

      <!-- 多模态分析表单 -->
      <div v-if="multimodalForm.visible" class="px-card" style="margin-bottom:16px">
        <div class="px-card-title">▸ {{ multimodalForm.module }} 分析配置</div>
        <div class="px-grid px-grid-2" style="margin-bottom:16px">
          <div>
            <label class="px-label">品牌名称 *</label>
            <input v-model="multimodalForm.brandName" class="px-input" placeholder="品牌名称" />
          </div>
          <div>
            <label class="px-label">产品类型 *</label>
            <input v-model="multimodalForm.productType" class="px-input" placeholder="产品类型" />
          </div>
        </div>
        <div style="margin-bottom:16px">
          <label class="px-label">媒体 URL（每行一个）</label>
          <textarea v-model="multimodalForm.urls" class="px-textarea" rows="4"
            placeholder="https://example.com/image1.jpg&#10;https://example.com/video1.mp4"></textarea>
        </div>
        <div style="display:flex; gap:12px">
          <button class="px-btn px-btn-primary" @click="submitMultimodalAnalysis">▶ 提交分析</button>
          <button class="px-btn" @click="multimodalForm.visible = false">✕ 取消</button>
        </div>
      </div>

      <!-- 多模态分析结果 -->
      <div v-if="multimodalResult" class="px-card" style="margin-bottom:16px">
        <div class="px-card-title">▸ 分析结果 — ANALYSIS RESULT</div>
        <div class="multimodal-result">
          <div class="result-summary">
            <div class="summary-item">
              <div class="summary-label">品牌检测数</div>
              <div class="summary-value" style="color:var(--px-neon-cyan)">{{ multimodalResult.brand_detected }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">平均置信度</div>
              <div class="summary-value" style="color:var(--px-neon-green)">{{ (multimodalResult.avg_confidence * 100).toFixed(1) }}%</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">平均相关性</div>
              <div class="summary-value" style="color:var(--px-neon-purple)">{{ (multimodalResult.avg_geo_relevance * 100).toFixed(1) }}%</div>
            </div>
          </div>
          <div class="result-details">
            <div v-for="item in multimodalResult.items" :key="item.id" class="result-detail-item">
              <div class="detail-preview">{{ item.icon }}</div>
              <div class="detail-info">
                <div class="detail-title">{{ item.title }}</div>
                <div class="detail-meta">置信度: {{ (item.confidence * 100).toFixed(1) }}% · 相关性: {{ (item.relevance * 100).toFixed(1) }}%</div>
              </div>
              <div class="detail-score" :style="{ color: item.confidence > 0.7 ? '#39ff14' : '#fff200' }">
                {{ (item.confidence * 100).toFixed(0) }}
              </div>
            </div>
          </div>
        </div>
        <button class="px-btn" style="margin-top:16px" @click="multimodalResult = null">◀ 重新分析</button>
      </div>

      <!-- Phase B 路线图 -->
      <div class="px-card" style="margin-top:16px">
        <div class="px-card-title">▸ Phase B 技术路线图</div>
        <div class="roadmap">
          <div class="roadmap-item">
            <div class="roadmap-phase">Phase B.1</div>
            <div class="roadmap-content">
              <div class="roadmap-title">CLIP + YOLO 视觉识别</div>
              <div class="roadmap-desc">接入 OpenAI CLIP 模型进行图文匹配，YOLO v8 进行 Logo/物体检测，支持品牌 Logo 自动识别</div>
            </div>
          </div>
          <div class="roadmap-item">
            <div class="roadmap-phase">Phase B.2</div>
            <div class="roadmap-content">
              <div class="roadmap-title">Whisper v3 语音转写</div>
              <div class="roadmap-desc">接入 OpenAI Whisper large-v3 模型，支持多语言 ASR，自动提取品牌名/竞品名提及</div>
            </div>
          </div>
          <div class="roadmap-item">
            <div class="roadmap-phase">Phase B.3</div>
            <div class="roadmap-content">
              <div class="roadmap-title">Video-LLaVA 视频理解</div>
              <div class="roadmap-desc">接入 Video-LLaVA 多模态大模型，对视频关键帧进行语义理解，自动生成视频摘要</div>
            </div>
          </div>
          <div class="roadmap-item">
            <div class="roadmap-phase">Phase B.4</div>
            <div class="roadmap-content">
              <div class="roadmap-title">跨模态融合引擎</div>
              <div class="roadmap-desc">构建多模态特征融合层，输出统一的品牌可见性指数（BVI），支持文本+图像+视频+音频联合分析</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Tab 3: 竞品逆向
         ═══════════════════════════════════════════════════════════ -->
    <div v-show="activeTab === 'competitor'">
      <div class="px-card" style="margin-bottom:16px">
        <div class="px-card-title">▸ 竞品逆向研究 — COMPETITOR REVERSE ENGINEERING</div>
        <div style="font-size:11px; color:var(--px-text-dim); line-height:1.6; margin-bottom:16px">
          深度拆解竞品 GEO 策略，从内容打法、关键词布局、AI 可见性、渠道组合、创意模式等 6 个维度逆向分析，找出可攻击的薄弱环节。
        </div>
        <div class="px-grid px-grid-2" style="margin-bottom:16px">
          <div>
            <label class="px-label">我的品牌 *</label>
            <input v-model="competitorForm.brandName" class="px-input" placeholder="品牌名称" />
          </div>
          <div>
            <label class="px-label">产品类型 *</label>
            <input v-model="competitorForm.productType" class="px-input" placeholder="产品类型" />
          </div>
        </div>
        <div style="margin-bottom:16px">
          <label class="px-label">竞品名称（每行一个）*</label>
          <textarea v-model="competitorForm.competitors" class="px-textarea" rows="4"
            placeholder="竞品A&#10;竞品B&#10;竞品C"></textarea>
        </div>
        <div style="margin-bottom:16px">
          <label class="px-label">分析维度（默认全选）</label>
          <div class="dimension-grid">
            <label v-for="dim in competitorDimensions" :key="dim.key" class="dimension-checkbox"
              :class="{ active: competitorForm.dimensions.includes(dim.key) }">
              <input type="checkbox" :value="dim.key" v-model="competitorForm.dimensions" />
              <span class="dimension-icon">{{ dim.icon }}</span>
              <div>
                <div class="dimension-name">{{ dim.name }}</div>
                <div class="dimension-desc">{{ dim.desc }}</div>
              </div>
            </label>
          </div>
        </div>
        <div style="display:flex; gap:12px">
          <button class="px-btn px-btn-primary" @click="startCompetitorAnalysis">▶ 启动逆向分析</button>
          <span style="font-size:10px; color:var(--px-text-muted); align-self:center">
            预计 3-5 分钟 · 6 维度深度拆解
          </span>
        </div>
      </div>

      <!-- 竞品分析进度 -->
      <div v-if="competitorAnalyzing" class="px-card" style="margin-bottom:16px">
        <div class="px-card-title">▸ 逆向分析进行中</div>
        <div class="competitor-progress">
          <div v-for="comp in competitorForm.competitors.split('\n').filter(c => c.trim())" :key="comp"
            class="competitor-item">
            <div class="competitor-name">{{ comp.trim() }}</div>
            <div class="competitor-status">
              <span class="px-loading"></span>
              <span style="margin-left:8px">正在分析...</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 竞品分析结果 -->
      <div v-if="competitorResult" style="margin-bottom:16px">
        <div class="px-card" style="margin-bottom:16px">
          <div class="px-card-title">▸ 竞品对标矩阵 — BENCHMARK MATRIX</div>
          <div class="benchmark-grid">
            <div v-for="comp in competitorResult.competitors" :key="comp.name" class="benchmark-card">
              <div class="benchmark-header">
                <div class="benchmark-name">{{ comp.name }}</div>
                <div class="benchmark-score" :style="{ color: comp.score >= 80 ? '#39ff14' : comp.score >= 60 ? '#fff200' : '#ff2e97' }">
                  {{ comp.score }}
                </div>
              </div>
              <div class="benchmark-position">{{ comp.position }}</div>
              <div class="benchmark-dimensions">
                <div v-for="(val, key) in comp.dimensions" :key="key" class="benchmark-dim">
                  <span class="dim-label">{{ dimensionNameMap[key] || key }}</span>
                  <div class="dim-bar">
                    <div class="dim-bar-fill" :style="{ width: val.score + '%', background: val.score >= 70 ? '#39ff14' : val.score >= 50 ? '#fff200' : '#ff2e97' }"></div>
                  </div>
                  <span class="dim-score">{{ val.score }}</span>
                </div>
              </div>
              <div class="benchmark-insights">
                <div class="insight-title">优势</div>
                <div v-for="s in comp.strengths" :key="s" class="insight-item">+ {{ s }}</div>
                <div class="insight-title" style="color:var(--px-neon-pink)">弱点</div>
                <div v-for="w in comp.weaknesses" :key="w" class="insight-item">- {{ w }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="px-card" style="margin-bottom:16px">
          <div class="px-card-title">▸ 可攻击的薄弱环节 — ATTACKABLE GAPS</div>
          <div class="attack-grid">
            <div v-for="comp in competitorResult.competitors" :key="comp.name" class="attack-card">
              <div class="attack-name">{{ comp.name }}</div>
              <div class="attack-gaps">
                <div v-for="gap in comp.attackable_gaps" :key="gap" class="attack-gap">
                  <span class="attack-icon">⚔</span>
                  <span>{{ gap }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="px-card">
          <div class="px-card-title">▸ 战略建议 — STRATEGIC RECOMMENDATIONS</div>
          <div class="strategic-grid">
            <div v-for="(rec, idx) in competitorResult.recommendations" :key="idx" class="strategic-card">
              <div class="strategic-num">{{ String(idx + 1).padStart(2, '0') }}</div>
              <div class="strategic-title">{{ rec.title }}</div>
              <div class="strategic-desc">{{ rec.desc }}</div>
              <div class="strategic-priority" :class="rec.priority">{{ rec.priorityLabel }}</div>
            </div>
          </div>
        </div>

        <button class="px-btn" style="margin-top:16px" @click="competitorResult = null">◀ 重新分析</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'

const API_BASE = '/api/v2'

const tabs = [
  { key: 'diagnosis', icon: '◈', label: '品牌 GEO 诊断', sub: 'CANG-HE v4.1' },
  { key: 'multimodal', icon: '◎', label: '多模态诊断', sub: 'IMAGE · VIDEO · AUDIO' },
  { key: 'competitor', icon: '▤', label: '竞品逆向', sub: 'REVERSE ENGINEERING' },
]
const activeTab = ref('diagnosis')

// ═══ Tab 1: 品牌 GEO 诊断 ═══
const form = ref({ brandName: '', productType: '', website: '', platforms: [1,2,3,4,5,6,7,8] })
const allPlatforms = [
  { code: 1, name: 'DeepSeek', icon: 'D' }, { code: 2, name: '豆包', icon: '豆' },
  { code: 3, name: '元宝', icon: '元' }, { code: 4, name: '通义千问', icon: '通' },
  { code: 5, name: '文心一言', icon: '文' }, { code: 6, name: '纳米搜索', icon: '纳' },
  { code: 7, name: 'Kimi', icon: 'K' }, { code: 8, name: '智谱清言', icon: '智' },
]
const diagnosing = ref(false)
const currentStage = ref(0)
const diagResult = ref(null)
const taskId = ref(null)
let pollTimer = null
const stages = [
  { name: '阶段 1 · 基础调研', desc: '用户画像 + 基建评估 + 竞品分析' },
  { name: '阶段 2 · 收录 + 可见性', desc: '8 平台虚拟收录查询 + GEO 效果统计' },
  { name: '阶段 3 · 舆情分析', desc: '负面舆情词 → 收录 → 情感分析' },
  { name: '阶段 4 · 评分建议', desc: 'AIVO 四维评分 + 综合优化建议' },
]
const progressPct = computed(() => Math.round(currentStage.value / 4 * 100))
const aivoDimensions = computed(() => {
  if (!diagResult.value) return []
  const s = diagResult.value.aivo
  return [
    { key: 'ai_visibility', label: 'AI 搜索可见性', value: s.aiVisibility, color: '#00f0ff' },
    { key: 'infrastructure', label: '基建完善度', value: s.infrastructure, color: '#39ff14' },
    { key: 'advantage', label: '竞争优势', value: s.advantage, color: '#b537f2' },
    { key: 'sentiment', label: '舆情健康度', value: s.sentiment, color: '#fff200' },
  ]
})
const totalScore = computed(() => diagResult.value?.totalScore || 0)
const totalScoreColor = computed(() =>
  totalScore.value >= 90 ? '#39ff14' : totalScore.value >= 75 ? '#00f0ff' : totalScore.value >= 60 ? '#fff200' : '#ff2e97'
)
const totalScoreGrade = computed(() =>
  totalScore.value >= 90 ? '● 优秀' : totalScore.value >= 75 ? '● 良好' : totalScore.value >= 60 ? '● 一般' : '● 较差'
)
const radarLabels = ['AI可见性', '基建', '竞争优势', '舆情']
const Math2 = Math
const radarBg = (r) => {
  return [0,1,2,3].map(i => {
    const angle = i * Math2.PI/2 - Math2.PI/2
    return `${100 + r * Math2.cos(angle)},${100 + r * Math2.sin(angle)}`
  }).join(' ')
}
const radarPoints = computed(() => {
  if (!diagResult.value) return ''
  const vals = aivoDimensions.value.map(d => d.value)
  return vals.map((v, i) => {
    const r = v * 0.8
    const angle = i * Math2.PI/2 - Math2.PI/2
    return `${100 + r * Math2.cos(angle)},${100 + r * Math2.sin(angle)}`
  }).join(' ')
})
const radarDots = computed(() => {
  if (!diagResult.value) return []
  const vals = aivoDimensions.value.map(d => d.value)
  return vals.map((v, i) => {
    const r = v * 0.8
    const angle = i * Math2.PI/2 - Math2.PI/2
    return { x: 100 + r * Math2.cos(angle), y: 100 + r * Math2.sin(angle) }
  })
})

const startDiagnosis = async () => {
  if (!form.value.brandName.trim()) { alert('请输入品牌名称'); return }
  if (!form.value.productType.trim()) { alert('请输入产品类型'); return }
  diagnosing.value = true
  currentStage.value = 0
  diagResult.value = null
  taskId.value = null
  try {
    const startRes = await fetch(`${API_BASE}/geo/diagnosis/start`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brandName: form.value.brandName, productType: form.value.productType,
        website: form.value.website || null, platforms: form.value.platforms })
    })
    if (!startRes.ok) throw new Error(`启动诊断失败: ${startRes.status}`)
    const startData = await startRes.json()
    taskId.value = startData.taskId
    pollTimer = setInterval(async () => {
      try {
        const statusRes = await fetch(`${API_BASE}/geo/diagnosis/status/${taskId.value}`)
        if (!statusRes.ok) return
        const statusData = await statusRes.json()
        currentStage.value = statusData.currentStage
        if (statusData.completed && statusData.result) {
          clearInterval(pollTimer); pollTimer = null
          diagResult.value = statusData.result
          diagnosing.value = false
        }
      } catch (e) { console.error('轮询状态失败:', e) }
    }, 2000)
  } catch (err) {
    console.error('诊断启动失败:', err)
    alert('后端服务连接失败，使用本地模拟数据')
    for (let i = 0; i < 4; i++) {
      currentStage.value = i
      await new Promise(r => setTimeout(r, 800))
    }
    currentStage.value = 4
    diagResult.value = generateMockResult(form.value.brandName)
    diagnosing.value = false
  }
}
const resetDiagnosis = () => {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  diagResult.value = null
  currentStage.value = 0
  taskId.value = null
}
const exportReport = async () => {
  if (!taskId.value) return
  alert('报告导出功能开发中，敬请期待')
}

function generateMockResult(brand) {
  const bias = () => Math.floor(Math.random() * 8) - 4
  return {
    totalScore: 72, aivo: { aiVisibility: 68 + bias(), infrastructure: 75 + bias(), advantage: 70 + bias(), sentiment: 78 + bias() },
    platforms: [
      { name: 'DeepSeek', icon: 'D', rate: 62 + bias(), color: '#00f0ff' },
      { name: '豆包', icon: '豆', rate: 75 + bias(), color: '#39ff14' },
      { name: '元宝', icon: '元', rate: 58 + bias(), color: '#b537f2' },
      { name: '通义千问', icon: '通', rate: 51 + bias(), color: '#fff200' },
      { name: '文心一言', icon: '文', rate: 80 + bias(), color: '#ff6b00' },
      { name: '纳米搜索', icon: '纳', rate: 45 + bias(), color: '#ff2e97' },
      { name: 'Kimi', icon: 'K', rate: 55 + bias(), color: '#3b82f6' },
      { name: '智谱清言', icon: '智', rate: 48 + bias(), color: '#8b5cf6' },
    ],
    infrastructure: [
      { icon: '⊡', label: '官网建设', detail: '存在 / 响应速度良好 / SEO 基础缺失', score: 72 },
      { icon: '⊕', label: '自媒体矩阵', detail: '已覆盖 6 平台 / 知乎/小红书较活跃', score: 68 },
      { icon: '▤', label: '权威媒体收录', detail: '3 篇权威报道 / 覆盖不足', score: 45 },
      { icon: '◎', label: '百科词条', detail: '百度百科已创建 / 互动百科缺失', score: 60 },
      { icon: '◇', label: 'Schema 标记', detail: '未检测到结构化数据', score: 30 },
    ],
    sentiment: {
      health: 82,
      breakdown: [
        { label: '正面提及', count: 156, color: '#39ff14' },
        { label: '中性提及', count: 234, color: '#00f0ff' },
        { label: '负面提及', count: 18, color: '#ff2e97' },
        { label: '投诉相关', count: 7, color: '#ff6b00' },
      ]
    },
    competitors: [
      { name: brand, geoScore: 72, marketShare: 8, threatLevel: '-', aiMention: 62, position: '本品牌', isBrand: true },
      { name: '竞品A', geoScore: 85, marketShare: 18, threatLevel: 'high', aiMention: 78, position: '行业领导者', isBrand: false },
      { name: '竞品B', geoScore: 76, marketShare: 12, threatLevel: 'medium', aiMention: 68, position: '快速增长', isBrand: false },
      { name: '竞品C', geoScore: 65, marketShare: 6, threatLevel: 'medium', aiMention: 52, position: '区域强势', isBrand: false },
      { name: '竞品D', geoScore: 58, marketShare: 4, threatLevel: 'low', aiMention: 38, position: '新进入者', isBrand: false },
    ],
    suggestions: [
      { title: '补充官网 Schema 结构化数据', desc: '当前官网未部署 Organization / Product / FAQ 等 JSON-LD 标记，AI 搜索引擎难以提取品牌信息', priority: 'high', impact: 'AI 可见性 +12%' },
      { title: '增加权威媒体报道覆盖', desc: '权威媒体收录仅 3 篇，远低于行业平均 15 篇，需重点补充 ZOL/太平洋/IT168 等渠道', priority: 'high', impact: '基建完善度 +18%' },
      { title: '布局长尾问答内容', desc: '品牌相关长尾问题 AI 回答中提及率仅 45%，需在知乎/小红书批量铺设问答', priority: 'medium', impact: 'AI 可见性 +8%' },
      { title: '建立竞品对比内容', desc: 'DeepSeek/Kimi 在对比类问题中倾向推荐竞品，需创建对比类内容争夺推荐位', priority: 'medium', impact: '竞争优势 +15%' },
      { title: '统一多平台品牌信息', desc: '各平台品牌描述/产品特性不一致，影响 AI 模型对品牌的统一认知', priority: 'low', impact: '基建完善度 +6%' },
      { title: '处理负面舆情内容', desc: '发现 18 条负面提及，主要集中在售后/价格维度，需及时响应', priority: 'low', impact: '舆情健康度 +10%' },
    ]
  }
}

// ═══ Tab 2: 多模态诊断 ═══
const multimodalCapabilities = [
  {
    module: 'image', icon: '🖼️', name: '图像分析', color: '#00f0ff', status: 'ready', statusLabel: '可用',
    description: '对图像进行品牌 Logo 检测、OCR 文字提取、视觉主题识别、品牌相关性评分',
    features: ['Logo 检测', 'OCR', '视觉主题', '相关性评分', '竞品识别'],
  },
  {
    module: 'video', icon: '🎬', name: '视频分析', color: '#39ff14', status: 'ready', statusLabel: '可用',
    description: '对视频进行关键帧采样、Logo 追踪、语音转写、情感分析、竞品口播识别',
    features: ['关键帧', 'Logo 追踪', '语音转写', '情感分析', '竞品识别'],
  },
  {
    module: 'audio', icon: '🎧', name: '音频分析', color: '#b537f2', status: 'ready', statusLabel: '可用',
    description: '对音频进行 ASR 转写、品牌名识别、情感分类、主题抽取',
    features: ['ASR 转写', '品牌识别', '情感分类', '主题抽取'],
  },
  {
    module: 'mixed', icon: '🔀', name: '跨模态融合', color: '#fff200', status: 'planned', statusLabel: '规划中',
    description: '整合图像/视频/音频分析结果，输出统一的品牌可见性指数（BVI）',
    features: ['多维曝光', '一致性校验', '综合评分'],
  },
]
const multimodalForm = ref({ visible: false, module: '', brandName: '', productType: '', urls: '' })
const multimodalResult = ref(null)

const openMultimodalForm = (module) => {
  multimodalForm.value.visible = true
  multimodalForm.value.module = module
}
const submitMultimodalAnalysis = async () => {
  if (!multimodalForm.value.brandName.trim() || !multimodalForm.value.productType.trim()) {
    alert('请输入品牌名称和产品类型'); return
  }
  const urls = multimodalForm.value.urls.split('\n').filter(u => u.trim())
  try {
    const res = await fetch(`${API_BASE}/geo/multimodal/${multimodalForm.value.module}/analyze`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        brand_name: multimodalForm.value.brandName,
        product_type: multimodalForm.value.productType,
        media_type: multimodalForm.value.module,
        source_urls: urls,
        analysis_focus: 'brand_visibility',
      })
    })
    if (!res.ok) throw new Error(`分析失败: ${res.status}`)
    const data = await res.json()
    multimodalResult.value = {
      brand_detected: data.results.filter(r => r.brand_detected).length,
      avg_confidence: data.results.reduce((s, r) => s + r.brand_confidence, 0) / data.results.length,
      avg_geo_relevance: data.results.reduce((s, r) => s + r.geo_relevance, 0) / data.results.length,
      items: data.results.map(r => ({
        id: r.image_id || r.video_id || r.audio_id,
        icon: multimodalForm.value.module === 'image' ? '🖼️' : multimodalForm.value.module === 'video' ? '🎬' : '🎧',
        title: r.url,
        confidence: r.brand_confidence || r.brand_time_ratio || (r.brand_mentioned_count > 0 ? 0.8 : 0.3),
        relevance: r.geo_relevance || r.geo_score / 100 || 0.5,
      }))
    }
    multimodalForm.value.visible = false
  } catch (err) {
    console.error('多模态分析失败:', err)
    alert('后端服务连接失败，使用本地模拟数据')
    multimodalResult.value = {
      brand_detected: 2, avg_confidence: 0.75, avg_geo_relevance: 0.68,
      items: [
        { id: '1', icon: '🖼️', title: 'mock_image_1.jpg', confidence: 0.85, relevance: 0.72 },
        { id: '2', icon: '🖼️', title: 'mock_image_2.jpg', confidence: 0.65, relevance: 0.58 },
        { id: '3', icon: '🖼️', title: 'mock_image_3.jpg', confidence: 0.92, relevance: 0.81 },
      ]
    }
    multimodalForm.value.visible = false
  }
}

// ═══ Tab 3: 竞品逆向 ═══
const competitorDimensions = [
  { key: 'content_strategy', icon: '📝', name: '内容策略', desc: '内容主题/频率/平台/风格拆解' },
  { key: 'seo_tactics', icon: '🔍', name: 'SEO 战术', desc: '官网 SEO / 长尾词 / 外链 / 结构化数据' },
  { key: 'ai_visibility', icon: '🤖', name: 'AI 可见性', desc: '竞品在 8 大 AI 平台的推荐率/提及率' },
  { key: 'keyword_playbook', icon: '🔑', name: '关键词打法', desc: '核心词 / 长尾词 / 问题词布局' },
  { key: 'channel_mix', icon: '📡', name: '渠道组合', desc: '知乎/小红书/B站/公众号/抖音覆盖' },
  { key: 'creative_pattern', icon: '🎨', name: '创意模式', desc: 'KOL 测评/故事/对比/场景化创意' },
]
const dimensionNameMap = {
  content_strategy: '内容策略', seo_tactics: 'SEO 战术', ai_visibility: 'AI 可见性',
  keyword_playbook: '关键词打法', channel_mix: '渠道组合', creative_pattern: '创意模式',
}
const competitorForm = ref({ brandName: '', productType: '', competitors: '', dimensions: competitorDimensions.map(d => d.key) })
const competitorAnalyzing = ref(false)
const competitorResult = ref(null)

const startCompetitorAnalysis = async () => {
  if (!competitorForm.value.brandName.trim() || !competitorForm.value.productType.trim()) {
    alert('请输入品牌名称和产品类型'); return
  }
  const comps = competitorForm.value.competitors.split('\n').map(c => c.trim()).filter(c => c)
  if (comps.length === 0) { alert('请至少输入一个竞品名称'); return }
  competitorAnalyzing.value = true
  competitorResult.value = null
  try {
    const res = await fetch(`${API_BASE}/geo/competitor/analyze`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        brand_name: competitorForm.value.brandName,
        product_type: competitorForm.value.productType,
        competitor_names: comps,
        analysis_dimensions: competitorForm.value.dimensions,
        depth: 'standard',
      })
    })
    if (!res.ok) throw new Error(`分析失败: ${res.status}`)
    const data = await res.json()
    // 轮询结果
    const pollTimer = setInterval(async () => {
      try {
        const statusRes = await fetch(`${API_BASE}/geo/competitor/status/${data.task_id}`)
        if (!statusRes.ok) return
        const statusData = await statusRes.json()
        if (statusData.completed && statusData.result) {
          clearInterval(pollTimer)
          competitorAnalyzing.value = false
          competitorResult.value = {
            competitors: statusData.result.competitors.map(c => ({
              name: c.competitor, score: c.geo_score, position: c.market_position,
              dimensions: c.dimensions,
              strengths: c.strengths, weaknesses: c.weaknesses,
              attackable_gaps: c.attackable_gaps,
            })),
            recommendations: statusData.result.benchmark_summary.recommendation_priority.map((r, i) => ({
              title: r, desc: '基于竞品逆向分析的战略建议', priority: i === 0 ? 'high' : i === 1 ? 'medium' : 'low',
              priorityLabel: i === 0 ? '紧急' : i === 1 ? '重要' : '建议',
            }))
          }
        }
      } catch (e) { console.error('轮询失败:', e) }
    }, 2000)
  } catch (err) {
    console.error('竞品分析失败:', err)
    alert('后端服务连接失败，使用本地模拟数据')
    competitorAnalyzing.value = false
    competitorResult.value = {
      competitors: comps.map(c => ({
        name: c, score: Math.floor(Math.random() * 30) + 60, position: '行业参与者',
        dimensions: Object.fromEntries(competitorForm.value.dimensions.map(d => [d, { score: Math.floor(Math.random() * 40) + 50, insights: ['数据占位'] }])),
        strengths: ['品牌知名度高', '渠道覆盖广'],
        weaknesses: ['价格偏高', '创新不足'],
        attackable_gaps: ['在纳米搜索提及率低', '长尾问题覆盖不足', '负面舆情响应慢'],
      })),
      recommendations: [
        { title: '强化品牌问答内容铺设', desc: '在知乎/小红书批量铺设问答，提升 AI 平台可见性', priority: 'high', priorityLabel: '紧急' },
        { title: '补齐 Schema 结构化数据', desc: '官网部署 Organization / Product / FAQ 等 JSON-LD', priority: 'medium', priorityLabel: '重要' },
        { title: '针对竞品薄弱环节发起内容攻势', desc: '针对竞品在 AI 搜索中的薄弱环节，定向铺设内容', priority: 'low', priorityLabel: '建议' },
      ]
    }
  }
}

onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })
</script>

<style scoped>
/* ═══ Tab 切换器 ═══ */
.tab-switcher {
  display: flex; gap: 8px; margin-bottom: 20px; padding: 4px;
  background: var(--px-bg-deep); border: 1px solid var(--px-border);
}
.tab-btn {
  flex: 1; padding: 12px 16px; background: transparent; border: 1px solid transparent;
  color: var(--px-text-dim); cursor: pointer; transition: all 0.2s;
  display: flex; flex-direction: column; align-items: flex-start; gap: 2px;
  font-family: 'JetBrains Mono', monospace;
}
.tab-btn:hover { color: var(--px-text-primary); background: rgba(0,240,255,0.04); }
.tab-btn.active {
  color: var(--px-neon-cyan); background: rgba(0,240,255,0.08);
  border-color: var(--px-neon-cyan); box-shadow: 0 0 12px rgba(0,240,255,0.15);
}
.tab-icon { font-size: 16px; margin-bottom: 2px; }
.tab-label { font-size: 13px; font-weight: 500; }
.tab-sub { font-size: 9px; color: var(--px-text-muted); letter-spacing: 1px; }

/* ═══ 多模态能力网格 ═══ */
.capability-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.capability-card {
  background: var(--px-bg-deep); border: 1px solid var(--px-border); border-left: 3px solid;
  padding: 16px; display: flex; flex-direction: column; gap: 10px;
}
.capability-header { display: flex; align-items: center; gap: 12px; }
.capability-icon { font-size: 24px; }
.capability-name { font-size: 14px; color: var(--px-text-primary); font-weight: 500; }
.capability-status { font-size: 10px; padding: 2px 6px; border-radius: 2px; }
.capability-status.ready { background: rgba(57,255,20,0.15); color: var(--px-neon-green); }
.capability-status.planned { background: rgba(255,242,0,0.15); color: var(--px-neon-yellow); }
.capability-desc { font-size: 11px; color: var(--px-text-dim); line-height: 1.6; }
.capability-features { display: flex; flex-wrap: wrap; gap: 6px; }
.feature-tag {
  font-size: 10px; padding: 2px 8px; background: rgba(0,240,255,0.08);
  border: 1px solid var(--px-border); color: var(--px-text-dim);
}
.px-btn-sm { padding: 6px 12px; font-size: 11px; background: transparent; border: 1px solid; cursor: pointer; }

/* ═══ 多模态结果 ═══ */
.multimodal-result { display: flex; flex-direction: column; gap: 16px; }
.result-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.summary-item { text-align: center; padding: 12px; background: var(--px-bg-deep); border: 1px solid var(--px-border); }
.summary-label { font-size: 11px; color: var(--px-text-muted); margin-bottom: 6px; }
.summary-value { font-family: 'VT323', monospace; font-size: 32px; }
.result-details { display: flex; flex-direction: column; gap: 8px; }
.result-detail-item {
  display: flex; align-items: center; gap: 12px; padding: 10px;
  background: var(--px-bg-deep); border: 1px solid var(--px-border);
}
.detail-preview { font-size: 24px; width: 40px; text-align: center; }
.detail-info { flex: 1; }
.detail-title { font-size: 12px; color: var(--px-text-primary); margin-bottom: 4px; }
.detail-meta { font-size: 10px; color: var(--px-text-muted); }
.detail-score { font-family: 'VT323', monospace; font-size: 24px; }

/* ═══ 路线图 ═══ */
.roadmap { display: flex; flex-direction: column; gap: 12px; }
.roadmap-item { display: flex; gap: 16px; padding: 12px; background: var(--px-bg-deep); border: 1px solid var(--px-border); }
.roadmap-phase {
  font-family: 'VT323', monospace; font-size: 14px; color: var(--px-neon-cyan);
  padding: 4px 10px; background: rgba(0,240,255,0.08); border: 1px solid var(--px-border);
  height: fit-content; white-space: nowrap;
}
.roadmap-content { flex: 1; }
.roadmap-title { font-size: 13px; color: var(--px-text-primary); margin-bottom: 4px; }
.roadmap-desc { font-size: 11px; color: var(--px-text-dim); line-height: 1.6; }

/* ═══ 竞品逆向 ═══ */
.dimension-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.dimension-checkbox {
  display: flex; align-items: center; gap: 10px; padding: 10px;
  background: var(--px-bg-deep); border: 1px solid var(--px-border); cursor: pointer;
  transition: all 0.15s;
}
.dimension-checkbox input { display: none; }
.dimension-checkbox.active { border-color: var(--px-neon-cyan); background: rgba(0,240,255,0.06); }
.dimension-icon { font-size: 18px; }
.dimension-name { font-size: 12px; color: var(--px-text-primary); }
.dimension-desc { font-size: 10px; color: var(--px-text-muted); }

.competitor-progress { display: flex; flex-direction: column; gap: 8px; }
.competitor-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px; background: var(--px-bg-deep); border: 1px solid var(--px-border);
}
.competitor-name { font-size: 13px; color: var(--px-text-primary); }
.competitor-status { display: flex; align-items: center; font-size: 11px; color: var(--px-neon-cyan); }

.benchmark-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.benchmark-card { background: var(--px-bg-deep); border: 1px solid var(--px-border); padding: 16px; }
.benchmark-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.benchmark-name { font-size: 16px; color: var(--px-text-primary); font-weight: 500; }
.benchmark-score { font-family: 'VT323', monospace; font-size: 32px; }
.benchmark-position { font-size: 11px; color: var(--px-text-muted); margin-bottom: 12px; }
.benchmark-dimensions { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.benchmark-dim { display: flex; align-items: center; gap: 8px; }
.dim-label { font-size: 10px; color: var(--px-text-muted); width: 60px; }
.dim-bar { flex: 1; height: 6px; background: var(--px-bg-card); }
.dim-bar-fill { height: 100%; transition: width 0.3s; }
.dim-score { font-family: 'VT323', monospace; font-size: 14px; color: var(--px-text-dim); width: 24px; text-align: right; }
.benchmark-insights { display: flex; flex-direction: column; gap: 4px; }
.insight-title { font-size: 11px; color: var(--px-neon-green); margin-top: 4px; }
.insight-item { font-size: 10px; color: var(--px-text-dim); padding-left: 12px; }

.attack-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.attack-card { background: var(--px-bg-deep); border: 1px solid var(--px-border); padding: 12px; }
.attack-name { font-size: 13px; color: var(--px-text-primary); margin-bottom: 8px; }
.attack-gaps { display: flex; flex-direction: column; gap: 6px; }
.attack-gap { display: flex; align-items: center; gap: 8px; font-size: 11px; color: var(--px-text-dim); }
.attack-icon { color: var(--px-neon-pink); }

.strategic-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.strategic-card {
  background: var(--px-bg-deep); border: 1px solid var(--px-border); padding: 16px;
  position: relative;
}
.strategic-num { font-family: 'VT323', monospace; font-size: 24px; color: var(--px-text-muted); }
.strategic-title { font-size: 13px; color: var(--px-text-primary); margin: 8px 0; }
.strategic-desc { font-size: 11px; color: var(--px-text-dim); line-height: 1.6; }
.strategic-priority {
  margin-top: 12px; font-size: 10px; padding: 2px 8px; display: inline-block;
}
.strategic-priority.high { background: rgba(255,46,151,0.15); color: var(--px-neon-pink); }
.strategic-priority.medium { background: rgba(255,242,0,0.15); color: var(--px-neon-yellow); }
.strategic-priority.low { background: rgba(57,255,20,0.15); color: var(--px-neon-green); }

.px-textarea {
  width: 100%; padding: 10px; background: var(--px-bg-deep); border: 1px solid var(--px-border);
  color: var(--px-text-primary); font-family: 'JetBrains Mono', monospace; font-size: 12px;
  resize: vertical;
}
.px-textarea:focus { outline: none; border-color: var(--px-neon-cyan); }

@media (max-width: 1200px) {
  .capability-grid, .benchmark-grid, .attack-grid { grid-template-columns: 1fr; }
  .dimension-grid { grid-template-columns: 1fr; }
  .strategic-grid { grid-template-columns: 1fr; }
  .result-summary { grid-template-columns: 1fr; }
}
</style>
