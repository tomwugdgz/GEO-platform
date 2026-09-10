<template>
  <div class="px-app">
    <!-- ═══ 侧边栏 ═══ -->
    <aside class="px-sidebar">
      <div class="px-logo">
        <div class="px-logo-icon"></div>
        <div>
          <div class="px-logo-text">MTO</div>
          <div class="px-logo-sub">MACHINE TRUST OPTIMIZATION</div>
        </div>
      </div>

      <!-- 分组：MTO 平台 -->
      <div class="px-group">
        <div class="px-group-title">▹ MTO 平台</div>
        <router-link to="/about-mto" class="px-nav-item">
          <span class="px-nav-icon">🔐</span> 关于 MTO
          <span class="px-nav-indicator"></span>
        </router-link>
      </div>

      <!-- 分组：认知底座 -->
      <div class="px-group">
        <div class="px-group-title">▹ 认知底座</div>
        <router-link to="/" class="px-nav-item">
          <span class="px-nav-icon">⌂</span> 品牌首页
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/dashboard" class="px-nav-item">
          <span class="px-nav-icon">◈</span> 数据驾驶舱
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/brand-diagnosis" class="px-nav-item">
          <span class="px-nav-icon">⚡</span> 品牌诊断
          <span class="px-nav-indicator"></span>
        </router-link>
      </div>

      <!-- 分组：SOP 工作流 -->
      <div class="px-group">
        <div class="px-group-title">▹ SOP 工作流</div>
        <router-link to="/workflow" class="px-nav-item">
          <span class="px-nav-icon">⊞</span> 全流程总览
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/keywords" class="px-nav-item">
          <span class="px-nav-icon">◇</span> 蒸馏主词
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/question-creation" class="px-nav-item">
          <span class="px-nav-icon">✎</span> 问题创作
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/gallery" class="px-nav-item">
          <span class="px-nav-icon">▣</span> 素材图库
          <span class="px-nav-indicator"></span>
        </router-link>
      </div>

      <!-- 分组：分发与追踪 -->
      <div class="px-group">
        <div class="px-group-title">▹ 分发与追踪</div>
        <router-link to="/social" class="px-nav-item">
          <span class="px-nav-icon">⊕</span> 自媒体授权
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/writing" class="px-nav-item">
          <span class="px-nav-icon">⎔</span> AI 写作
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/omni-distribution" class="px-nav-item">
          <span class="px-nav-icon">⇗</span> 全域分发
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/ai-tracking" class="px-nav-item">
          <span class="px-nav-icon">◉</span> AI 追踪
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/monitoring" class="px-nav-item">
          <span class="px-nav-icon">▤</span> 监测看板
          <span class="px-nav-indicator"></span>
        </router-link>
      </div>

      <!-- 分组：知识库 -->
      <div class="px-group">
        <div class="px-group-title">▹ 知识库</div>
        <router-link to="/intent" class="px-nav-item">
          <span class="px-nav-icon">◎</span> 意图地图
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/knowledge" class="px-nav-item">
          <span class="px-nav-icon">⊡</span> 知识编辑
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/content" class="px-nav-item">
          <span class="px-nav-icon">≡</span> 内容库
          <span class="px-nav-indicator"></span>
        </router-link>
      </div>

      <!-- 分组：GeoLook 引擎 -->
      <div class="px-group">
        <div class="px-group-title">▹ GeoLook 引擎</div>
        <!-- 当前项目：子页面（站点审计/工单/验收…）默认操作该项目 -->
        <div v-if="currentSlug" class="px-current-project" :title="`当前项目：${currentSlug}`">
          <span class="px-current-label">当前项目</span>
          <span class="px-current-slug">{{ currentSlug }}</span>
        </div>
        <router-link to="/geolook" class="px-nav-item">
          <span class="px-nav-icon">⚙</span> GEO 诊断
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/geo/siteaudit" class="px-nav-item">
          <span class="px-nav-icon">🔍</span> 站点审计
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/geo/plan" class="px-nav-item">
          <span class="px-nav-icon">📋</span> 工单管理
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/geo/competitors" class="px-nav-item">
          <span class="px-nav-icon">🏆</span> 竞品分析
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/geo/channels" class="px-nav-item">
          <span class="px-nav-icon">🗺️</span> 渠道地图
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/geo/gaps" class="px-nav-item">
          <span class="px-nav-icon">🎯</span> 缺口诊断
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/geo/verify" class="px-nav-item">
          <span class="px-nav-icon">✅</span> 验收闭环
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/settings" class="px-nav-item">
          <span class="px-nav-icon">⚙️</span> 引擎配置
          <span class="px-nav-indicator"></span>
        </router-link>
        <router-link to="/web-publishing" class="px-nav-item">
          <span class="px-nav-icon">🌐</span> 网站优化助手
          <span class="px-nav-indicator"></span>
        </router-link>
      </div>

      <!-- 分组：团队协作 -->
      <div class="px-group">
        <div class="px-group-title">▹ 团队协作</div>
        <router-link to="/team-collaboration" class="px-nav-item">
          <span class="px-nav-icon">⊛</span> 团队协作
          <span class="px-nav-indicator"></span>
        </router-link>
      </div>

      <!-- ═══ 版权与使用声明 ═══ 个人非商业项目，详见 /THIRD_PARTY_NOTICES.md -->
      <div class="px-legal-notice">
        <div class="px-legal-title">⚖ 使用声明</div>
        <p>
          <strong>MTO（机器信任优化）概念目前仍属理论推演阶段，尚未全面落地，请勿据此做商业决策。</strong>
          本项目为个人非商业学习研究项目，无商业部署意图。
        </p>
        <p>
          GEO 引擎内核源自开源项目
          <a href="https://github.com/aigclink/geolook" target="_blank" rel="noopener noreferrer">GeoLook</a>
          （MIT · Copyright (c) 2026 GeoLook contributors），与上游无隶属或背书关系。
        </p>
        <p>
          如认为本作品侵犯您的权益，请联系
          <a href="mailto:duckwolf@qq.com">duckwolf@qq.com</a>，
          核实后立即删除，不作抗辩。
        </p>
      </div>
    </aside>

    <!-- ═══ 顶栏 ═══ -->
    <header class="px-topbar">
      <div class="px-crumb">
        <span>MTO</span>
        <span class="sep">/</span>
        <span class="current">{{ currentPageName }}</span>
      </div>

      <div class="px-topbar-status">
        <span><span class="px-status-dot"></span>SYSTEM ONLINE</span>
        <span class="px-separator">|</span>
        <span>API:5006</span>
        <span class="px-separator">|</span>
        <select v-model="currentTenant" class="px-select-inline">
          <option value="">-- 租户 --</option>
          <option v-for="t in tenants" :key="t.id" :value="t.id">{{ t.name }}</option>
        </select>
        <select v-model="currentBrand" class="px-select-inline" v-if="brands.length">
          <option value="">-- 品牌 --</option>
          <option v-for="b in brands" :key="b.id" :value="b.id">{{ b.name }}</option>
        </select>
      </div>
    </header>

    <!-- ═══ 主内容 ═══ -->
    <main class="px-main px-fade-in">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/axios'
import { getStoredSlug, SLUG_CHANGED_EVENT } from '@/composables/useGeoProject'

const route = useRoute()

// localStorage 在沙箱化预览（opaque origin）中会抛 SecurityError，
// 统一降级为内存变量，避免顶层调用直接打断整个应用初始化。
const safeGetStorage = (key) => {
  try { return localStorage.getItem(key) || '' } catch { return '' }
}
const safeSetStorage = (key, value) => {
  try { localStorage.setItem(key, value) } catch { /* 忽略 */ }
}

const currentTenant = ref(safeGetStorage('tenant_id'))
const currentBrand = ref(safeGetStorage('brand_id'))
const tenants = ref([])
const brands = ref([])

/**
 * 租户 / 品牌引导：首次访问时 localStorage 为空，
 * 各业务页面会把空租户传给后端（导致 422 / 500 与空白列表），
 * 这里在应用启动时自动选中首个可用租户及其首个品牌。
 */
const bootstrapTenant = async () => {
  try {
    const res = await api.get('/api/v2/tenants')
    tenants.value = res.data || []
    if (!tenants.value.length) return

    if (!currentTenant.value || !tenants.value.some((t) => t.id === currentTenant.value)) {
      currentTenant.value = tenants.value[0].id
    }

    const brandRes = await api.get(`/api/v2/tenants/${currentTenant.value}/brands`)
    brands.value = brandRes.data || []
    if (!currentBrand.value || !brands.value.some((b) => b.id === currentBrand.value)) {
      currentBrand.value = brands.value[0]?.id || ''
    }
  } catch {
    /* 后端不可用时保持空值，页面自行展示空态 */
  }
}

const pageNames = {
  '/': '品牌首页',
  '/dashboard': '数据驾驶舱',
  '/workflow': '全流程总览',
  '/intent': '意图地图',
  '/knowledge': '知识编辑',
  '/content': '内容库',
  '/monitor': '监测面板',
  '/gallery': '素材图库',
  '/keywords': '蒸馏主词',
  '/social': '自媒体授权',
  '/writing': 'AI 写作',
  '/distribution': '分发管理',
  '/monitoring': '监测看板',
  '/brand-diagnosis': '品牌诊断',
  '/question-creation': '问题创作',
  '/omni-distribution': '全域分发',
  '/ai-tracking': 'AI 追踪',
  '/team-collaboration': '团队协作',
  '/about-mto': '关于 MTO',
  '/geolook': 'GEO 诊断',
  '/geo/siteaudit': '站点审计',
  '/geo/plan': '工单管理',
  '/geo/competitors': '竞品分析',
  '/geo/channels': '渠道地图',
  '/geo/gaps': '缺口诊断',
  '/geo/verify': '验收闭环',
  '/settings': '引擎配置',
  '/web-publishing': '网站优化助手',
}

const currentPageName = computed(() => pageNames[route.path] || 'MTO')

// 当前 GeoLook 项目：子页面（站点审计/工单/验收…）默认操作它
const currentSlug = ref(getStoredSlug())
const syncSlug = () => { currentSlug.value = getStoredSlug() }
watch(() => route.path, syncSlug)
onMounted(() => window.addEventListener(SLUG_CHANGED_EVENT, syncSlug))
onBeforeUnmount(() => window.removeEventListener(SLUG_CHANGED_EVENT, syncSlug))

watch(currentTenant, (v) => { safeSetStorage('tenant_id', v) })
watch(currentBrand, (v) => { safeSetStorage('brand_id', v) })

onMounted(() => {
  document.title = 'MTO — Machine Trust Optimization · 机器信任优化'
  bootstrapTenant()
})
</script>

<style>
.px-separator {
  color: var(--px-text-muted);
  margin: 0 8px;
}

.px-select-inline {
  padding: 4px 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: var(--px-text-dim);
  background: var(--px-bg-deep);
  border: 1px solid var(--px-border);
  outline: none;
  cursor: pointer;
}

.px-select-inline:focus {
  border-color: var(--px-neon-cyan);
}

/* ═══ 侧边栏底部：版权与使用声明 ═══ */
.px-legal-notice {
  margin: 16px 8px 12px;
  padding: 10px 10px 11px;
  background: var(--px-bg-deep);
  border: 1px solid var(--px-border);
  border-left: 3px solid var(--px-neon-yellow);
  font-size: 10px;
  line-height: 1.65;
  color: var(--px-text-muted);
}

.px-legal-title {
  margin-bottom: 6px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--px-neon-yellow);
  text-transform: uppercase;
}

.px-legal-notice p {
  margin: 0 0 6px;
}

.px-legal-notice p:last-child {
  margin-bottom: 0;
}

.px-legal-notice a {
  color: var(--px-text-dim);
  text-decoration: underline;
  text-underline-offset: 2px;
  word-break: break-all;
}

.px-legal-notice a:hover {
  color: var(--px-neon-cyan);
}
</style>
