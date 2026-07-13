<template>
  <loading :loading="loading"/>
  <v-data-table
    v-if="!loading"
    :headers="table_headers"
    :items="count_of_team_software_executions"
    density="compact"
  />
</template>

<script lang="ts">
import { inject } from 'vue'

import { Loading } from '.'
import { get, inject_response, reportError } from '../utils'

interface CountOfTeamSoftwareExecutions {
  team: string,
  software_count: number,
  executed_on_unique_datasets: number,
  executed_on_datasets: number,
}

export default {
  name: "overview-team-software-executions",
  components: { Loading },
  props: ['task'],
  data() {
    return {
      loading: true,
      count_of_team_software_executions: [] as CountOfTeamSoftwareExecutions[],
      rest_url: inject("REST base URL"),
      table_headers: [
        { title: 'Team', key: 'team' },
        { title: 'Software', key: 'software_count' },
        { title: 'Executed on Unique Datasets', key: 'executed_on_unique_datasets' },
        { title: 'Executed on Datasets', key: 'executed_on_datasets' },
      ],
    }
  },
  beforeMount() {
    this.loading = true
    get(this.rest_url + '/api/count-of-team-software-executions/' + this.task.task_id)
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem While Loading the Overview of Software Executions per Team", "This might be a short-term hiccup, please try again. We got the following error: "))
  }
}
</script>
