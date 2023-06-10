<template>
  <v-app>
    <v-main>
      <component :is="currentView" />
    </v-main>
  </v-app>
</template>

<style>
  #app #task-search input {
    border: none !important;
    outline: none !important;
    margin: 0px !important;
    padding: 22px 6px 6px 6px !important;
  }
  #app #dataset-select input {
    border: none !important;
    outline: none !important;
    margin: 0px !important;
    padding: 0px 6px 6px 6px !important;
  }
  #app h3 {
    margin: 0px !important;
  }
</style>

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue'
  import Home from './Home.vue'
  import Tasks from './Tasks.vue'
  import TaskOverview from './TaskOverview.vue'
  import RunUpload from './RunUpload.vue'

  const routes: { [id: string] : any; } =  {
    '/': Home,
    '/tasks': Tasks,
    '/task-overview': TaskOverview,
    '/run-upload': RunUpload,
    // TODO: Temporary additional routes for transition form previous TIRA UI version.
    '/frontend-vuetify/': Home,
    '/frontend-vuetify/tasks': Tasks,
    '/frontend-vuetify/task-overview': TaskOverview,
    '/frontend-vuetify/run-upload': RunUpload
  }

  const currentPath = ref(window.location.hash)
  const currentLocation = ref(window.location.pathname)

  const currentView = computed(() => {
    console.log('Path changed: ' + currentLocation.value + ' or hash changed: ' + currentPath)
    if (currentLocation.value.startsWith('/task-overview')) {
      return TaskOverview
    }

    let p = currentPath.value.slice(1) 

    if (p.startsWith('/task-overview') || p.startsWith('/frontend-vuetify/task-overview')) {
      return TaskOverview
    }

    return routes[p || '/'] || Home
  })

  onMounted(() => {
    window.addEventListener('hashchange', () => {
      currentPath.value = window.location.hash
      currentLocation.value = window.location.pathname
    });
    window.addEventListener('popstate', () => {
      currentPath.value = window.location.hash
      currentLocation.value = window.location.pathname
    });
  })
</script>
