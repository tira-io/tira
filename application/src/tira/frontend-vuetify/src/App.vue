<template>
  <v-app>
    <v-main class="position-relative">
      <tira-alert class="position-absolute"/>
      <router-view></router-view>
    </v-main>
  </v-app>
</template>

<style>
  #app main{
    overflow-y: hidden;
  }
  #app input {
    margin: 0px !important;
    padding: 0px !important;
    left: auto !important;
  }
  .v-overlay-container input {
    margin: 0px !important;
    padding: 0px !important;
    left: auto !important;
  }
  #app #docker-submission-readonly-input input {
    padding: 10px 0 0 10px !important;
    color: #BDBDBD;
  }

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

<script lang="ts">
import TiraAlert from './components/TiraAlert.vue'
export default {
  name: "app",
  components: {TiraAlert},
}
</script>
