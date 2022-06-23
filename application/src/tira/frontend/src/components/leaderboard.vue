<script>
export default {
  props: ['keys', 'evaluation', 'role', 'dataset_id', 'task_id', 'hide_private'],
  computed: {
    getEvaluations() {
      if (this.hide_private){
        return this.evaluation.filter(i => i.published === true)
      }
      return this.evaluation
    }
  }
}
</script>
<template>
<div class="scrollable-table">
<table class="uk-margin-small uk-table uk-table-small uk-table-striped uk-table-middle">
  <thead>
  <tr>
      <th></th>
      <th class="uk-table-shrink" v-if="role == 'admin'">&nbsp;</th>
      <th class="uk-table-shrink" v-if="role == 'admin'">&nbsp;</th>
      <th class="header uk-table-shrink uk-text-nowrap"><span>Virtual Machine</span></th>
      <th class="header uk-table-shrink uk-text-nowrap"><span>Run</span></th>
      <th class="header" v-for="key in keys"><span>{{ key }}</span></th>
      <th class="header uk-text-center"><span>Actions</span></th>
  </tr>
  </thead>
  <tbody>
  <!-- naming the loop variable "eval" will lead to an error within webpack (keyword) -->
  <tr class="uk-padding-remove" v-for="evaluation in getEvaluations">
      <td :id="dataset_id + '-' + evaluation.vm_id + '-' + evaluation.run_id"></td>
      <td class="uk-table-shrink uk-padding-remove-vertical" v-if="role === 'admin'">
          <div uk-tooltip="This run is blinded" v-if="evaluation.blinded">
              <i class="fas fa-user-slash dataset-detail-icon"></i>
          </div>
          <div uk-tooltip="This run is visible to the participant" v-else>
              <i class="fas fa-user dataset-detail-icon uk-text-success"></i>
          </div>
      </td>
      <td class="uk-table-shrink uk-padding-remove-vertical" v-if="role === 'admin'"> [&gt; Icons &lt;]
          <div uk-tooltip="This run is on the leaderbords" v-if="evaluation.published">
              <i class="fas fa-users dataset-detail-icon uk-text-success"></i>
          </div>
          <div uk-tooltip="This run is not published" v-else>
              <i class="fas fa-users-slash dataset-detail-icon"></i>
          </div>
      </td>
      <td class="uk-table-shrink uk-text-nowrap uk-padding-remove-vertical">{{ evaluation.vm_id }}</td>
      <td class="uk-table-shrink uk-text-nowrap uk-padding-remove-vertical">{{ evaluation.run_id }}</td>
      <td class="uk-padding-remove-vertical" v-for="measure in evaluation.measures">{{ measure }}</td>
      <td class="uk-align-right uk-text-nowrap uk-table-expand uk-margin-remove uk-padding-remove-vertical uk-padding-remove-right">
        <button class="uk-button uk-button-small uk-button-default uk-background-default"
           target="_blank"
           :href="'/task/' + task_id + '/user/' + evaluation.vm_id + '/dataset/' + dataset_id + '/download/' + evaluation.input_run_id + '.zip'"><i class="fas fa-download"></i> run</button>
        <button class="uk-button uk-button-small uk-button-default uk-background-default"
           target="_blank"
           :href="'/task/' + task_id + '/user/' + evaluation.vm_id + '/dataset/' + dataset_id + '/download/' + evaluation.run_id + '.zip'"><i class="fas fa-download"></i> result</button>
      </td>
  </tr>
  </tbody>
</table>
</div>
</template>
