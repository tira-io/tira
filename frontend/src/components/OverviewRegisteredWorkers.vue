<template>
    <loading :loading="loading"/>
    <v-data-table v-if="!loading" :headers="table_headers" :items="active_workers" density="compact"/>
</template>
  
<script lang="ts">
import { inject } from 'vue'

import { Loading } from '.'
import { get, reportError, inject_response} from '../utils'

export default {
  name: "overview-registered-workers",
  components: {Loading},
  data() { return {
    loading: true,
    active_workers:[],
    table_headers: [
      { title: 'Worker', key: 'name'},
      { title: 'Queues', key: 'queues'},
      { title: 'Running Tasks', key: 'tasks'},
      { title: 'Uptime', key: 'uptime'},
      { title: 'Jobs', key: 'total'},
    ],
  }},
   beforeMount() {
    this.loading = true
    get(inject("REST base URL")+'/v1/admin/registered-workers/admin')
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem While Loading the rgistered workers", "This might be a short-term hiccup, please try again. We got the following error: "))
  }
}
</script>
