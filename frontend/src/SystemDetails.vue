<template>
    <tira-breadcrumb />
    <h3 class="text-h3 py-5">System Details</h3>
    {{ system_details }}
    <h3 class="text-h3 py-5">Public Submissions</h3>
    We only show submissions of {{ team }}/{{ system }} that have at least one positively validated and published submission for the software.
</template>
    
  <script lang="ts">
    import { inject } from 'vue'
    
    import { get, reportError, fetchUserInfo, type UserInfo } from './utils';
    import { Loading, TiraBreadcrumb } from './components'
    
    export default {
      name: "systems",
      components: { Loading, TiraBreadcrumb },
      data() {
        return {
          userinfo: { role: 'guest', organizer_teams: [], 'context': {user_id: 'guest'} } as UserInfo,
          system_details: undefined,
          team: undefined as undefined | string,
          system: undefined as undefined | string,
        }
      },
      methods: {
        logData(toLog: any) {
          console.log(toLog)
        }
      },
      beforeMount() {
        this.team = this.$route.params.team as undefined | string
        this.system = this.$route.params.system as undefined | string
  
        fetchUserInfo().then((result) => { this.$data.userinfo = result })
        get(inject("REST base URL") + '/v1/systems/' + this.team + '/' + this.system).then((result) => { this.$data.system_details = result})
    }
}
    
    </script>
    