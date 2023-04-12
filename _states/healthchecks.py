"""
Interface with the Healthchecks v2 API.

For configuration instructions, the see ref:`execution module docs <hlcks-setup>`.
"""
import logging

from salt.exceptions import CommandExecutionError, SaltInvocationError

__virtualname__ = "healthchecks"

log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def check_present(
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
    Ensure a check is present.

    name
        The name of the check.

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
    ret = {
        "name": name,
        "result": True,
        "comment": "The check is already in the correct state",
        "changes": {},
    }
    try:
        current = __salt__["healthchecks.fetch_check"](name=name, **kwargs)
        changes = {}

        if current is not None:
            parsed_params = __salt__["healthchecks.parse_check_params"](
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

        if not changes:
            return ret
        ret["changes"] = changes

        if __opts__["test"]:
            ret["result"] = None
            ret[
                "comment"
            ] = f"The check would have been {'created' if not current else 'updated'}"
            return ret

        __salt__["healthchecks.write_check"](
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
        ret["comment"] = f"The check has been {'created' if not current else 'updated'}"
    except (CommandExecutionError, SaltInvocationError) as err:
        ret["result"] = False
        ret["comment"] = str(err)
        ret["changes"] = {}
    return ret


def check_absent(name, **kwargs):
    """
    Ensure a check does not exist.

    CLI Example:

    .. code-block:: bash

        salt '*' healthchecks.delete_check mycheck

    name
        The name of the check.
    """
    ret = {
        "name": name,
        "result": True,
        "comment": "The check is already in the correct state",
        "changes": {},
    }
    try:
        current = __salt__["healthchecks.fetch_check"](name=name, **kwargs)
        if current is None:
            return ret
        ret["changes"]["deleted"] = name

        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = "The check would have been deleted"
            return ret

        __salt__["healthchecks.delete_check"](
            name=name,
            **kwargs,
        )
        ret["comment"] = "The check has been deleted"
    except (CommandExecutionError, SaltInvocationError) as err:
        ret["result"] = False
        ret["comment"] = str(err)
        ret["changes"] = {}
    return ret


def check_state_managed(name, paused=False, **kwargs):
    """
    Manage the pause state of an existing check.

    name
        The name of the check.

    paused
        Whether the check should be paused. Defaults to false.
    """
    ret = {
        "name": name,
        "result": True,
        "comment": "The check is already in the correct state",
        "changes": {},
    }
    try:
        current = __salt__["healthchecks.fetch_check"](name=name, **kwargs)
        if current is None:
            raise CommandExecutionError("Could not find check")
        if (current["status"] == "paused") is paused:
            return ret
        verb = "pause" if paused else "resume"
        ret["changes"][f"{verb}d"] = name

        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"The check would have been {verb}d"
            return ret

        __salt__[f"healthchecks.{verb}_check"](
            name=name,
            **kwargs,
        )
        ret["comment"] = f"The check has been {verb}d"
    except (CommandExecutionError, SaltInvocationError) as err:
        ret["result"] = False
        ret["comment"] = str(err)
        ret["changes"] = {}
    return ret
