<template>
  <div class="px-app">
    <!-- ═══ 侧边栏 ═══ -->
    <aside class="px-sidebar">
      <div class="px-logo">
        <div class="px-logo-icon"></div>
        <div>
          <div class="px-logo-text">GEO.AI</div>
          <div class="px-logo-sub">GENERATIVE ENGINE OPTIMIZATION</div>
        </div>
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

      <!-- 分组：团队协作 -->
      <div class="px-group">
        <div class="px-group-title">▹ 团队协作</div>
        <router-link to="/team-collaboration" class="px-nav-item">
          <span class="px-nav-icon">⊛</span> 团队协作
          <span class="px-nav-indicator"></span>
        </router-link>
      </div>
    </aside>

    <!-- ═══ 顶栏 ═══ -->
    <header class="px-topbar">
      <div class="px-crumb">
        <span>GEO</span>
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const currentTenant = ref(localStorage.getItem('tenant_id') || '')
const currentBrand = ref(localStorage.getItem('brand_id') || '')
const tenants = ref([
  { id: 'demo-tenant', name: '演示租户' }
])
const brands = ref([
  { id: 'demo-brand', name: '演示品牌' }
])

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
}

const currentPageName = computed(() => pageNames[route.path] || 'GEO')

watch(currentTenant, (v) => { localStorage.setItem('tenant_id', v) })
watch(currentBrand, (v) => { localStorage.setItem('brand_id', v) })

onMounted(() => {
  document.title = 'GEO.AI — Generative Engine Optimization'
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
</style>
