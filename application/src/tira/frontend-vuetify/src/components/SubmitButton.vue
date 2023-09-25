<template>
  <v-btn v-if="show_login" href="/login" variant="outlined" block>Submit</v-btn>

  <register-form v-if="show_register" :task="task"  @update-user-vms-for-task="(newUserVm) => additional_vms = [newUserVm]"/>

  <v-btn v-if="!show_register && !show_login && vm_id" :href="'/submit/' + task.task_id + '/user/' + vm_id" variant="outlined" block>Submit</v-btn>

  <v-menu v-if="!show_register && !show_login && vm_ids" transition="slide-y-transition">
    <template v-slot:activator="{ props }">
      <v-btn v-bind="props" variant="outlined" block>Submit</v-btn>
    </template>
    <v-list>
      <v-list-item v-for="(item, i) in vm_ids" :key="i">
        <v-btn :href="'/submit/' + task.task_id + '/user/' + item" variant="outlined" block>Submit as {{ item }}</v-btn>
      </v-list-item>
    </v-list>
  </v-menu>
</template>
  
<script lang="ts">
import RegisterForm from "./RegisterForm.vue"

export default {
  name: "submit-button",
  props: ['task', 'vm', 'user_vms_for_task', 'user_id'],
  data: () => ({
    additional_vms: [''],
  }),
  components: {RegisterForm},
  computed: {
    vm_id() {
      if (!this.vm_ids && this.vm) {
        return this.vm
      } else if (this.user_vms_for_task && this.user_vms_for_task.length == 1) {
        return this.user_vms_for_task[0]
      } else if(this.additional_vms && this.additional_vms.length > 0 && this.additional_vms[0]) {
        return this.additional_vms[0]
      } else if (!this.vm_ids && this.user_id && !this.task.require_groups && !this.task.restrict_groups) {
        return this.user_id + '-default'
      }

      return null;
    },
    vm_ids() {
      return this.user_vms_for_task.length > 1 ? this.user_vms_for_task : null;
    },
    show_login() {
      return !this.vm_id && !this.vm_ids && !this.user_id
    },
    show_register() {
      return !this.show_login && !this.vm_ids && !this.vm_id && this.user_id
    }
  }
}
</script>
