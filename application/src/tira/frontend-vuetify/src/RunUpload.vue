<template>
  <div class="px2 my-10 ">
  <!--
  <div class="w-75 mx-auto my-5">
  <div class="my-5">
    <h2><b>{{task.userVmsForTask}}</b> on Task: {{task.task_id}}</h2>
  </div>
  -->

  <v-tabs
    v-model="tab"
    fixed-tabs
  >
    <v-tab value="uploadSubmission">
      <v-icon class="mr-4">mdi-folder-upload-outline</v-icon>
      Upload Submission
    </v-tab>
    <v-tab value="dockerSubmission">
      <v-icon class="mr-4">mdi-docker</v-icon>
      Docker Submission
    </v-tab>
    <v-tab value="virtualMachineSubmission">
      <v-icon class="mr-4">mdi-code-json</v-icon>
      Virtual Machine Submission
    </v-tab>
  </v-tabs>
  <v-window v-model="tab">
      <v-window-item value="uploadSubmission">
        <UploadSubmission/>
      </v-window-item>
    <v-window-item value="dockerSubmission">
        <DockerSubmission/>
      </v-window-item>
    <v-window-item value="virtualMachineSubmission">
        <VirtualMachineSubmission/>
      </v-window-item>
    </v-window>
    <div class="my-5">
      <ExplainationToggle />
    </div>
    </div>
</template>

<script>
// import DeleteConfirm from '../elements/delete-confirm'
// import { get, submitPost } from "../../utils/getpost"
import DockerSubmission from "@/submission-components/DockerSubmission.vue";
import VirtualMachineSubmission from "@/submission-components/VirtualMachineSubmission.vue";
import UploadSubmission from "@/submission-components/UploadSubmission";
import ExplainationToggle from "@/submission-components/ExplainationToggle";
export default {
  name: "run-upload",
  components: {UploadSubmission, VirtualMachineSubmission, DockerSubmission, ExplainationToggle},
  data() {
    return {
      tab: null,
      task: {
            "task_id": "clickbait-spoiling",
            "task_name": "Clickbait Challenge at SemEval 2023 - Clickbait Spoiling",
            "task_description": "Clickbait posts link to web pages and advertise their content by arousing curiosity instead of providing informative summaries. Clickbait spoiling aims at generating short texts that satisfy the curiosity induced by a clickbait post.",
            "organizer": "PAN",
            "organizer_id": "pan",
            "web": "https://pan.webis.de/semeval23/pan23-web/clickbait-challenge.html",
            "year": "2012-2021",
            "dataset_count": 4,
            "software_count": 9,
            "teams": 12,
            "userVmsForTask": 'example-vm'
        },
    }
  }
}
</script>