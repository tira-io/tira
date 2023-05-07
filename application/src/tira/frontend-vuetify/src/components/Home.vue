<template>
  <v-container class="fill-height">
    <v-responsive class="d-flex align-center text-center fill-height">
      
      <v-img height="300" src="@/assets/logo.svg" />
      <div class="py-5" />
      <div class="text-body-2 font-weight-light mb-n1">Welcome to</div>
      <div class="py-2" />
      <h2 class="text-h2 font-weight-bold">TIRA</h2>
      <div class="py-1" />
      <h5 class="text-h5">Reproducible experiments<br/>for computer science</h5>
      <div class="py-5" />

      <v-row class="d-flex align-center justify-center">
        <v-col cols="auto">
          <v-btn
            color="primary"
            href=""
            min-width="228"
            rel="noopener noreferrer"
            size="x-large"
            variant="flat"
          >
            <v-icon
              icon="mdi-speedometer"
              size="large"
              start
            />

            Get Started
          </v-btn>
        </v-col>
      </v-row>

      <div class="py-5" />

      <v-row class="d-flex align-center justify-center">
        <v-col cols="auto">
          <v-btn
            href=""
            min-width="164"
            rel="noopener noreferrer"
            variant="text"
          >
            <v-icon
              icon="mdi-view-dashboard"
              size="large"
              start
            />

            My tasks
          </v-btn>
        </v-col>
        
        <v-col cols="auto">
          <v-btn
            href="/categories"
            min-width="164"
            rel="noopener noreferrer"
            variant="text"
          >
            <v-icon
              icon="mdi-account-group"
              size="large"
              start
            />

            Help
          </v-btn>
        </v-col>
      </v-row>
    </v-responsive>
  </v-container>
</template>

<script setup lang="ts">
  //
</script>
