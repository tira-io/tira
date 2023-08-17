<template>
  <loading :loading="loading"/>
  <v-container v-if="!loading">
    {{ docker_software_details }}

    {{ resources }}

    {{ datasets }}
  </v-container>

  <run-list :task_id="task_id" :organizer="organizer" :organizer_id="organizer_id" :vm_id="user_id" :docker_software_id="docker_software_id" />
</template>
  
<script lang="ts">
import {Loading, RunList} from "../components"
import { get, reportError, inject_response, extractTaskFromCurrentUrl } from '../utils'

export default {
  name: "existing-docker-submission",
  components: {Loading, RunList},
  props: ['user_id', 'datasets', 'resources', 'docker_software_id', 'organizer', 'organizer_id'],
  data() { return {
    loading: true,
    docker_software_details: {'display_name': 'loading ...', 'user_image_name': 'loading', 'command': 'loading',
                              'description': 'loading ...'},
    task_id: extractTaskFromCurrentUrl()
    }
  },
  beforeMount() {
    this.loading = true
    get('/api/docker-softwares-details/' + this.user_id + '/' + this.docker_software_id)
        .then(inject_response(this, {'loading': false}))
        .catch(reportError("Problem While Loading the details of the software", "This might be a short-term hiccup, please try again. We got the following error: "))
  },
}
</script>
