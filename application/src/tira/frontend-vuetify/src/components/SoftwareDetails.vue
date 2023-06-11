<template>
  <v-card v-if="!loading" flat class="my-5">
    <h3>Details</h3>
    <v-card-item class="d-md-none" v-if="run && run.link_to_team"><b>Team: </b> <a :href="run.link_to_team"> {{ run.vm_id }}</a></v-card-item>
    <div v-for="(value, key) in run">
      <v-card-item v-if="!fields_to_skip.includes(key + '')"><b>{{  key }} </b>: {{ value }}</v-card-item>
    </div>
    <v-card-item><b>Description: </b> {{details.description}}</v-card-item>
    <v-card-item v-if="details.previous_stage"><b>Previous stage: </b>{{details.previous_stage}}</v-card-item>
  </v-card>

  <v-card v-if="!loading && !details_not_visible" flat class="my-5">
    <h3>Reproduction</h3>
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

  <v-card v-if="details_not_visible" flat class="my-5">
    <h3>Reproduction</h3>
    <v-card-item>TIRA allows to reproduce/replicate submitted software approaches via a single command using Docker. This software is not yet made publicly available.</v-card-item>
    <v-card-item>Please <a :href="contact_organizer">contact</a> the organizer <a :href="link_organizer"> {{ organizer }}</a> or the team <a :href="run.link_to_team">{{ run.vm_id }}</a> if you want to have access to this software or its results, as they can decide (in consultation with each other) to make the software and/or its results publicly available via TIRA.</v-card-item>
  </v-card>

  <loading :loading="loading"/>
</template>

<script lang="ts">
import Loading from './Loading.vue'
import { get, inject_response, extractRole, extractTaskFromCurrentUrl, get_link_to_organizer, get_contact_link_to_organizer } from '../utils';

export default {
  name: "software-details",
  props: ['run', 'organizer', 'organizer_id', 'columns_to_skip'],
  components: {Loading},
  data() {
    return {
      loading: true,
      task_id: extractTaskFromCurrentUrl(),
      details: {'description': 'No description available.', 'previous_stage': null, 'cli_command': '', 'python_command': '', 'docker_command': ''},
      details_not_visible: false,
      role: extractRole(), // Values: user, participant, admin,
      tab: null,
    }
  },
  computed: {
    link_organizer() {return get_link_to_organizer(this.organizer_id);},
    contact_organizer() {return get_contact_link_to_organizer(this.organizer_id);},
    fields_to_skip() {
      let ret = ['vm_id', 'input_software_name', 'published', 'blinded', 'link_to_team']

      for (var i of this.columns_to_skip) {
        ret.push(i.key)
      }

      return ret
    }
  },
  methods: {
    fetchData() {
      this.loading = true
      console.log(this.run)
      get('/task/' + this.task_id + '/vm/' + this.run.vm_id + '/run_details/' + this.run.run_id)
        .then(inject_response(this, {'loading': false}))
        .catch(() => {this.details_not_visible = true; this.loading = false})
      }
  },
  beforeMount() {this.fetchData()},
  watch: {
    run(o, n) {this.fetchData()},
    task_id(o, n) {this.fetchData()},
    columns_to_skip(o, n) {this.fetchData()},
  }
}
</script>
