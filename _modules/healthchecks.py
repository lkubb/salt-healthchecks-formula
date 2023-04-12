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

.. _hlcks-setup:
"""
import json
import logging

import healthchecksutil as hcutil
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
                    parsed_channels.append(match["ping_url"].split("/ping/")[-1])
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


def _get_check_uuid(name, uuid, **kwargs):
    check = fetch_check(name=name if uuid is None else None, uuid=uuid, **kwargs)
    if not check:
        raise CommandExecutionError(f"Specified check {uuid or name} does not exist")
    if not uuid:
        uuid = check["ping_url"].split("/ping/")[-1]
    return uuid
