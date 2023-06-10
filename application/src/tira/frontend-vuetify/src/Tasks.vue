<template>
  <loading :loading="task_list.length === 0"/>

  <v-container v-if="task_list.length > 0">
    <h3 class="text-h3 py-5">Choose a Task</h3>
    <div class="py-5" />
    <div class="d-flex">
      <v-responsive min-width="220px">
        <v-text-field class="px-4" clearable label="Type here to filter &hellip;" prepend-inner-icon="mdi-magnify"
                      variant="underlined" v-model="task_filter"/>
      </v-responsive>
      <div class="pe-2">
        <v-btn class="d-sm-none" color="primary" icon="mdi-plus" />
        <v-btn class="d-none d-sm-flex" color="primary" prepend-icon="mdi-plus" size="large">
          New Task
        </v-btn>
      </div>
    </div>
    <div class="py-2" />
    <v-data-table :headers="headers_md" :items="task_list" :itemsPerPage="25" :search="task_filter" density="compact"
                  expand-on-click hover show-expand no-data-text="No tasks have been added, yet." class="d-none d-md-block">
      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length" class="py-3">{{ item.raw.task_description }}</td>
        </tr>
      </template>
      <template #item.task_name="{ item }">
        <a :href="'/task-overview/' + item.value.task_id" style="text-decoration: none !important;">{{ item.value.task_name }}</a>
      </template>
    </v-data-table>

    <!-- TODO: Vuetify will likely introduce a prop to hide columns based on size. Reduce redundancy when that happens. -->
    <v-data-table :headers="headers_xs" :items="task_list" :itemsPerPage="10" :search="task_filter" density="compact"
                  expand-on-click fixed-footer hover show-expand no-data-text="No tasks have been added, yet." class="d-md-none">
      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length" class="py-3">{{ item.raw.task_description }}</td>
        </tr>
      </template>
      <template #item.task_name="{ item }">
        <a :href="'/task-overview/' + item.value.task_id" style="text-decoration: none !important;">{{ item.value.task_name }}</a>
      </template>
    </v-data-table>
  </v-container>
</template>

<script lang="ts">
  import { get, reportError, inject_response, extractRole } from './utils';

  export default {
    name: "tasks",
    data() {
      return {
        role: extractRole(), // Values: user, participant, admin
        task_filter: null,
        expanded: [],
        headers_md: [
          { title: 'Task', key: 'task_name', align: 'start' },
          { title: 'Subs', key: 'software_count', align: 'end' },
          { title: 'Data', key: 'dataset_count', align: 'end' },
          { title: 'Host', key: 'organizer' },
          { title: 'Latest Activity', key: 'dataset_last_modified', minWidth: '300' },
          { text: 'Description', value: 'data-table-expand' },
        ],
        // TODO: Vuetify will likely introduce a prop to hide columns based on size. Reduce redundancy when that happens.
        headers_xs: [
          { title: 'Task', key: 'task_name', align: 'start' },
          { title: 'Subs', key: 'software_count', align: 'end' },
          { text: 'Description', value: 'data-table-expand' },
        ],
        task_list: [],
      }
    },
    beforeMount() {
      get('/api/task-list')
        .then(inject_response(this))
        .catch(reportError)
    }
  }
  
</script>
