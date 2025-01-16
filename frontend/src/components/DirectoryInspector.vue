<template>
    <div v-if="file_listing">
        <v-treeview :items="file_listing" item-value="title" activatable open-on-click open-all density="compact"/>
    </div>
</template>
  
  
<script lang="ts">
  export default {
    name: "directory-inspector",
    props: ['file_listing']
  }
</script>