<template>
  <v-app>
    <v-main>
      <component :is="currentView" />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue'
  import Home from '@/components/Home.vue'
  import Tasks from './Tasks.vue'

  const routes: { [id: string] : any; } =  {
    '/': Home,
    '/tasks': Tasks,
    // TODO: Temporary additional routes for transition form previous TIRA UI version.
    '/frontend-vuetify/': Home,
    '/frontend-vuetify/tasks': Tasks
  }

  const currentPath = ref(window.location.hash)

  const currentView = computed(() => {
    return routes[currentPath.value.slice(1) || '/'] || Home
  })

  onMounted(() => {
    window.addEventListener('hashchange', () => {
      currentPath.value = window.location.hash
    })
  })

</script>
