<template>
  <tira-breadcrumb/>
  <div :class="!$vuetify.display.mdAndUp ? 'my-0 px-3' : 'my-5 px-10'">
  <div class="my-5">
    <h2><b>{{this.user_id}}</b> on Task: {{this.task_id}}</h2>
  </div>

  <loading :loading="loading" />
  <div v-if="!loading">
  <running-processes class="mb-12" ref="running-processes"/>
  
  <v-tabs v-model="tab" class="d-none d-md-block"  fixed-tabs >
    <v-tab :value="v.id" v-for="v in all_tabs">
      <v-icon class="mr-4">{{v.icon}}</v-icon> {{v.title}}
    </v-tab>
  </v-tabs>
  <v-row class="d-md-none">
    <v-col cols="12"><v-select v-model="tab" :items="all_tabs" variant="outlined" block item-title="title" item-value="id" label="Submission"/></v-col>
  </v-row>


  <v-window v-model="tab" :touch="{left: null, right: null}">
      <v-window-item value="code-submission">
        <code-submission :organizer="organizer" :organizer_id="organizer_id" :user_id="user_id" :task_id="task_id" :is_ir_task="is_ir_task"/>
      </v-window-item>
      <v-window-item value="docker-submission">
        <docker-submission :organizer="organizer" :organizer_id="organizer_id" :step_prop="step === null ? '' : step" :is_ir_task="is_ir_task" @refresh_running_submissions="refresh_running_submissions()"/>
      </v-window-item>
      <v-window-item value="upload-submission">
        <upload-submission :organizer="organizer" :organizer_id="organizer_id"  @refresh_running_submissions="refresh_running_submissions()"/>
      </v-window-item>
      <v-window-item value="upload-submission-simplified">
        <simplified-upload-submission :organizer="organizer" :organizer_id="organizer_id"  @refresh_running_submissions="refresh_running_submissions()" simplified-upload="true"/>
      </v-window-item>
      <v-window-item value="upload-models">
        <upload-models :organizer="organizer" :organizer_id="organizer_id"/>
      </v-window-item>
    </v-window>
    </div>
    </div>
</template>

<script>
import { inject } from 'vue'

import DockerSubmission from "@/submission-components/DockerSubmission.vue";
import CodeSubmission from "@/submission-components/CodeSubmission.vue";
import UploadSubmission from "@/submission-components/UploadSubmission";
import SimplifiedUploadSubmission from './submission-components/SimplifiedUploadSubmission.vue';
import UploadModels from "@/submission-components/UploadModels";
import RunningProcesses from "@/submission-components/RunningProcesses.vue";
import { TiraBreadcrumb } from './components'
import Loading from './components/Loading.vue';

import { extractSubmissionTypeFromCurrentUrl, extractCurrentStepFromCurrentUrl, extractTaskFromCurrentUrl, extractUserFromCurrentUrl, get, inject_response, reportError } from "@/utils";
export default {
  name: "run-upload",
  components: {UploadSubmission, SimplifiedUploadSubmission, Loading, UploadModels, TiraBreadcrumb, CodeSubmission, DockerSubmission, RunningProcesses},
  data() {
    return {
        tab: extractSubmissionTypeFromCurrentUrl(),
        step: extractCurrentStepFromCurrentUrl(),
        task_id: extractTaskFromCurrentUrl(),
        user_id: extractUserFromCurrentUrl(),
        is_ir_task: false, task_name: "", task_description: "",
        organizer: "", organizer_id: "", web: "",
        submission_tabs: [],
        all_available_tabs: [
          {'id': 'code-submission', 'title': 'Code Submissions', 'icon': 'mdi-code-json'},
          {'id': 'docker-submission', 'title': 'Docker Submissions', 'icon': 'mdi-docker'},
          {'id': 'upload-submission', 'title': 'Run Uploads', 'icon': 'mdi-folder-upload-outline'},
          {'id': 'upload-submission-simplified', 'title': 'Run Uploads', 'icon': 'mdi-folder-upload-outline'},
          {'id': 'upload-models', 'title': 'Upload Models', 'icon': 'mdi-folder-upload-outline'}
        ]
    }
  },
  beforeMount() {
    get(inject("REST base URL")+'/api/task/' + this.task_id)
            .then(inject_response(this, {}, true, 'task'))
            .catch(reportError("Problem loading the data of the task.", "This might be a short-term hiccup, please try again. We got the following error: "))
  },
  computed: {
    loading() { return this.organizer == ''},
    all_tabs() {
      const ret = []
      const available_submission_tabs = this.all_available_tabs.reduce((acc, item) => {
        acc[item.id] = item;
        return acc;
      }, {});

      let tabs = this.submission_tabs

      if (!tabs || tabs.length == 0) {
        tabs = []
        for (let i of this.all_available_tabs) {
          if (i.id == 'upload-submission-simplified') {
            continue
          }
          tabs.push(i.id)
        }
      }

      for (let i of tabs) {
        ret.push(available_submission_tabs[i])
      }

      if (this.tab == null) {
        this.tab = tabs[0]
      }

      this.updateUrlToSelectedSubmissionType()

      return ret
    }
  },
  methods: {
    updateUrlToSelectedSubmissionType() {
      this.$router.replace({name: 'submission', params: {submission_type: this.tab}})
    },
    refresh_running_submissions() {
      this.$refs['running-processes'].pollRunningSoftware('True')
    }
  },
  watch: {
    tab(old_value, new_value) {
      this.updateUrlToSelectedSubmissionType()
    }
  },
}
</script>
