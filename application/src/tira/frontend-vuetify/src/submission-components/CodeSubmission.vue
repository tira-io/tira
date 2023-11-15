<template>
  <v-card class="mt-10 text-center">
    <v-card-item><v-card-title><h3>You have not connected your Code Repository yet</h3></v-card-title>
    <v-card-text>
      <v-row class="d-flex align-center justify-center">
        <v-col cols="6"><v-text block text="Your GitHub Account"/></v-col>
        <v-col cols="6"><v-btn block color="primary" @click="runSoftware()" text="Add Code Repository"/></v-col>
      </v-row>
    </v-card-text>
    </v-card-item>
  </v-card>
</template>

<script>
import {extractRole} from "@/utils";

export default {
  name: "code-submission",
  props: ['organizer', 'organizer_id', 'user_id'],
  methods: {
    extractRole,
  },
  data() {
    return {
        tab: extractSubmissionTypeFromCurrentUrl(),
    }
  }
}
</script>