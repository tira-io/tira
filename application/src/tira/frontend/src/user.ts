import NotificationBar from './components/notificationbar.vue'
import VmControlPanel from './components/vmcontrolpanel.vue'
import UploadSubmissionPanel from './components/uploadsubmissionpanel.vue'
import DockerSubmissionPanel from './components/dockersubmissionpanel.vue'
import VmSubmissionPanel from './components/vmsubmissionpanel.vue'
import SubmissionResultsPanel from './components/submissionresultspanel.vue'
import RunningProcessList from './components/runningprocesslist.vue'

import {createApp} from 'vue';
import UIkit from 'uikit';

// Fontawesome Icons
import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { faCheck, faTimes, faUserSlash, faUsers, faUsersSlash, faLevelUpAlt, faUser, faSearch, faCircleNotch,
    faDownload, faSave, faTrashAlt, faCog, faPlus, faBoxOpen, faTerminal, faUpload, faFolderPlus, faQuestion } from '@fortawesome/free-solid-svg-icons'

library.add(faCheck, faTimes, faUserSlash, faUsers, faUsersSlash, faLevelUpAlt, faUser, faSearch, faDownload, faSave,
    faTrashAlt, faCog, faPlus, faBoxOpen, faTerminal, faUpload, faFolderPlus, faQuestion, faCircleNotch)


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
            pollSoftwareInterval: null,
            runningEvaluations: [],
            runningSoftware: [],
            pollStateInterval: null,
            selectedSubmissionType: 'upload',
            loading: true,
            csrf: (<HTMLInputElement>document.querySelector('[name=csrfmiddlewaretoken]')).value
        }
    },
    components: {
        NotificationBar, VmControlPanel, UploadSubmissionPanel, DockerSubmissionPanel, VmSubmissionPanel,
        SubmissionResultsPanel, RunningProcessList
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
            // TODO Review Modals
            const inspectModal = document.getElementById('inspect-modal')
            UIkit.modal(inspectModal).hide();
        },
        removeRun(runId, type) {
            if (type === 'upload') {
                this.upload.runs = this.upload.runs.filter(e => {
                    return e.run_id !== runId
                })
            }
            if (type === 'docker') {
                this.docker.runs = this.docker.runs.filter(e => {
                    return e.run_id !== runId
                })
            }
            if (type === 'vm') {
                this.software.runs = this.software.runs.filter(e => {
                    return e.run_id !== runId
                })
            }

        },
        addSoftware(newSoftware) {
            this.software.push(newSoftware)
        },
        deleteSoftware(softwareId) {
            this.software = this.software.filter(e => {
                return e.software.id !== softwareId
            })
        },
        addContainer(newContainer) {
            this.docker.docker_softwares.push(newContainer.context)
        },
        deleteContainer(containerId) {
            this.docker.docker_softwares = this.docker.docker_softwares.filter(e => {
                return e.docker_software_id !== containerId
            })
        },
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
                // TODO: When the tira-host is unavailable (planned occurrence) the server will still throw a 500.
                // I've removed this notification here because it distresses the users.
                // this.addNotification('error', error)
                this.polling.vmInfo = false
            })
        },
        pollVmState() {
            console.log('poll state')
            this.get(`/grpc/${this.vm.vm_id}/vm_state`).then(message => {
                if (this.isInTransition){
                    if (this.isSoftwareRunning){
                        if (!this.polling.state) {
                            this.polling.state = true
                            this.pollStateInterval = setInterval(this.pollVmState, 10000)  // Note: https://stackoverflow.com/questions/61683534/continuous-polling-of-backend-in-vue-js
                        }
                        this.polling.state=true;
                    }
                    this.vmState = message.state;
                } else {
                    clearInterval(this.pollState)
                    this.pollStateInterval = null
                    if (this.polling.state) {
                        this.get(`/api/task/${this.task.task_id}/user/${this.vm.vm_id}`).then(message => {
                            this.software = message.context.software  // NOTE: this should add the new runs
                        })
                    }
                }
            }).catch(error => {
                this.addNotification('error', error)
            })
        },
        pollRunningEvaluations() {  // TODO, this should also update the evaluations when it succeeds.
            console.log('poll running evaluations')
            this.get(`/grpc/${this.vm.vm_id}/vm_running_evaluations`).then(message => {
                console.log('found running evaluations', message)
                if (message.running_evaluations === true){
                    if (!this.polling.evaluation) {
                        this.polling.evaluation=true;
                        this.pollEvaluationsInterval = setInterval(this.pollRunningEvaluations, 10000)  // Note: https://stackoverflow.com/questions/61683534/continuous-polling-of-backend-in-vue-js
                    }
                    this.get(`/grpc/${this.vm.vm_id}/get_running_evaluations`).then(message => {
                        console.log('running evaluations: ', message)
                        // NOTE: this should update the running evaluations.
                        this.runningEvaluations = message.running_evaluations
                    }).catch(error => {
                        this.addNotification('error', error)
                    })
                } else {
                    clearInterval(this.pollEvaluationsInterval)
                    this.pollEvaluationsInterval = null
                    console.log("clear eval poll interval")
                    if (this.polling.evaluation) {
                        this.polling.evaluation = false
                        this.runningEvaluations = []  // When the call finished, clear all running evaluations.
                        console.log("polling evaluations succeeded")
                    }
                }
            }).catch(error => {
                this.addNotification('error', error)
            })
        },
        pollRunningSoftware() {
            console.log('poll running containers')

            this.get(`/api/task/${this.task.task_id}/user/${this.userId}/software/running`).then(message => {
                console.log('containers: ', message.context.running_software)
                if (message.context.running_software.length > 1) {
                    this.runningSoftware = message.context.running_software
                    if (!this.polling.software) {
                        this.polling.software = true
                        this.pollSoftwareInterval = setInterval(this.pollRunningSoftware, 10000)  // Note: https://stackoverflow.com/questions/61683534/continuous-polling-of-backend-in-vue-js
                    }
                } else {
                    clearInterval(this.pollSoftwareInterval)
                    this.pollSoftwareInterval = null
                    console.log("clear software poll interval")
                    if (this.polling.software) {
                        this.polling.software = false
                        this.runningSoftware = []  // When the call finished, clear all running evaluations.
                        console.log("polling software finished")
                    }
                }
            }).catch(error => {
                this.addNotification('error', error.message)
            })

        },
        loaded(submissionType) {
            if (this.loading) {
                return false
            }
            if (this.selectedSubmissionType === submissionType) {
               if (submissionType === 'upload' && this.upload) {
                   return true
               } else if (submissionType === 'docker') {
                   return true
               } else if (submissionType === 'vm' && this.software && !this.isDefault) {
                   return true
               } else if (submissionType === 'vm') {  // TODO for testing, maybe we can leave this in
                   return true
               }
            }
        }
    },
    beforeMount() {
        // Here we get the inital user information to render the page from the rest api
        this.get(`/api/role`).then(message => {
            this.role = message.role
            let pageUrlSplits = window.location.pathname.split("/")
            this.get(`/api/task/${pageUrlSplits.at(-3)}/user/${pageUrlSplits.at(-1)}`).then(message => {
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
                    this.pollVmState()
                }
                this.pollRunningEvaluations()
                this.pollRunningSoftware()
                this.loading = false
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
        },
        runningSoftware(newRunningSoftware, oldRunningSoftware) {
        /* Check if a container finished by comparing the new and old lists of running containers.
        *  Reload the submission if true.
        *  */
            let newRunningSoftwareIds = newRunningSoftware.map(software => {
                return software.run_id
            })
            for (let ind in oldRunningSoftware) {
                if (!newRunningSoftwareIds.includes(oldRunningSoftware[ind].run_id)) {
                    this.get(`/api/task/${this.task.task_id}/user/${this.userId}`).then(message => {
                        this.docker = message.context.docker
                    })
                    return
                }
            }
        },
    }
})
app.component('font-awesome-icon', FontAwesomeIcon)

app.config.compilerOptions.delimiters = ['[[', ']]']
app.mount("#vue-user-mount");
