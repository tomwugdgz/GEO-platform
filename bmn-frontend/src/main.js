import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './styles/pixel.css'

// ── 路由配置
const routes = [
  { path: '/', name: 'story', component: () => import('./views/geo/StoryPage.vue') },
  { path: '/workflow', name: 'workflow', component: () => import('./views/geo/WorkflowView.vue') },
  { path: '/dashboard', name: 'dashboard', component: () => import('./views/geo/Dashboard.vue') },
  { path: '/intent', name: 'intent', component: () => import('./views/geo/IntentMap.vue') },
  { path: '/knowledge', name: 'knowledge', component: () => import('./views/geo/KnowledgeEditor.vue') },
  { path: '/content', name: 'content', component: () => import('./views/geo/ContentList.vue') },
  { path: '/monitor', name: 'monitor', component: () => import('./views/geo/MonitorBoard.vue') },
  // 商业工作流模块
  { path: '/gallery', name: 'gallery', component: () => import('./views/Gallery.vue') },
  { path: '/keywords', name: 'keywords', component: () => import('./views/Keywords.vue') },
  { path: '/social', name: 'social', component: () => import('./views/Social.vue') },
  { path: '/writing', name: 'writing', component: () => import('./views/Writing.vue') },
  { path: '/distribution', name: 'distribution', component: () => import('./views/Distribution.vue') },
  { path: '/monitoring', name: 'monitoring', component: () => import('./views/Monitoring.vue') },
  // 5大高级模块
  { path: '/brand-diagnosis', name: 'brandDiagnosis', component: () => import('./views/BrandDiagnosis.vue') },
  { path: '/question-creation', name: 'questionCreation', component: () => import('./views/QuestionCreation.vue') },
  { path: '/omni-distribution', name: 'omniDistribution', component: () => import('./views/OmniDistribution.vue') },
  { path: '/ai-tracking', name: 'aiTracking', component: () => import('./views/AITracking.vue') },
  { path: '/team-collaboration', name: 'teamCollaboration', component: () => import('./views/TeamCollaboration.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ── 创建应用
const app = createApp(App)
app.use(router)
app.mount('#app')
