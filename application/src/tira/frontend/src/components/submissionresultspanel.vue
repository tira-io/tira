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
        <th class="header uk-table-expand">Dataset</th>
        <th class="header uk-table-shrink uk-text-nowrap"></th>
        <th class="header uk-table-shrink uk-text-nowrap"></th>
        <th class="header uk-table-shrink uk-text-nowrap"></th>
    </tr>
    </thead>
    <tbody>
<!--    TODO: there may be differences between upload runs and software runs here -->
    <tr v-for="run in runs"  class="uk-padding-remove" :id="run.software + '-' + run.run_id + '-run'"
    :class="{ 'table-background-green': run.review.noErrors,
              'table-background-red': (run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors),
              'uk-background-default': !(run.review.noErrors || run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors),
              'table-background-yellow': run.review.published // when on leaderboard
            }">
        <td class="uk-table-shrink uk-padding-remove uk-margin-remove" :id="'run-' + user_id + '-' + run.run_id"></td>
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
        <td class="uk-table-shrink uk-text-nowrap">
            <span v-if="run.input_run_id !== ''">
                <font-awesome-icon icon="fas fa-level-up-alt" flip="horizontal"/>
            </span>&nbsp;{{ run.run_id }}</td>
        <td class="uk-table-shrink uk-text-nowrap" ><a :href="'#run-' + user_id + '-' + run.input_run_id" v-if="run.input_run_id != 'none'">{{ run.input_run_id }}</a>
        </td>
<!--        TODO: quick look at reviews. Maybe this makes sense? -->
<!--        <td class="uk-padding-remove-vertical uk-text-nowrap uk-text-truncate" v-if="for_review">-->
<!--           <span v-if="run.review.reviewer" class="uk-text-bold">{{ run.review.reviewer }}&nbsp;</span>-->
<!--           <span v-if="run.review.hasErrorOutput">Output Error -&nbsp;</span>-->
<!--           <span v-else-if="run.review.otherErrors">Software Error -&nbsp;</span>-->
<!--           <span v-if="run.review.comment != ''">{{ run.review.comment }}</span>-->
<!--           </td>-->
        <td class="uk-padding-remove-vertical uk-text-truncate">{{ run.dataset }}</td>


        <td class="uk-table-shrink uk-text-nowrap uk-padding-remove uk-margin-remove uk-preserve-width">
            <a class="uk-button uk-button-small run-evaluate-button uk-background-default"
               :class="{ 'uk-button-disabled': runningEvaluationIds.includes(run.run_id), 'uk-button-default': !runningEvaluationIds.includes(run.run_id)}"
               :disabled="runningEvaluationIds.includes(run.run_id)"
               @click="evaluateRun(run.dataset, run.run_id)"
               v-if="run.input_run_id === ''">
<!--                <div v-show="runningEvaluationIds.includes(run.run_id)" class="run-evaluate-spinner" uk-spinner="ratio: 0.4"></div>-->
                <font-awesome-icon v-show="runningEvaluationIds.includes(run.run_id)" icon="fas fa-cog" spin />
                <font-awesome-icon v-show="!runningEvaluationIds.includes(run.run_id)" icon="fas fa-cog" />
                evaluate</a>
        </td>
        <td class="uk-table-shrink uk-text-nowrap uk-padding-remove uk-margin-remove uk-preserve-width">
          <review-button :task_id="task_id" :user_id="vm.vm_id" :dataset_id="run.run.dataset"
                         :run_id="run.run.run_id" :csrf="csrf"
                          @add-notification="(type, message) => this.$emit('add-notification', type, message)"
                          @update-review="newReview => updateReview(newReview)"
          />
        </td>
        <td class="uk-table-shrink uk-text-nowrap uk-padding-remove uk-margin-remove uk-preserve-width">
            <a class="uk-button uk-button-small uk-button-danger"
               @click="deleteRun(run.dataset, run.run_id)">
              <font-awesome-icon icon="fas fa-trash-alt" /></a>
        </td>
    </tr>
    </tbody>
</table>
<div v-if="runs.length === 0" class="uk-text-center">There are no runs yet.</div>
</div>
</template>

<script>
import ReviewButton from "./reviewbutton";

export default {
    name: "submissionresultspanel",
    props: ['runs', 'task_id', 'user_id', 'running_evaluations', 'csrf'],
    emits: ['add-notification', 'poll-evaluations', 'remove-run'],
    data() {
        return {
            runningEvaluationIds: []
        }
    },
    components: {
        ReviewButton
    },
    methods: {
        async get(url) {
            const response = await fetch(url)
            if (!response.ok) {
                throw new Error(`Error fetching endpoint: ${url} with ${response.status}`);
            }
            let results = await response.json()
            if (results.status === 1) {
                throw new Error(`${results.message}`);
            }
            return results
        },
        updateReview(newReview) {
          for (const run of this.runs){
            if (run.run.run_id === newReview.run_id) {
              run.review.blinded = !newReview.isVisibleToParticipant
              run.review.published = newReview.isOnLeaderboard
              run.noErrors =newReview.no_errors
              run.hasErrors = !newReview.no_errors
              run.comment =newReview. comment
              run.hasErrorOutput = newReview.output_error
              run.otherErrors = newReview.software_error
              run.reviewer = newReview.reviewer
              run.reviewed = newReview.no_errors || newReview.output_error || newReview.software_error
            }
          }
        },

        deleteRun(datasetId, runId) {
            if(datasetId === ""){
                datasetId=null
            }
            this.get(`/grpc/${this.user_id}/run_delete/${datasetId}/${runId}`).then(message => {
                console.log(message)
                this.$emit('remove-run', runId)
            }).catch(error => {
                this.$emit('add-notification', 'error', error.message)
            })
        },
        evaluateRun(datasetId, runId) {
            console.log('runs', this.runs)
            if(datasetId === ""){
                datasetId=null
            }
            this.get(`/grpc/${this.user_id}/run_eval/${datasetId}/${runId}`).then(message => {
                console.log(message)
                this.$emit('poll-evaluations')
            }).catch(error => {
                this.$emit('add-notification', 'error', error.message)
            })
        }
    },
    beforeMount() {
        this.runningEvaluationIds = this.running_evaluations.map(e => {return e.run_id})
    }
}
</script>
