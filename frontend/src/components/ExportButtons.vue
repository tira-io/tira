<template>
  <v-col cols="12" v-for="button in task.export_buttons" :key="button.value">
    <v-btn v-if="vm_id" variant="outlined" :href="export_url(button, vm_id)" target="_blank" block>{{ button.display_name }}</v-btn>

    <v-menu v-else-if="vm_ids" transition="slide-y-transition">
      <template v-slot:activator="{ props }">
        <v-btn v-bind="props" variant="outlined" block>{{ button.display_name }}</v-btn>
      </template>
      <v-list>
        <v-list-item v-for="(item, i) in vm_ids" :key="i">
          <v-btn :href="export_url(button, item)" variant="outlined" target="_blank" block>{{ button.display_name }} for {{ item }}</v-btn>
        </v-list-item>
      </v-list>
    </v-menu>
  </v-col>
</template>

<script lang="ts">
import { vm_id } from "@/utils";

export default {
  name: "export-buttons",
  props: ['task', 'vm', 'user_vms_for_task', 'user_id', 'userinfo'],
  data: () => ({
    additional_vms: [''],
  }),
  computed: {
    vm_ids() {
      return this.user_vms_for_task.length > 1 ? this.user_vms_for_task : null;
    },
    vm_id() {
      const resolved = vm_id(this.vm_ids, this.vm, this.user_vms_for_task, this.additional_vms, this.user_id, this.task)
      // Admins are not necessarily registered for a team on this task, so fall back to the task's master vm:
      // check_permissions already lets admins bypass the vm-ownership check regardless of the vm_id used.
      if (!resolved && !this.vm_ids && this.userinfo && this.userinfo.role === 'admin') {
        return this.task.master_vm_id
      }
      return resolved
    },
  },
  methods: {
    export_url(button: { value: string }, vmId: string) {
      return '/task/' + this.task.task_id + '/export/' + vmId + '/' + button.value + '.zip'
    }
  }
}
</script>
