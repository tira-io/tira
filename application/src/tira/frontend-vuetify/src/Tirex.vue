<template>
    <v-container class="text-center">
      <v-img class="mx-auto" height="300px" max-width="100%" width="300px" src="@/assets/tirex.png"/>
      <section>
        <h1 class="text-h3 text-sm-h3 py-4">
          TIREx: The Information Retrieval Experiment Platform
        </h1>
        <p class="mx-auto py-4 tira-explanation">
          TIREx integrates <a href="https://ir-datasets.com/" target="_blank">ir_datasets</a>, <a href="https://ir-measur.es/" target="_blank">ir_measures</a>, and <a href="https://github.com/terrier-org/pyterrier" target="_blank">PyTerrier</a> with <a href="/">TIRA</a> to promote standardized, reproducible, and blinded retrieval experiments.
        </p>
        <v-row class="d-flex justify-center py-4">
          <v-col cols="auto">
            <v-btn color="primary" href="https://github.com/tira-io/ir-experiment-platform#submission" target="_blank"  min-width="228" rel="noopener noreferrer" size="x-large" variant="flat">
              <v-icon icon="mdi-speedometer" size="large" start/>
              Get Started
            </v-btn>
          </v-col>
          <v-col cols="auto text-primary">
            <v-btn href="https://downloads.webis.de/publications/papers/froebe_2023e.pdf" target="_blank"  min-width="228"  rel="noopener noreferrer" size="x-large" variant="outlined">
              <v-icon size="large" start>
                <v-img src="@/assets/tirex.png" />
              </v-icon>
              Why TIREx?
            </v-btn>
          </v-col>
          <v-col cols="auto">
            <v-btn class="home-button" href="https://github.com/tira-io/ir-experiment-platform" target="_blank" min-width="228" rel="noopener noreferrer" size="x-large" variant="flat">
              <v-icon icon="mdi-github" size="large" start/>
              GitHub
            </v-btn>
          </v-col>
        </v-row>
        <v-row class="d-flex align-center justify-center">
          <v-col cols="auto">
            <v-btn href="/task-overview/ir-benchmarks" min-width="164" rel="noopener noreferrer" variant="text">
              <v-icon icon="mdi-view-dashboard" size="large" start/>
              Leaderboard
            </v-btn>
          </v-col>
          <v-col cols="auto">
            <v-btn href="/categories" min-width="164" rel="noopener noreferrer" variant="text">
              <v-icon icon="mdi-account-group" size="large" start/>
              Help
            </v-btn>
          </v-col>
        </v-row>

        <v-row class="d-flex align-center justify-center">
          <v-col cols="auto">
            <v-btn href="/tirex/components" min-width="164" rel="noopener noreferrer" variant="text">
              <v-icon icon="mdi-view-dashboard" size="large" start/>
              Components
            </v-btn>
          </v-col>
        </v-row>
      </section>
      <section class="mt-10">
        <v-row class="justify-center py-4">
            <v-card color="primary" variant="tonal" class="mx-auto" max-width="500">
              <v-card-item>
                <div>
                  <div class="text-h6 mb-1">Current Shared Tasks</div>
                  <div class="text-caption">
                    The <a href="/task-overview/ir-benchmarks">TIREx leaderboard</a> is always open for run or software submissions. Three additional shared tasks are open at the moment as part of (1) the <a href="https://opensearchfoundation.org/wows2024" target="_blank">Workshop on Open Web Search</a>, (2) <a href="https://touche.webis.de/clef24/touche24-web/image-retrieval-for-arguments.html" target="_blank">Touch&#233; 2024@CLEF</a>, and (3) the <a href="https://www.tira.io/task-overview/ir-lab-jena-leipzig-wise-2023" target="_blank">IR Lab 2023/2024</a> to foster student submissions to <a href="https://clef-longeval.github.io/" target="_blank">LongEval 2024@CLEF</a>.
                    <br>
                    We would be happy to host your <a href="/tasks">shared task</a> on TIREx.

                  </div>
                </div>
              </v-card-item>
            </v-card>
        </v-row>
      </section>
      <section>
        <v-row class="justify-center py-4">
            <v-card color="primary" variant="outlined" class="mx-auto" max-width="500">
              <v-card-item>
                <div>
                  <div class="text-h6 mb-1">Past Shared Tasks</div>
                  <div class="text-caption">
                    <a href="https://touche.webis.de/clef23/touche23-web" target="_blank">Touch&#233; 2023@CLEF</a> and the <a href="/task-overview/ir-lab-jena-leipzig-sose-2023">2023 IR Lab Leipzig/Jena</a> did run on TIREx, together with many tasks hosted in <a href="/tasks">TIRA</a>.
                  </div>
                </div>
              </v-card-item>
            </v-card>
        </v-row>
      </section>
    </v-container>
  </template>
  
  <style scoped>
    .tira-explanation {
      font-size: 1.25rem;
      font-weight: 300;
      max-width: 525px;
    }
    .home-button {
      color: #fff;
      background: #000;
    }
    .home-button:hover {
      color: #fff;
      background: #000;
    }
    .home-button:visited {
      color: #fff;
      background: #000;
    }
  </style>