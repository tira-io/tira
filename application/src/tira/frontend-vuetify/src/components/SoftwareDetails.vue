<template>
  <v-card v-if="!loading" flat class="px-0 mx-0">
    <v-select class="d-md-none" v-model="selectedComponentTab" label="Select item to get more information" :items="tabs"></v-select>
    <v-tabs v-model="component_tab" show-arrows :class="!$vuetify.display.mdAndUp ? 'd-none' : ''">
      <v-tab value="details">Details</v-tab>
      <v-tab value="references">References</v-tab>
      <v-tab value="reproduction">Reproduction</v-tab>
      <v-tab value="actions" class="d-md-none">Actions</v-tab>
    </v-tabs>

    <v-card-text>
      <v-window v-model="component_tab" :touch="{left: () => {}, right: () => {}}">
        <v-window-item value="details">
          <v-card-item class="d-md-none" v-if="run && run.link_to_team"><b>Team: </b>
            <submission-icon :submission="run" />
            <a v-if="role != 'admin'" target="_blank" :href="run.link_to_team">{{ run.vm_id }}</a>
            <v-menu v-if="role == 'admin'" transition="slide-y-transition">
              <template v-slot:activator="{ props }">
                <a href="javascript:void(0)" v-bind="props">{{ run.vm_id }}</a>
              </template>
              <v-list>
                <v-list-item key="team-page"><a target="_blank" :href="run.link_to_team">Team Page of {{ run.vm_id }}</a></v-list-item>
                <v-list-item key="submission-page"><a target="_blank" :href="'/submit/' + task_id + '/user/' + run.vm_id">Submission Page of {{ run.vm_id }}</a></v-list-item>
              </v-list>
            </v-menu>  
          </v-card-item>
          <div v-for="(value, key) in run">
            <v-card-item v-if="!fields_to_skip.includes(key + '')"><b>{{  key }} </b>: {{ value }}</v-card-item>
          </div>
          <v-card-item><b>Description: </b> {{description}}</v-card-item>
          <v-card-item v-if="previous_stage"><b>Previous stage: </b>{{previous_stage}}</v-card-item>
        </v-window-item>

        <v-window-item value="references">
          <v-dialog transition="dialog-bottom-transition" width="auto">
            <template v-slot:activator="{ props }">
              <v-btn class="pa0 ma0" v-bind="props">Show Bibtex</v-btn>
            </template>
            <template v-slot:default="{ isActive }">
              <v-card>
                <v-toolbar color="primary" :title="'Relevant Bibtex-Entries for run ' + run.run_id"/>
                <v-code tag="pre">{{ references_bibtex }}</v-code>
              </v-card>
            </template>
          </v-dialog>
          <div v-html="references_markdown"></div>
        </v-window-item>

        <v-window-item value="reproduction" v-if="cli_command && python_command && docker_command">
          <v-tabs v-model="tab" show-arrow>
            <v-tab value="one">CLI command</v-tab>
            <v-tab value="two">Python command</v-tab>
            <v-tab value="three">Docker command</v-tab>
          </v-tabs>

          <v-card-text>
            <v-window v-model="tab" :touch="{left: () => {}, right: () => {}}">
              <v-window-item value="one">
                <tira-data-export :run_export="tira_run_export" />
                <v-code tag="pre" > {{ cli_command }}</v-code>
              </v-window-item>

              <v-window-item value="two">
                <tira-data-export :run_export="tira_run_export" />
                <v-code tag="pre" > {{ python_command }}</v-code>
              </v-window-item>

              <v-window-item value="three">
                <tira-data-export :run_export="tira_run_export" />
                <v-code tag="pre" > {{ docker_command }}</v-code>
              </v-window-item>
            </v-window>
          </v-card-text>
        </v-window-item>

        <v-window-item value="reproduction"  v-if="!cli_command || !python_command || !docker_command">
          <div class="ma-2">
            <v-card-item>TIRA allows to reproduce/replicate submitted software approaches via a single command using Docker. This software is not yet made publicly available.</v-card-item>
            <v-card-item>Please <a :href="contact_organizer">contact</a> the organizer <a :href="link_organizer"> {{ organizer }}</a> or the team <a :href="run.link_to_team">{{ run.vm_id }}</a> if you want to have access to this software or its results, as they can decide (in consultation with each other) to make the software and/or its results publicly available via TIRA.</v-card-item>
          </div>
        </v-window-item>

        <v-window-item class="d-md-none" value="actions">
          <div class="ma-2"><run-actions :run="run" @reviewRun="(i: any) => $emit('review-run', i)"/></div>
        </v-window-item >
      </v-window>
    </v-card-text>
  </v-card>

  <loading :loading="loading"/>
</template>

<script lang="ts">
import Loading from './Loading.vue'
import TiraDataExport from './TiraDataExport.vue'
import RunActions from './RunActions.vue'
import SubmissionIcon from "./SubmissionIcon.vue"
import { get, inject_response, extractRole, extractTaskFromCurrentUrl, get_link_to_organizer, get_contact_link_to_organizer } from '../utils';

export default {
  name: "software-details",
  props: ['run', 'organizer', 'organizer_id', 'columns_to_skip'],
  emits: ['review-run'],
  components: {Loading, TiraDataExport, RunActions, SubmissionIcon},
  data() {
    return {
      loading: true,
      task_id: extractTaskFromCurrentUrl(),
      description: 'No description available.',
      previous_stage: null,
      cli_command: '',
      python_command: '',
      docker_command: '',
      tira_run_export: '',
      references_markdown: 'Loading...',
      references_bibtex: 'Loading...',
      details_not_visible: false,
      role: extractRole(), // Values: user, participant, admin,
      tabs: ['details', 'references', 'reproduction', 'actions'],
      selectedComponentTab: 'details',
      tab: '',
      component_tab: '',
    }
  },
  computed: {
    link_organizer() {return get_link_to_organizer(this.organizer_id);},
    contact_organizer() {return get_contact_link_to_organizer(this.organizer_id);},
    fields_to_skip() {
      let ret = ['vm_id', 'input_software_name', 'published', 'blinded', 'link_to_team', 'link_results_download', 'link_run_download', 'link_serp', 'is_upload', 'is_software', 'dataset_id', 'selectable', 'review_state', 'owned_by_user', 'link_code']

      for (var i of this.columns_to_skip) {
        ret.push(i.key)
      }

      return ret
    }
  },
  methods: {
    fetchData() {
      this.loading = true
      get('/task/' + this.task_id + '/vm/' + this.run.vm_id + '/run_details/' + this.run.run_id)
        .then(inject_response(this, {'loading': false}))
        .catch(() => {this.details_not_visible = true; this.loading = false})
    },
    updateTab() {
      this.component_tab = this.selectedComponentTab
    }
  },
  beforeMount() {this.fetchData()},
  watch: {
    run(o, n) {this.fetchData()},
    task_id(o, n) {this.fetchData()},
    columns_to_skip(o, n) {this.fetchData()},
    selectedComponentTab(o, n) {this.updateTab()}
  }
}
</script>
