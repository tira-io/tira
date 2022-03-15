export default {
    data() {
        return {
            createVmError: '',
            batched: '',
            batchInput: '',
            vmIdInput: '',
            selectedOva: '',
            selectedHost: '',
            ovaList: [],
            hostList: [],
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
                'X-CSRFToken': this.csrf})

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
        createVm() {
            this.createVmError = ''
            if (this.selectedOva === '') {
                this.createVmError += 'Please select a VM Template;\n'
            }
            if (this.selectedHost === '') {
                this.createVmError += 'Please select a target host;\n'
            }
            if (this.vmIdInput === '') {
                this.createVmError += 'Please provide an id for the new VM;\n'
            }
            if (this.createVmError !== '') {
                return
            }
            this.submitPost('tira-admin/create-vm', {
                'vm_id': this.vmIdInput,
                'ova': this.selectedOva,
                'host': this.selectedHost
            }).then(message => {
                this.$emit('addnotification', 'success', message.message)
            }).catch(error => {
                console.log(error)
                this.createVmError = error
            })
        },
        createInBatches() {
            if (this.batchInput === '') {
                this.createVmError = 'Please select a VM Template'
                return
            }
            let lines = this.batchInput.split('\n');
            for (const elem of lines) {
                let params = elem.split(",")
                // error if not formatted
                if (params[0] === undefined || params[1] === undefined || params[2] === undefined){
                    this.$emit('addnotification', 'error', `Ill-defined parameters: ${elem}. Skipping this line.`)
                    continue
                }
                this.submitPost('tira-admin/create-vm', {
                    'vm_id': params[0],
                    'ova': params[1],
                    'host': params[2]
                }).then(message => {
                    this.$emit('addnotification', 'success', `Accepted vm create for vm ${params[0]}: ${message.message}`)
                }).catch(error => {
                    this.createVmError = error
                })
            }
        },
    },
    beforeMount() {
        this.get(`/api/ova-list`).then(message => {
            this.ovaList = message.context.ova_list
        }).catch(error => {
            this.$emit('addnotification', 'error', `Error loading template list: ${error}`)
        })
        this.get(`/api/host-list`).then(message => {
            this.hostList = message.context.host_list
        }).catch(error => {
            this.$emit('addnotification', 'error', `Error loading host list: ${error}`)
        })
    },
    template: `
<div class="uk-grid-small uk-margin-small" uk-grid>
    <div class="uk-margin-right">
        <h2>Create VM</h2>
    </div>
    <div class="uk-margin-small-top">
        <input id="batch-create" class="uk-checkbox" type="checkbox" v-model="this.batched">&nbsp;
        <label for="batch-create">Create in batches</label>
    </div>
</div>
<div v-if="this.batched">
    <div class="uk-margin-small">
        <label for="batch-create-input">Batch Create</label>
        <textarea id="batch-create-input" class="uk-textarea" type="text" 
                  placeholder="vm_id_1,template_id,hostname\nvm_id_2,template_id,hostname"
                  :class="{'uk-form-danger': (this.createVmError !== '' && this.batchInput === '')}" 
                  v-model="batchInput"/>
    </div>
    <button class="uk-button uk-button-primary" @click="createInBatches" >Create VMs</button>
    <span class="uk-text-danger uk-margin-small-left">[[ this.createVmError ]]</span>
</div>
<div v-else>
    <div class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-expand">
            <label for="vm-id-input">VM ID</label>
            <input id="vm-id-input" class="uk-input" type="text" placeholder="Please provide a vm_id ..."
                   :class="{'uk-form-danger': (this.createVmError !== '' && this.vmIdInput === '')}"
                   v-model="vmIdInput">
        </div>
        <div class="uk-width-1-4">
            <label for="ova-select">VM Template</label>
            <select id="ova-select" class="uk-select" v-model="this.selectedOva"
                   :class="{'uk-form-danger': (this.createVmError !== '' && this.selectedOva === '')}">
                <option disabled value="">Please select a vm template</option>
                <option v-for="ova in this.ovaList" :value="ova">[[ ova ]]</option>
            </select>
        </div>
        <div class="uk-width-1-4">
            <label for="host-select">Host</label>
            <select id="host-select" class="uk-select" v-model="this.selectedHost"
                   :class="{'uk-form-danger': (this.createVmError !== '' && this.selectedHost === '')}">
                <option disabled value="">Please select a host</option>
                <option v-for="host in this.hostList" :value="host">[[ host ]]</option>
            </select>
        </div>
    </div>
    <button class="uk-button uk-button-primary" @click="createVm">Create VM</button>
    <span class="uk-text-danger uk-margin-small-left">[[ this.createVmError ]]</span>
</div>`
}