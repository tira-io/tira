<script charset="utf-8">
export default {
    data() {
        return {
            modifyVmError: '',
            vmInput: '',
            memoryInput: '',
            cpusInput: '',
            storageInput: '',
            selectedStorage: 'hdd',
        }
    },
    emits: ['addnotification'],
    props: ['csrf'],
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
        async submitPost(url, params) {
            const headers = new Headers({
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrf
            })

            const response = await fetch(url, {
                method: "POST",
                headers,
                body: JSON.stringify(params)
            })
            if (!response.ok) {
                throw new Error(`Error fetching endpoint: ${url} with ${response.status}`);
            }
            let results = await response.json()
            if (results.status === 1) {
                throw new Error(`${results.message}`);
            }
            return results
        },
        modify() {
            this.modifyVmError = ''
            if (this.selectedStorage === '') {
                this.createTaskError += 'Please select a Task;\n'
            }
            if (this.datasetNameInput === '') {
                this.createTaskError += 'Please provide a name for the new Dataset;\n'
            }
            if (!(this.trainingCheck || this.devCheck || this.testCheck)) {
                this.createTaskError += 'Please declare if you create a training, test, and/or dev dataset for this name\n'
            }
            if (this.createTaskError !== '') {
                return
            }
            this.submitPost('tira-admin/add-dataset', {
                'dataset_id': this.datasetId,
                'name': this.datasetNameInput,
                'master_id': this.masterVmInput,
                'task': this.selectedTask.task_id,
                'training': this.trainingCheck,
                'dev': this.devCheck,
                'test': this.testCheck,
                'evaluator_working_directory': this.evaluatorWorkingDirectory,
                'evaluator_command': this.evaluatorCommand,
                'evaluation_measures': this.evaluationMeasures,
            }).then(message => {
                this.$emit('addnotification', 'success', message.message)
            }).catch(error => {
                console.log(error)
                this.createTaskError = error
            })
        },
        string_to_slug(str) {
            str = str.replace(/^\s+|\s+$/g, ''); // trim
            str = str.toLowerCase();

            // remove accents, swap ñ for n, etc
            var from = "àáäâèéëêìíïîòóöôùúüûñç·/_,:;";
            var to = "aaaaeeeeiiiioooouuuunc------";
            for (var i = 0, l = from.length; i < l; i++) {
                str = str.replace(new RegExp(from.charAt(i), 'g'), to.charAt(i));
            }

            str = str.replace(/\./g, '-')
                .replace(/[^a-z0-9 -]/g, '') // remove invalid chars
                .replace(/\s+/g, '-') // collapse whitespace and replace by -
                .replace(/-+/g, '-'); // collapse dashes

            return str;
        },
    },
    beforeMount() {
        this.get(`/api/task-list`).then(message => {
            this.taskList = message.context.task_list
        }).catch(error => {
            this.$emit('addnotification', 'error', `Error loading task list: ${error}`)
        })
    },
    watch: {
        datasetNameInput(newName, oldName) {
            this.datasetId = this.string_to_slug(newName)
        }
    }
}
</script>
<template>
<div>
    Does not work yet. Empty fields will not be changed.
</div>
<div class="uk-grid-small uk-margin-small" uk-grid>
    <div class="uk-margin-right">
        <h2>Modify VM</h2>
    </div>
</div>
<div class="uk-margin-small">
    <div class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-1-3@m uk-width-1-1@s">
            <label for="vm-input">VM ID</label>
            <input id="vm-input" class="uk-input" type="text" placeholder="id-lowercase-with-dashes"
                   :class="{'uk-form-danger': (this.modifyVmError !== '' && this.vmInput === '')}"
                   v-model="vmInput">
        </div>
        <div class="uk-width-1-6@m uk-width-1-1@s">
            <label for="memory-input">Memory (GB)</label>
            <input id="memory-input" class="uk-input" type="text" placeholder="4"
                   :class="{'uk-form-danger': (this.modifyVmError !== '' && this.memoryInput === '')}"
                   v-model="memoryInput">
        </div>
        <div class="uk-width-1-6@m uk-width-1-1@s">
            <label for="cpus-input">CPUs</label>
            <input id="cpus-input" class="uk-input" type="text" placeholder="1"
                   v-model="cpusInput">
        </div>
        <div class="uk-width-1-6@m uk-width-1-2@s">
        <label for="storage-input">Storage (GB)</label>
        <input id="storage-input" class="uk-input" type="text" placeholder="10"
               v-model="storageInput">
        </div>
        <div class="uk-width-1-6@m uk-width-1-2@s">
            <label for="storage-select">Storage Type</label>
            <select id="storage-select" class="uk-select" v-model="this.selectedStorage">
                <option value="hdd" selected>hdd</option>
                <option value="sftp">SFTP</option>
            </select>
        </div>
    </div>
    <div class="uk-margin-small">
        <button class="uk-button uk-button-primary" @click="modify">Modify</button>
        <span class="uk-text-danger uk-margin-small-left">{{ this.modifyVmError }}</span>
    </div>
    *mandatory
</div>
</template>
