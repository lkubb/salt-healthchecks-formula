Available states
----------------

The following states are found in this formula:

.. contents::
   :local:


``healthchecks``
^^^^^^^^^^^^^^^^
*Meta-state*.

This installs the healthchecks containers,
manages their configuration and starts their services.
Also manages checks, if configured.
If there are multiple projects, each one needs a separate
API key. You can include them in the check definitions,
see ``healthchecks_profile`` or ``healthchecks_token``.


``healthchecks.package``
^^^^^^^^^^^^^^^^^^^^^^^^
Installs the healthchecks containers only.
This includes creating systemd service units.


``healthchecks.config``
^^^^^^^^^^^^^^^^^^^^^^^
Manages the configuration of the healthchecks containers.
Has a dependency on `healthchecks.package`_.


``healthchecks.service``
^^^^^^^^^^^^^^^^^^^^^^^^
Starts the healthchecks container services
and enables them at boot time.
Has a dependency on `healthchecks.config`_.


``healthchecks.checks``
^^^^^^^^^^^^^^^^^^^^^^^
Manages configured checks.
Has a dependency on `healthchecks.service`_.


``healthchecks.clean``
^^^^^^^^^^^^^^^^^^^^^^
*Meta-state*.

Undoes everything performed in the ``healthchecks`` meta-state
except configured checks in reverse order, i.e. stops the healthchecks services,
removes their configuration and then removes their containers.


``healthchecks.package.clean``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Removes the healthchecks containers
and the corresponding user account and service units.
Has a depency on `healthchecks.config.clean`_.
If ``remove_all_data_for_sure`` was set, also removes all data.


``healthchecks.config.clean``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Removes the configuration of the healthchecks containers
and has a dependency on `healthchecks.service.clean`_.

This does not lead to the containers/services being rebuilt
and thus differs from the usual behavior.


``healthchecks.service.clean``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Stops the healthchecks container services
and disables them at boot time.


``healthchecks.checks.clean``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Removes all managed checks.


