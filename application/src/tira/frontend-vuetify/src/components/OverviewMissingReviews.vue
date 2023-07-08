<template>
    <loading :loading="loading"/>
    <v-data-table v-if="!loading" :headers="table_headers"
                    :items="count_of_missing_reviews" density="compact" show-select>
    </v-data-table>
    <v-row class="pt-2">
      <v-col cols="12"><v-btn variant="outlined" block>Review Selected</v-btn></v-col>
    </v-row>
</template>
  
<script lang="ts">
import Loading from "./Loading.vue"
import { get, reportError, inject_response } from '../utils'
 
export default {
  name: "overview-missing-reviews",
  components: {Loading},
  props: ['task_id'],
  data() { return {
    loading: true,
    count_of_missing_reviews: [],
    table_headers: [
      { title: 'Dataset', key: 'dataset_id' },
      { title: 'Review Missing', key: 'to_review' },
      { title: 'Submissions', key: 'submissions' },
    ],
  }},
  beforeMount() {
    this.loading = true
    get('/api/count-of-missing-reviews/' + this.task_id)
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem While Loading the Overview of missing Reviews", "This might be a short-term hiccup, please try again. We got the following error: "))
  },
}
</script>