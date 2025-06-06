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
  <v-container fluid>
    <v-dialog v-model="renameStoryDialog" width="600">
      <v-card class="pa-4">
        <h3>Rename story</h3>
        <br />
        <v-form @submit.prevent="rename()">
          <v-text-field outlined dense autofocus v-model="titleDraft" @focus="$event.target.select()"> </v-text-field>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn text @click="renameStoryDialog = false"> Cancel </v-btn>
            <v-btn color="primary" text @click="rename()"> Save </v-btn>
          </v-card-actions>
        </v-form>
      </v-card>
    </v-dialog>

      <v-dialog v-model="deleteStoryDialog" max-width="300">
        <v-card>
          <v-card-title class="headline">Delete Story</v-card-title>
          <v-card-text>
            Are you sure you want to delete this story?
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn text @click="deleteStoryDialog = false">Cancel</v-btn>
            <v-btn color="error" text @click="deleteStory">Delete</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

    <v-hover v-slot="{ hover }">
      <v-toolbar dense flat class="mt-n3" color="transparent">
        <v-toolbar-title @dblclick="renameStoryDialog = true"> {{ title }}</v-toolbar-title>
        <v-btn v-if="hover" icon small @click="renameStoryDialog = true">
          <v-icon small>mdi-pencil</v-icon>
        </v-btn>
        <v-btn v-if="hover" icon small @click="deleteStoryDialog = true">
          <v-icon small title="Delete Story">mdi-trash-can-outline</v-icon>
        </v-btn>
      </v-toolbar>
    </v-hover>
    <div class="pa-4">
      <div v-for="(block, index) in blocks" :key="index">
        <!-- Text block -->
        <div v-if="!block.componentName">
          <v-hover v-slot="{ hover }">
            <div @dblclick="editTextBlock(block)" @keydown.esc="block.edit = false" style="min-height: 30px">
              <v-card outlined class="float-right px-2" v-if="hover && !block.edit">
                <v-btn icon small @click="editTextBlock(block)"><v-icon small>mdi-pencil</v-icon></v-btn>
                <v-btn icon small @click="deleteBlock(index)"><v-icon small>mdi-trash-can-outline</v-icon></v-btn>
              </v-card>

              <!-- Render the markdown content -->
              <div class="markdown-body" v-if="!block.edit" v-html="toHtml(block.content)"></div>

              <!-- Edit markdown content. Work will be stored as draft until saved. -->
              <v-card v-if="block.edit" flat outlined class="mb-2">
                <v-toolbar flat dense>
                  <v-tabs v-model="block.currentTab">
                    <v-tab>Edit</v-tab>
                    <v-tab>Preview</v-tab>
                  </v-tabs>
                  <v-spacer></v-spacer>
                  <v-btn v-if="hasContent" icon @click="deleteBlock(index)">
                    <v-icon small>mdi-trash-can-outline</v-icon>
                  </v-btn>
                </v-toolbar>
                <v-divider></v-divider>
                <v-tabs-items v-model="block.currentTab">
                  <v-tab-item :transition="false">
                    <v-textarea
                      solo
                      flat
                      :value="block.draft"
                      @input="updateDraft($event, block)"
                      placeholder="Your story starts here.."
                      rows="5"
                      auto-grow
                      autofocus
                    ></v-textarea>
                  </v-tab-item>
                  <v-tab-item :transition="false">
                    <div class="markdown-body pa-4" v-html="toHtml(block.draft)"></div>
                  </v-tab-item>
                </v-tabs-items>

                <v-divider v-if="block.edit"></v-divider>
                <v-card-actions v-if="block.edit">
                  <v-btn text color="primary" @click="save()" :disabled="!block.draft">Save</v-btn>
                  <v-btn text @click="block.edit = false" :disabled="!hasContent">Cancel</v-btn>
                </v-card-actions>
              </v-card>
            </div>
          </v-hover>
        </div>

        <!-- Interactive data components -->
        <div v-if="block.componentName">
          <!-- Saved Searches -->
          <div>
            <v-card v-if="block.componentName === 'TsEventList'" outlined class="mb-2">
              <v-toolbar dense flat>
                <router-link
                  style="cursor: pointer; text-decoration: none"
                  :to="{ name: 'Explore', query: { view: block.componentProps.view.id } }"
                >
                  <span @click="setActiveView(block.componentProps.view)">{{ block.componentProps.view.name }}</span>
                </router-link>

                <v-spacer></v-spacer>
                <v-btn icon @click="deleteBlock(index)">
                  <v-icon small>mdi-trash-can-outline</v-icon>
                </v-btn>
              </v-toolbar>
              <v-divider></v-divider>
              <v-card-text>
                <component :is="block.componentName" v-bind="formatComponentProps(block)"></component>
              </v-card-text>
            </v-card>
            <v-card v-if="block.componentName === 'TsAggregationGroupCompact'" outlined class="mb-2">
              <v-toolbar dense flat
                >{{ block.componentProps.aggregation_group.name }}
                <v-spacer></v-spacer>
                <v-btn icon @click="deleteBlock(index)">
                  <v-icon small>mdi-trash-can-outline</v-icon>
                </v-btn>
              </v-toolbar>
              <v-divider></v-divider>
              <v-card-text>Legacy group Aggregations are not supported. Please view this Story in the old UI or update your analyzer.</v-card-text>
            </v-card>
            <v-card v-if="block.componentName === 'TsAggregationCompact'" outlined class="mb-2">
              <v-toolbar dense flat
                >{{ block.componentProps.aggregation.name }}
                <v-spacer></v-spacer>
                <v-btn icon @click="deleteBlock(index)">
                  <v-icon small>mdi-trash-can-outline</v-icon>
                </v-btn>
              </v-toolbar>
              <v-divider></v-divider>
              <v-card-text>Legacy aggregations are not supported. Please view this Story in the old UI or update your analyzer.</v-card-text>
            </v-card>
            <v-card v-if="block.componentName === 'TsCytoscapePlugin'" outlined class="mb-2">
              <v-toolbar dense flat>
                <router-link
                  style="cursor: pointer; text-decoration: none"
                  :to="{ name: 'Graph', query: { plugin: block.componentProps.graphPluginName } }"
                >
                  <span @click="setActiveGraph(block.componentProps.graphPluginName)">{{
                    block.componentProps.graphPluginName
                  }}</span>
                </router-link>

                <v-spacer></v-spacer>
                <v-btn icon @click="deleteBlock(index)">
                  <v-icon small>mdi-trash-can-outline</v-icon>
                </v-btn>
              </v-toolbar>
              <v-divider></v-divider>
              <v-card-text>
                <component :is="'TsCytoscape'" v-bind="formatComponentProps(block)"></component>
              </v-card-text>
            </v-card>
            <v-card v-if="block.componentName === 'TsCytoscapeSavedGraph'" outlined class="mb-2">
              <v-toolbar dense flat>
                <router-link
                  style="cursor: pointer; text-decoration: none"
                  :to="{ name: 'Graph', query: { graph: block.componentProps.graph } }"
                >
                  <span @click="setActiveGraph(block.componentProps.savedGraphId)">{{ block.graphName }}</span>
                </router-link>

                <v-spacer></v-spacer>
                <v-btn icon @click="deleteBlock(index)">
                  <v-icon small>mdi-trash-can-outline</v-icon>
                </v-btn>
              </v-toolbar>
              <v-divider></v-divider>
              <v-card-text>
                <component :is="'TsCytoscape'" v-bind="formatComponentProps(block)"></component>
              </v-card-text>
            </v-card>
            <v-card v-if="block.componentName === 'TsSavedVisualization'" outlined class="mb-2">
              <v-toolbar dense flat>
                <router-link
                  style="cursor: pointer; text-decoration: none"
                  :to="{ name: 'VisualizationView', params: { aggregationId: block.componentProps.savedVisualizationId } }"
                >
                  {{ block.componentProps.name }}
                </router-link>

                <v-spacer></v-spacer>
                <v-btn icon @click="deleteBlock(index)">
                  <v-icon small>mdi-trash-can-outline</v-icon>
                </v-btn>
              </v-toolbar>
              <v-divider></v-divider>
              <v-card-text>
                <TsSavedVisualization :aggregationId="block.componentProps.savedVisualizationId">
                </TsSavedVisualization>
              </v-card-text>
            </v-card>
            <v-card v-if="block.componentName === 'TsInvestigativeQuestion'" outlined class="mb-2">
              <v-toolbar dense flat>
                <span>{{ block.componentProps.questionName }}</span>
                <v-spacer></v-spacer>
                <v-btn icon @click="deleteBlock(index)">
                  <v-icon small>mdi-trash-can-outline</v-icon>
                </v-btn>
              </v-toolbar>
              <v-divider></v-divider>
              <v-card-text class="pa-0">
                <!-- TODO: Since in a Story only the conclusions are relevant, add a better conclusion view here instead of the full Question card! -->
                <TsQuestionCard :questionId="block.componentProps.questionId" :key="block.componentProps.questionId + '-' + block.componentProps.questionName" :initialTab=2>
                </TsQuestionCard>
              </v-card-text>
            </v-card>
          </div>
        </div>

        <!-- Add controls to add new blocks to the page -->
        <v-hover v-slot="{ hover }">
          <div class="mb-2 mt-2">
            <div
              :class="{
                hidden: !hover && !block.isActive && !block.showGraphMenu && !block.showSavedSearchMenu && !block.showSavedVisualizationMenu && !block.showQuestionMenu  && hasContent,
              }"
            >
              <!-- Text block -->
              <v-btn v-if="hasContent" class="mr-2" rounded outlined small @click="addTextBlock(index)">
                <v-icon left small>mdi-plus</v-icon>
                Text
              </v-btn>
              <!-- Saved Search selector -->
              <v-menu offset-y v-model="block.showSavedSearchMenu">
                <template v-slot:activator="{ on, attrs }">
                  <v-btn class="mr-2" rounded outlined small :disabled="!meta.views.length" v-bind="attrs" v-on="on">
                    <v-icon left small>mdi-plus</v-icon>
                    Saved Search
                  </v-btn>
                </template>
                <v-card width="475">
                  <v-list>
                    <v-list-item-group color="primary">
                      <v-list-item v-for="savedSearch in meta.views" :key="savedSearch.id">
                        <v-list-item-content @click="addEventListBlock(savedSearch, index)">
                          {{ savedSearch.name }}
                        </v-list-item-content>
                      </v-list-item>
                    </v-list-item-group>
                  </v-list>
                </v-card>
              </v-menu>
              <v-menu offset-y v-model="block.showGraphMenu">
                <template v-slot:activator="{ on, attrs }">
                  <v-btn class="mr-2" rounded outlined small :disabled="!graphPlugins.length" v-bind="attrs" v-on="on">
                    <v-icon left small>mdi-plus</v-icon>
                    Graphs
                  </v-btn>
                </template>
                <v-card width="475">
                  <v-list>
                    <v-list-item-group color="primary">
                      <v-subheader>Saved Graphs</v-subheader>
                      <v-list-item v-for="savedGraph in savedGraphs" :key="savedGraph.id">
                        <v-list-item-content @click="addSavedGraphBlock(savedGraph, index)">
                          {{ savedGraph.name }}
                        </v-list-item-content>
                      </v-list-item>
                      <v-subheader>Plugins</v-subheader>
                      <v-list-item v-for="graphPlugin in graphPlugins" :key="graphPlugin.name">
                        <v-list-item-content @click="addGraphPluginBlock(graphPlugin, index)">
                          {{ graphPlugin.name }}
                        </v-list-item-content>
                      </v-list-item>
                    </v-list-item-group>
                  </v-list>
                </v-card>
              </v-menu>
              <v-menu offset-y v-model="block.showSavedVisualizationMenu">
                <template v-slot:activator="{ on, attrs }">
                  <v-btn class="mr-2" rounded outlined small :disabled="!savedVisualizations.length" v-bind="attrs" v-on="on">
                    <v-icon left small>mdi-plus</v-icon>
                    Visualizations
                  </v-btn>
                </template>
                <v-card>
                  <v-list>
                    <v-list-item-group color="primary">
                      <v-subheader>Saved Visualizations</v-subheader>
                      <v-list-item v-for="savedVisualization in savedVisualizations" :key="savedVisualization.id">
                        <v-list-item-content @click="addSavedVisualization(savedVisualization, index)">
                          {{ savedVisualization.name }}
                        </v-list-item-content>
                      </v-list-item>
                    </v-list-item-group>
                  </v-list>
                </v-card>
              </v-menu>
              <v-menu offset-y v-model="block.showQuestionMenu">
                <template v-slot:activator="{ on, attrs }">
                  <v-btn rounded outlined small :disabled="!availableSketchQuestions.length" v-bind="attrs" v-on="on">
                    <v-icon left small>mdi-plus</v-icon>
                    Investigative Question
                  </v-btn>
                </template>
                <v-card width="475">
                  <v-list>
                    <v-list-item-group color="primary">
                      <v-list-item v-for="question in availableSketchQuestions" :key="question.id">
                        <v-list-item-content @click="addQuestionBlock(question, index)">
                          {{ question.name }}
                        </v-list-item-content>
                      </v-list-item>
                    </v-list-item-group>
                  </v-list>
                </v-card>
              </v-menu>
            </div>
          </div>
        </v-hover>
      </div>
    </div>
  </v-container>
</template>

<script>
import ApiClient from '../utils/RestApiClient.js'
import EventBus from '../event-bus.js'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import _ from 'lodash'

import TsEventList from '../components/Explore/EventList.vue'
import TsCytoscape from '../components/Graph/Cytoscape.vue'
import TsSavedVisualization from '../components/Visualization/SavedVisualization.vue'
import TsQuestionCard from '../components/Scenarios/QuestionCard.vue'
import TsQuestionConclusion from '../components/Scenarios/QuestionConclusion.vue'

const defaultBlock = () => {
  return {
    componentName: '',
    componentProps: {},
    content: '',
    draft: '',
    edit: true,
    isActive: false,
    showGraphMenu: false,
    showSavedSearchMenu: false,
    showSavedVisualizationMenu: false,
    showQuestionMenu: false,
  }
}

const componentCompatibility = () => {
  return {
    TsViewEventList: 'TsEventList',
  }
}

export default {
  props: ['sketchId', 'storyId'],
  components: {
    TsEventList,
    TsCytoscape,
    TsSavedVisualization,
    TsQuestionCard,
    TsQuestionConclusion
  },
  data: function () {
    return {
      title: '',
      titleDraft: '',
      blocks: [],
      renameStoryDialog: false,
      deleteStoryDialog: false,
      sketchQuestions: [],
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    hasContent() {
      if (!this.blocks.length) {
        return false
      }
      if (this.blocks.length < 2 && !this.blocks[0].componentName && !this.blocks[0].content) {
        return false
      }
      return true
    },
    graphPlugins() {
      return this.$store.state.graphPlugins
    },
    savedGraphs() {
      return this.$store.state.savedGraphs
    },
    savedVisualizations() {
      if (!this.$store.state.savedVisualizations) {
        return []
      }
      return this.$store.state.savedVisualizations.filter(
          (e) => JSON.parse(e.parameters)['aggregator_class'] === 'apex'
      )
    },
    availableSketchQuestions() {
      // Filter out questions that are already in the story
       const addedQuestionIds = this.blocks
         .filter(block => block.componentName === 'TsInvestigativeQuestion')
         .map(block => block.componentProps.questionId);
       const questions = Array.isArray(this.sketchQuestions) ? this.sketchQuestions : [];
       return questions.filter(question => !addedQuestionIds.includes(question.id));
    },
  },
  methods: {
    updateDraft: _.debounce(function (e, block) {
      block.draft = e
    }, 300),
    async fetchStory() {
      ApiClient.getStory(this.sketchId, this.storyId)
        .then((response) => {
          this.title = response.data.objects[0].title
          this.titleDraft = this.title
          let content = response.data.objects[0].content
          if (content === '[]') {
            this.blocks = [defaultBlock()]
          } else {
            this.blocks = JSON.parse(content)
          }
          this.formatBlocks(this.blocks)
          // Set first page in edit mode if the story is empty
          if (this.blocks.length < 2 && !this.blocks[0].componentName && !this.blocks[0].content) {
            this.blocks[0].edit = true
          }
        })
        .catch((e) => {
          console.error(e)
        })
    },
    formatBlocks(blocks) {
      // Format block to support backwards compatibility for old style blocks
      let compat = componentCompatibility()
      blocks.forEach((block) => {
        if (block.componentName in compat) {
          block.componentName = compat[block.componentName]
        }
      })
      return blocks
    },
    formatComponentProps(block) {
      // Backwards compatibility for old style TsViewEventList props
      if (block.componentName === 'TsEventList' || block.componentName === 'TsViewEventList') {
        const EVENTS_PER_PAGE = 10
        let queryString = block.componentProps.view.query_string || block.componentProps.view.query
        let queryFilter = block.componentProps.view.query_filter || block.componentProps.view.filter
        let queryRequest = {}

        // Make sure there is a query filter present
        if (!queryFilter || queryFilter === undefined) {
          queryFilter = {}
        } else {
          queryFilter = JSON.parse(queryFilter)
        }

        queryFilter.size = EVENTS_PER_PAGE
        queryFilter.terminate_after = EVENTS_PER_PAGE
        queryRequest['queryString'] = queryString
        queryRequest['queryFilter'] = queryFilter
        queryRequest['incognito'] = true
        return {
          queryRequest: queryRequest,
          disableSaveSearch: true,
          itemsPerPage: EVENTS_PER_PAGE,
        }
      }
      return block.componentProps
    },
    toHtml(markdown) {
      return DOMPurify.sanitize(marked(markdown))
    },
    addTextBlock(index) {
      let newIndex = index + 1
      let newBlock = defaultBlock()
      this.blocks.splice(newIndex, 0, newBlock)
    },
    addEventListBlock(savedSearch, index) {
      let newIndex = index + 1
      let newBlock = defaultBlock()
      newBlock.componentName = 'TsEventList'
      newBlock.componentProps = { view: savedSearch }
      this.blocks.splice(newIndex, 0, newBlock)
      this.save()
    },
    addGraphPluginBlock(graphPlugin, index) {
      let newIndex = index + 1
      let newBlock = defaultBlock()
      newBlock.componentName = 'TsCytoscapePlugin'
      newBlock.componentProps = { graphPluginName: graphPlugin.name, canvasHeight: '500px', disableZoom: true }
      this.blocks.splice(newIndex, 0, newBlock)
      this.save()
    },
    addSavedGraphBlock(savedGraph, index) {
      let newIndex = index + 1
      let newBlock = defaultBlock()
      newBlock.componentName = 'TsCytoscapeSavedGraph'
      newBlock.componentProps = { savedGraphId: savedGraph.id, canvasHeight: '400px', disableZoom: true }
      newBlock.graphName = savedGraph.name
      this.blocks.splice(newIndex, 0, newBlock)
      this.save()
    },
    addSavedVisualization(savedVisualization, index) {
      let newIndex = index + 1
      let newBlock = defaultBlock()
      newBlock.componentName = 'TsSavedVisualization'
      newBlock.componentProps = {
        name: savedVisualization.name,
        savedVisualizationId: savedVisualization.id,
      }
      this.blocks.splice(newIndex, 0, newBlock)
      this.save()
    },
    async addQuestionBlock(question, index) {
      let newIndex = index + 1
      let newBlock = defaultBlock()
      newBlock.componentName = 'TsInvestigativeQuestion'
      newBlock.componentProps = {
        questionName: question.name,
        questionId: question.id
      }
      this.blocks.splice(newIndex, 0, newBlock)
      await this.save()
      await this.fetchStory()
    },
    editTextBlock(block) {
      if (block.edit) {
        return
      } else {
        block.edit = true
      }
      block.draft = block.content
    },
    deleteBlock(index) {
      if (confirm('Delete block?')) {
        this.blocks.splice(index, 1)
        if (!this.blocks.length) {
          this.blocks = [defaultBlock()]
        }
        this.save()
      }
    },
    setActiveView: function (savedSearch) {
      EventBus.$emit('setActiveView', savedSearch)
    },
    setActiveGraph: function (graph) {
      if (typeof graph === 'string') {
        EventBus.$emit('setGraphPlugin', graph)
      } else if (typeof graph === 'number') {
        EventBus.$emit('setSavedGraph', graph)
      }
    },
    async save() {
      let content
      this.blocks.forEach(function (block) {
        block.isActive = false
        block.showGraphMenu = false
        block.showSavedSearchMenu = false
        block.showSavedVisualizationMenu = false
        block.showQuestionMenu = false
        block.edit = false
        if (block.draft) {
          block.content = block.draft
          block.draft = ''
        }
      })
      if (!this.hasContent) {
        content = JSON.stringify([])
        this.blocks = [defaultBlock()]
      } else {
        content = JSON.stringify(this.blocks)
      }
      ApiClient.updateStory(this.title, content, this.sketchId, this.storyId)
        .then((response) => {
          this.$store.dispatch('updateSketch', this.sketchId)
        })
        .catch((e) => {})
    },
    rename() {
      this.renameStoryDialog = false
      this.title = this.titleDraft
      this.save()
    },
    deleteStory() {
      this.deleteStoryDialog = false

      ApiClient.deleteStory(this.sketchId, this.storyId)
        .then((response) => {
          this.blocks = []

          ApiClient.getStoryList(this.sketchId)
            .then((storyListResponse) => {
              const stories = storyListResponse.data.objects[0]

              if (stories && stories.length > 0) {
                const nextStoryId = stories[0].id
                this.$router.push({
                  name: "Story",
                  params: { sketchId: this.sketchId, storyId: nextStoryId },
                })
              } else {
                this.$router.push({
                  name: "Overview",
                  params: { sketchId: this.sketchId },
                })
              }
            })
            .catch(e => {
              console.error('Error getStoryList', e)
              this.$router.push({ name: 'Sketches' })
            })

          this.$store.dispatch("updateSketch", this.sketchId)
        })
        .catch((error) => {
          console.error("Error deleting story:", error)
          this.$router.push({ name: 'Sketches' })
        })
    },
    async getSketchQuestions() {
      try {
        const response=await ApiClient.getOrphanQuestions(this.sketch.id)
        this.sketchQuestions=response.data.objects[0]
      } catch(e) {
        console.error(e)
      }
    },
  },
  mounted() {
    if (this.storyId) {
      this.fetchStory()
    }
    this.getSketchQuestions()
  },
  watch: {
    storyId: function (newVal) {
      if (this.storyId) {
        this.fetchStory()
      }
    },
  },
}
</script>

<style lang="scss">
.markdown-body {
  box-sizing: border-box;
  min-width: 200px;
  max-width: 980px;
  margin: 0 auto;
}

.hidden {
  visibility: hidden;
}

.theme--light.v-application code {
  background-color: transparent !important;
}

.theme--dark.v-application code {
  background-color: transparent !important;
}
</style>
