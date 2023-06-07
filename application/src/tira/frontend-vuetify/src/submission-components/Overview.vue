<template>
  <div>
  <v-card class="px2 my-5 ">
    <v-card-item title="About this Task" class="text-h4 mb-1">
    </v-card-item>

      <div class="d-flex py-3">
        <v-list-item density="compact" prepend-icon="mdi-calendar-blank-outline">
          <v-list-item-subtitle>{{task.year}}</v-list-item-subtitle>
          <v-tooltip activator="parent" location="bottom">On Tira since {{task.year}}</v-tooltip>
        </v-list-item>

        <v-list-item density="compact" prepend-icon="mdi-account-group">
          <v-list-item-subtitle>{{task.teams}}</v-list-item-subtitle>
          <v-tooltip activator="parent" location="bottom">{{ task.teams }} Teams</v-tooltip>
        </v-list-item>

        <v-list-item density="compact" prepend-icon="mdi-database-outline">
          <v-list-item-subtitle>{{task.dataset_count}}</v-list-item-subtitle>
          <v-tooltip activator="parent" location="bottom">{{task.dataset_count}} Datasets</v-tooltip>
        </v-list-item>

        <v-list-item density="compact" prepend-icon="mdi-briefcase-outline">
          <v-list-item-subtitle>{{task.software_count}}</v-list-item-subtitle>
          <v-tooltip activator="parent" location="bottom">{{task.software_count}} Software Submissions</v-tooltip>
        </v-list-item>
        </div>

    <v-card-text class="py-0 text-lg-body-1 text-justify my-2">
      Description: {{task.task_description}}
      <v-divider class="my-3"></v-divider>
        <div class="my-6">
          <p class="my-6">{{description}}</p>
          <p class="my-6">{{data}}</p>
          <p class="my-6">{{classes}}</p>
        </div>
      </v-card-text>
<!--
    <v-card-actions>
      <v-layout class="overflow-visible" style="height: 56px;">
      </v-layout>
    </v-card-actions>
-->
  </v-card>
  </div>
</template>

<script lang="ts">
export default {
    name: "Overview",
    components: {},
    data() {
      return {
        tab: null,
        description: "Task: Given corresponding action and replay frames, and player bounding boxes in these frames, try to identify each player across the different camera views. Basically, this means linking the bounding boxes between these video frames from different viewpoints.\n ",
        data: "The SoccerNet Re-Identification (ReID) dataset is composed of 340.993 players thumbnails extracted from the SoccerNet videos at events annotated for the action spotting task, and images from their replays. The challenge set is composed of separate players thumbnails from different games.\n ",
        classes: "The classes are not taken into account in the baseline or the evaluation, but the object to retrieve are among the following classes: {player team left, player team right, goalkeeper team left, goalkeeper team right, main referee, side referee, staff}.\n ",

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
      }
    }
  }
</script>