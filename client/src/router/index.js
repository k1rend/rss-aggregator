import { createRouter, createWebHistory } from 'vue-router';
import AuthView from '../views/AuthView.vue';
import MainView from '../views/MainView.vue';
import { auth } from '../stores/auth';

const routes = [
  {
    path: '/auth',
    name: 'auth',
    component: AuthView,
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    name: 'main',
    component: MainView,
    meta: { requiresAuth: true },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: { name: 'main' },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const isAuthenticated = Boolean(auth.state.token);
  if (to.meta.requiresAuth && !isAuthenticated) {
    return { name: 'auth', query: { redirect: to.fullPath } };
  }
  if (to.name === 'auth' && isAuthenticated) {
    return { name: 'main' };
  }
  return true;
});

export default router;
