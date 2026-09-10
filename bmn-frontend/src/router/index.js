/**
 * 全局路由表（唯一真源）
 *
 * 说明：早期版本把路由内联写在 main.js 里，导致这里的配置长期失效、
 * 新增页面（GeoLook 子页面等）无法访问。现统一由本文件维护，
 * main.js 只负责挂载。全部页面走懒加载，保持按页分包。
 */
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // ── 品牌主线 ──
  { path: '/', name: 'story', component: () => import('@/views/geo/StoryPage.vue') },
  { path: '/dashboard', name: 'dashboard', component: () => import('@/views/geo/Dashboard.vue') },
  { path: '/workflow', name: 'workflow', component: () => import('@/views/geo/WorkflowView.vue') },
  { path: '/brand-diagnosis', name: 'brandDiagnosis', component: () => import('@/views/BrandDiagnosis.vue') },

  // ── 内容生产线 ──
  { path: '/intent', name: 'intent', component: () => import('@/views/geo/IntentMap.vue') },
  { path: '/keywords', name: 'keywords', component: () => import('@/views/Keywords.vue') },
  { path: '/knowledge', name: 'knowledge', component: () => import('@/views/geo/KnowledgeEditor.vue') },
  { path: '/content', name: 'content', component: () => import('@/views/geo/ContentList.vue') },
  { path: '/question-creation', name: 'questionCreation', component: () => import('@/views/QuestionCreation.vue') },
  { path: '/gallery', name: 'gallery', component: () => import('@/views/Gallery.vue') },

  // ── 分发与监测 ──
  { path: '/social', name: 'social', component: () => import('@/views/Social.vue') },
  { path: '/writing', name: 'writing', component: () => import('@/views/Writing.vue') },
  { path: '/omni-distribution', name: 'omniDistribution', component: () => import('@/views/OmniDistribution.vue') },
  { path: '/distribution', name: 'distribution', component: () => import('@/views/Distribution.vue') },
  { path: '/ai-tracking', name: 'aiTracking', component: () => import('@/views/AITracking.vue') },
  { path: '/monitoring', name: 'monitoring', component: () => import('@/views/Monitoring.vue') },
  { path: '/monitor', name: 'monitor', component: () => import('@/views/geo/MonitorBoard.vue') },

  // ── 团队协作 ──
  { path: '/team-collaboration', name: 'teamCollaboration', component: () => import('@/views/TeamCollaboration.vue') },

  // ── MTO 概念与共建 ──
  { path: '/about-mto', name: 'aboutMto', component: () => import('@/views/AboutMTO.vue') },

  // ── GeoLook 引擎（原有） ──
  { path: '/geolook', name: 'geolook', component: () => import('@/views/GeoLook.vue') },
  { path: '/web-publishing', name: 'webPublishing', component: () => import('@/views/WebPublishing.vue') },

  // ── GeoLook 引擎（新增模块） ──
  { path: '/geo/siteaudit', name: 'geoSiteAudit', component: () => import('@/views/GeoLookSiteAudit.vue') },
  { path: '/geo/plan', name: 'geoPlan', component: () => import('@/views/GeoLookPlan.vue') },
  { path: '/geo/competitors', name: 'geoCompetitors', component: () => import('@/views/GeoLookCompetitors.vue') },
  { path: '/geo/channels', name: 'geoChannels', component: () => import('@/views/GeoLookChannels.vue') },
  { path: '/geo/gaps', name: 'geoGaps', component: () => import('@/views/GeoLookGaps.vue') },
  { path: '/geo/verify', name: 'geoVerify', component: () => import('@/views/GeoLookVerify.vue') },
  { path: '/settings', name: 'geoSettings', component: () => import('@/views/GeoLookSettings.vue') },

  // ── 兜底：未知路径回到首页 ──
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

export default router
