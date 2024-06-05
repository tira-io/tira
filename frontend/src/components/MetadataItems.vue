<template>
  <v-table>
    <tbody>
      <tr v-for="item in items" :key="item.key">
        <td>{{ item.key }}</td>
        <td>{{ item.value }}</td>
      </tr>
    </tbody>
  </v-table>
</template>
<script lang="ts">
export default {
  name: "metadata-items",
  props: ['items'],
}
</script>
