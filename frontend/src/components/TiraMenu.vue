<template>
    <v-app-bar style="background-color: #323232; color: white;" v-if="showMenu">
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
  
            <v-menu v-if="userinfo !== undefined">
              <template v-slot:activator="{ props }">
                <v-btn icon v-bind="props">
                  <img width="48" height="48" src="https://webis.de/weimar/people/img/silhouette-female.jpg" style="border-radius: 50%;">
                </v-btn>
              </template>
  
              <v-card min-width="300">
          <v-list>
            <v-list-item href="foo"
              prepend-avatar="https://webis.de/weimar/people/img/silhouette-female.jpg"
              subtitle="Short description..."
              :title="userinfo.context.user_id"
            >
              <template v-slot:append>
                <v-btn
                  :class="'text-red'"
                  icon="mdi-heart"
                  variant="text"
                ></v-btn>
              </template>
            </v-list-item>
          </v-list>
  
          <v-divider></v-divider>
  

          <v-list>
            <v-list-item>
                <a href="/foo">{{ userinfo.organizer_teams.length }} Teams</a>
            </v-list-item>

            <v-list-item>
                Role: <a href="/foo">{{ userinfo.role }}</a>
            </v-list-item>
          </v-list>


          <v-divider></v-divider>

          <v-list>
            <v-list-item>
              <v-switch
                color="purple"
                label="Enable messages"
                hide-details
              ></v-switch>
            </v-list-item>
  
            <v-list-item>
              <v-switch
                color="purple"
                label="Enable hints"
                hide-details
              ></v-switch>
            </v-list-item>
          </v-list>
  
          <v-card-actions>
            <v-spacer></v-spacer>
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
import { fetchUserInfo, WellKnownAPI, type UserInfo, logout } from '../utils';
  export default {
    name: "tira-menu",
    data() {
        return {
          userinfo: inject('userinfo') as UserInfo,
          showMenu: false as Boolean
        }
    },
    methods: {
      logout() {logout(this.userinfo.context.user_id)}
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
