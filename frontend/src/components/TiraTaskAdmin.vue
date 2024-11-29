<template>
  <v-container v-if="userinfo.role == 'admin'">
    <h2>Admin</h2>
    <v-expansion-panels>
      <v-expansion-panel>
        <v-expansion-panel-title>Manage Task</v-expansion-panel-title>
        <v-expansion-panel-text>
          <h3>Task Configuration</h3>
          You can edit this task: <edit-task :task_id_for_edit="task_id" :userinfo="userinfo" />
        </v-expansion-panel-text>
      </v-expansion-panel>

      <v-expansion-panel>
        <v-expansion-panel-title>Manage Datasets</v-expansion-panel-title>
        <v-expansion-panel-text>

          <h3>Add new Dataset</h3>
          You can add new datasets: <edit-dataset :task_id="task_id" :is_ir_task="task.is_ir_task"
            @addDataset="(x: any) => addDataset(x)" />

          <v-divider class="my-4" />
          <h3>Edit existing Dataset</h3>
          <v-row><v-col cols="6"><v-autocomplete v-model="selectedDataset" :items="datasets" item-title="display_name"
                item-value="dataset_id" label="Dataset" outlined /></v-col><v-col cols="6">
              <edit-dataset :dataset_id_from_props="selectedDataset" :disabled="selectedDataset === ''"
                :task_id="task_id" :is_ir_task="task.is_ir_task"
                @addDataset="(x: any) => addDataset(x)" /></v-col></v-row>

          <v-divider class="my-4" />
          <h3>Delete existing Dataset</h3>
          <v-row><v-col cols="6"><v-autocomplete v-model="selectedDatasetForDelete" :items="datasets"
                item-title="display_name" item-value="dataset_id" label="Dataset" outlined /></v-col><v-col cols="6">
              <confirm-delete :disabled="selectedDatasetForDelete === ''"
                :to_delete="{ dataset_id: selectedDatasetForDelete, 'action': 'delete_dataset' }"
                :label="'Delete dataset ' + selectedDatasetForDelete + '.'"
                @deleteConfirmed="(i: any) => deleteDataset(i)" />
            </v-col></v-row>
        </v-expansion-panel-text>
      </v-expansion-panel>

      <v-expansion-panel>
        <v-expansion-panel-title>Export Dataset</v-expansion-panel-title>
        <v-expansion-panel-text>
          <p>Organizers/Admins can export the dataset. Public datasets can also be exported by users, e.g., after a
            shared task has ended or for participants to verify their software.
          </p>
          <v-autocomplete v-model="selectedDataset" :items="datasets" item-title="display_name" item-value="dataset_id"
            label="Dataset" outlined />
          <ul v-if="selectedDataset !== ''">
            <li><a
                :href="'/data-download/' + (selectedDataset.endsWith('-training') ? 'training' : 'test') + '/input-/' + selectedDataset + '.zip'"
                target="_blank">Download Input for Systems</a> (a .zip file with the content available to participant
              submissions)</li>
            <li><a
                :href="'/data-download/' + (selectedDataset.endsWith('-training') ? 'training' : 'test') + '/input-truth/' + selectedDataset + '.zip'"
                target="_blank">Download Input for Evaluators</a> (a .zip file with the truth available to the
              evaluator)</li>
          </ul>
        </v-expansion-panel-text>
      </v-expansion-panel>
      <v-expansion-panel>
        <v-expansion-panel-title>Overview Missing Reviews</v-expansion-panel-title>
        <v-expansion-panel-text>
          <overview-missing-reviews :task="task" />
        </v-expansion-panel-text>
      </v-expansion-panel>
      <v-expansion-panel>
        <v-expansion-panel-title>Overview Registered Teams</v-expansion-panel-title>
        <v-expansion-panel-text>
          <overview-registered-teams :task="task" />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </v-container>
</template>

<script lang="ts">
import { inject } from 'vue'

import { extractTaskFromCurrentUrl, get, reportError, reportSuccess, type DatasetInfo, type UserInfo } from '../utils'
import { VAutocomplete } from "vuetify/components";
import OverviewMissingReviews from './OverviewMissingReviews.vue';
import OverviewRegisteredTeams from './OverviewRegisteredTeams.vue';
import EditTask from './EditTask.vue';
import EditDataset from './EditDataset.vue';
import ConfirmDelete from './ConfirmDelete.vue';

export default {
  name: "tira-task-admin",
  components: { OverviewMissingReviews, OverviewRegisteredTeams, EditTask, VAutocomplete, EditDataset, ConfirmDelete },
  props: {
    'datasets': {
      type: Object as () => DatasetInfo[],
      required: true,
    },
    'task': {
      type: Object, // TODO: add type info
      required: true,
    },
    'userinfo': {
      type: Object as () => UserInfo,
      required: true,
    },
  },
  emits: ['add-dataset', 'delete-dataset'],
  data() {
    return {
      task_id: extractTaskFromCurrentUrl() as string,
      selectedDataset: '',
      selectedDatasetForDelete: '',
    }
  },
  methods: {
    addDataset(x: any) {
      this.$emit('add-dataset', x);
      this.selectedDataset = x['dataset_id']
    },
    deleteDataset(x: any) {
      if (x['action'] == 'delete_dataset') {
        get(inject("REST base URL") + '/tira-admin/delete-dataset/' + x['dataset_id'])
          .then(() => {
            this.$emit('delete-dataset', x['dataset_id'])
            this.selectedDatasetForDelete = ''
          })
          .then(reportSuccess("Deletion of dataset " + x['dataset_id'] + " was successfull."))
          .catch(reportError("Deletion of dataset " + x['dataset_id'] + " failed."))
      }
    }
  }
}
</script>
