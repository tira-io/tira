var dataset_tables = new Vue({
    el: "#dataset_tables",
    delimiters:["[[", "]]"],
    data: {
        task_id: null,
        dataset_id: null,
        role: null,
        ev_keys: null,
        evaluations: null,
        vms: null,
        selected: 'Please select dataset'
    },
    mounted: function () {
        this.task_id = this.$el.getAttribute('tira-data-task-id');
        this.update_tables(this.task_id, this.selected)
    },
    watch: {
        selected: function (dataset_id) {
            this.update_tables(this.task_id, dataset_id)
        }
    },
    methods: {
        update_tables: function (task_id, dataset_id) {
            var vue = this
            $.ajax({
                type: "GET",
                url: "/data_api/evaluations/" + task_id + "/" + dataset_id,
                data: {},
                success: function (data) {
                    vue.dataset_id = data["context"]["dataset_id"]
                    vue.role = data["context"]["role"]
                    vue.ev_keys = data["context"]["ev_keys"]
                    vue.evaluations = data["context"]["evaluations"]
                    $("#tira-load-dataset-icon").removeAttr("uk-spinner")
                }
            })

            $.ajax({
                type: "GET",
                url: "/data_api/runs/" + task_id + "/" + dataset_id,
                data: {},
                success: function (data) {
                    vue.dataset_id = data["context"]["dataset_id"]
                    vue.role = data["context"]["role"]
                    vue.vms = data["context"]["vms"]
                }
            })

            $.ajax({
                type: "GET",
                url: "/data_api/runs/" + task_id + "/" + dataset_id,
                data: {},
                success: function (data) {
                    vue.dataset_id = data["context"]["dataset_id"]
                    vue.role = data["context"]["role"]
                    vue.vms = data["context"]["vms"]
                    console.log(vue.vms)
                }
            })
        }
    }
})
