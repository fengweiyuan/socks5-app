import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/dashboard'
        },
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue')
        },
        {
          path: 'users',
          name: 'Users',
          component: () => import('@/views/Users.vue')
        },
        {
          path: 'traffic',
          name: 'Traffic',
          component: () => import('@/views/Traffic.vue')
        },
        {
          path: 'logs',
          name: 'Logs',
          component: () => import('@/views/Logs.vue')
        },
        {
          path: 'filters',
          name: 'Filters',
          component: () => import('@/views/Filters.vue')
        },
        {
          path: 'proxy-health',
          name: 'ProxyHealth',
          component: () => import('@/views/ProxyHealth.vue')
        }
      ]
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.token) {
    next('/login')
  } else if (to.path === '/login' && authStore.token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
