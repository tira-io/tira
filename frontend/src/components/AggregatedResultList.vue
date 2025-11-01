<template>
    <v-data-table :headers="table_headers" :items="lines" v-model:sort-by="table_sort_by" density="compact" class="elevation-1 d-none d-md-block" hover>
    </v-data-table>

    <v-data-table :headers="table_headers_small_layout" :items="lines" v-model:sort-by="table_sort_by" expand-on-click density="compact" class="elevation-1 d-md-none" hover>
    </v-data-table>
</template>

<script lang="ts">

export default {
  name: "aggregated-result-list",
  props: ['table_headers', 'table_headers_small_layout', 'initial_table_sort_by', 'lines'],
    data() {
    return {
      table_sort_by: [],
    }
  },
    beforeMount() {
      this.table_sort_by = this.initial_table_sort_by
  },
  watch: {
    initial_table_sort_by(old_value, new_value) { this.table_sort_by = new_value},
  }
}
</script>
