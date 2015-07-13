import requests


def monkey_pytoggl(PyToggl):
    def _query(self, url, params, method, query_type=None, return_type='json'):
        """
        Monkey the _query method to allow PUT requests
        """
        if query_type == 'report':
            api_url = self.api_reports_url + url
        else:
            api_url = self.api_url + url

        auth = (self.api_token, 'api_token')
        headers = {'content-type': 'application/json'}

        if method == "POST":
            response = requests.post(api_url, auth=auth, headers=headers, params=params)
        elif method == "GET":
            response = requests.get(api_url, auth=auth, headers=headers, params=params)
        elif method == "PUT":
            response = requests.put(api_url, auth=auth, headers=headers, params=params)
        else:
            raise UserWarning('GET or POST or PUT are the only supported request methods.')

        # If the response errored, raise for that.
        if response.status_code != requests.codes.ok:
            response.raise_for_status()

        if return_type == 'json':
            return response.json()
        else:
            return response

    PyToggl._query = _query
    return PyToggl
