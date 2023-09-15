<!--
Copyright 2023 Google Inc. All rights reserved.

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
  <v-chip
  class="mr-2 mb-3 pr-1 timeline-chip"
  :class="$vuetify.theme.dark ? 'dark-highlight' : 'light-highlight'"
  :style="getTimelineStyle()"
  @click:close="$emit('click:close')"
  :close="close"
  >
    <div class="chip-content">
      <v-icon left :color="timelineChipColor" size="26" class="ml-n2"> mdi-circle </v-icon>
      <v-tooltip bottom :disabled="timeline.name.length < 30" open-delay="300">
        <template v-slot:activator="{ on: onTooltip, attrs }">
          <span
            class="timeline-name-ellipsis"
            v-bind="attrs"
            v-on="onTooltip"
            >{{ timeline.name }}</span
          >
        </template>
        <span>{{ timeline.name }}</span>
      </v-tooltip>
      <span class="right">
        <span class="events-count" x-small>
          {{ eventsCount | compactNumber }}
        </span>
      </span>
    </div>
  </v-chip>
</template>

<script>
export default {
  props: {
    timeline: Object,
    close: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    timelineChipColor() {
      if (!this.timeline.color.startsWith('#')) {
        return '#' + this.timeline.color
      }
      return this.timeline.color
    },
    eventsCount: function () {
      return this.timeline.datasources[0].total_file_events
    },
  },
  methods: {
    getTimelineStyle() {
      return {
        backgroundColor: this.$vuetify.theme.dark ? '#282828' : '#ededed',
        cursor: 'pointer',
      }
    },
  },
}
</script>

<style scoped lang="scss">
.timeline-chip {
  .right {
    margin-left: auto;
    margin-right: auto;
  }

  .chip-content {
    margin: 0;
    padding: 0;
    display: flex;
    align-items: center;
    width: 300px;
  }
}

// TODO: Fix the close icon/button margin right!
// .v-chip__close.v-icon.v-icon--right {
//   margin-right: 0 !important;
// }

.events-count {
  font-size: 0.8em;
}
</style>
