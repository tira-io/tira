<template>
  <p v-if="expand_message !== '' && !expanded">
    {{ expand_message }} (<a href="javascript:void(0)" @click="expanded=true">see details</a>)
  </p>
  <v-card v-if="expand_message === '' || expanded" class="bg-grey-darken-4">
    <v-card-title :class="$vuetify.display.mdAndDown ? 'bg-grey-darken-3 white--text d-flex justify-space-between px-2 flex-column' : 'bg-grey-darken-3 white--text d-flex justify-space-between px-2 '">
      <span>{{ title }}</span>
      <v-btn @click="copyToClipboard" color="primary" icon="mdi-clipboard"></v-btn>
    </v-card-title>
    <div class="d-flex justify-space-evenly">
      <v-card-text class="overflow-y-auto overflow-x-auto">
      <!--<pre class="language-python pt-4" v-for="(line,lineNumber) of code.split('\n')">{{ line }}</pre>-->
      <pre class="language-python pt-4 px-2">{{ code }}</pre>
    </v-card-text>
    </div>
  </v-card>
</template>
    
<script lang="ts">
  import { reportSuccess } from '@/utils';
  export default {
    name: "tira-code",
    props: ['title', 'code', 'expand_message'],
    data() {
      return {
        expanded: false,
      }
    },
    methods: {
      copyToClipboard () {
        //https://stackoverflow.com/questions/58733960/copy-url-to-clipboard-via-button-click-in-a-vuejs-component
        navigator.clipboard.writeText(this.code).then(reportSuccess("Successfully copied code to clipboard", ""));
      }
    }
  }
  </script>