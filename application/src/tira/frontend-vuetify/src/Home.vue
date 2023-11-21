<template>
  <v-container class="text-center">
    <v-img class="mx-auto" height="300px" max-width="100%" width="300px" src="@/assets/logo.svg"/>
    <section>
      <h1 class="text-h3 text-sm-h3 py-4 mt-10">
        TIRA Integrated Research Architecture
      </h1>
      <p class="mx-auto py-4 tira-explanation">
        TIRA is a platform for experiments in artificial intelligence that ensures blinded experiments and reproducibility.
      </p>
      <v-row class="d-flex justify-center py-4">
        <v-col cols="auto">
          <v-btn color="primary" href="/tasks" min-width="228" rel="noopener noreferrer" size="x-large" variant="flat">
            <v-icon icon="mdi-speedometer" size="large" start/>
            Get Started
          </v-btn>
        </v-col>
        <v-col cols="auto text-primary">
          <v-btn href="https://webis.de/downloads/publications/papers/potthast_2019p.pdf" min-width="228" rel="noopener noreferrer" size="x-large" variant="outlined">
            <v-icon size="large" start>
              <v-img src="@/assets/logo.svg" />
            </v-icon>
            Why TIRA?
          </v-btn>
        </v-col>
        <v-col cols="auto">
          <v-btn class="home-button" href="https://github.com/tira-io" min-width="228" rel="noopener noreferrer" size="x-large" variant="flat">
            <v-icon icon="mdi-github" size="large" start/>
            GitHub
          </v-btn>
        </v-col>
      </v-row>
      <v-row class="d-flex align-center justify-center">
        <v-col cols="auto">
          <v-btn disabled href="" min-width="164" rel="noopener noreferrer" variant="text">
            <v-icon icon="mdi-view-dashboard" size="large" start/>
            My tasks
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
        <v-col cols="auto text-primary">
          <v-btn href="/tirex" min-width="228"  rel="noopener noreferrer" size="x-large" variant="text">
            <v-icon size="large" start><v-img src="@/assets/tirex.png"/></v-icon>
            TIREx
          </v-btn>
        </v-col>
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