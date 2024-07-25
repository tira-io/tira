<template>
  <p>You need a dataset with the same structure of the original dataset. For example, export the dataset used in this run via this command to a directory "tira-dataset":</p>
  <v-code tag="pre" > {{ run_export }}</v-code>
  <p>If you have the input data in a directory "tira-dataset", you can run this software via:</p>
</template>
  
<script lang="ts">
  export default {
    name: "tira-data-export",
    props: ['run_export']
  }
 </script>
  