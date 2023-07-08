<template>
  <v-container v-if="role == 'admin'">
    <h2>Admin</h2>
    <v-expansion-panels>
      <v-expansion-panel>
        <v-expansion-panel-title>Manage Task</v-expansion-panel-title>
        <v-expansion-panel-text>
          The admin functionality is not yet ported to the new vuetify frontend. Please <a :href="'/task/' + task_id">go to the old task page to do the administration</a>.
        </v-expansion-panel-text>
      </v-expansion-panel>
      <v-expansion-panel>
        <v-expansion-panel-title>Overview Missing Reviews</v-expansion-panel-title>
        <v-expansion-panel-text>
          <overview-missing-reviews :task_id="task_id" />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </v-container>
</template>

<script lang="ts">
import { extractTaskFromCurrentUrl, extractRole } from '../utils'
import OverviewMissingReviews from './OverviewMissingReviews.vue';
export default {
  name: "tira-task-admin",
  components: {OverviewMissingReviews},
  data() {
      return {
        task_id: extractTaskFromCurrentUrl(),
        role: extractRole(), // Values: guest, user, participant, admin
      }
    }
}
</script>