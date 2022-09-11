<template>
<div class="uk-grid-small uk-grid-match" uk-grid>
    <div class="uk-card uk-card-small uk-card-body uk-card-default uk-width-1-2">
        <table>
            <tr>
                <td>Host</td>
                <td id="vm-info-host">
                    <div v-show="polling.vmInfo" uk-spinner="ratio: 0.5"></div>
                </td>
            </tr>
            <tr>
                <td>OS</td>
                <td>{{ vmstatus.os }}</td>
            </tr>
            <tr>
                <td>RAM</td>
                <td>{{ vmstatus.ram }}</td>
            </tr>
            <tr>
                <td>CPU</td>
                <td>{{ vmstatus.cpus }}</td>
            </tr>
        </table>
    </div>
    <div class="uk-card uk-card-small uk-card-body uk-card-default uk-width-1-4" id="vm_state">
        <table>
            <tr>
                <td>State</td>
                <td>
                    <div v-show="polling.state" uk-spinner="ratio: 0.5"></div>
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
                    <div v-if="vmstatus.isSshOpen"
                         uk-tooltip="title: You can connect to this machine via secure shell (SSH). Consult the user documentation for an explanation on how to connect to VMs.; delay: 500"
                         class="uk-label uk-label-success">open</div>
                    <div v-if="!vmstatus.isSshOpen"
                         uk-tooltip="title: SSH is closed and you can not connect. If the machine is running, but this port is closed, consult the FAQ or the support forums.; delay: 500"
                         class="uk-label uk-label-danger">closed</div>
                </td>
            </tr>
            <tr>
                <td class="uk-table-shrink uk-text-nowrap uk-table-middle">
                    RDP <span class="uk-text-lead uk-text-small">port {{ vm.rdp }} </span>&nbsp;&nbsp;
                </td>
                <td>
                    <div v-if="vmstatus.isRdpOpen"
                         uk-tooltip="title: You can connect to this machine via remote desktop (RDP). Consult the user documentation for an explanation on how to connect to VMs.; delay: 500"
                         class="uk-label uk-label-success">open</div>
                    <div v-if="!vmstatus.isRdpOpen"
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
                :class="{ 'uk-button-disabled': vmstate !== 2, 'uk-button-primary': vmstate === 2}"
                :disabled="vmstate !== 2">Power On</button>
        <button @click="vmAction(`/grpc/${this.vm.vm_id}/vm_shutdown`, 4)"
                uk-tooltip="title: Gracefully shut down the machine. This only works when the machine is idle.; delay: 500"
                class="uk-button uk-text-center uk-width-1-1"
                :class="{ 'uk-button-disabled': vmstate !== 1, 'uk-button-danger': vmstate === 1}"
                :disabled="vmstate !== 1">Shut Down</button>
        <button @click="vmAction(`/grpc/${this.vm.vm_id}/vm_stop`, 4)"
                uk-tooltip="title: Pull the plug. Use with great care.; delay: 500"
                class="uk-button uk-text-center uk-width-1-1"
                :class="{ 'uk-button-disabled': ![3,4].includes(vmstate), 'uk-button-danger': [3,4].includes(vmstate)}"
                :disabled="![3,4].includes(vmstate)">Stop VM</button>
        <button @click="vmAction(`/grpc/${this.vm.vm_id}/run_abort`, 0)"
                uk-tooltip="title: Abort a run and attempt to unsandbox.; delay: 500"
                class="uk-button uk-text-center uk-width-1-1"
                :class="{ 'uk-button-disabled': ![5,6,7].includes(vmstate), 'uk-button-danger': [5,6,7].includes(vmstate)}"
                :disabled="![5,6,7].includes(vmstate)">Abort Run</button>
    </div>
</div>

<div id="modal-command-help" class="uk-modal-container" uk-modal>
    <div class="uk-modal-dialog uk-modal-body uk-margin-auto-vertical">
        <button class="uk-modal-close-default" type="button" uk-close></button>
        <h2 class="uk-modal-title">Commands Help for {{ task.task_name }}</h2>
        <p>
        The <em>Command</em> will be executed on your Virtual Machine. By default, it will be run from your user's home directory.
            You can select a different location in the <em>Working Directory</em> input.
        </p>
        <table v-if="isDefaultCommand"
            class="uk-table uk-table-small uk-table-divider uk-align-center uk-margin-bottom">
            <thead>
                <tr><td colspan="2">You can use the following variables in your Commands:</td></tr>
                <tr><th>Variable</th><th>Description</th></tr>
            </thead>
            <tfoot>
            <tr><td class="uk-text-bold">$inputDataset</td><td>This will resolve to the full path to the directory that contains the <em>dataset you have selected</em>.</td></tr>
            <tr><td class="uk-text-bold">$outputDir</td><td>This will resolve to the full path to the directory where <em>your software must write it's output</em></td></tr>
            </tfoot>
        </table>
        <div v-if="!isDefaultCommand">{{ task.command_description }}</div>

        <div v-if="isDefaultCommandPlaceholder">
            <label class="uk-form-label">Example Command in TIRA</label>
            <pre><code>my-software/run.sh -i $inputDataset -o $outputDir</code></pre>
            <label class="uk-form-label">Example Command in the Virtual Machine</label>
            <pre><code>my-software/run.sh -i /media/training-datasets/{{ task.task_id }}/&lt;Input Dataset&gt; -o /tmp/{{ vm_id }}/&lt;RUN&gt;/output</code></pre>
        </div>
        <div v-if="!isDefaultCommandPlaceholder">
            <label class="uk-form-label">Example Command in TIRA</label>
            <pre><code>{{ task.command_placeholder }}</code></pre>
        </div>
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
    props: ['csrf', 'dataset_id', 'vm', 'vmstatus', 'polling', 'statelabels', 'vmstate', 'task'],
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
                    this.vmstate = newState
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
            return `title: ${this.stateToolTips[this.vmstate]}; delay: 500`
        },
        stateLabel() {
            return this.statelabels[this.vmstate]
        },
        warningState() {
            return [3, 5, 6, 7, 9].includes(this.vmstate)
        },
        successState() {
            return [1, 8].includes(this.vmstate)
        },
        dangerState() {
            return [0, 2, 10].includes(this.vmstate)
        },
        sshConnectionExample() {
            return `ssh ${this.vm.vm_id}@${this.vm.host} -p ${this.vm.ssh} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no`
        },
        isDefaultCommand() {
            return (this.task.command_description === 'Available variables: <code>$inputDataset</code>, <code>$inputRun</code>, <code>$outputDir</code>, <code>$dataServer</code>, and <code>$token</code>.')
        },
        isDefaultCommandPlaceholder() {
            return (this.task.command_placeholder === 'mySoftware -c $inputDataset -r $inputRun -o $outputDir')
        }
    }
}
</script>