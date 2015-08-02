import json
import requests
from PyToggl.PyToggl import PyToggl


ADD_TAG = 'add'
REMOVE_TAG = 'remove'
class Toggl(PyToggl):

    def _query(self, url, params, method, query_type=None, return_type='json', data=None):
        """
        Monkey the _query method to allow PUT requests
        """
        if query_type == 'report':
            api_url = self.api_reports_url + url
        else:
            api_url = self.api_url + url

        auth = (self.api_token, 'api_token')
        headers = {'content-type': 'application/json'}

        if data is not None and not isinstance(data, str):
            data = json.dumps(data)

        if method == "POST":
            response = requests.post(api_url, auth=auth, headers=headers, params=params, data=data)
        elif method == "GET":
            response = requests.get(api_url, auth=auth, headers=headers, params=params, data=data)
        elif method == "PUT":
            response = requests.put(api_url, auth=auth, headers=headers, params=params, data=data)
        else:
            raise UserWarning('GET or POST or PUT are the only supported request methods.')

        # If the response errored, raise for that.
        if response.status_code != requests.codes.ok:
            response.raise_for_status()

        if return_type == 'json':
            return response.json()
        else:
            return response

    def query(self, url, params=None, method='GET', query_type='report', return_type='json', data=None):
        params = params or {}
        return self._query(url, params, method, return_type=return_type, data=data)

    def update_tags(self, ids, tags, tag_action=ADD_TAG):
        """
        https://github.com/toggl/toggl_api_docs/blob/master/chapters/time_entries.md#bulk-update-time-entries-tags
        :param ids: a list of toggl ids to add the tags to
        :param tags: a list of tags to add to the time entries
        :return: the request response
        """
        assert isinstance(tags, list)
        return self.query(
            '/time_entries/%s' % (','.join(map(str, ids))),
            method='PUT',
            data={
                'time_entry': {
                    'tags': tags,
                    'tag_action': tag_action
                }
            }
        )


