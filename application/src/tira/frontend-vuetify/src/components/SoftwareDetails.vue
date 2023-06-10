<template>
  <v-card v-if="!loading" flat class="my-5">
    <v-card-item><b>Description: </b> {{details.description}}</v-card-item>
    <v-card-item><b>Previous stage: </b>{{details.previous_stage}}</v-card-item>
    <v-tabs v-model="tab">
      <v-tab value="one">CLI command</v-tab>
      <v-tab value="two">Python command</v-tab>
      <v-tab value="three">Docker command</v-tab>
    </v-tabs>
  
    <v-card-text>
      <v-window v-model="tab">
        <v-window-item value="one">
          <v-code>{{ details.cli_command }}</v-code>
        </v-window-item>
      
        <v-window-item value="two">
          <v-code>{{ details.python_command }}</v-code>
        </v-window-item>
  
        <v-window-item value="three">
          <v-code>{{ details.docker_command }}</v-code>
        </v-window-item>
      </v-window>
    </v-card-text>
  </v-card>

  <loading :loading="loading"/>
</template>

<script lang="ts">
import Loading from './Loading.vue'

export default {
  name: "software-details",
  props: ['software_id'],
  components: {Loading},
  data() {
    return {
      loading: true,
      details: {'description': '', 'previous_stage': '', 'cli_command': '', 'python_command': '', 'docker_command': ''},
      role: 'guest', // Values: user, participant, admin,
      tab: null,
    }
  },
  beforeMount() {
    setTimeout(()  => {
      this.details = {
        'description': 'Description of the run',
        'previous_stage': 'Previous stages of the run',
        'cli_command': '--cli command',
        'python_command': 'python3 run tira',
        'docker_command': 'docker exec -it container bash',
      }
      this.loading = false
    }, 1000)
  }
}
</script>
