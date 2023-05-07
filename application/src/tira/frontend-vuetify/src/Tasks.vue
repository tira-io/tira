<template>
  <v-container>
    <h3 class="text-h3 py-5">Tasks</h3>
    <div class="py-5" />
    <div class="d-flex">
      <v-responsive min-width="220px">
        <v-text-field 
          class="px-4"
          clearable
          label="Type here to filter &hellip;"
          prepend-inner-icon="mdi-magnify" 
          v-model="task_filter" 
          variant="underlined"
        />
      </v-responsive>
      <div class="pe-2">
        <v-btn class="d-sm-none" color="primary" icon="mdi-plus" />
        <v-btn
          class="d-none d-sm-flex"
          color="primary"
          prepend-icon="mdi-plus"
          size="large"
        >
          New Task
        </v-btn>
      </div>
    </div>
    <div class="py-2" />
    <v-data-table-virtual 
      :headers="headers"
      :items="tasks"
      :itemsPerPage="-1"
      :search="task_filter"
      show-expand
    >
      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length">
            More info about
          </td>
        </tr>
      </template>
    </v-data-table-virtual>
  </v-container>
</template>

<script lang="ts">
export default {
  name: "hello-world",
  data() {
    return {
      role: 'guest', // user, participant, admin
      task_filter: null,
      expanded: [],
      headers: [
        { title: 'Task', align: 'start', key: 'task_name' },
        { title: 'Featured', key: 'featured' },
        { title: 'Latest Datasets', key: 'dataset_last_created' },
        { title: 'Created', key: 'dataset_first_created' },
        { title: 'Organization', key: 'organizer' },
        { text: '', value: 'data-table-expand' },
      ],
      tasks: [
        { 'task_name': 'task-1', 'featured': true, 'dataset_last_created': 'now', 'organizer': 'Organizer 1' },
        { 'task_name': 'task-2', 'featured': true, 'dataset_last_created': 'now', 'organizer': 'Organizer 2' },
        { 'task_name': 'task-3', 'featured': true, 'dataset_last_created': 'now', 'organizer': 'Organizer 3' },
        { 'task_name': 'task-4', 'featured': true, 'dataset_last_created': 'now', 'organizer': 'Organizer 4' },
        { 'task_name': 'task-5', 'featured': true, 'dataset_last_created': 'now', 'organizer': 'Organizer 5' },
      ],
    }
  }
}
</script>