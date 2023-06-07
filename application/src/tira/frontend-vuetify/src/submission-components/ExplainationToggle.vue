<template>
  <v-expansion-panels class="mb-6" variant="accordion">
    <v-expansion-panel>
      <v-expansion-panel-title disable-icon-rotate>
        How to choose a submission type
        <template v-slot:actions>
          <v-icon class="mr-4" icon="mdi-help-circle-outline"></v-icon>
        </template>
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <v-table>
          <thead>
            <tr>
              <th class="text-center">{{ empty }}</th>
              <th class="text-center">Upload Submission</th>
              <th class="text-center">Virtual Machine Submission</th>
              <th class="text-center">Docker Submission</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in props" :key="item.name" class="text-center">
              <td>{{ item.name }}</td>
              <td>
                <v-icon
                  class="mr-4"
                  :color="getIconColor(item.upload)"
                  :icon="getIcon(item.upload)"
                ></v-icon>
              </td>
              <td>
                <v-icon
                  class="mr-4"
                  :color="getIconColor(item.vm)"
                  :icon="getIcon(item.vm)"
                ></v-icon>
              </td>
              <td>
                <v-icon
                  class="mr-4"
                  :color="getIconColor(item.docker)"
                  :icon="getIcon(item.docker)"
                ></v-icon>
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script>
export default {
  name: "ExplainationToggle",
  data() {
    return {
      empty: "",
      description: "here you can see the differences",
      props: [
        {
          name: "Reproducibility",
          upload: "No",
          docker: "Yes",
          vm: "Yes",
        },
        {
          name: "Perfomance",
          upload: "No",
          docker: "Yes",
          vm: "No",
        },
        {
          name: "Boot time",
          upload: "Low",
          docker: "Low",
          vm: "High",
        },
        {
          name: "Portability",
          upload: "No",
          docker: "Yes",
          vm: "No",
        },
        {
          name: "Security",
          upload: "No",
          docker: "No",
          vm: "Yes",
        },
        {
          name: "Effort",
          upload: "Low",
          docker: "High",
          vm: "High",
        },
      ],
    };
  },
  methods: {
    getIconColor(value) {
      return value === "Low" || value === "Yes" ? "teal" : "error";
    },
    getIcon(value) {
      return value === "Low" || value === "Yes"
        ? "mdi-arrow-top-right"
        : "mdi-arrow-bottom-left";
    },
  },
};
</script>
