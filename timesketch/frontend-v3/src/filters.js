/*
Copyright 2024 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
import dayjs from '@/plugins/dayjs'

export const initialLetter = (input) => {
  if (!input) return '';
  input = input.toString();
  return input.charAt(0).toUpperCase();
};

export const shortDateTime = (date) => {
    return dayjs.utc(date).format('YYYY-MM-DD HH:mm')
};

export const timeSince = (date) => {
  if (!date) {
    return ''
  }
  return dayjs.utc(date).fromNow()
}
