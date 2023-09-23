<template>
  <v-container v-if="role == 'admin'">
    <h2>Admin</h2>
    <v-expansion-panels>
      <v-expansion-panel>
        <v-expansion-panel-title>Manage Task</v-expansion-panel-title>
        <v-expansion-panel-text>
          <h3>Task Configuration</h3>
          You can edit this task: <edit-task :task_id_for_edit="task_id"/>

          <v-divider class="my-4"/>
          <h3>Edit existing Dataset</h3>
          <v-row><v-col cols="6"><v-autocomplete v-model="selectedDataset" :items="datasets" item-title="display_name" item-value="dataset_id" label="Dataset" outlined/></v-col><v-col cols="6">
            <edit-dataset :dataset_id_from_props="selectedDataset" :disabled="selectedDataset === ''" :task_id="task_id"/></v-col></v-row>

          <v-divider class="my-4"/>
          <h3>Add new Dataset</h3>
          You can add new datasets: <edit-dataset :task_id="task_id"/>

          <v-divider class="my-4"/>
          <h3>Legacy Administration</h3>
          Not everything of the old admin functionality already ported to the new vuetify frontend.
          Please <a :href="'/task/' + task_id">go to the old task page if you need some administration functionality not covered above</a>.
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
import {VAutocomplete} from "vuetify/components";
import OverviewMissingReviews from './OverviewMissingReviews.vue';
import EditTask from './EditTask.vue';
import EditDataset from './EditDataset.vue';

export default {
  name: "tira-task-admin",
  components: {OverviewMissingReviews, EditTask, VAutocomplete, EditDataset},
  props: ['datasets'],
  data() {
      return {
        task_id: extractTaskFromCurrentUrl(),
        role: extractRole(), // Values: guest, user, participant, admin
        selectedDataset: '',
      }
    }
}
</script>