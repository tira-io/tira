<template>
  <tira-breadcrumb/>
  <div class=" my-5 px-10">
  <div class="my-5">
    <h2><b>{{this.user_id}}</b> on Task: {{this.task_id}}</h2>
  </div>
    <RunningProcesses class="mb-12"/>
  <v-tabs
    v-model="tab"
    fixed-tabs
  >
    <v-tab value="upload-submission">
      <v-icon class="mr-4">mdi-folder-upload-outline</v-icon>
      Upload Submission
    </v-tab>
    <v-tab value="docker-submission">
      <v-icon class="mr-4">mdi-docker</v-icon>
      Docker Submission
    </v-tab>
    <v-tab value="vm-submission">
      <v-icon class="mr-4">mdi-code-json</v-icon>
      Virtual Machine Submission
    </v-tab>
  </v-tabs>
  <v-window v-model="tab">
      <v-window-item value="upload-submission">
        <upload-submission :organizer="organizer" :organizer_id="organizer_id"/>
      </v-window-item>
    <v-window-item value="docker-submission">
        <docker-submission :organizer="organizer" :organizer_id="organizer_id" step_prop="step-1"/>
      </v-window-item>
    <v-window-item value="vm-submission">
        <virtual-machine-submission :organizer="organizer" :organizer_id="organizer_id" />
      </v-window-item>
    </v-window>
    </div>
</template>

<script>
import DockerSubmission from "@/submission-components/DockerSubmission.vue";
import VirtualMachineSubmission from "@/submission-components/VirtualMachineSubmission.vue";
import UploadSubmission from "@/submission-components/UploadSubmission";
import RunningProcesses from "@/submission-components/RunningProcesses.vue";
import { TiraBreadcrumb } from './components'

import { extractSubmissionTypeFromCurrentUrl, extractCurrentStepFromCurrentUrl, extractTaskFromCurrentUrl, extractUserFromCurrentUrl, extractRole } from "@/utils";
export default {
  name: "run-upload",
  components: {UploadSubmission, TiraBreadcrumb, VirtualMachineSubmission, DockerSubmission, RunningProcesses},
  data() {
    return {
        tab: extractSubmissionTypeFromCurrentUrl(),
        step: extractCurrentStepFromCurrentUrl(),
        task_id: extractTaskFromCurrentUrl(),
        user_id: extractUserFromCurrentUrl(),
        role: extractRole(), // Values: guest, user, participant, admin
        task: { "task_id": "", "task_name": "", "task_description": "",
                "organizer": "", "organizer_id": "", "web": "", "year": "",
                "dataset_count": 0, "software_count": 0, "teams": 0
        },
    }
  },
  methods: {
    updateUrlToSelectedSubmissionType() {
      this.$router.replace({name: 'submission', params: {submission_type: this.tab}})
    }
  },
  watch: {
    tab(old_value, new_value) {
      this.updateUrlToSelectedSubmissionType()
    }
  },
}
</script>