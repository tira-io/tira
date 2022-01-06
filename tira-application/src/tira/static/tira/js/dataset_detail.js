var dataset_tables = new Vue({
    el: "#dataset_tables",
    delimiters:["[[", "]]"],
    data: {
        task_id: "",
        dataset_id: "",
        role: null,
        ev_keys: [],
        evaluations: [],
        vms: [],
        selected: ""
    },
    mounted: function () {
        this.task_id = this.$el.getAttribute('tira-data-task-id');
        this.selected = this.$el.getAttribute('tira-data-dataset-id');
        this.update_tables(this.task_id, this.selected)
    },
    watch: {
        selected: function (selected) {
            this.update_tables(this.task_id, selected)
        }
    },
    methods: {
        update_tables: function (task_id, dataset_id) {
            var vue = this
            $("#tira-load-dataset-icon").attr("uk-spinner", "ratio: 0.5")
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
        }
    }
})
