<template>
  <v-app>
  <v-container class="fill-height">
        <v-row no-gutters>
            <h1>Shared Tasks</h1>
        </v-row>

        <v-row class="pb-1">
            <v-col cols=4>
                <v-text-field v-model="task_filter"
                              append-inner-icon="mdi-magnify"
                              placeholder="Type to filter&hellip;"/>
            </v-col>
            <v-col cols=4>
                <v-btn size="x-large" block prepend-icon="mdi-magnify" >Add Task</v-btn>
            </v-col>
            <v-col cols=4>
                <v-btn size="x-large" block prepend-icon="mdi-magnify">Edit Organizations</v-btn>
            </v-col>
        </v-row>


        <v-data-table-virtual :headers="headers"
                      :items="tasks"
                      :itemsPerPage="-1"
                      :search="task_filter"
                      show-expand
                      show-select>
                      <template v-slot:expanded-row="{ columns, item }">
      <tr>
        <td :colspan="columns.length">
          More info about
        </td>
      </tr>
    </template>
        </v-data-table-virtual>
    </v-container>
  </v-app>
</template>

<script lang="ts">
export default {
  name: "hello-world",
  data() {
    return {
      task_filter: null,
      expanded: [],
      headers: [
        {title: 'Task', align: 'start', key: 'task_name'},
        {title: 'Featured', key: 'featured'},
        {title: 'Latest Datasets', key: 'dataset_last_created'},
        {title: 'Created', key: 'dataset_first_created'},
        {title: 'Organization', key: 'organizer'},
        { text: '', value: 'data-table-expand' },
      ],
      tasks: [
        {'task_name': 'task-1', 'featured': true, 'dataset_last_created': 'now', 'organizer': 'Organizer 1'},
        {'task_name': 'task-2', 'featured': true, 'dataset_last_created': 'now', 'organizer': 'Organizer 2'},
        {'task_name': 'task-3', 'featured': true, 'dataset_last_created': 'now', 'organizer': 'Organizer 3'},
        {'task_name': 'task-4', 'featured': true, 'dataset_last_created': 'now', 'organizer': 'Organizer 4'},
        {'task_name': 'task-5', 'featured': true, 'dataset_last_created': 'now', 'organizer': 'Organizer 5'},
      ],
    }
  }
}

</script>