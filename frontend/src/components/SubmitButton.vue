<template>
  <v-btn v-if="show_login" href="/login" variant="outlined" block>Submit</v-btn>

  <register-form v-if="show_register" :task="task"  @update-user-vms-for-task="(newUserVm) => additional_vms = [newUserVm]"/>

  <router-link v-if="!show_register && !show_login && vm_id" :to="'/submit/' + task.task_id + '/user/' + vm_id">
    <v-btn variant="outlined" block>Submit</v-btn>
  </router-link>

  <v-menu v-if="!show_register && !show_login && vm_ids" transition="slide-y-transition">
    <template v-slot:activator="{ props }">
      <v-btn v-bind="props" variant="outlined" block>Submit</v-btn>
    </template>
    <v-list>
      <v-list-item v-for="(item, i) in vm_ids" :key="i">
        <router-link :to="'/submit/' + task.task_id + '/user/' + item">
          <v-btn variant="outlined" block>Submit as {{ item }}</v-btn>
        </router-link>
      </v-list-item>
    </v-list>
  </v-menu>
</template>
  
<script lang="ts">
import RegisterForm from "./RegisterForm.vue"
import { vm_id } from "@/utils";

export default {
  name: "submit-button",
  props: ['task', 'vm', 'user_vms_for_task', 'user_id'],
  data: () => ({
    additional_vms: [''],
  }),
  components: {RegisterForm},
  computed: {
    vm_id() {
      return vm_id(this.vm_ids, this.vm, this.user_vms_for_task, this.additional_vms, this.user_id, this.task)
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
