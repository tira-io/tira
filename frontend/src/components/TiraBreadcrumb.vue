<template>
  <v-breadcrumbs :items="items" :class="!$vuetify.display.mdAndUp ? 'px-3' : 'px-10'">
    <template v-slot:title="{ item }">
      {{ item.title.toUpperCase() }}
    </template>
  </v-breadcrumbs>
</template>

<script lang="ts">
import { extractTaskFromCurrentUrl } from '../utils'
export default {
  name: "tira-breadcrumb",
  computed: {
    items() {
      var ret = [{title: 'TIRA', disabled: false, href: '/'}]

      if (this.$route.path.startsWith('/datasets')) {
        ret.push({title: 'Datasets', disabled: false, href: '/datasets'})
      } else if (this.$route.path.startsWith('/systems')) {
        ret.push({title: 'Systems', disabled: false, href: '/systems'})
        if (this.$route.params.team) {
          ret.push({title: this.$route.params.team as string, disabled: false, href: '/systems/' + this.$route.params.team})

          if (this.$route.params.system) {
            ret.push({title: this.$route.params.system as string, disabled: false, href: '/systems/' + this.$route.params.team + '/' + this.$route.params.system})
          }
        }
      } else {
        ret.push({title: 'Tasks', disabled: false, href: '/tasks'})
        let task = extractTaskFromCurrentUrl()

        if (task) {
          ret.push({title: task, disabled: false, href: '/task-overview/' + task})
        }
      }

      return ret;
    }
  },
}
</script>
