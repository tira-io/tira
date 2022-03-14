export default {
    data() {
        return {
            createVmError: '',
            batched: '',
            batchInput: '',
            vmIdInput: '',
            ova_list: [],
            host_list: [],
        }
    },
    props: ['csrf'],
    methods: {
        async get(url) {
            const response = await fetch(url)
            if (!response.ok) {
                throw new Error(`Error fetching endpoint: ${url} with ${response.status}`);
            }
            let results = await response.json()
            if (results.status === 0) {
                throw new Error(`Error: ${results.message}`);
            }
            return results
        },
        async submitPost(url, params) {
            const response = await fetch(url)
            if (!response.ok) {
                throw new Error(`Error fetching endpoint: ${url} with ${response.status}`);
            }
            let results = await response.json()
            if (results.status === 0) {
                throw new Error(`Error: ${results.message}`);
            }
            return results
        },
        createVm() {

        },
        createInBatches() {
            // parse input, check input, then submit in a loop to create_vm
        },
    },
    beforeMount() {
        this.get(`/api/ova-list`).then(message => {
            this.ova_list = message.context.ova_list
            console.log(message)
        }).catch(error => {
            console.log(error)
            // todo emit error
        })
        this.get(`/api/host-list`).then(message => {
            this.host_list = message.context.host_list
            console.log(message)
        }).catch(error => {
            console.log(error)
            // todo emit error
        })
    },
    template: `
<div class="uk-grid-small uk-margin-medium" uk-grid>
    <div class="uk-margin-right">
        <h2>Create VM</h2>
    </div>
    <div class="uk-margin-small-top">
        <input id="batch-create" class="uk-checkbox" type="checkbox" v-model="this.batched">&nbsp;
        <label for="batch-create">Create in batches</label>
    </div>
</div>
<div v-if="this.batched">
    <label for="batch-create-input">Batch Create</label>
    <textarea id="batch-create-input" class="uk-textarea" type="text" placeholder="hostname,vm_id_1,ova_id
hostname,vm_id_2,..." 
              v-model="batchInput"/>
    <span class="uk-text-danger">[[ this.createVmError ]]</span>
    <button class="uk-button uk-button-primary" @click="createInBatches" >Create VMs</button>
</div>
<div v-else>
    <div class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-expand">
            <label for="vm-id-input">VM ID</label>
            <input id="vm-id-input" class="uk-input" type="text" placeholder="Please provide a vm_id ..."
                   v-model="vmIdInput">
        </div>
        <div class="uk-width-1-4">
            <label for="ova-select">VM Template</label>
            <select id="ova-select" class="uk-select" v-model="this.selected_ova">
                <option disabled value="None">Please select a vm template</option>
                <option v-for="ova in this.ova_list" :value="ova">[[ ova ]]</option>
            </select>
        </div>
        <div class="uk-width-1-4">
            <label for="host-select">Host</label>
            <select id="host-select" class="uk-select" v-model="this.selected_host">
                <option disabled value="">Please select a host</option>
                <option v-for="host in this.host_list" :value="host">[[ host ]]</option>
            </select>
        </div>
    </div>
    <span class="uk-text-danger">[[ this.createVmError ]]</span>
    <button class="uk-button uk-button-primary" @click="createVm">Create VM</button>
</div>`
}