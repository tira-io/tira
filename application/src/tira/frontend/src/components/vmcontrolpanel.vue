<template>
<div class="uk-grid-small uk-grid-match" uk-grid>
    <div class="uk-card uk-card-small uk-card-body uk-card-default uk-width-1-2">
        <table class="uk-margin-small uk-table uk-table-divider uk-table-small uk-table-middle">
            <tr>
                <td class="uk-table-shrink" >Host</td>
                <td class="uk-text-nowrap">
                    {{ vm_status.host }} <div v-show="polling.vmInfo" uk-spinner="ratio: 0.4"></div>
                </td>
            </tr>
            <tr>
                <td class="uk-table-shrink" >OS</td>
                <td class="uk-text-nowrap">{{ vm_status.os }}</td>
            </tr>
            <tr>
                <td class="uk-table-shrink" >RAM</td>
                <td>{{ vm_status.ram }}</td>
            </tr>
            <tr>
                <td class="uk-table-shrink" >CPU</td>
                <td>{{ vm_status.cpus }}</td>
            </tr>
        </table>
    </div>
    <div class="uk-card uk-card-small uk-card-body uk-card-default uk-width-1-4" id="vm_state">
        <table>
            <tr>
                <td>State</td>
                <td>
                    <div v-show="polling.state" uk-spinner="ratio: 0.4"></div>
                    <div :uk-tooltip="stateToolTip"
                         class="uk-label"
                         :class="{ 'uk-label-success': successState, 'uk-label-warning': warningState, 'uk-label-danger': dangerState}" >
                      {{ stateLabel }}
                    </div>
                </td>
            </tr>
            <tr>
                <td class="uk-table-shrink uk-text-nowrap uk-table-middle">
                    SSH <span class="uk-text-lead uk-text-small">port {{ vm.ssh }} </span>&nbsp;&nbsp;
                </td>
                <td>
                    <div v-if="vm_status.isSshOpen"
                         uk-tooltip="title: You can connect to this machine via secure shell (SSH). Consult the user documentation for an explanation on how to connect to VMs.; delay: 500"
                         class="uk-label uk-label-success">open</div>
                    <div v-if="!vm_status.isSshOpen"
                         uk-tooltip="title: SSH is closed and you can not connect. If the machine is running, but this port is closed, consult the FAQ or the support forums.; delay: 500"
                         class="uk-label uk-label-danger">closed</div>
                </td>
            </tr>
            <tr>
                <td class="uk-table-shrink uk-text-nowrap uk-table-middle">
                    RDP <span class="uk-text-lead uk-text-small">port {{ vm.rdp }} </span>&nbsp;&nbsp;
                </td>
                <td>
                    <div v-if="vm_status.isRdpOpen"
                         uk-tooltip="title: You can connect to this machine via remote desktop (RDP). Consult the user documentation for an explanation on how to connect to VMs.; delay: 500"
                         class="uk-label uk-label-success">open</div>
                    <div v-if="!vm_status.isRdpOpen"
                         uk-tooltip="title: Remote desktop (RDP) is closed and you can not connect. If the machine is running, but this port is closed, consult the FAQ or the support forums.; delay: 500"
                         class="uk-label uk-label-danger">closed</div>
                </td>
            </tr>
        </table>

        <!-- The modal that shows the connection information -->
        <button class="uk-button uk-button-default uk-margin-small-right uk-margin-small-top" type="button" uk-toggle="target: #modal-close-default">Connection Info</button>
        <div id="modal-close-default" class="uk-modal-container" uk-modal>
            <div class="uk-modal-dialog uk-modal-body uk-margin-auto-vertical">
                <button class="uk-modal-close-default" type="button" uk-close></button>
                <h2 class="uk-modal-title">Connection Info:</h2>
                <table class="uk-table-small uk-margin-bottom">
                    <tr><td class="uk-text-bold">Host:</td><td>{{ vm.host }}</td></tr>
                    <tr><td><span class="uk-text-bold">User: </span></td><td>{{ vm.vm_id }}</td><td><span class="uk-text-bold">SSH Port: </span></td><td>{{ vm.ssh }}</td></tr>
                    <tr><td><span class="uk-text-bold">Password: </span></td><td>{{ vm.user_password }}</td><td><span class="uk-text-bold">RDP Port: </span></td><td>{{ vm.rdp }}</td></tr>
                </table>
                <label class="uk-form-label" for="form-stacked-text">SSH Example</label>
                <div class="uk-form-controls">
                    <input class="uk-input uk-width-3-4" id="form-stacked-text" type="text"
                           :value="sshConnectionExample">
                </div>
            </div>
        </div>
    </div>
    <div class="uk-width-1-4">
        <button @click="vmAction(`/grpc/${this.vm.vm_id}/vm_start`, 3)"
                uk-tooltip="title: Start the machine.; delay: 500"
                class="uk-button uk-text-center uk-width-1-1"
                :class="{ 'uk-button-disabled': vm_state !== 2, 'uk-button-primary': vm_state === 2}"
                :disabled="vm_state !== 2">Power On</button>
        <button @click="vmAction(`/grpc/${this.vm.vm_id}/vm_shutdown`, 4)"
                uk-tooltip="title: Gracefully shut down the machine. This only works when the machine is idle.; delay: 500"
                class="uk-button uk-text-center uk-width-1-1"
                :class="{ 'uk-button-disabled': vm_state !== 1, 'uk-button-danger': vm_state === 1}"
                :disabled="vm_state !== 1">Shut Down</button>
        <button @click="vmAction(`/grpc/${this.vm.vm_id}/vm_stop`, 4)"
                uk-tooltip="title: Pull the plug. Use with great care.; delay: 500"
                class="uk-button uk-text-center uk-width-1-1"
                :class="{ 'uk-button-disabled': ![3,4].includes(vm_state), 'uk-button-danger': [3,4].includes(vm_state)}"
                :disabled="![3,4].includes(vm_state)">Stop VM</button>
        <button @click="vmAction(`/grpc/${this.vm.vm_id}/run_abort`, 0)"
                uk-tooltip="title: Abort a run and attempt to unsandbox.; delay: 500"
                class="uk-button uk-text-center uk-width-1-1"
                :class="{ 'uk-button-disabled': ![5,6,7].includes(vm_state), 'uk-button-danger': [5,6,7].includes(vm_state)}"
                :disabled="![5,6,7].includes(vm_state)">Abort Run</button>
    </div>
</div>
</template>
<script>
export default {
    name: "vmcontrolpanel",
    data() {
        return {
            stateToolTips: [
              "This machine is idle.",
              "This machine is powering on, please stand by.",
              "This machine is powering off, please stand by.",
              "This machine is turned off. You can start the machine with 'POWER ON'",
              "This machine is sandboxed and running a software. You can not connect to or use the VM, nor start other runs until it finishes or the run is aborted. Running a software may take a long time.",
              "This machine is moved to the sandbox, please stand by.",
              "This machine is being removed from the sandbox, please stand by.",
              "This machine is in the archives. Please contact the support to get it reinstated.",
              "This machine is being reanimated.",
              "The state of this machine is not defined. Please contact the support.",
            ],
        }
    },
    emits: ['addnotification', 'closemodal', 'pollstate', "pollvminfo"],
    props: ['csrf', 'dataset_id', 'vm', 'vm_status', 'polling', 'state_labels', 'vm_state', 'task'],
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
        vmAction(endpoint, newState){
            this.get(endpoint).then(message => {
                if (message.status === 0) {
                    this.vm_state = newState
                    this.$emit('pollState')
                }
            }).catch(error => {
                this.$emit('addnotification', 'error', error.message)
                this.$emit('pollVmInfo')
            })
        },
    },
    beforeMount() {
    },
    computed: {
        stateToolTip() {
            return `title: ${this.stateToolTips[this.vm_state]}; delay: 500`
        },
        stateLabel() {
            return this.state_labels[this.vm_state]
        },
        warningState() {
            return [3, 5, 6, 7, 9].includes(this.vm_state)
        },
        successState() {
            return [1, 8].includes(this.vm_state)
        },
        dangerState() {
            return [0, 2, 10].includes(this.vm_state)
        },
        sshConnectionExample() {
            return `ssh ${this.vm.vm_id}@${this.vm.host} -p ${this.vm.ssh} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no`
        }
    }
}
</script>