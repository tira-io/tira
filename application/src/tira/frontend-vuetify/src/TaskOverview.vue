<template>
  <v-container>
  <v-card class="px2" max-width="2560">
    <v-card-item :title="task.task_name">
      <template v-slot:subtitle>by {{ task.organizer }}</template>
    </v-card-item>

    <v-card-text class="py-0">
      <v-row no-gutters>
        <v-col cols="10">
          {{task.task_description}}
        </v-col>
      </v-row>
    </v-card-text>

    <div class="d-flex py-3">
      <v-list-item density="compact" prepend-icon="mdi-calendar-blank-outline">
        <v-list-item-subtitle>{{task.year}}</v-list-item-subtitle>
      </v-list-item>

      <v-list-item density="compact" prepend-icon="mdi-account-group">
        <v-list-item-subtitle>{{task.teams}}</v-list-item-subtitle>
      </v-list-item>

      <v-list-item density="compact" prepend-icon="mdi-database-outline">
        <v-list-item-subtitle>{{task.dataset_count}}</v-list-item-subtitle>
      </v-list-item>
      
      <v-list-item density="compact" prepend-icon="mdi-briefcase-outline">
        <v-list-item-subtitle>{{task.software_count}}</v-list-item-subtitle>
      </v-list-item>
    </div>

    <v-divider></v-divider>

    <v-card-actions>
      <v-row>
        <v-col cols="6"><v-btn variant="outlined" block>Submit</v-btn></v-col>
        <v-col cols="6"><v-btn variant="outlined" block>Task Website</v-btn></v-col>
      </v-row>
    </v-card-actions>
  </v-card>
  </v-container>

  <v-container>
    <h2>Submissions</h2>

    <v-autocomplete label="Dataset" 
                    :items="datasets" 
                    item-title="display_name"
                    item-value="dataset_id"
                    v-model="selectedDataset"
                    variant="underlined"
                    clearable/>

    <v-data-table v-if="selectedDataset"
      :headers="headers"
      :items="desserts"
      item-value="name"
      show-select
      class="elevation-1"/>

      <v-row v-if="selectedDataset" class="pt-2">
        <v-col cols="6"><v-btn variant="outlined" block>Download Selected</v-btn></v-col>
        <v-col cols="6"><v-btn variant="outlined" block>Compare Selected</v-btn></v-col>
      </v-row>
  </v-container>
</template>

<script lang="ts">
import { NONAME } from 'dns';


  export default {
    name: "task-overview",
    data() {
      return {
        task_id = ref(window.location.hash).split('')
        headers: [
          {
            title: 'Dessert (100g serving)',
            align: 'start',
            sortable: false,
            key: 'name',
          },
          { title: 'Calories', align: 'end', key: 'calories' },
          { title: 'Fat (g)', align: 'end', key: 'fat' },
          { title: 'Carbs (g)', align: 'end', key: 'carbs' },
          { title: 'Protein (g)', align: 'end', key: 'protein' },
          { title: 'Iron (%)', align: 'end', key: 'iron' },
        ],
        desserts: [
          {
            name: 'Frozen Yogurt',
            calories: 159,
            fat: 6.0,
            carbs: 24,
            protein: 4.0,
            iron: '1',
          },
          {
            name: 'Jelly bean',
            calories: 375,
            fat: 0.0,
            carbs: 94,
            protein: 0.0,
            iron: '0',
          },
          {
            name: 'Gingerbread',
            calories: 356,
            fat: 16.0,
            carbs: 49,
            protein: 3.9,
            iron: '16',
          }
        ],
        role: 'guest', // Values: user, participant, admin
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
            "teams": 12
        },
        datasets: [{
                "dataset_id": "1",
                "display_name": "task-1-type-classification",
                "is_confidential": true, 
                "is_deprecated": false, 
                "year": "2022-11-15 06:51:49.117415", 
                "task": "clickbait-spoiling", 
                "software_count": 10,
                "runs_count": 220,
                "created": "2022-11-15",
                "last_modified": "2022-11-15"
            }, {
                "dataset_id": "2",
                "display_name": "task-1-type-classification-validation",
                "is_confidential": false,
                "is_deprecated": false, 
                "year": "2022-11-15 06:51:49.117415", 
                "task": "clickbait-spoiling", 
                "software_count": 20,
                "runs_count": 100,
                "created": "2022-11-15",
                "last_modified": "2022-11-15"
            }
        ],
    }
  }
}
</script>
