<template>
  <v-app>
    <v-app-bar style="background-color: #323232; color: white;">

      <v-container style="max-width: 1110px;" class="d-md-none">
        <v-row>
          <v-col>
            <a href="/">
              <img id="site-logo" src="https://assets.tira.io/tira-icons/tira-banner-120x360-dark.png" alt="TIRA" style="height: 2.667em">
            </a>
          </v-col>

          <v-col class="text-right">
            <v-btn icon>
              <v-icon>mdi-menu</v-icon>
            </v-btn>
          </v-col>
        </v-row>

      </v-container>
      
      <v-container style="max-width: 1110px;" class="d-none d-md-block">
        <v-row>
          <v-col>
        <a href="/">
          <img id="site-logo" src="https://assets.tira.io/tira-icons/tira-banner-120x360-dark.png" alt="TIRA" style="height: 2.667em">
        </a>
      </v-col>

        <v-col class="text-right">
          <v-btn>
            API
          </v-btn>
          <v-btn>
            Forum
          </v-btn>
          <v-btn icon>
            <v-icon>mdi-menu</v-icon>
          </v-btn>

          <v-btn icon>
            <img width="48" height="48" src="https://api.tira.io/user_avatar/api.tira.io/maik_froebe/96/5_2.png" style="border-radius: 50%;">
          </v-btn>
        </v-col>
      </v-row>
      </v-container>
    </v-app-bar>
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
