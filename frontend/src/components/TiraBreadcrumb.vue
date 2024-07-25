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
      var ret = [{title: 'TIRA', disabled: false, href: '/'}, {title: 'Tasks', disabled: false, href: '/tasks'}]
      let task = extractTaskFromCurrentUrl()

      if (task) {
        ret.push({title: task, disabled: false, href: '/task-overview/' + task})
      }

      return ret;
    }
  },
}
</script>
