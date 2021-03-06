# Copyright 2015, Rackspace, US, Inc.
# Copyright 2015, Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import mock

from openstack_dashboard.api.rest import glance
from openstack_dashboard.test import helpers as test


class ImagesRestTestCase(test.TestCase):
    #
    # Version
    #
    @mock.patch.object(glance.api, 'glance')
    def test_version_get(self, gc):
        request = self.mock_rest_request()
        gc.get_version.return_value = '2.0'
        response = glance.Version().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"version": "2.0"})
        gc.get_version.assert_called_once_with()

    @mock.patch.object(glance.api, 'glance')
    def test_image_get_single(self, gc):
        request = self.mock_rest_request()
        gc.image_get.return_value.to_dict.return_value = {'name': '1'}

        response = glance.Image().get(request, "1")
        self.assertStatusCode(response, 200)
        gc.image_get.assert_called_once_with(request, "1")

    @mock.patch.object(glance.api, 'glance')
    def test_image_get_metadata(self, gc):
        request = self.mock_rest_request()
        gc.image_get.return_value.properties = {'a': '1', 'b': '2'}

        response = glance.ImageProperties().get(request, "1")
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"a": "1", "b": "2"})
        gc.image_get.assert_called_once_with(request, "1")

    @mock.patch.object(glance.api, 'glance')
    def test_image_edit_metadata(self, gc):
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, "removed": ["c", "d"]}'
        )

        response = glance.ImageProperties().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        gc.image_update_properties.assert_called_once_with(
            request, '1', ['c', 'd'], a='1', b='2'
        )

    @mock.patch.object(glance.api, 'glance')
    def test_image_get_list_detailed(self, gc):
        kwargs = {
            'sort_dir': 'desc',
            'sort_key': 'namespace',
            'marker': 1,
            'paginate': False,
        }
        filters = {'name': 'fedora'}
        request = self.mock_rest_request(
            **{'GET': dict(kwargs, **filters)})
        gc.image_list_detailed.return_value = ([
            mock.Mock(**{'to_dict.return_value': {'name': 'fedora'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'cirros'}})
        ], False, False)

        response = glance.Images().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"name": "fedora"}, {"name": "cirros"}],
                          "has_more_data": False, "has_prev_data": False})
        gc.image_list_detailed.assert_called_once_with(request,
                                                       filters=filters,
                                                       **kwargs)

    @mock.patch.object(glance.api, 'glance')
    def test_namespace_get_list(self, gc):
        request = self.mock_rest_request(**{'GET': {}})
        gc.metadefs_namespace_full_list.return_value = (
            [{'namespace': '1'}, {'namespace': '2'}], False, False
        )

        response = glance.MetadefsNamespaces().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"namespace": "1"}, {"namespace": "2"}],
                          "has_more_data": False, "has_prev_data": False})
        gc.metadefs_namespace_full_list.assert_called_once_with(
            request, filters={}
        )

    @mock.patch.object(glance.api, 'glance')
    def test_namespace_get_list_kwargs_and_filters(self, gc):
        kwargs = {
            'sort_dir': 'desc',
            'sort_key': 'namespace',
            'marker': 1,
            'paginate': False,
        }
        filters = {'resource_types': 'type'}
        request = self.mock_rest_request(
            **{'GET': dict(kwargs, **filters)})
        gc.metadefs_namespace_full_list.return_value = (
            [{'namespace': '1'}, {'namespace': '2'}], False, False
        )

        response = glance.MetadefsNamespaces().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"namespace": "1"}, {"namespace": "2"}],
                          "has_more_data": False, "has_prev_data": False})
        gc.metadefs_namespace_full_list.assert_called_once_with(
            request, filters=filters, **kwargs
        )
