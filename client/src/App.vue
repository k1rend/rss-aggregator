<script setup>
import { watch } from 'vue';
import { useRouter } from 'vue-router';
import { auth } from './stores/auth';

const router = useRouter();


watch(
  () => auth.state.token,
  (token) => {
    if (token) return;
    const route = router.currentRoute.value;
    if (route.meta.requiresAuth) {
      router.replace({ name: 'auth', query: { redirect: route.fullPath } });
    }
  }
);
</script>

<template>
  <router-view />
</template>
