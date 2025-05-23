<template>
  <tira-breadcrumb />

  <v-skeleton-loader type="card" v-if="task_list === undefined || serverinfo === undefined" />

  <v-container v-if="task_list !== undefined && serverinfo !== undefined">
    <h3 class="text-h3 py-5">Featured Tasks</h3>
    <div class="d-none d-md-block">
      <v-row>
        <v-col cols="4" v-for="t in featured_tasks">
          <router-link :to="'/task-overview/' + t.task_id" style="text-decoration: none;">
            <v-card :text="t.task_description" :title="t.task_name" style="max-height: 100px; min-height: 100px"/>
          </router-link>
        </v-col>
      </v-row>
    </div>
    <div class="d-md-none">
      <v-row>
        <v-col cols="12" v-for="t in featured_tasks">
          <router-link :to="'/task-overview/' + t.task_id" style="text-decoration: none;">
            <v-card :text="t.task_description" :title="t.task_name" style="max-height: 100px; min-height: 100px"/>
          </router-link>
        </v-col>
      </v-row>
    </div>

    <div class="pt-5">TIRA hosts {{ task_list.length }} tasks with <router-link to="/systems">{{ serverinfo.publicSystemCount }} public systems</router-link> and <router-link to="/datasets">{{ serverinfo.datasetCount }} datasets</router-link>.</div>

    <h3 class="text-h3 py-5">All Task</h3>
    <div class="py-5"></div>
    <div class="d-flex">
      <v-responsive min-width="220px" id="task-search">
        <v-text-field class="px-4" clearable label="Type here to filter &hellip;" prepend-inner-icon="mdi-magnify"
          variant="underlined" v-model="task_filter" />
      </v-responsive>
      <div class="pe-2"><edit-task task_id_for_edit="" :userinfo="userinfo" /></div>
    </div>
    <div class="py-2"></div>
    <v-data-table :headers="headers_md" :items="task_list" :itemsPerPage="25" :search="task_filter" density="compact"
      item-value="task_id" hover show-expand no-data-text="No tasks have been added, yet." class="d-none d-md-block">
      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length" class="py-3">{{ item.task_description }}</td>
        </tr>
      </template>
      <template #item.task_name="{ item }">
        <router-link :to="'/task-overview/' + item.task_id" style="text-decoration: none !important;">{{ item.task_name }}</router-link>
      </template>
    </v-data-table>

    <!-- TODO: Vuetify will likely introduce a prop to hide columns based on size. Reduce redundancy when that happens. -->
    <v-data-table :headers="headers_xs" :items="task_list" :itemsPerPage="10" :search="task_filter" density="compact"
      fixed-footer hover show-expand no-data-text="No tasks have been added, yet." class="d-md-none">
      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length" class="py-3">{{ item }}</td>
        </tr>
      </template>
      <template #item.task_name="{ item }">
        <router-link :to="'/task-overview/' + item.task_id" style="text-decoration: none !important;">{{ item.task_name }}</router-link>
      </template>
    </v-data-table>
  </v-container>
</template>

<script lang="ts">
import { inject } from 'vue'

import { get_from_archive, reportError, inject_response, type UserInfo, ServerInfo } from './utils';
import { TiraBreadcrumb, EditTask } from './components'

interface Task {
  "task_id": String,
  "task_name": string,
  "task_description": string,
  "organizer": String,
  "organizer_id": String,
  "web": String,
  "year": String,
  "featured": Boolean,
  "require_registration": Boolean,
  "require_groups": Boolean,
  "restrict_groups": Boolean,
  "allowed_task_teams": String,
  "master_vm_id": String,
  "is_ir_task": Boolean,
  "irds_re_ranking_image": String,
  "irds_re_ranking_command": String,
  "irds_re_ranking_resource": String,
  "dataset_count": Number,
  "software_count": Number,
  "max_std_out_chars_on_test_data": Number,
  "max_std_err_chars_on_test_data": Number,
  "max_file_list_chars_on_test_data": Number,
  "command_placeholder": String,
  "command_description": String,
  "dataset_label": String,
  "max_std_out_chars_on_test_data_eval": Number,
  "max_std_err_chars_on_test_data_eval": Number,
  "max_file_list_chars_on_test_data_eval": Number,
  "dataset_last_modified": Date

}

export default {
  name: "tasks",
  components: { TiraBreadcrumb, EditTask },
  data() {
    return {
      userinfo: inject('userinfo') as UserInfo,
      task_filter: '',
      expanded: [],
      headers_md: [
        { title: 'Task', key: 'task_name' },
        { title: 'Subs', key: 'software_count' },
        { title: 'Data', key: 'dataset_count' },
        { title: 'Host', key: 'organizer' },
        { title: 'Latest Activity', key: 'dataset_last_modified', minWidth: '300' },
        { text: 'Description', key: 'data-table-expand' },
      ],
      // TODO: Vuetify will likely introduce a prop to hide columns based on size. Reduce redundancy when that happens.
      headers_xs: [
        { title: 'Task', key: 'task_name' },
        { title: 'Subs', key: 'software_count' },
        { text: 'Description', value: 'data-table-expand' },
      ],
      task_list: undefined as (Task[] | undefined),
      serverinfo: inject("serverInfo") as ServerInfo,
    }
  },
  computed: {
    featured_tasks(): Task[] {
      return this.task_list === undefined ? [] : this.task_list?.filter(i => i.featured)
    },
  },
  beforeMount() {
    get_from_archive('/api/task-list')
      .then(inject_response(this))
      .catch(reportError("Problem While Loading the Overview of the Tasks.", "This might be a short-term hiccup, please try again. We got the following error: "))
  }
}

</script>
