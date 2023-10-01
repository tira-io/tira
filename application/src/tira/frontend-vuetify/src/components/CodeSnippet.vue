<template>
  <p v-if="expand_message !== '' && !expanded">
    {{ expand_message }} (<a href="javascript:void(0)" @click="expanded=true">see details</a>)
  </p>
  <v-card v-if="expand_message === '' || expanded" class="bg-grey-darken-4">
    <v-card-title class="bg-grey-darken-3 white--text d-flex justify-space-between">
      <span>{{ title }}</span>
      <v-btn @click="copyToClipboard" color="primary">Copy</v-btn>
    </v-card-title>
    <v-card-text class="language-python overflow-scroll">
      <!--<pre class="language-python pt-4" v-for="(line,lineNumber) of code.split('\n')">{{ line }}</pre>-->
      <pre class="language-python pt-4">{{ code }}</pre>
    </v-card-text>
  </v-card>
</template>
    
<script lang="ts">
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
        navigator.clipboard.writeText(this.code);
        console.log(this.code)
      }
    }
  }
  </script>