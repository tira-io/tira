import Loading from "./Loading.vue";
import RunActions from "./RunActions.vue";
import RunList from "./RunList.vue";
import SoftwareDetails from "./SoftwareDetails.vue";
import SubmitButton from "./SubmitButton.vue";
import TiraBreadcrumb from "./TiraBreadcrumb.vue";
import TiraTaskAdmin from "./TiraTaskAdmin.vue";
import TaskDocumentation from "./TaskDocumentation.vue"
import RegisterForm from "./RegisterForm.vue"
import LoginToSubmit from "./LoginToSubmit.vue";
import ExistingDockerSubmission from "../submission-components/ExistingDockerSubmission.vue";
import NewDockerSubmission from "../submission-components/NewDockerSubmission.vue";
import EditTask from "./EditTask.vue"
import SubissionIcon from "./SubmissionIcon.vue"
import ConfirmDelete from "./ConfirmDelete.vue"
import CodeSnippet from "./CodeSnippet.vue"

import { useDisplay } from 'vuetify'

function is_mobile() {   
    const { mobile } = useDisplay()
    return mobile.value
}

export {Loading, RunActions, RunList, SoftwareDetails, SubmitButton, TiraBreadcrumb, TiraTaskAdmin, TaskDocumentation, RegisterForm, LoginToSubmit, ExistingDockerSubmission, NewDockerSubmission, EditTask, SubissionIcon, ConfirmDelete, CodeSnippet, is_mobile}
