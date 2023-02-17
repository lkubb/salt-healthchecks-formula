# vim: ft=sls

{#-
    Starts the healthchecks container services
    and enables them at boot time.
    Has a dependency on `healthchecks.config`_.
#}

include:
  - .running
