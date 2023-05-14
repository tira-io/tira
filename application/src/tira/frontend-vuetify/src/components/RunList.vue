<template>
  <loading :loading="loading"/>
  <v-container v-if="!loading">
    <v-data-table v-if="dataset_id" v-model:expanded="expanded" show-expand :headers="headers"
                  :items="runs" item-value="name" show-select class="elevation-1" hover>
      <template v-slot:top>
        <v-toolbar flat>
          <v-toolbar-title>Submissions</v-toolbar-title>
        </v-toolbar>
      </template>
      <template v-slot:item.actions="{item}">
        <run-actions :run_id="item.calories" />
      </template>
      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length">
            <software-details :software_id="item.calories"/>
          </td>
        </tr>
      </template>
    </v-data-table>

    <v-row v-if="dataset_id" class="pt-2">
      <v-col cols="6"><v-btn variant="outlined" block>Download Selected</v-btn></v-col>
      <v-col cols="6"><v-btn variant="outlined" block>Compare Selected</v-btn></v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import RunActions from './RunActions.vue'
import SoftwareDetails from './SoftwareDetails.vue'
import Loading from "./Loading.vue"

export default {
  name: "run-list",
  components: {RunActions, SoftwareDetails, Loading},
  props: ['task_id', 'dataset_id'],
  data() { return {
      expanded: [],
      loading: true,
      tableLoading: false,
      runs: [],
      headers: [],
      headers_small_layout: []
    }
  },
  methods: {
    /*loadItems ({ page, itemsPerPage, sortBy }) {
      this.tableLoading = true
      get('').then((message) => {

      }).catch((error) => {

      })
    }*/
  }
}
</script>