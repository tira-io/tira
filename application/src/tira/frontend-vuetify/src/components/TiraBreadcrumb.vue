<template>
  <v-breadcrumbs :items="items">
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
      var ret = [{title: 'TIRA', disabled: false, href: '/frontend-vuetify/'}, {title: 'Tasks', disabled: false, href: '/frontend-vuetify/#/tasks'}]
      
      let task = extractTaskFromCurrentUrl()

      if (task) {
        ret.push({title: task, disabled: false, href: '/task-overview/' + task})
      }

      return ret;
    }
  },
}
</script>
