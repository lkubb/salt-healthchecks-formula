"""
Interface with the Healthchecks v2 API.

Note that check names are assumed to be unique by this module.

Configuration
-------------
This module assumes an API key that is not read-only.

Connection parameters
~~~~~~~~~~~~~~~~~~~~~

This module accepts connection configuration details either as
parameters or as configuration settings retrievable by
:py:func:`config.option <salt.modules.config.option>`.

.. code-block:: yaml

    hlcks:
      url: http://localhost:3000
      token: my-token
      verify: null

To override the default profile name (``hlcks``), you can pass ``healthchecks_profile`` as a supplemental kwarg.

To override url/token/verify during a function call, you can pass
``healthchecks_url``/``healthchecks_token``/``healthchecks_verify`` as kwargs.

Remote issuance of ping URLs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
It is possible to request a ping URL from another minion.

Peer communication
^^^^^^^^^^^^^^^^^^
To be able to use this functionality, it is required to configure the Salt
master to allow :term:`Peer Communication`:

.. code-block:: yaml

    # /etc/salt/master.d/peer.conf

    peer:
      .*:
        - healthchecks.get_ping_url_remote

Issuance policies
^^^^^^^^^^^^^^^^^
In addition, the minion issuing the ping urls needs to have at least one
issuance policy configured, remote calls not referencing one are always
rejected.

The parameters specified in this policy override any
parameters passed from the minion requesting the ping url. It can be
configured in the issuing minion's pillar, which takes precedence, or any
location :py:func:`config.get <salt.modules.config.get>` looks up in.
Issuance policies are defined under ``healthchecks_policies``.

You can restrict which minions can request a ping url under a configured
issuance policy by specifying a matcher in ``minions``. This can be a glob
or compound matcher (the latter requires further setup @TODO document).

.. code-block:: yaml

    healthchecks_policies:
      borgmatic:
        - minions: 'www*'
        - channels:
            - kind: email
        - timeout: 3600

.. _hlcks-setup:
"""
import json
import logging

import healthchecksutil as hcutil
import salt.cache
from salt.exceptions import CommandExecutionError, SaltInvocationError

__virtualname__ = "healthchecks"

log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def _client(
    healthchecks_profile="hlcks",
    healthchecks_token=None,
    healthchecks_url=None,
    healthchecks_verify=None,
    **kwargs,
):
    if any(not kwarg.startswith("_") for kwarg in kwargs):
        raise SaltInvocationError(
            f"Unknown keyword arguments: {list(kwarg for kwarg in kwargs if not kwarg.startswith('_'))}"
        )
    profile = healthchecks_profile or "hlcks"
    config = __salt__["config.get"](profile)
    try:
        token = healthchecks_token or config["token"]
    except KeyError as err:
        raise SaltInvocationError(
            f"Missing token: {profile}:token / healthchecks_token"
        ) from err
    url = healthchecks_url or config.get("url", "http://localhost:3475")
    verify = (
        healthchecks_verify if healthchecks_verify is not None else config.get("verify")
    )
    if (url, token, verify) not in __context__:
        __context__[(url, token, verify)] = hcutil.HealthchecksClient(
            url, token, verify
        )
    return __context__[(url, token, verify)]


def fetch_check(name=None, uuid=None, **kwargs):
    """
    Return a check or None.

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.fetch_check name=mycheck

    name
        The name of the check. Specify either this or ``uuid``.

    uuid
        The UUID of the check. Specify either this or ``name``.
    """
    client = _client(**kwargs)
    if uuid is None and name is None or uuid and name:
        raise SaltInvocationError("Need either uuid or name, exclusive")
    if uuid:
        try:
            return client.get(f"checks/{uuid}")
        except hcutil.HlcksNotFoundError:
            return None
    checks = list_checks(**kwargs)
    for check in checks:
        if check["name"] == name:
            return check
    return None


def write_check(
    name,
    tags=None,
    desc=None,
    timeout=None,
    grace=None,
    schedule=None,
    tz=None,
    manual_resume=None,
    methods=None,
    channels=None,
    start_kw=None,
    success_kw=None,
    failure_kw=None,
    filter_subject=None,
    filter_body=None,
    **kwargs,
):
    """
    Create/overwrite a check.

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.write_check mycheck timeout=3600

    name
        The name of the check to write.

    tags
        A list of tags to associate with this check.

    desc
        A description of this check.

    timeout
        The expected period of this check in seconds.

    grace
        The grace period for this check in seconds.

    schedule
        A cron expression defining this check's schedule. Takes precedence
        over ``timeout``.

    tz
        Server's timezone. This setting only has an effect in combination
        with the schedule parameter.

    manual_resume
        Controls whether a paused check automatically resumes when pinged
        (the default) or not.

    methods
        Specifies the allowed HTTP methods for making ping requests.
        Must be one of the two values: "" (an empty string) or "POST".

    channels
        List of assigned integrations (channels).
        Set this to "*" to automatically assign all existing integrations.
        You can define list items as dicts, which will be interpreted
        as keyword arguments to ``list_channels`` (``kind``, ``name``).

    start_kw
        List of keywords for classifying inbound email messages as "Start" signals.

    success_kw
        List of keywords for classifying inbound email messages as "Success" signals.

    failure_kw
        List of keywords for classifying inbound email messages as "Failure" signals.

    filter_subject
        Enables filtering of inbound email messages by looking for keywords
        in their subject lines. Defaults to false.

    filter_body
        Enables filtering of inbound email messages by looking for keywords
        in their message body. Defaults to false.
    """
    client = _client(**kwargs)
    payload = parse_check_params(
        name=name,
        tags=tags,
        desc=desc,
        timeout=timeout,
        grace=grace,
        schedule=schedule,
        tz=tz,
        manual_resume=manual_resume,
        methods=methods,
        channels=channels,
        start_kw=start_kw,
        success_kw=success_kw,
        failure_kw=failure_kw,
        filter_subject=filter_subject,
        filter_body=filter_body,
        **kwargs,
    )
    payload["unique"] = ["name"]
    try:
        return client.post("checks/", payload=payload)
    except hcutil.HlcksException as err:
        raise CommandExecutionError(f"{type(err).__name__}: {err}") from err


def update_check(
    name=None,
    uuid=None,
    tags=None,
    desc=None,
    timeout=None,
    grace=None,
    schedule=None,
    tz=None,
    manual_resume=None,
    methods=None,
    channels=None,
    start_kw=None,
    success_kw=None,
    failure_kw=None,
    filter_subject=None,
    filter_body=None,
    **kwargs,
):
    """
    Update select parameters of an existing check.

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.write_check mycheck timeout=3600

    name
        The name of the check to write.

    uuid
        The UUID of the check. Specify either this or ``name``.

    tags
        A list of tags to associate with this check.

    desc
        A description of this check.

    timeout
        The expected period of this check in seconds.

    grace
        The grace period for this check in seconds.

    schedule
        A cron expression defining this check's schedule. Takes precedence
        over ``timeout``.

    tz
        Server's timezone. This setting only has an effect in combination
        with the schedule parameter.

    manual_resume
        Controls whether a paused check automatically resumes when pinged
        (the default) or not.

    methods
        Specifies the allowed HTTP methods for making ping requests.
        Must be one of the two values: "" (an empty string) or "POST".

    channels
        List of assigned integrations (channels).
        Set this to "*" to automatically assign all existing integrations.
        You can define list items as dicts, which will be interpreted
        as keyword arguments to ``list_channels`` (``kind``, ``name``).

    start_kw
        List of keywords for classifying inbound email messages as "Start" signals.

    success_kw
        List of keywords for classifying inbound email messages as "Success" signals.

    failure_kw
        List of keywords for classifying inbound email messages as "Failure" signals.

    filter_subject
        Enables filtering of inbound email messages by looking for keywords
        in their subject lines. Defaults to false.

    filter_body
        Enables filtering of inbound email messages by looking for keywords
        in their message body. Defaults to false.
    """
    client = _client(**kwargs)
    check = fetch_check(name=name if uuid is None else None, uuid=uuid, **kwargs)
    if not check:
        raise CommandExecutionError(f"Specified check {uuid or name} does not exist")
    if not uuid:
        uuid = check["ping_url"].split("/ping/")[-1]
    payload = parse_check_params(
        name=name,
        tags=tags,
        desc=desc,
        timeout=timeout,
        grace=grace,
        schedule=schedule,
        tz=tz,
        manual_resume=manual_resume,
        methods=methods,
        channels=channels,
        start_kw=start_kw,
        success_kw=success_kw,
        failure_kw=failure_kw,
        filter_subject=filter_subject,
        filter_body=filter_body,
        defaults=check,
        **kwargs,
    )
    try:
        return client.post(f"checks/{uuid}", payload=payload)
    except hcutil.HlcksException as err:
        raise CommandExecutionError(f"{type(err).__name__}: {err}") from err


def list_checks(tags=None, **kwargs):
    """
    Return a list of all checks.

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.list_checks

    tags
        A list of tags to filter for.
    """
    params = {}
    if tags:
        if not isinstance(tags, list):
            tags = [tags]
        params["tag"] = tags
    client = _client(**kwargs)
    try:
        return client.get("checks/", params=params)["checks"]
    except hcutil.HlcksException as err:
        raise CommandExecutionError(f"{type(err).__name__}: {err}") from err


def delete_check(name=None, uuid=None, **kwargs):
    """
    Delete an existing check.

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.delete_check mycheck

    name
        The name of the check. Specify either this or ``uuid``.

    uuid
        The UUID of the check. Specify either this or ``name``.
    """
    uuid = _get_check_uuid(name=name, uuid=uuid)
    client = _client(**kwargs)
    try:
        return client.delete(f"checks/{uuid}")
    except hcutil.HlcksException as err:
        raise CommandExecutionError(f"{type(err).__name__}: {err}") from err


def pause_check(name=None, uuid=None, **kwargs):
    """
    Pause an existing check.

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.pause_check mycheck

    name
        The name of the check. Specify either this or ``uuid``.

    uuid
        The UUID of the check. Specify either this or ``name``.
    """
    uuid = _get_check_uuid(name=name, uuid=uuid)
    client = _client(**kwargs)
    try:
        return client.post(f"checks/{uuid}/pause")
    except hcutil.HlcksException as err:
        raise CommandExecutionError(f"{type(err).__name__}: {err}") from err


def resume_check(name=None, uuid=None, **kwargs):
    """
    Resume an existing check.

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.resume_check mycheck

    name
        The name of the check. Specify either this or ``uuid``.

    uuid
        The UUID of the check. Specify either this or ``name``.
    """
    uuid = _get_check_uuid(name=name, uuid=uuid)
    client = _client(**kwargs)
    try:
        return client.post(f"checks/{uuid}/resume")
    except hcutil.HlcksException as err:
        raise CommandExecutionError(f"{type(err).__name__}: {err}") from err


def list_pings(name=None, uuid=None, limit=None, **kwargs):
    """
    List pings of an existing check.

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.list_pings mycheck

    name
        The name of the check. Specify either this or ``uuid``.

    uuid
        The UUID of the check. Specify either this or ``name``.

    limit
        Limit the maximum number of return values to the last n.
    """
    uuid = _get_check_uuid(name=name, uuid=uuid)
    client = _client(**kwargs)
    try:
        pings = client.get(f"checks/{uuid}/pings/")["pings"]
    except hcutil.HlcksException as err:
        raise CommandExecutionError(f"{type(err).__name__}: {err}") from err
    if limit and len(pings) > limit:
        pings = pings[:limit]
    return pings


def fetch_ping(number, name=None, uuid=None, **kwargs):
    """
    Get the full body of a ping of an existing check.

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.fetch_ping 42 name=mycheck

    number
        The ping number to fetch.

    name
        The name of the check. Specify either this or ``uuid``.

    uuid
        The UUID of the check. Specify either this or ``name``.
    """
    uuid = _get_check_uuid(name=name, uuid=uuid)
    client = _client(**kwargs)
    try:
        res = client.get(f"checks/{uuid}/pings/{number}/body", decode_json=False)
    except hcutil.HlcksException as err:
        raise CommandExecutionError(f"{type(err).__name__}: {err}") from err
    try:
        return json.loads(res)
    except json.JSONDecodeError:
        return res


def list_flips(
    name=None, uuid=None, seconds=None, start=None, end=None, limit=None, **kwargs
):
    """
    List flips of an existing check.

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.list_flips mycheck

    name
        The name of the check. Specify either this or ``uuid``.

    uuid
        The UUID of the check. Specify either this or ``name``.

    seconds
        Return the flips from the last n seconds.

    start
        Return flips that are newer than the specified UNIX timestamp.

    end
        Return flips that are older than the specified UNIX timestamp

    limit
        Limit the maximum number of return values to the last n.
    """
    params = {}
    if seconds:
        params["seconds"] = seconds
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    uuid = _get_check_uuid(name=name, uuid=uuid)
    client = _client(**kwargs)
    try:
        flips = client.get(f"checks/{uuid}/flips/", params=params)["flips"]
    except hcutil.HlcksException as err:
        raise CommandExecutionError(f"{type(err).__name__}: {err}") from err
    if limit and len(flips) > limit:
        flips = flips[:limit]
    return flips


def list_channels(kind=None, name=None, **kwargs):
    """
    List existing integrations (channels).

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.list_channels
        salt '*' healthchecks.list_channels kind='[po, email]'
        salt '*' healthchecks.list_channels kind=discord
        salt '*' healthchecks.list_channels name='[check1, check2]'

    kind
        A list of integrations to filter for. Can be a string or list of strings.

    name
        A list of names to filter for. Can be a string or list of strings.
    """
    if not isinstance(name, list):
        name = [name]
    if not isinstance(kind, list):
        kind = [kind]
    ret = []
    client = _client(**kwargs)
    try:
        channels = client.get("channels/")["channels"]
    except hcutil.HlcksException as err:
        raise CommandExecutionError(f"{type(err).__name__}: {err}") from err
    if not kind or name:
        return channels
    name = name or []
    kind = kind or []
    for channel in channels:
        if kind and channel["kind"] not in kind:
            continue
        if name and channel["name"] not in name:
            continue
        ret.append(channel)
    return ret


def fetch_channel(name=None, uuid=None, **kwargs):
    """
    Return an integration (channel) or None.

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.fetch_channel name=mydiscord

    name
        The name of the channel. Specify either this or ``uuid``.

    uuid
        The UUID of the channel. Specify either this or ``name``.
    """
    if uuid is None and name is None or uuid and name:
        raise SaltInvocationError("Need either uuid or name, exclusive")
    channels = list_channels(**kwargs)
    for channel in channels:
        if (name and channel["name"] == name) or (uuid and channel["id"] == uuid):
            return channel
    return None


def get_ping_url(
    name,
    server=None,
    policy=None,
    cache=True,
    **kwargs,
):
    """
    Return a ping URL for a check with the specified configuration applied.
    It is possible to request another minion to issue it in order to avoid
    having to distribute API access to each minion requesting a ping URL.

    This function accepts all parameters ``write_check`` supports.

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.get_ping_url mycheck timeout=86400 channels='*'
        salt '*' healthchecks.get_ping_url mycheck server=healthchecks policy=borgmatic timeout=86400 channels='*'

    name
        The name of the check. If it does not exist, it will be created.

    server
        Request a ping URL from this minion instead of issuing one locally.

    policy
        When requesting a ping URL from another minion, an issuance policy is
        required. This will only be respected for remote issuance.
        The name of the policy has to be defined on the issuing minion.
        See `Issuance policies`_ for details.

    cache
        Cache received ping URLs. The cache will only be accessed if there is
        a problem receiving the ping URL to prevent (highstate) rendering issues.
        If it has not been cached before, will still error. Defaults to true.
    """
    cbank = "hlcks/check_returns"
    cache = salt.cache.factory(__opts__)

    try:
        if server and server != __grains__["id"]:
            if not policy:
                raise SaltInvocationError("Remote issuance requires a policy")
            kwargs["name"] = name
            result = _query_remote(server, policy, kwargs)
            cache.store(cbank, name, result)
            return result

        if policy:
            pol = _get_policy(policy)
            # Sensibility is questionable, more for consistency
            if "minions" in pol:
                if not _match_minions(pol.pop("minions"), __grains__["id"]):
                    raise CommandExecutionError(
                        "minion not permitted to use specified policy"
                    )
            kwargs.pop("healthchecks_token", None)
            kwargs.pop("healthchecks_url", None)
            kwargs.pop("healthchecks_verify", None)
            kwargs.update(pol)
            if server:
                name = f"{__grains__['id']} {name}"

        changes = get_managed_changes(name, **kwargs)
        if changes:
            write_check(name, **kwargs)
        check = fetch_check(
            name,
            healthchecks_profile=kwargs.get("healthchecks_profile"),
            healthchecks_token=kwargs.get("healthchecks_token"),
            healthchecks_url=kwargs.get("healthchecks_url"),
            healthchecks_verify=kwargs.get("healthchecks_verify"),
        )
        cache.store(cbank, name, check["ping_url"])
        return check["ping_url"]
    except (CommandExecutionError, SaltInvocationError) as err:
        log.error(f"Could not manage check {name}: {err}")
        if cache.contains(cbank, name):
            return cache.fetch(cbank, name)
        raise


def _query_remote(server, policy, kwargs):
    result = __salt__["publish.publish"](
        server,
        "healthchecks.get_ping_url_remote",
        arg=[policy, kwargs],
    )

    if not result:
        raise SaltInvocationError(
            "server did not respond."
            " Salt master must permit peers to"
            " call the get_ping_url_remote function."
        )
    result = result[next(iter(result))]
    if not isinstance(result, dict) or "data" not in result:
        log.error("Received invalid return value from server: %s", result)
        raise CommandExecutionError(
            "Received invalid return value from server. See minion log for details"
        )
    if result.get("errors"):
        raise CommandExecutionError(
            "server reported errors:\n" + "\n".join(result["errors"])
        )
    return result["data"]


def get_ping_url_remote(policy, kwargs, **more_kwargs):
    """
    Request a healthcheck ping URL from an issuing minion.
    This is for internal use.

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.get_ping_url_remote borgmatic kwargs="{'name': 'test'}"

    policy
        The name of the policy to use. Required.

    kwargs
        A dict containing all the arguments to be passed into the
        ``healthchecks.write_check`` function.
    """
    ret = {"data": None, "errors": []}
    try:
        policy = _get_policy(policy)
        if not policy:
            ret["errors"].append(
                "policy must be specified and defined on issuing minion"
            )
            return ret
        if "minions" in policy:
            if "__pub_id" not in more_kwargs:
                ret["errors"].append(
                    "minion sending this request could not be identified"
                )
                return ret
            # also pop "minions" to avoid leaking more details than necessary
            if not _match_minions(policy.pop("minions"), more_kwargs["__pub_id"]):
                ret["errors"].append("minion not permitted to use specified policy")
                return ret
        name = kwargs.get("name", "")
        name = more_kwargs["__pub_id"] + (f" {name}" if name else name)
        kwargs.update(policy)
        kwargs["name"] = name
        # Ensure only local configuration is used
        kwargs.pop("healthchecks_token", None)
        kwargs.pop("healthchecks_url", None)
        kwargs.pop("healthchecks_verify", None)
        kwargs.pop("server", None)
        kwargs.pop("policy", None)
    except Exception as err:  # pylint: disable=broad-except
        log.error(str(err))
        return {
            "data": None,
            "errors": [
                "Failed building the policy. See issuing minion server log for details."
            ],
        }
    try:
        ret["data"] = get_ping_url(**kwargs)
        return ret
    except Exception as err:  # pylint: disable=broad-except
        log.exception(err)
        ret["data"] = None
        ret["errors"].append(str(err))
        return ret

    err_message = "Internal error. This is most likely a bug."
    log.error(err_message)
    return {"data": None, "errors": [err_message]}


def _get_policy(name):
    if name is None:
        return {}
    policies = __salt__["pillar.get"]("healthchecks_policies", {}).get(name)
    policies = policies or __salt__["config.get"]("healthchecks_policies", {}).get(name)
    return policies or {}


def _match_minions(test, minion):
    if "@" in test:
        # This runner is currently not found in salt master
        # https://github.com/saltstack/salt/pull/63297
        match = __salt__["publish.runner"]("match.compound_matches", arg=[test, minion])
        if match is None:
            raise CommandExecutionError(
                "Could not check minion match for compound expression. "
                "Is this minion allowed to run `match.compound_matches` on the master?"
            )
        if match == minion:
            return True
        return False
    return __salt__["match.glob"](test, minion)


def parse_check_params(
    name=None,
    tags=None,
    desc=None,
    timeout=None,
    grace=None,
    schedule=None,
    tz=None,
    manual_resume=None,
    methods=None,
    channels=None,
    start_kw=None,
    success_kw=None,
    failure_kw=None,
    filter_subject=None,
    filter_body=None,
    defaults=None,
    **kwargs,
):
    """
    Parses parameters for check create/update operations.
    Internal use. Cannot easily be inside the utils module since it
    needs to list channels.
    """
    payload = {}
    if methods and methods not in ("", "POST"):
        raise SaltInvocationError(
            "methods must be either an empty string or POST, if set"
        )
    if tags:
        if not isinstance(tags, list):
            tags = [tags]
        tags = " ".join(tags)
    if start_kw:
        if not isinstance(start_kw, list):
            start_kw = [start_kw]
        start_kw = ",".join(start_kw)
    if success_kw:
        if not isinstance(success_kw, list):
            success_kw = [success_kw]
        success_kw = ",".join(success_kw)
    if failure_kw:
        if not isinstance(failure_kw, list):
            failure_kw = [failure_kw]
        failure_kw = ",".join(failure_kw)
    if channels:
        if not isinstance(channels, list):
            channels = [channels]
        parsed_channels = []
        for channel in channels:
            if isinstance(channel, dict):
                # find channels of type and/or with name
                for match in list_channels(**channel, **kwargs):
                    parsed_channels.append(match["id"])
                continue
            parsed_channels.append(channel)
        channels = ",".join(parsed_channels)
    if schedule and timeout:
        log.warning("Both schedule and timeout were specified. Ignoring timeout.")
        timeout = None
    if timeout and tz:
        log.warning("tz only works in conjunction with schedule. Ignoring tz.")
        tz = None
    for param, val in (
        ("name", name),
        ("tags", tags),
        ("desc", desc),
        ("timeout", timeout),
        ("grace", grace),
        ("schedule", schedule),
        ("tz", tz),
        ("manual_resume", manual_resume),
        ("methods", methods),
        ("channels", channels),
        ("start_kw", start_kw),
        ("success_kw", success_kw),
        ("failure_kw", failure_kw),
        ("filter_subject", filter_subject),
        ("filter_body", filter_body),
    ):
        if val is not None:
            payload[param] = val
        elif defaults and param in defaults:
            payload[param] = defaults[param]

    return payload


def get_managed_changes(
    name,
    tags=None,
    desc=None,
    timeout=None,
    grace=None,
    schedule=None,
    tz=None,
    manual_resume=None,
    methods=None,
    channels=None,
    start_kw=None,
    success_kw=None,
    failure_kw=None,
    filter_subject=None,
    filter_body=None,
    **kwargs,
):
    """
    Internal use. This is what would actually be found in the state module
    as part of check_present.

    Since ``get_ping_url`` needs access to this function and might be
    called during a highstate on the minion acting as a server,
    ``state.single`` cannot be used reliably (multiple parallel state calls
    are not allowed).
    """
    current = fetch_check(name=name, **kwargs)
    changes = {}

    if current is not None:
        parsed_params = parse_check_params(
            name=name,
            tags=tags,
            desc=desc,
            timeout=timeout,
            grace=grace,
            schedule=schedule,
            tz=tz,
            manual_resume=manual_resume,
            methods=methods,
            channels=channels,
            start_kw=start_kw,
            success_kw=success_kw,
            failure_kw=failure_kw,
            filter_subject=filter_subject,
            filter_body=filter_body,
            **kwargs,
        )
        for param, val in parsed_params.items():
            if current[param] != val:
                changes[param] = {"old": current[param], "new": val}
    else:
        changes["created"] = name

    return changes


def _get_check_uuid(name, uuid, **kwargs):
    check = fetch_check(name=name if uuid is None else None, uuid=uuid, **kwargs)
    if not check:
        raise CommandExecutionError(f"Specified check {uuid or name} does not exist")
    if not uuid:
        uuid = check["ping_url"].split("/ping/")[-1]
    return uuid
