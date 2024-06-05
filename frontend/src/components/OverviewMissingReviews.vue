<template>
    <loading :loading="loading"/>
    <v-data-table v-if="!loading" :headers="table_headers" :items="count_of_missing_reviews" density="compact" v-model:expanded="expanded" show-expand expand-on-click item-value="dataset_id">
      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length">
            More info about {{ item.dataset_id }}
            <run-list :task_id="task.task_id" :organizer="task.organizer" :organizer_id="task.organizer_id" :dataset_id="item.dataset_id" show_only_unreviewed="true"/>
          </td>
        </tr>
      </template>
    </v-data-table>
    <v-row class="pt-2">
      <v-col cols="12"><v-btn variant="outlined" block>Review Selected</v-btn></v-col>
    </v-row>
</template>
  
<script lang="ts">
import { inject } from 'vue'

import { RunList, Loading } from '.'
import { get, reportError, inject_response } from '../utils'

interface CountOfMissingReviews {
  dataset_id: String,
}
 
export default {
  name: "overview-missing-reviews",
  components: {Loading, RunList},
  props: ['task'],
  data() { return {
    loading: true,
    expanded: [] as string[], 
    count_of_missing_reviews: [] as CountOfMissingReviews[],
    table_headers: [
      { title: 'Dataset', key: 'dataset_id' },
      { title: 'Review Missing', key: 'to_review' },
      { title: 'Submissions', key: 'submissions' },
    ],
  }},
  beforeMount() {
    this.loading = true
    get(inject("REST base URL")+'/api/count-of-missing-reviews/' + this.task.task_id)
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem While Loading the Overview of missing Reviews", "This might be a short-term hiccup, please try again. We got the following error: "))
  },
}
</script>
