import NotificationBar from './components/notificationbar.vue'
import VmControlPanel from './components/vmcontrolpanel.vue'

import {createApp} from 'vue';
import UIkit from 'uikit';
import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

// CSS
require('../../static/tira/css/tira-style.css');

const app = createApp({
    data() {
        return {
            notifications: [],
            role: '',
            task: '',
            userId: '',
            vm: '',
            vmState: 10,
            vmStatus: {
                host: '',
                os: '',
                ram: '',
                cpus: '',
                isSshOpen: '',
                isRdpOpen: '',
                connectionError: false
            },
            stateLabels: {0: "error", 1: "running", 2: "stopped", 3: "powering on", 4: "powering off", 5: "sandboxing",
                6: "unsandboxing", 7: "executing", 8: "archived", 9: "unarchiving", 10: "unavailable",
            },
            software: '',
            datasets: '',
            upload: '',
            docker: '',
            isDefault: '',
            polling: {
                state: false,
                software: false,
                evaluation: false,
                vmInfo: false,
            },
            pollEvaluationsInterval: null,
            pollStateInterval: null,
            csrf: (<HTMLInputElement>document.querySelector('[name=csrfmiddlewaretoken]')).value
        }
    },
    components: {
        NotificationBar, VmControlPanel
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
        addNotification(type, message) {  // TODO: replace warningAlert calls with this
            // valid types are: success, warning, error
            this.notifications.push({'type': type, 'message': message})
        },
        closeModal() {
            // TODO
            const inspectModal = document.getElementById('inspect-modal')
            UIkit.modal(inspectModal).hide();
        },
        // addSoftwareEvents() {
        //     if(is_default != "True"){
        //         $('#add-software').click(function () {
        //             addSoftware(taskId, vmId);
        //         });
        //         $('.software-run-button').click(function () {
        //             runSoftware(taskId, vmId, $(this).data('tiraSoftwareId'))
        //         });
        //         $('.software-save-button').click(function () {
        //             saveSoftware(taskId, vmId, $(this).data("tiraSoftwareId"));
        //         })
        //         $('.software-delete-button').click(function () {
        //             let formId = '#' + $(this).data("tiraSoftwareId") + '-row'
        //             deleteSoftware(taskId, vmId, $(this).data("tiraSoftwareId"), $(formId));
        //         })
        //         $('.software-select').change(function () {
        //             updateSoftwareRunButton()
        //         });
        //         $('.command-input').change(function () {
        //             updateSoftwareRunButton()
        //         });
        //     }
        //     $('#upload-button').click(function (e) {
        //         e.preventDefault()
        //         upload(taskId, vmId);
        //     })
        //     $('#docker-add-button').click(function (e) {
        //         e.preventDefault()
        //         addDockerSoftware(taskId, vmId);
        //     })
        //     $('.docker-delete-button').click(function (e) {
        //             e.preventDefault()
        //             deleteDockerSoftware(taskId, vmId, $(this).data("tiraDockerSoftwareId"));
        //     })
        //     $('.docker-run-button').click(function (e) {
        //             e.preventDefault()
        //             docker_software_id = $(this).data('tiraRunDockerSoftwareId')
        //             runDockerSoftware(taskId, vmId, docker_software_id);
        //     })
        //     $('.run-delete-button').click(function () {
        //         deleteRun($(this).data('tiraDataset'),
        //             $(this).data('tiraVmId'),
        //             $(this).data('tiraRunId'), $(this).parent().parent())
        //     })
        //     $('.run-evaluate-button').click(function () {
        //         evaluateRun($(this).data('tiraDataset'),
        //                      $(this).data('tiraVmId'),
        //                      $(this).data('tiraRunId'))
        //     });
        // },
        loadVmInfo() {
            console.log('load vm info', this.vm)
            this.polling.vmInfo = true
            this.get(`/grpc/${this.vm.vm_id}/vm_info`).then(message => {
                console.log('load vm info: ', message)
                if (message.status === 'Accepted') {
                    this.state = message.state
                    this.vmStatus.os = message.guestOs
                    this.vmStatus.host = message.host
                    this.vmStatus.ram = message.memorySize
                    this.vmStatus.cpus = message.numberOfCpus
                    this.vmState = message.state
                    this.vmStatus.isSshOpen = message.sshPortStatus
                    this.vmStatus.isRdpOpen = message.rdpPortStatus

                    if (this.isInTransition(message.state) && !this.polling.state){
                        this.pollStateInterval = setInterval(this.pollVmState, 10000)
                        this.polling.state = true;
                    } else if (message.state === 1 && (!message.sshPortStatus || !message.rdpPortStatus) ) {
                        this.polling.state = true;
                        this.pollStateInterval = setInterval(this.pollVmState, 10000)
                    }
                } else {
                    this.vmStatus.connectionError = true
                    this.vmState = 10
                }
                this.polling.vmInfo = false
            }).catch(error => {
                this.addNotification('error', error)
                this.polling.vmInfo = false
            })
        },
        pollVmState() {
            console.log('poll state')
            this.get(`/grpc/${this.vm.vm_id}/vm_state`).then(message => {
                if (this.isInTransition){
                    if (this.isSoftwareRunning){
                        this.polling.software=true;
                    }
                    this.vmState = message.state;
                } else {
                    // Note: It's easiest to reload the page here instead of adding the runs to the table via JS. TODO
                    clearInterval(this.pollState)
                    if (this.polling.software) location.reload();
                }
            }).catch(error => {
                this.addNotification('error', error)
            })
        },
        pollRunningEvaluations() {
            console.log('poll running evaluations')
            this.get(`/grpc/${this.vm.vm_id}/vm_running_evaluations`).then(message => {
                if (message.running_evaluations === true){
                    this.polling.evaluation=true;
                } else {
                    // Note: It's easiest to reload the page here instead of adding the runs to the table via JS. TODO
                    clearInterval(this.pollEvaluationsInterval)
                    if (this.polling.evaluation) {
                        setTimeout(function () {
                            location.reload()
                        }, 3000);
                    }
                }
            }).catch(error => {
                this.addNotification('error', error)
            })
        }
    },
    beforeMount() {
        // Here we get the inital user information to render the page from the rest api
        this.get(`/api/role`).then(message => {
            this.role = message.role
            let pageUrlSplits = window.location.pathname.split("/")
            this.get(`/api/task/${pageUrlSplits.at(-3)}/user/${pageUrlSplits.at(-1)}`).then(message => {
                console.log(message.context)
                this.task = message.context.task
                this.userId = message.context.user_id
                this.vm = message.context.vm
                this.software = message.context.software
                this.datasets = message.context.datasets
                this.upload = message.context.upload
                this.docker = message.context.docker
                this.isDefault = message.context.is_default
                if(!this.isDefault) {
                    this.loadVmInfo()
                    this.pollStateInterval = setInterval(this.pollVmState, 10000)
                }
                this.pollEvaluationsInterval = setInterval(this.pollRunningEvaluations, 10000)  // Note: https://stackoverflow.com/questions/61683534/continuous-polling-of-backend-in-vue-js
            })
        }).catch(error => {
            this.addNotification('error', error)
        })
    },
    computed: {
        userDisplayName() {
            return this.userId.replace(/-default/, '')
        },
        isInTransition() {
            return [3, 4, 5, 6, 7].includes(this.vmState);
        },
        isSoftwareRunning() {
            return [5, 6, 7].includes(this.vmState);
        },
        vmConnectionError() {
            return this.vm.connectionError
        }
    },
    watch: {
        vmState(newState, oldState){
            if (newState === 0) {
                this.pollStateInterval = setInterval(this.pollVmState, 10000)

            }
        }
    }
})
app.component('font-awesome-icon', FontAwesomeIcon)

app.config.compilerOptions.delimiters = ['[[', ']]']
app.mount("#vue-user-mount");
