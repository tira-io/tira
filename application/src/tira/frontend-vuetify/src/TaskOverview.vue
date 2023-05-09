<template>
  <v-container>
    <h1>TBD</h1>
  </v-container>
</template>

<script lang="ts">

  export default {
    name: "task-overview",
    data() {
      return {
        role: 'guest', // Values: user, participant, admin
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
        },
        datasets: {
            "task-1-type-classification-20221115-test": {
                "display_name": "task-1-type-classification",
                "is_confidential": true, 
                "is_deprecated": false, 
                "year": "2022-11-15 06:51:49.117415", 
                "task": "clickbait-spoiling", 
                "software_count": 10,
                "runs_count": 220,
                "created": "2022-11-15",
                "last_modified": "2022-11-15"
            }, 
            "task-1-type-classification-validation-20220924-training": {
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
        }
    }
  }
}
</script>
