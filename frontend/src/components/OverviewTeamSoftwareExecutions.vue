<template>
  <loading :loading="loading"/>
  <v-row v-if="!loading">
    <v-col cols="12" md="6">
      <v-text-field
        v-model.number="minimum_unique_datasets"
        label="Minimum Executed on Unique Datasets"
        type="number"
        min="0"
      />
    </v-col>
    <v-col cols="12" md="6">
      <v-text-field
        v-model.number="minimum_datasets"
        label="Minimum Executed on Datasets"
        type="number"
        min="0"
      />
    </v-col>
  </v-row>
  <v-data-table
    v-if="!loading"
    :headers="table_headers"
    :items="filteredSoftwareExecutions"
    item-value="software_id"
    density="compact"
  >
    <template v-slot:item="row">
      <tr>
        <td>{{row.item.team}}</td>
        <td>{{row.item.software}}</td>
        <td>{{row.item.executed_on_unique_datasets}}</td>
        <td>{{row.item.executed_on_datasets}}</td>
        <td>
          <a :href="row.item.link">link to {{row.item.team}}`s page</a>
        </td>
        <td>
          <a :href="row.item.link_submission">link to {{row.item.team}}`s page</a>
        </td>
      </tr>
    </template>
  </v-data-table>
</template>

<script lang="ts">
import { inject } from 'vue'

import { Loading } from '.'
import { get, inject_response, reportError } from '../utils'

interface CountOfTeamSoftwareExecutions {
  team: string,
  software: string,
  software_id: number,
  executed_on_unique_datasets: number,
  executed_on_datasets: number,
  link: string,
  link_submission: string,
}

export default {
  name: "overview-team-software-executions",
  components: { Loading },
  props: ['task'],
  data() {
    return {
      loading: true,
      count_of_team_software_executions: [] as CountOfTeamSoftwareExecutions[],
      minimum_unique_datasets: 0,
      minimum_datasets: 0,
      rest_url: inject("REST base URL"),
      table_headers: [
        { title: 'Team', key: 'team' },
        { title: 'Software', key: 'software' },
        { title: 'Executed on Unique Datasets', key: 'executed_on_unique_datasets' },
        { title: 'Executed on Datasets', key: 'executed_on_datasets' },
        { title: 'Team Page', key: 'link' },
        { title: 'Submission Page', key: 'link_submission' },
      ],
    }
  },
  computed: {
    filteredSoftwareExecutions(): CountOfTeamSoftwareExecutions[] {
      const minimumUniqueDatasets = Math.max(0, Number(this.minimum_unique_datasets) || 0)
      const minimumDatasets = Math.max(0, Number(this.minimum_datasets) || 0)
      return this.count_of_team_software_executions.filter(item =>
        item.executed_on_unique_datasets >= minimumUniqueDatasets
        && item.executed_on_datasets >= minimumDatasets
      )
    },
  },
  beforeMount() {
    this.loading = true
    get(this.rest_url + '/api/count-of-team-software-executions/' + this.task.task_id)
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem While Loading the Overview of Software Executions per Team", "This might be a short-term hiccup, please try again. We got the following error: "))
  }
}
</script>
