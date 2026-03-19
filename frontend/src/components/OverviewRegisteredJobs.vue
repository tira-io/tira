<template>
    <loading :loading="loading"/>
    <v-data-table v-if="!loading" :headers="table_headers" :items="jobs" density="compact"/>
</template>
  
<script lang="ts">
import { inject } from 'vue'

import { Loading } from '.'
import { get, reportError, inject_response} from '../utils'

export default {
  name: "overview-registered-jobs",
  components: {Loading},
  props: ['task'],
  data() { return {
    loading: true,
    jobs:[],
    table_headers: [
      { title: 'UUID', key: 'uuid'},
      { title: 'Task', key: 'task'},
      { title: 'Team', key: 'vm_id'},
      { title: 'Dataset', key: 'dataset_id'},
      { title: 'Details', key: 'details'},
    ],
  }},
   beforeMount() {
    this.loading = true
    get(inject("REST base URL")+'/v1/admin/active-jobs/admin/' + this.task)
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem While Loading the rgistered workers", "This might be a short-term hiccup, please try again. We got the following error: "))
  }
}
</script>
