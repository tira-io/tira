import NotificationBar from './components/elements/notification-bar.vue'
import VmControlPanel from './components/submission/vm-control-panel.vue'
import UploadSubmissionPanel from './components/submission/upload-submission-panel.vue'
import DockerSubmissionPanel from './components/submission/docker-submission-panel.vue'
import VmSubmissionPanel from './components/submission/vm-submission-panel.vue'
import RunningProcessList from './components/running-process-list.vue'

import {createApp, createCommentVNode} from 'vue';
import UIkit from 'uikit';

// Fontawesome Icons
import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import {
    faCheck,
    faTimes,
    faUserSlash,
    faUsers,
    faUsersSlash,
    faLevelUpAlt,
    faUser,
    faSearch,
    faCircleNotch,
    faDownload,
    faSave,
    faTrashAlt,
    faCog,
    faPlus,
    faBoxOpen,
    faTerminal,
    faUpload,
    faFolderPlus,
    faQuestion,
    faInfo,
    faBan,
    faSortAmountUp, faEye, faEyeSlash, faSortNumericDown
} from '@fortawesome/free-solid-svg-icons'

library.add(faCheck, faTimes, faUserSlash, faUsers, faUsersSlash, faLevelUpAlt, faUser, faSearch, faDownload, faSave,
    faTrashAlt, faCog, faPlus, faBoxOpen, faTerminal, faUpload, faFolderPlus, faQuestion, faCircleNotch, faInfo, faBan,
    faSortAmountUp, faEye, faEyeSlash, faSortNumericDown)


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
                host: '-',
                os: '-',
                ram: '-',
                cpus: '-',
                isSshOpen: false,
                isRdpOpen: false,
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
        RunningProcessList
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
        stopRun(runId) {
            this.get(`/grpc/${this.task.task_id}/${this.vm.vm_id}/stop_docker_software/${runId}`).then(message => {
                console.log(message)
            }).catch(error => {
                console.log(error)
            })
            
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
                this.vmStatus = {
                    host: message.context.host,
                    os: message.context.guestOs,
                    ram: message.context.memorySize,
                    cpus: message.context.numberOfCpus,
                    isSshOpen: message.context.sshPortStatus,
                    isRdpOpen: message.context.rdpPortStatus,
                    connectionError: false
                }
                this.vmState = message.context.state
            }).catch(error => {
                this.vmStatus = {
                    host: '-',
                    os: '-',
                    ram: '-',
                    cpus: '-',
                    isSshOpen: false,
                    isRdpOpen: false,
                    connectionError: true
                }
                this.vmState = 10
            })
            this.polling.vmInfo = false
        },
        pollVmState() {
            console.log('poll state')
            this.get(`/grpc/${this.vm.vm_id}/vm_state`).then(message => {
                console.log('state message: ', message)
                this.vmState = parseInt(message.state)
                if (this.isInTransition){
                    if (!this.polling.state) {
                        this.polling.state = true
                        this.pollStateInterval = setInterval(this.pollVmState, 10000)  // Note: https://stackoverflow.com/questions/61683534/continuous-polling-of-backend-in-vue-js
                    }
                }
                else if (this.vmState === 1 && (!this.vmStatus.isSshOpen || !this.vmStatus.isRdpOpen) ) {
                    this.loadVmInfo()
                    if (!this.polling.state) {
                        this.polling.state = true
                        this.pollStateInterval = setInterval(this.pollVmState, 10000)  // Note: https://stackoverflow.com/questions/61683534/continuous-polling-of-backend-in-vue-js
                    }
                }
                else {
                    clearInterval(this.pollStateInterval)
                    this.pollStateInterval = null
                    if (this.polling.state) {
                        this.get(`/api/task/${this.task.task_id}/user/${this.vm.vm_id}`).then(message => {
                            this.software = message.context.software  // NOTE: this should add the new runs
                        })
                        this.polling.state = false
                    }
                }
            }).catch(error => {
                this.addNotification('error', error)
                clearInterval(this.pollStateInterval)
                this.pollStateInterval = null
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
                clearInterval(this.pollEvaluationsInterval)
                this.pollEvaluationsInterval = null
            })
        },
        pollRunningSoftware() {
            console.log('poll running containers')
            this.get(`/api/task/${this.task.task_id}/user/${this.userId}/software/running`).then(message => {
                if (message.context.running_software.length > 0) {
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
                clearInterval(this.pollSoftwareInterval)
                this.pollSoftwareInterval = null
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
            return [3, 4, 5, 6, 7, 9].includes(this.vmState);
        },
        isSoftwareRunning() {
            return [5, 6, 7].includes(this.vmState);
        },
        vmConnectionError() {
            return this.vm.connectionError
        }
    },
    watch: {
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
