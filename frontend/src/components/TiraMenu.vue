<template>
    <v-app-bar style="background-color: #323232; color: white;" v-if="showMenu">
        <v-container style="max-width: 1110px;" class="d-md-none">
          <v-row>
            <v-col>
              <router-link to="/">
                <img id="site-logo" src="https://assets.tira.io/tira-icons/tira-archive-banner-120x360-dark.png" alt="TIRA" style="height: 2.667em">
              </router-link>
            </v-col>

            <v-col class="text-right">
              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn v-bind="props" class="text-red">
                    <v-icon>mdi-menu</v-icon>Archive
                  </v-btn>
                </template>
                <v-card min-width="300">
                <v-list>
                  <v-list-item href="https://archive.tira.io" prepend-avatar="https://webis.de/weimar/people/img/silhouette-female.jpg" subtitle="Read only archive of TIRA." title="archive.tira.io">
                    <template v-slot:append>
                      <v-btn icon="mdi-database" variant="text"/>
                    </template>
                  </v-list-item>
                </v-list>

                <v-divider></v-divider>
                <p style="max-width: 400px;" class="pa-2">
                  You are at <a href="https://archive.tira.io">archive.tira.io</a> which hosts a read-only archive of previous shared tasks. Visit <a href="https://www.tira.io">www.tira.io</a> to make submissions.
                </p>

                <v-card-actions>
                  <v-spacer/>
                  <v-btn variant="text">Cancel</v-btn>
                  <v-btn color="primary" v-if="userinfo.role !== 'guest'" variant="text" @click="logout">Logout</v-btn>
                  <v-btn color="primary" v-if="userinfo.role === 'guest'" variant="text" href="https://www.tira.io/login" target="_blank">Login</v-btn>
                </v-card-actions>
              </v-card>
              </v-menu>
            </v-col>
          </v-row>

        </v-container>
        
        <v-container style="max-width: 1110px;" class="d-none d-md-block">
          <v-row>
            <v-col>
            <router-link to="/">
              <img id="site-logo" src="https://assets.tira.io/tira-icons/tira-archive-banner-120x360-dark.png" alt="TIRA" style="height: 2.667em">
            </router-link>
          </v-col>
  
          <v-col class="text-right">
            <v-btn href="https://pypi.org/project/tira/">API</v-btn>
            <v-btn href="https://www.tira.io/categories">Forum</v-btn>
            <v-menu>
              <template v-slot:activator="{ props }">
                <v-btn v-bind="props">
                  <v-icon>mdi-menu</v-icon>Archive
                </v-btn>
              </template>

              <v-card min-width="300">
                <v-list>
                  <v-list-item href="https://archive.tira.io" prepend-avatar="https://webis.de/weimar/people/img/silhouette-female.jpg" subtitle="Read only archive of TIRA." title="archive.tira.io">
                    <template v-slot:append>
                      <v-btn icon="mdi-database" variant="text"/>
                    </template>
                  </v-list-item>
                </v-list>

                <v-divider></v-divider>
                
                <p style="max-width: 400px;" class="pa-2">
                  You are at <a href="https://archive.tira.io">archive.tira.io</a> which hosts a read-only archive of previous shared tasks. Visit <a :href="tira_href">www.tira.io</a> to make submissions.
                </p>
                
                <v-card-actions>
                  <v-spacer/>
                  <v-btn variant="text">Cancel</v-btn>
                  <v-btn color="primary" v-if="userinfo.role !== 'guest'" variant="text" @click="logout">Logout</v-btn>
                  <v-btn color="primary" v-if="userinfo.role === 'guest'" variant="text" href="https://www.tira.io/login" target="_blank">Login</v-btn>
                </v-card-actions>
              </v-card>
            </v-menu>
          </v-col>
        </v-row>
        </v-container>
    </v-app-bar>
</template>

<script lang="ts">
 import { inject } from 'vue';
import { WellKnownAPI, type UserInfo, logout } from '../utils';
  export default {
    name: "tira-menu",
    data() {
        return {
          userinfo: inject('userinfo') as UserInfo,
          showMenu: false as Boolean
        }
    },
    computed: {
      tira_href() {return 'https://www.tira.io' + location.pathname}
    },
    methods: {
      logout() {logout(this.userinfo.context.user_id)},
    },
    beforeMount() {
      let wellKnown = inject('.wellKnown') as WellKnownAPI
      this.$data.showMenu = !wellKnown.disraptorURL.toLowerCase().includes(location.host.toLowerCase())

      if (this.$data.showMenu) {
        this.$data.userinfo = inject('userinfo') as UserInfo
      }
    }
}
</script>
