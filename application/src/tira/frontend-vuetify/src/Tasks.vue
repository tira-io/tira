<template>
  <tira-breadcrumb/>
  <loading :loading="task_list.length === 0"/>

  <v-container v-if="task_list.length > 0">
    <h3 class="text-h3 py-5">Choose a Task</h3>
    <div class="py-5"></div>
    <div class="d-flex">
      <v-responsive min-width="220px" id="task-search">
        <v-text-field class="px-4" clearable label="Type here to filter &hellip;" prepend-inner-icon="mdi-magnify"
                      variant="underlined" v-model="task_filter"/>
      </v-responsive>
      <div class="pe-2"><edit-task task_id_for_edit=""/></div>
    </div>
    <div class="py-2"></div>
    <v-data-table :headers="headers_md" :items="task_list" :itemsPerPage="25" :search="task_filter" density="compact"
                  hover show-expand no-data-text="No tasks have been added, yet." class="d-none d-md-block">
      <template v-slot:expanded-row="{ columns, internalItem }">
        <tr>
          <td :colspan="columns.length" class="py-3">{{ internalItem.value.task_description }}</td>
        </tr>
      </template>
      <template #item.task_name="{ internalItem }">
        <a :href="'/task-overview/' + internalItem.value.task_id" style="text-decoration: none !important;">{{ internalItem.value.task_name }}</a>
      </template>
    </v-data-table>

    <!-- TODO: Vuetify will likely introduce a prop to hide columns based on size. Reduce redundancy when that happens. -->
    <v-data-table :headers="headers_xs" :items="task_list" :itemsPerPage="10" :search="task_filter" density="compact"
                  fixed-footer hover show-expand no-data-text="No tasks have been added, yet." class="d-md-none">
      <template v-slot:expanded-row="{ columns, internalItem }">
        <tr>
          <td :colspan="columns.length" class="py-3">{{ internalItem.value.task_description }}</td>
        </tr>
      </template>
      <template #item.task_name="{ internalItem }">
        <a :href="'/task-overview/' + internalItem.value.task_id" style="text-decoration: none !important;">{{ internalItem.value.task_name }}</a>
      </template>
    </v-data-table>
  </v-container>
</template>

<script lang="ts">
  import { get, reportError, inject_response, extractRole } from './utils';
  import { Loading, TiraBreadcrumb, EditTask } from './components'
  import { VSheet } from 'vuetify/components';
  import { type ExtractPropTypes } from 'vue'

  type VSheetPropTypes = Partial<ExtractPropTypes<typeof VSheet>>

  export default {
    name: "tasks",
    components: {Loading, TiraBreadcrumb, EditTask},
    data() {
      return {
        role: extractRole(), // Values: user, participant, admin
        task_filter: '',
        expanded: [],
        headers_md: [
          { title: 'Task', key: 'task_name'},
          { title: 'Subs', key: 'software_count'},
          { title: 'Data', key: 'dataset_count'},
          { title: 'Host', key: 'organizer' },
          { title: 'Latest Activity', key: 'dataset_last_modified', minWidth: '300' },
          { text: 'Description', value: 'data-table-expand' },
        ],
        // TODO: Vuetify will likely introduce a prop to hide columns based on size. Reduce redundancy when that happens.
        headers_xs: [
          { title: 'Task', key: 'task_name'},
          { title: 'Subs', key: 'software_count'},
          { text: 'Description', value: 'data-table-expand' },
        ],
        task_list: [],
      }
    },
    beforeMount() {
      get('/api/task-list')
        .then(inject_response(this))
        .catch(reportError("Problem While Loading the Overview of the Tasks.", "This might be a short-term hiccup, please try again. We got the following error: "))
    }
  }
  
</script>
