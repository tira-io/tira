export default {
    data() {
        return {
            editOrganizerError: '',
            addOrganizerError: '',
            selectedOrganizer: '',
            newOrgId: '',
            name: '',
            newName: '',
            newYears: '',
            years: '',
            web: '',
            newWeb: '',
            organizerList: [],
        }
    },
    emits: ['addnotification', 'closemodal'],
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
                'X-CSRFToken': this.csrf
            })

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
        editOrganizer() {
            this.editOrganizerError = ''
            if (this.selectedOrganizer === '') {
                this.editOrganizerError += 'Please select an Organizer first;\n'
            }
            if (this.name === '') {
                this.editOrganizerError += 'Please provide a name for the Organizer;\n'
            }
            if (this.years === '') {
                this.editOrganizerError += 'Please provide a the active years for the Organizer;\n'
            }
            if (this.web === '') {
                this.editOrganizerError += 'Please provide a website for the Organizer;\n'
            }
            if (this.editOrganizerError !== '') {
                return
            }
            this.submitPost(`/tira-admin/edit-organizer/${this.selectedOrganizer.organizer_id}`, {
                'name': this.name,
                'years': this.years,
                'web': this.web,
            }).then(message => {
                this.$emit('addnotification', 'success', message.message)
                this.$emit('closemodal')
            }).catch(error => {
                this.editOrganizerError = error
            })
        },
        addOrganizer() {
            this.addOrganizerError = ''
            if (this.newOrgId === '') {
                this.addOrganizerError += 'Please select an Organizer first;\n'
            }
            if (this.newName === '') {
                this.addOrganizerError += 'Please provide a name for the Organizer;\n'
            }
            if (this.newYears === '') {
                this.addOrganizerError += 'Please provide a the active years for the Organizer;\n'
            }
            if (this.newWeb === '') {
                this.addOrganizerError += 'Please provide a website for the Organizer;\n'
            }
            if (this.editOrganizerError !== '') {
                addOrganizerError
            }
            this.submitPost(`/tira-admin/add-organizer/${this.newOrgId}`, {
                'name': this.newName,
                'years': this.newYears,
                'web': this.newWeb,
            }).then(message => {
                this.$emit('addnotification', 'success', message.message)
                this.$emit('closemodal')
            }).catch(error => {
                this.addOrganizerError = error
            })
        },
        string_to_slug (str) {
            str = str.replace(/^\s+|\s+$/g, ''); // trim
            str = str.toLowerCase();

            // remove accents, swap ñ for n, etc
            var from = "àáäâèéëêìíïîòóöôùúüûñç·/_,:;";
            var to   = "aaaaeeeeiiiioooouuuunc------";
            for (var i=0, l=from.length ; i<l ; i++) {
                str = str.replace(new RegExp(from.charAt(i), 'g'), to.charAt(i));
            }

            str = str.replace(/\./g, '-')
                .replace(/[^a-z0-9 -]/g, '') // remove invalid chars
                .replace(/\s+/g, '-') // collapse whitespace and replace by -
                .replace(/-+/g, '-'); // collapse dashes

            return str;
        },
    },
    beforeMount() {
        this.get(`/api/organizer-list`).then(message => {
            this.organizerList = message.context.organizer_list
        }).catch(error => {
            this.$emit('addnotification', 'error', `Error loading organizer list: ${error}`)
        })
    },
    watch: {
        newName(newOrgId, oldName) {
            this.newOrgId = this.string_to_slug(newOrgId)
        },
        selectedOrganizer(newOrg, oldName) {
            console.log(newOrg)
            this.name = newOrg.name
            this.years = newOrg.years
            this.web = newOrg.web
        }
    },
    template: `
<div class="uk-grid-small uk-margin-small" uk-grid>
    <div class="uk-margin-right">
        <h2>Edit Organization <span class="uk-text-lead uk-text-muted">ID: [[ this.selectedOrganizer.organizer_id ]]</span></h2>
    </div>
</div>
<div class="uk-margin-small">
    <div class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-1-4">
            <label><select class="uk-select" v-model="this.selectedOrganizer"
                   :class="{'uk-form-danger': (this.editOrganizerError !== '' && this.editOrganizerError === '')}">
                <option disabled value="">Please select an organizer</option>
                <option v-for="organizer in this.organizerList" :value="organizer">[[ organizer.name ]]</option>
            </select>Organizer*</label>
        </div>
        <div class="uk-width-1-4">
            <label><input class="uk-input" type="text"
                   :class="{'uk-form-danger': (this.editOrganizerError !== '' && this.name === '')}"
                   v-model="this.name" /> Organization Name</label>
        </div>
        <div class="uk-width-1-4">
            <label><input class="uk-input" type="text"
                   :class="{'uk-form-danger': (this.editOrganizerError !== '' && this.years === '')}"
                   v-model="this.years" /> Active Years</label>
        </div>
        <div class="uk-width-1-4">
            <label><input class="uk-input" type="text"
                   :class="{'uk-form-danger': (this.editOrganizerError !== '' && this.web === '')}"
                   v-model="this.web" /> Website</label>
        </div>
    </div>
    <div class="uk-margin-small">
        <button class="uk-button uk-button-primary" @click="editOrganizer">Save Changes</button>
        <span class="uk-text-danger uk-margin-small-left">[[ this.editOrganizerError ]]</span>
    </div>
</div>
<div class="uk-margin-small">
    <div class="uk-margin-right">
        <h2>Add Organization <span class="uk-text-lead uk-text-muted">ID: [[ this.newOrgId ]]</span></h2>
    </div>
    <div class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-1-3">
            <label><input class="uk-input" type="text"
                   :class="{'uk-form-danger': (this.addOrganizerError !== '' && this.newName === '')}"
                   v-model="this.newName" /> Organization Name</label>
        </div>
        <div class="uk-width-1-3">
            <label><input class="uk-input" type="text"
                   :class="{'uk-form-danger': (this.addOrganizerError !== '' && this.newYears === '')}"
                   v-model="this.newYears" /> Active Years</label>
        </div>
        <div class="uk-width-1-3">
            <label><input class="uk-input" type="text"
                   :class="{'uk-form-danger': (this.addOrganizerError !== '' && this.newWeb === '')}"
                   v-model="this.newWeb" /> Website</label>
        </div>
    </div>
    <div class="uk-margin-small">
        <button class="uk-button uk-button-primary" @click="addOrganizer">Add Organization</button>
        <span class="uk-text-danger uk-margin-small-left">[[ this.addOrganizerError ]]</span>
    </div>
</div>`
}
