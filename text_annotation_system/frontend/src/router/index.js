import { createRouter, createWebHistory } from 'vue-router'
import SchemeList from '../views/SchemeList.vue'
import SchemeDetail from '../views/SchemeDetail.vue'
import Annotate from '../views/Annotate.vue'
import TaskMonitor from '../views/TaskMonitor.vue'
import Config from '../views/Config.vue'

const routes = [
  { path: '/', redirect: '/schemes' },
  { path: '/schemes', name: 'SchemeList', component: SchemeList },
  { path: '/schemes/:id', name: 'SchemeDetail', component: SchemeDetail },
  { path: '/annotate', name: 'Annotate', component: Annotate },
  { path: '/tasks', name: 'TaskMonitor', component: TaskMonitor },
  { path: '/config', name: 'Config', component: Config },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
