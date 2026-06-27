import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomePage.vue'),
    },
    {
      path: '/workspace',
      name: 'workspace',
      component: () => import('../views/WorkspacePage.vue'),
    },
    {
      path: '/result/:id',
      name: 'result',
      component: () => import('../views/ResultPage.vue'),
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('../views/HistoryPage.vue'),
    },
  ],
})

export default router
