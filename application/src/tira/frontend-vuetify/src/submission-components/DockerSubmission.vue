<template>
<v-card tonal class="my-10">
          <v-card-item>
            <v-btn variant="outlined"
                @click="showAddContainerCard = true; showUploadInformation=false">
                Add Container
            </v-btn>
            <v-btn variant="outlined"
                   @click="showUploadInformation = true; showAddContainerCard=false">
                   <v-icon>mdi-information-outline</v-icon>Instructions
            </v-btn>
            <v-btn variant="outlined"
                v-for="docker_software in docker.docker_softwares"
                @click="showNewImageForm=false; showUploadInformation=false; showAddContainerCard=false;">
                {{docker_software }}
            </v-btn>
          </v-card-item>
          <v-card-item v-if="showAddContainerCard">
            <v-form>

            <v-autocomplete
              label="Previous stage(s)"
              :items=docker.docker_softwares
              v-model="selectedDockerSoftware"
              multiple
              clearable
              chips
            />
            <v-text-field clearable label="Command" :model-value="addContainerCommand" hint="Available variables: $inputDataset, $inputRun, $outputDir, $dataServer, and $token."/>
            <v-autocomplete label="Docker Image"
                      :items="docker.images"
                      v-model="selectedDockerImage"
                      clearable/>
            <v-btn variant="outlined" @click="showAddContainerCard = true; selectedContainerId = null; showUploadInformation = false;">
              Add Container
            </v-btn>
            </v-form>
          </v-card-item>
          <v-card-item v-if="showUploadInformation">
            <v-card-text><p>Please upload your docker images according to your personalized documentation below. All uploaded docker images can be selected from the dropdown when adding containers</p></v-card-text>
            <v-card-text>
              <span v-html="docker.docker_software_help"></span>
            </v-card-text>



          </v-card-item>
          <v-card-item v-if="!showUploadInformation && !showAddContainerCard">
            <v-card-actions class="d-flex justify-lg-end">
              <div>
              <v-btn variant="outlined" color="#303f9f"><v-icon>mdi-file-edit-outline</v-icon>Edit</v-btn>
              <v-btn @click="snackbar = true" variant="outlined" color="red"><v-tooltip
                activator="parent"
                location="bottom"
              >Attention! This deletes the container and ALL runs associated with it</v-tooltip><v-icon>mdi-delete-alert-outline</v-icon>Delete</v-btn>
              <v-snackbar
                  v-model="snackbar"
                  :timeout="timeout"
                  color="green"
                  rounded="pill"
                >
                  {{ snackbarText }}

                  <template v-slot:actions>
                    <v-btn
                      color="blue"
                      variant="text"
                      @click="snackbar = false"
                    >
                      Close
                    </v-btn>
                     </template>
              </v-snackbar>
              </div>

            </v-card-actions>
            <v-text-field disabled label="Command (immutable for reproducibility)" :model-value="addContainerCommand" hint="Available variables: $inputDataset, $inputRun, $outputDir, $dataServer, and $token."/>
            <div class="d-flex">
              <v-text-field disabled label="Used image (immutable for reproducibility)" :model-value="addContainerCommand" hint="Available variables: $inputDataset, $inputRun, $outputDir, $dataServer, and $token."/>
              <v-autocomplete class="mx-2"
                  v-model="selectedRessources"
                  :items="ressources"
                  label="Ressources for execution"
                />
              <v-autocomplete label="Input Dataset"
                      :items="datasets"
                      item-title="display_name"
                      item-value="dataset_id"
                      v-model="selectedDataset"
                      clearable/>
            </div>
            <v-btn variant="outlined">Run Container</v-btn>
          </v-card-item>
        </v-card>
</template>

<script>

import { VAutocomplete } from 'vuetify/components'

export default {
  name: "DockerSubmission",
  components: {VAutocomplete},
  data() {
    return {
      selectedDockerSoftware: '',
      showAddContainerCard: true,
      showUploadInformation: false,
      selectedContainer: null,
      selectedDockerImage: '',
      snackbar: false,
      snackbarText: 'Successfully deleted container',
      timeout: 2000,
      addContainerCommand: 'mySoftware -c $inputDataset -r $inputRun -o $outputDir',
      docker: {
        "docker_softwares": [
            'test1',
            'test2',
            'test3',
            'test4',
            'test5',
        ],
        "images": [
            'image-test1',
            'image-test2',
            'image-test3',
            'image-test4',
            'image-test5',
        ],
        "docker_software_help": "<h3>Test</h3><p>Test</p>",
      },
      selectedRessources: '',
      ressources: [
          "Small (1 CPU Core, 10GB of RAM)",
          "Small (1 CPU Core, 10GB of RAM, IRDS)",
          "Small w. GPU (1 CPU Core, 10GB of RAM, 1 NVIDIA GTX 1080 with 8GB)",
          "Medium (2 CPU Cores, 20GB of RAM)",
          "Large (4 CPU Cores, 40GB of RAM)",

      ],
      selectedDataset: '',
      datasets: [{
                "dataset_id": "1",
                "display_name": "task-1-type-classification",
                "is_confidential": true,
                "is_deprecated": false,
                "year": "2022-11-15 06:51:49.117415",
                "task": "clickbait-spoiling",
                "software_count": 10,
                "runs_count": 220,
                "created": "2022-11-15",
                "last_modified": "2022-11-15"
            }, {
                "dataset_id": "2",
                "display_name": "task-1-type-classification-validation",
                "is_confidential": false,
                "is_deprecated": false,
                "year": "2022-11-15 06:51:49.117415",
                "task": "clickbait-spoiling",
                "software_count": 20,
                "runs_count": 100,
                "created": "2022-11-15",
                "last_modified": "2022-11-15"
            }
        ],
    }
  }
}
</script>