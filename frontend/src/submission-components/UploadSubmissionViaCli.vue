<template>
  <code-snippet
    title="Step 1: Make sure that your TIRA client is up to date and authenticated"
    expand_message=""
    :code="tira_setup_code"
  />
  <br>
  <br>

  Please select the dataset for which you want to upload your run<br>
  <v-autocomplete
    label="Dataset"
    :items="datasets"
    item-title="display_name"
    item-value="dataset_id"
    prepend-icon="mdi-file-document-multiple-outline"
    v-model="selectedDataset"
    variant="underlined"
    clearable
  />

  <br>

  <code-snippet
    v-if="selectedDataset"
    title="Step 2: Upload your submission"
    :code="command"
    expand_message=""
  />
</template>
  
<script lang="ts">
  
import CodeSnippet from "../components/CodeSnippet.vue"
import { extractTaskFromCurrentUrl } from '../utils'
import { VAutocomplete } from "vuetify/components"

export default {
  name: "upload-submission-via-cli",
  props: ['token', 'datasets', "approach"],
  components: { VAutocomplete, CodeSnippet },
    data() { return {
      task_id: extractTaskFromCurrentUrl(),
      submissions_of_user: [{'task_id': 'loading', 'title': 'loading', 'type': 'loading', 'id': 'loading'}],
      selectedDataset: undefined,
    }},
    computed: {
      command() {
        let ret = 'tira-cli upload --dataset ' + this.selectedDataset + ' --directory YOUR-UPLOAD';
        if (this.approach) {
            ret += " --system '" + this.approach + "'"
        }

        return ret
      },
      tira_setup_code() {
      return 'pip3 install --upgrade tira\ntira-cli login --token ' + this.token +'\n\ntira-cli verify-installation'
    },
    }
  }
</script>
