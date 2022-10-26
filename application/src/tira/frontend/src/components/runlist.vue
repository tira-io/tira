<template>
<div class="scrollable-table">
<table class="uk-margin-small uk-table uk-table-divider uk-table-small uk-table-middle">
    <thead>
    <tr>
        <th></th>
        <th class="uk-table-shrink"></th>
        <th class="uk-table-shrink"></th>
        <th class="uk-table-shrink"></th>
        <th class="header uk-table-shrink uk-text-nowrap"><span>Run</span></th>
        <th class="header uk-table-shrink uk-text-nowrap"><span>Input Run</span></th>
        <th class="header uk-table-expand"><span>Review</span></th>
        <th class="header uk-table-shrink uk-text-nowrap"></th>
        <th class="header uk-table-shrink uk-text-nowrap"></th>
    </tr>
    </thead>
    <tbody>
    <tr v-for="run in getRuns"  class="uk-padding-remove" :id="run.run.software.id + '-' + run.run.run_id + '-run'"
    :class="{ 'table-background-green': (run.review.noErrors) && !for_review,
              'table-background-red': (run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors) && !for_review,
              'uk-background-default': !(run.review.noErrors || run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors) && !for_review,
              'table-background-yellow': !(run.review.noErrors || run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors) && for_review,
              'uk-background-default': (run.review.noErrors || run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors) && for_review}">
        <td class="uk-table-shrink uk-padding-remove uk-margin-remove" :id="'run-' + vm_id + '-' + run.run.run_id"></td>
        <td class="uk-table-shrink uk-padding-remove-vertical"> <!-- run status Icon -->
            <div uk-tooltip="This run is OK" v-if="run.review.noErrors" class="dataset-detail-icon uk-text-success">
                <font-awesome-icon icon="fas fa-check"/>
            </div>
            <div uk-tooltip="This run has errors" v-else-if="run.review.hasErrors" class="dataset-detail-icon uk-text-danger">
                <font-awesome-icon icon="fas fa-times"/>
            </div>
            <div uk-tooltip="This run has not been reviewed yet. A task organizer will check each run and confirm it's validity." v-else class="dataset-detail-icon">
                <font-awesome-icon icon="fas fa-question" />
            </div>
        </td>
        <td class="uk-table-shrink uk-padding-remove-vertical"> <!-- run visibility Icon -->
            <div uk-tooltip="This run is blinded" v-if="run.review.blinded" class="dataset-detail-icon">
                <font-awesome-icon icon="fas fa-user-slash"/>
            </div>
            <div uk-tooltip="This run is visible to the participant" v-else class="dataset-detail-icon uk-text-success">
                <font-awesome-icon icon="fas fa-user" />
            </div>
        </td>
        <td class="uk-table-shrink uk-padding-remove-vertical"> <!-- published run Icon -->
            <div uk-tooltip="This run is on the leaderboards" v-if="run.review.published" class="dataset-detail-icon uk-text-success">
                <font-awesome-icon icon="fas fa-users" />
            </div>
            <div uk-tooltip="This run is not published" v-else class="dataset-detail-icon">
                <font-awesome-icon icon="fas fa-users-slash" />
            </div>
        </td>
        <td class="uk-table-shrink uk-text-nowrap"><span v-if="run.run.input_run_id != ''">
                <font-awesome-icon icon="fas fa-level-up-alt" flip="horizontal"/>
            </span>&nbsp;{{ run.run.run_id }}</td>
        <td class="uk-table-shrink uk-text-nowrap" ><a :href="'#run-' + vm_id + '-' + run.run.input_run_id" v-if="run.run.input_run_id != 'none'">{{ run.run.input_run_id }}</a>
        </td>
        <td class="uk-padding-remove-vertical uk-text-nowrap uk-text-truncate" v-if="for_review">
           <span v-if="run.review.reviewer" class="uk-text-bold">{{ run.review.reviewer }}&nbsp;</span> 
           <span v-if="run.review.hasErrorOutput">Output Error -&nbsp;</span>
           <span v-else-if="run.review.otherErrors">Software Error -&nbsp;</span>
           <span v-if="run.review.comment != ''">{{ run.review.comment }}</span>
           </td>
        <td class="uk-padding-remove-vertical uk-text-truncate" v-else>{{ dataset_id }}</td>
        <td class="uk-table-shrink uk-text-nowrap uk-padding-remove uk-margin-remove uk-preserve-width">
            <a class="uk-button uk-button-small uk-button-default uk-background-default"
                 :href="'/task/' + task_id + '/user/' + vm_id + '/dataset/' + dataset_id + '/run/' + run.run.run_id">
                  <font-awesome-icon icon="fas fa-search" />
                  REVIEW</a>
        </td>
        <td class="uk-table-shrink uk-text-nowrap uk-padding-remove uk-margin-remove uk-preserve-width">
            <a class="uk-button uk-button-small uk-button-default uk-background-default"
               target="_blank"
               :href="'/task/' + task_id + '/user/' + vm_id + '/dataset/' + dataset_id + '/download/' + run.run.run_id + '.zip'">
                <font-awesome-icon icon="fas fa-download" />
                </a>
        </td>
    </tr>
    </tbody>
</table>
</div>
</template>
<script>
export default {
    props: ['runs', 'vm_id', 'task_id', 'dataset_id', 'for_review', 'hide_reviewed'],
    computed: {
        getRuns() {
            if (this.hide_reviewed) {
                return this.runs.filter(run => (run.review.noErrors || run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors) === false)
            }
            return this.runs
        }
    }
}
</script>