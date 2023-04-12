import json
import requests

from salt.exceptions import SaltException


class HealthchecksClient:
    """
    Client for the Healthchecks API.
    """

    def __init__(self, url, token, verify=None, session=None):
        self.url = url
        self.token = token
        self.verify = verify
        if session is None:
            session = requests.Session()
        self.session = session

    def delete(self, endpoint, raise_error=True, add_headers=None):
        """
        Wrapper for client.request("DELETE", ...)
        """
        return self.request(
            "DELETE",
            endpoint,
            raise_error=raise_error,
            add_headers=add_headers,
        )

    def get(self, endpoint, params=None, raise_error=True, add_headers=None, decode_json=True):
        """
        Wrapper for client.request("GET", ...)
        """
        return self.request(
            "GET",
            endpoint,
            params=params,
            raise_error=raise_error,
            add_headers=add_headers,
            decode_json=decode_json,
        )

    def post(self, endpoint, payload=None, raise_error=True, add_headers=None):
        """
        Wrapper for client.request("POST", ...)
        """
        return self.request(
            "POST",
            endpoint,
            payload=payload,
            raise_error=raise_error,
            add_headers=add_headers,
        )

    def patch(self, endpoint, payload, raise_error=True, add_headers=None):
        """
        Wrapper for client.request("PATCH", ...)
        """
        return self.request(
            "PATCH",
            endpoint,
            payload=payload,
            raise_error=raise_error,
            add_headers=add_headers,
        )

    def request(
        self,
        method,
        endpoint,
        payload=None,
        params=None,
        raise_error=True,
        add_headers=None,
        decode_json=True,
        **kwargs,
    ):
        """
        Issue a request against the Healthchecks API.
        Returns boolean when no data was returned, otherwise the decoded json data
        """
        res = self.request_raw(
            method,
            endpoint,
            payload=payload,
            params=params,
            add_headers=add_headers,
            **kwargs,
        )
        if res.status_code == 204:
            return True
        if not res.ok:
            if raise_error:
                self._raise_status(res)
            return res.content
        if decode_json:
            return res.json()
        return res.content

    def request_raw(
        self, method, endpoint, payload=None, params=None, add_headers=None, **kwargs
    ):
        """
        Issue a request against the Healthchecks API. Returns the raw response object.
        """
        url = self._get_url(endpoint)
        headers = self._get_headers()
        try:
            headers.update(add_headers)
        except TypeError:
            pass
        res = self.session.request(
            method,
            url,
            headers=headers,
            json=payload,
            params=params,
            verify=self.verify,
            **kwargs,
        )
        return res

    def _get_url(self, endpoint):
        endpoint = endpoint.lstrip("/")
        return f"{self.url}/api/v2/{endpoint}"

    def _get_headers(self):
        return {"Content-Type": "application/json", "X-Api-Key": self.token}

    def _raise_status(self, res):
        try:
            error = res.json().get("message", "(No error message)")
        except json.JSONDecodeError:
            error = res.content
        if res.status_code == 400:
            raise HlcksInvocationError(error)
        if res.status_code == 403:
            raise HlcksPermissionDeniedError(error)
        if res.status_code == 404:
            raise HlcksNotFoundError(error)
        if res.status_code == 405:
            raise HlcksUnsupportedOperationError(error)
        if res.status_code == 412:
            raise HlcksPreconditionFailedError(error)
        if res.status_code in [500, 502]:
            raise HlcksServerError(error)
        if res.status_code == 503:
            raise HlcksUnavailableError(error)
        res.raise_for_status()


class HlcksException(SaltException):
    """
    Base class for exceptions raised by this module
    """


class HlcksInvocationError(HlcksException):
    """
    HTTP 400 and InvalidArgumentException for this module
    """


class HlcksPermissionDeniedError(HlcksException):
    """
    HTTP 403
    """


class HlcksNotFoundError(HlcksException):
    """
    HTTP 404
    """


class HlcksUnsupportedOperationError(HlcksException):
    """
    HTTP 405
    """


class HlcksPreconditionFailedError(HlcksException):
    """
    HTTP 412
    """


class HlcksServerError(HlcksException):
    """
    HTTP 500
    HTTP 502
    """


class HlcksUnavailableError(HlcksException):
    """
    HTTP 503
    """
