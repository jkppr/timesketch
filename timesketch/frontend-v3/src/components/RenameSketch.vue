<!--
Copyright 2025 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<template>
  <div>
    <h3>Rename sketch</h3>
    <br />
    <v-form @submit.prevent="renameSketch()">
      <v-text-field
        variant="outlined"
        density="compact"
        autofocus
        v-model="newSketchName"
        @focus="$event.target.select()"
        clearable
        :rules="sketchNameRules"
      >
      </v-text-field>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text @click="closeDialog()"> Cancel </v-btn>
        <v-btn :disabled="!newSketchName || newSketchName.length > 255" text color="primary" @click="renameSketch()">
          Save
        </v-btn>
      </v-card-actions>
    </v-form>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import { useAppStore } from "@/stores/app";

export default {
  data() {
    return {
      appStore: useAppStore(),
      newSketchName: '',
      sketchNameRules: [
        (v) => !!v || 'Sketch name is required.',
        (v) => (v && v.length <= 255) || 'Sketch name is too long.',
      ],
    }
  },
  computed: {
    sketch() {
      return this.appStore.sketch
    },
  },
  methods: {
    renameSketch() {
      ApiClient.saveSketchSummary(this.sketch.id, this.newSketchName, '')
        .then((response) => {
          this.appStore.updateSketch(this.sketch.id);
        })
        .catch((e) => {
          console.error(e)
        })
      this.$emit('close')
    },
    closeDialog: function () {
      this.newSketchName = this.sketch.name
      this.$emit('close')
    },
  },
  created() {
    this.newSketchName = this.sketch.name
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
