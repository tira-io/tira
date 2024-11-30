/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Components
import App from './App.vue'
import IrComponents from './IrComponents.vue'
import Home from './Home.vue'
import Tasks from './Tasks.vue'
import Tirex from './Tirex.vue'
import ClaimSubmission from './ClaimSubmission.vue'
import Datasets from './Datasets.vue'
import Systems from './Systems.vue'
import SystemDetails from './SystemDetails.vue'
import TaskOverview from './TaskOverview.vue'
import RunUpload from './RunUpload.vue'
import tiraConf from './tira.conf'
import { fetchWellKnownAPIs, fetchUserInfo, fetchServerInfo } from './utils';
import { useDisplay } from 'vuetify'

export function is_mobile() {
  const { mobile } = useDisplay()
  return mobile.value
}

// Composables
import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'

// Plugins
import { registerPlugins } from '@/plugins'

export default function register_app() {
  const app_selector = '#app'

  const app_elem = document.querySelector(app_selector)
  if (app_elem && '__vue_app__' in app_elem && app_elem.__vue_app__) {
    return;
  }

  const routes = [
    { path: '/', component: Home },
    { path: '/tasks', component: Tasks },
    { path: '/datasets', component: Datasets },
    { path: '/claim-submission/:uuid', component: ClaimSubmission },
    { path: '/systems', component: Systems },
    { path: '/systems/:team?', component: Systems },
    { path: '/systems/:team/:system', component: SystemDetails },
    { path: '/task-overview/:task_id?/:dataset_id?', component: TaskOverview },
    { path: '/task/:task_id?/:dataset_id?', component: TaskOverview },
    { path: '/submit/:task/user/:user/:submission_type?/:selected_step?', name: 'submission', component: RunUpload },
    { path: '/tirex/components/:component_types?/:focus_types?/:search_query?', name: 'tirex', component: IrComponents },
    { path: '/tirex/:pathMatch(.*)*', component: Tirex },

    // Fallback: everything matches to home.
    { path: '/:pathMatch(.*)*', component: Home },
  ]

  console.log(tiraConf.rest_endpoint)
  fetchWellKnownAPIs(tiraConf.rest_endpoint).then(wellKnown => { console.log(tiraConf.rest_endpoint + ' -> ' + wellKnown) })
  fetchWellKnownAPIs('https://tira.io').then(wellKnown => { console.log('https://tira.io -> ' + wellKnown) })

  fetchWellKnownAPIs(tiraConf.rest_endpoint).then(wellKnown => {
    if (wellKnown.archived.toLowerCase().includes('://' + location.host.toLowerCase())) {
      console.log('This client only works on the archived backup of TIRA.')
      wellKnown.grpc = wellKnown.archived
      wellKnown.api = wellKnown.archived
    }

    fetchUserInfo(wellKnown.api).then(userInfo => {
      fetchServerInfo(wellKnown.api).then(serverInfo => {
        const router = createRouter({
          history: createWebHistory(),
          routes: routes,
        })

        const app = createApp(App)

        app.provide("gRPC base URL", wellKnown.grpc)
        app.provide("REST base URL", wellKnown.api)
        app.provide("userinfo", userInfo)
        app.provide(".wellKnown", wellKnown)
        app.provide("Archived base URL", wellKnown.archived)
        app.provide("serverInfo", serverInfo)
        app.use(router)

        registerPlugins(app)
        app.mount(app_selector)
      })
    })
  })

}

declare global { interface Window { register_app: any; push_message: any } }
window.register_app = register_app;

register_app()
