import { createRouter, createWebHistory } from 'vue-router'
import StoryPage from '@/views/geo/StoryPage.vue'
import WorkflowView from '@/views/geo/WorkflowView.vue'
import Dashboard from '@/views/geo/Dashboard.vue'
import IntentMap from '@/views/geo/IntentMap.vue'
import KnowledgeEditor from '@/views/geo/KnowledgeEditor.vue'
import ContentList from '@/views/geo/ContentList.vue'
import MonitorBoard from '@/views/geo/MonitorBoard.vue'
import Gallery from '@/views/Gallery.vue'
import Keywords from '@/views/Keywords.vue'
import Social from '@/views/Social.vue'
import Writing from '@/views/Writing.vue'
import Distribution from '@/views/Distribution.vue'
import Monitoring from '@/views/Monitoring.vue'

const routes = [
  { path: '/', name: 'Story', component: StoryPage },
  { path: '/workflow', name: 'Workflow', component: WorkflowView },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard },
  { path: '/intent', name: 'Intent', component: IntentMap },
  { path: '/knowledge', name: 'Knowledge', component: KnowledgeEditor },
  { path: '/content', name: 'Content', component: ContentList },
  { path: '/monitor', name: 'Monitor', component: MonitorBoard },
  { path: '/gallery', name: 'Gallery', component: Gallery },
  { path: '/keywords', name: 'Keywords', component: Keywords },
  { path: '/social', name: 'Social', component: Social },
  { path: '/writing', name: 'Writing', component: Writing },
  { path: '/distribution', name: 'Distribution', component: Distribution },
  { path: '/monitoring', name: 'Monitoring', component: Monitoring }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
