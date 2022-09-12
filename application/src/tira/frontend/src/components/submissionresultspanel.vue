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
        <th class="header uk-text-center uk-width-1-4">Actions</th>
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
        <td :id="'run-' + user_id + '-' + run.run_id"></td>
        <td class="uk-table-shrink uk-padding-remove-vertical"> <!-- run status Icon -->
            <div uk-tooltip="This run is OK" v-if="run.review.noErrors" class="dataset-detail-icon uk-text-success">
                <font-awesome-icon icon="fas fa-check"/>
            </div>
            <div uk-tooltip="This run has errors" v-else-if="run.review.hasErrors" class="dataset-detail-icon uk-text-danger">
                <font-awesome-icon icon="fas fa-times"/>
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
                <font-awesome-icon icon="fas fa-level-up-alt" />
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

        <td class="uk-align-right uk-table-expand uk-text-nowrap uk-margin-remove uk-padding-remove-vertical uk-padding-remove-right">
            <a class="uk-button uk-button-small run-evaluate-button uk-background-default"
               :class="{ 'uk-button-disabled': runningEvaluationIds.includes(run.run_id), 'uk-button-default': !runningEvaluationIds.includes(run.run_id)}"
               :disabled="runningEvaluationIds.includes(run.run_id)"
               @click="evaluateRun(run.dataset, run.run_id)"
               v-if="run.input_run_id === ''">
                <div v-show="runningEvaluationIds.includes(run.run_id)" class="run-evaluate-spinner" uk-spinner="ratio: 0.4"></div> evaluate</a>
            <a class="uk-button uk-button-small uk-button-default uk-background-default"
               target="_blank"
               :href="'/task/' + task_id + '/user/'  + user_id + '/dataset/' + run.dataset + '/run/' + run.run_id">
                <font-awesome-icon icon="fas fa-search" />
                inspect</a>
            <a class="uk-button uk-button-small uk-button-default uk-background-default"
               v-if="run.input_run_id === 'none'"
               target="_blank"
               :href="'/task/' + task_id + '/user/' + user_id + '/dataset/' + run.dataset + '/download/' + run.run_id + '.zip'">
                <font-awesome-icon icon="fas fa-download" />
                </a>
            <a class="uk-button uk-button-small uk-button-danger run-delete-button"
               @click="deleteRun(run.dataset, run.run_id)">
              <font-awesome-icon icon="fas fa-trash-alt" /></a>
          </td>
    </tr>
    </tbody>
</table>
</div>
<!--
<table class="uk-margin-small uk-table uk-table-divider uk-table-small uk-table-responsive uk-table-middle">
    <thead>
    <tr>
        <th></th>
        <th class="uk-table-shrink"></th>
        <th class="uk-table-shrink"></th>
        <th class="uk-table-shrink"></th>
        <th class="header uk-table-shrink uk-text-nowrap"><span>Run</span></th>
        <th class="header uk-table-shrink uk-text-nowrap"><span>Input Run</span></th>
        <th class="header uk-table-expand"><span>Dataset</span></th>
        <th class="header uk-text-center uk-width-1-4">Actions</th>
    </tr>
    </thead>
    <tbody id="uploads-runs-tbody">
    {% for run in upload.runs %}
    <tr class="uk-padding-remove" id="upload-{{ run.run_id }}-run">
        <td></td>
        <td class="uk-table-shrink uk-padding-remove-vertical">
            {% if run.review.noErrors == True %}
            <div uk-tooltip="title: This run is OK; delay: 500">
                <i class="fas fa-check dataset-detail-icon uk-text-success"></i>
            </div>
            {% elif run.review.hasErrors == True %}
            <div uk-tooltip="title: This run has errors; delay: 500">
                <i class="fas fa-times dataset-detail-icon uk-text-danger"></i>
            </div>
            {% endif %}
        </td>
        <td class="uk-table-shrink uk-padding-remove-vertical">
            {% if run.review.blinded == True %}
            <div uk-tooltip="title: This run is blinded; delay: 500">
                <i class="fas fa-user-slash dataset-detail-icon"></i>
            </div>
            {% else %}
            <div uk-tooltip="title: You can inspect the results of this run; delay: 500">
                <i class="fas fa-user dataset-detail-icon uk-text-success"></i>
            </div>
            {% endif %}
        </td>
        <td class="uk-table-shrink uk-padding-remove-vertical">
            {% if run.review.published == True %}
            <div uk-tooltip="title: This run is on the leaderboards; delay: 500">
                <i class="fas fa-users dataset-detail-icon uk-text-success"></i>
            </div>
            {% else %}
            <div uk-tooltip="title: This run is not published; delay: 500">
                <i class="fas fa-users-slash dataset-detail-icon"></i>
            </div>
            {% endif %}
        </td>
        <td class="uk-table-shrink uk-text-nowrap uk-padding-remove-vertical">
            {% if run.input_run_id != "none" and run.input_run_id != "" %}<i class="fas fa-level-up-alt fa-flip-horizontal"></i>{% endif %}
            &nbsp;{{ run.run_id }}
        </td>
        <td class="uk-table-shrink uk-text-nowrap uk-padding-remove-vertical">
            {% if run.input_run_id != "none" and run.input_run_id != "" %}{{ run.input_run_id }}{% endif %}
        </td>
        <td class="uk-padding-remove-vertical">{{ run.dataset }}</td>
        <td class="uk-align-right uk-table-expand uk-margin-remove uk-padding-remove-vertical uk-padding-remove-right">
            {% if run.input_run_id == "none" or run.input_run_id == "" %}
            <a class="uk-button uk-button-small uk-button-default run-evaluate-button"
               data-tira-dataset="{{ run.dataset }}" data-tira-vm-id="{{ user_id }}"
               data-tira-run-id="{{ run.run_id }}">
                <div id="run-evaluate-spinner-{{ run.run_id }}" class="run-evaluate-spinner" uk-spinner="ratio: 0.4"></div> evaluate</a>
            {% endif %}
            <a class="uk-button uk-button-small uk-button-default"
               href="{% url 'tira:review' task_id=task_id vm_id=user_id dataset_id=run.dataset run_id=run.run_id %}">inspect</a>
            <a class="uk-button uk-button-small uk-button-danger run-delete-button"
               data-tira-dataset="{{ run.dataset }}" data-tira-vm-id="{{ user_id }}"
               data-tira-run-id="{{ run.run_id }}">delete</a>
        </td>
    </tr>
    {% endfor %}
    </tbody>
</table>
-->
</template>

<script>
export default {
    name: "submissionresultspanel",
    props: ['runs', 'task_id', 'user_id', 'running_evaluations'],
    emits: ['addnotification', 'pollevaluations', 'removerun'],
    data() {
        return {
            runningEvaluationIds: []
        }
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
        deleteRun(datasetId, runId) {
            if(datasetId === ""){
                datasetId=null
            }
            this.get(`/grpc/${this.user_id}/run_delete/${datasetId}/${runId}`).then(message => {
                console.log(message)
                this.$emit('removeRun', runId)
            }).catch(error => {
                this.$emit('addnotification', 'error', error.message)
            })
        },
        evaluateRun(datasetId, runId) {
            console.log('runs', this.runs)
            if(datasetId === ""){
                datasetId=null
            }
            this.get(`/grpc/${this.user_id}/run_eval/${datasetId}/${runId}`).then(message => {
                console.log(message)
                this.$emit('pollevaluations')
            }).catch(error => {
                this.$emit('addnotification', 'error', error.message)
            })
        }
    },
    beforeMount() {
        this.runningEvaluationIds = this.running_evaluations.map(e => {return e.run_id})
        console.log('running evaluation ids (uploads)', this.runningEvaluationIds)
    }
}
</script>
