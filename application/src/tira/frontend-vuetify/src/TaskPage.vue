<template>
  <v-container class=" my-10 py-5 ">
    <v-card >
      <v-card-item >
        <v-card-title>
          <p class="text-h4 text--primary  py-3">
            {{task.task_name}}
          </p>
        </v-card-title>
        <v-divider class="my-5"></v-divider>
        <v-card-subtitle class="text-h6 mb-1">
          Organized by {{ task.organizer }}
        </v-card-subtitle>
      </v-card-item>

      <v-card-actions>
        <v-layout class="overflow-visible " style="height: 56px; ">
          <v-bottom-navigation
              v-model="tab"
              color="primary"
              :elevation="10"
              grow

          >
            <v-btn value="Overview">
              <v-icon>mdi-home-analytics</v-icon>
              Overview
            </v-btn>

            <v-btn value="Leaderboard">
              <v-icon>mdi-google-analytics</v-icon>
              Leaderboard
            </v-btn>

            <v-btn value="Contributions">
              <v-icon>mdi-account-plus</v-icon>
              My Contributions
            </v-btn>

            <v-btn value="Submission">
              <v-icon>mdi-tooltip-plus</v-icon>
              Submission
            </v-btn>

            <v-btn value="ExplainationToggle">
              <v-icon>mdi-account-group-outline</v-icon>
              Discussion
            </v-btn>

          </v-bottom-navigation>
        </v-layout>
      </v-card-actions>
    </v-card>

    <v-window v-model="tab">

      <v-window-item value="Overview">
        <Overview/>
      </v-window-item>

      <v-window-item value="Leaderboard">
        <Tasks/>
      </v-window-item>
      <v-window-item value="Contributions">
        <VirtualMachineSubmission/>
      </v-window-item>

      <v-window-item value="Submission">
        <RunUpload/>
      </v-window-item>

      <v-window-item value="ExplainationToggle">
        <ExplainationToggle/>
      </v-window-item>

    </v-window>
  </v-container>
</template>

<script lang="ts">
  import RunList from './components/RunList.vue'
  import Loading from "./components/Loading.vue"
  import { extractTaskFromCurrentUrl, get, reportError, extractRole } from './utils'
  import DockerSubmission from "@/submission-components/DockerSubmission.vue";
  import VirtualMachineSubmission from "@/submission-components/VirtualMachineSubmission.vue";
  import UploadSubmission from "@/submission-components/UploadSubmission.vue";
  import RunUpload from "@/RunUpload.vue";
  import Tasks from "@/Tasks.vue";
  import Overview from "@/submission-components/Overview.vue";
  import ExplainationToggle from "@/submission-components/ExplainationToggle.vue";
  import {getTasksData} from "@/tmp_tasksdata";

  export default {
    name: "task-page",
    components: {ExplainationToggle, UploadSubmission, VirtualMachineSubmission, DockerSubmission, RunUpload, Overview, Tasks},
    data() {
      return {
        tab: null,
        task_id: extractTaskFromCurrentUrl(),
        loading: false,
        role: extractRole(), // Values: guest, user, participant, admin
        selectedDataset: '',
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
        datasets: [{'dataset_id': '', 'display_name': ''}],
                role2: 'guest', // Values: user, participant, admin
      }
    }
  }
</script>
