<template>
    <span v-if="submission.review_state === 'valid'" class="mr1">
        <v-icon>mdi-check</v-icon>
        <v-tooltip activator="parent" location="top">The submission is valid (manually reviewed by the organizers).</v-tooltip>
    </span>
    <span v-if="submission.review_state === 'invalid'" class="mr1">
        <v-icon>mdi-alert-circle-outline</v-icon>
        <v-tooltip activator="parent" location="top">The submission is not valid (manually reviewed by the organizers).</v-tooltip>
    </span>
    <span v-if="submission.review_state !== 'invalid' && submission.review_state !== 'valid'" class="mr1">
        <v-icon>mdi-help</v-icon>
        <v-tooltip activator="parent" location="top">The submission is not yet reviewed by the organizers.</v-tooltip>
    </span>
    <span v-if="submission.is_software">
        <v-icon>mdi-docker</v-icon>
        <v-tooltip activator="parent" location="top">Software Submission</v-tooltip>
    </span>
    <span v-if="submission.is_upload">
        <v-icon>mdi-file-document</v-icon>
        <v-tooltip activator="parent" location="top">Run Submission</v-tooltip>
    </span>
    <span v-if="!submission.published" class="mr1">
        <v-icon>mdi-eye-off-outline</v-icon>
        <v-tooltip activator="parent" location="top">Not Published on Leaderboard</v-tooltip>
    </span>
    <span v-if="submission.published" class="mr1">
        <v-icon>mdi-eye-outline</v-icon>
        <v-tooltip activator="parent" location="top">Published on Leaderboard</v-tooltip>
    </span>
</template>
  
<script lang="ts">
  
export default {
    name: "submission-icon",
    props: ['submission'],
}
</script>