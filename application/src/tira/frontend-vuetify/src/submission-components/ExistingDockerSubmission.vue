<template>
  <loading :loading="loading"/>
  <v-container v-if="!loading">
    {{ docker_software_details }}

    {{ resources }}

    {{ datasets }}
  </v-container>
</template>
  
<script lang="ts">
import Loading from "../components/Loading.vue"
import { get, reportError, inject_response } from '../utils'

export default {
  name: "existing-docker-submission",
  components: {Loading},
  props: ['user_id', 'datasets', 'resources', 'docker_software_id'],
  data() { return {
    loading: true,
    docker_software_details: {'display_name': 'loading ...', 'user_image_name': 'loading', 'command': 'loading',
                              'description': 'loading ...'}
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
