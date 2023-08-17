<template>
  <v-card class="mt-10 text-center">
    <v-card-item v-if="extractRole() === 'guest'">
      <v-card-title>
      <h3>No Virtual Machine</h3>
    </v-card-title>
    <v-card-text>
      <p>
        Your TIRA account is currently not associated with a virtual machine. Without a VM, you can only use 'Upload' to submit results.
Please contact your task organizer to obtain a TIRA virtual machine.
      </p>
    </v-card-text>
    </v-card-item>
    <v-card-item v-if="extractRole() !== 'guest' && !userHasVm(extractRole())">
      <v-card-title>
      <h3>No Virtual Machine</h3>
    </v-card-title>
    <v-card-text>
      <p>
        Your TIRA account is currently not associated with a virtual machine. Without a VM, you can only use 'Upload' to submit results.
Please contact your task organizer to obtain a TIRA virtual machine.
      </p>
    </v-card-text>
    </v-card-item>
    <v-card-item v-if="extractRole() !== 'guest' && userHasVm(extractRole())">
      <v-card-title>
      <h3>Virtual Machine Submission</h3>
    </v-card-title>
    <v-card-text>
      <p>
        Here you can submit your results using a virtual machine. Please make sure that you have read the task description and the submission guidelines.
      </p>
    </v-card-text>
    </v-card-item>
  </v-card>
</template>

<script>
import {extractRole} from "@/utils";

export default {
  name: "virtual-machine-submission",
  props: ['organizer', 'organizer_id'],
  methods: {
    extractRole,
    userHasVm(role) {
      return true
    }
  }
}
</script>