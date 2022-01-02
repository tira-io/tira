var dataset_tables = new Vue({
    el: "#dataset_tables",
    delimiters:["[[", "]]"],
    data: {
        dataset_id: null,
        role: null,
        ev_keys: null,
        evaluations: null,
        selected: 'Please select dataset'
    },
    created: function () {
        this.update_tables(this.selected)
    },
    watch: {
        selected: function (dataset_id) {
            this.update_tables(dataset_id)
        }
    },
    methods: {
        update_tables: function (dataset_id) {
            var vue = this
            $.ajax({
                type: "GET",
                url: "/data_api/evaluations/" + dataset_id,
                data: {},
                success: function (data) {
                    console.log(data["context"])
                    console.log(data["context"]["ev_keys"])
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
