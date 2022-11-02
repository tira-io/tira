<template>
<ul id="tira-run-accordion" class="uk-list uk-list-collapse uk-list-striped" uk-accordion="multiple: true">
    <li v-for="vm in vms">
        <div class="uk-accordion-title">
            <table class="uk-text-small uk-width-5-6">
                <tr>
                  <td class="uk-width-1-5 uk-text-left"><b>{{ vm.vm_id }}</b></td>
                  <td class="uk-width-1-5 uk-text-right">{{ vm.runs.length }} Runs</td>
                  <td class="uk-width-1-5 uk-text-right">
                      <span  v-if="vm.unreviewed_count > 0" class="uk-text-warning">
                      {{ vm.unreviewed_count }} Unreviewed</span></td>
                  <td class="uk-width-1-5 uk-text-right">{{ vm.blinded_count }} Blinded</td>
                  <td class="uk-width-1-5 uk-text-right">
                      <span v-if="vm.published_count === 0" class="uk-text-warning">
                      {{ vm.published_count }} Published</span></td>
                </tr>
            </table>
        </div>
        <div class="uk-accordion-content uk-margin-remove-top" v-if="vm">
            <a :href="'/task/' + task_id + '/user/' + vm.vm_id">[manage user]</a>
            <review-list @add-notification="(type, message) => $emit('addNotification', type, message)"
                         @remove-run="() => console.log('removing runs is not implemented in the review accordion')"
                         @poll-evaluation="() => console.log('starting evaluations is not implemented in the review accordion')"
                         :runs="vm.runs"
                         :task_id="task_id" :user_id="vm.vm_id" :hide_reviewed="hide_reviewed"
                         :csrf="csrf"/>
        </div>
    </li>
</ul>
</template>
<script>
import ReviewList from "../runs/review-list";

export default {
  data() {
    return {
    }
  },
  name: "reviewaccordion",
  props: {
    'vms': Array,
    'task_id': String,
    'hide_reviewed': Boolean,
    'csrf': String},
  emits: ['addNotification'],
  components: {
      ReviewList
  },
  methods: {
  },
  mounted() {
  }
}
</script>