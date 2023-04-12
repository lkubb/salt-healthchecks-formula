.. _readme:

Healthchecks Formula
====================

|img_sr| |img_pc|

.. |img_sr| image:: https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg
   :alt: Semantic Release
   :scale: 100%
   :target: https://github.com/semantic-release/semantic-release
.. |img_pc| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :alt: pre-commit
   :scale: 100%
   :target: https://github.com/pre-commit/pre-commit

Manage Healthchecks with Salt and Podman.

.. contents:: **Table of Contents**
   :depth: 1

General notes
-------------

See the full `SaltStack Formulas installation and usage instructions
<https://docs.saltstack.com/en/latest/topics/development/conventions/formulas.html>`_.

If you are interested in writing or contributing to formulas, please pay attention to the `Writing Formula Section
<https://docs.saltstack.com/en/latest/topics/development/conventions/formulas.html#writing-formulas>`_.

If you want to use this formula, please pay attention to the ``FORMULA`` file and/or ``git tag``,
which contains the currently released version. This formula is versioned according to `Semantic Versioning <http://semver.org/>`_.

See `Formula Versioning Section <https://docs.saltstack.com/en/latest/topics/development/conventions/formulas.html#versioning>`_ for more details.

If you need (non-default) configuration, please refer to:

- `how to configure the formula with map.jinja <map.jinja.rst>`_
- the ``pillar.example`` file
- the `Special notes`_ section

Special notes
-------------
* This formula is written with the custom `compose modules <https://github.com/lkubb/salt-podman-formula>`_ in mind and will not work without them.
* It also provides custom modules to interface with Healthchecks. A nice feature is that you can request ping URLs from a central location, similar to how the ``x509`` modules work. See the execution module for details.

Configuration
-------------
An example pillar is provided, please see `pillar.example`. Note that you do not need to specify everything by pillar. Often, it's much easier and less resource-heavy to use the ``parameters/<grain>/<value>.yaml`` files for non-sensitive settings. The underlying logic is explained in `map.jinja`.


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



Contributing to this repo
-------------------------

Commit messages
^^^^^^^^^^^^^^^

**Commit message formatting is significant!**

Please see `How to contribute <https://github.com/saltstack-formulas/.github/blob/master/CONTRIBUTING.rst>`_ for more details.

pre-commit
^^^^^^^^^^

`pre-commit <https://pre-commit.com/>`_ is configured for this formula, which you may optionally use to ease the steps involved in submitting your changes.
First install  the ``pre-commit`` package manager using the appropriate `method <https://pre-commit.com/#installation>`_, then run ``bin/install-hooks`` and
now ``pre-commit`` will run automatically on each ``git commit``. ::

  $ bin/install-hooks
  pre-commit installed at .git/hooks/pre-commit
  pre-commit installed at .git/hooks/commit-msg

State documentation
~~~~~~~~~~~~~~~~~~~
There is a script that semi-autodocuments available states: ``bin/slsdoc``.

If a ``.sls`` file begins with a Jinja comment, it will dump that into the docs. It can be configured differently depending on the formula. See the script source code for details currently.

This means if you feel a state should be documented, make sure to write a comment explaining it.

Testing
-------

Linux testing is done with ``kitchen-salt``.

Requirements
^^^^^^^^^^^^

* Ruby
* Docker

.. code-block:: bash

   $ gem install bundler
   $ bundle install
   $ bin/kitchen test [platform]

Where ``[platform]`` is the platform name defined in ``kitchen.yml``,
e.g. ``debian-9-2019-2-py3``.

``bin/kitchen converge``
^^^^^^^^^^^^^^^^^^^^^^^^

Creates the docker instance and runs the ``healthchecks`` main state, ready for testing.

``bin/kitchen verify``
^^^^^^^^^^^^^^^^^^^^^^

Runs the ``inspec`` tests on the actual instance.

``bin/kitchen destroy``
^^^^^^^^^^^^^^^^^^^^^^^

Removes the docker instance.

``bin/kitchen test``
^^^^^^^^^^^^^^^^^^^^

Runs all of the stages above in one go: i.e. ``destroy`` + ``converge`` + ``verify`` + ``destroy``.

``bin/kitchen login``
^^^^^^^^^^^^^^^^^^^^^

Gives you SSH access to the instance for manual testing.
