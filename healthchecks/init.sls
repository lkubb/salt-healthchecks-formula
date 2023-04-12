# vim: ft=sls

{#-
    *Meta-state*.

    This installs the healthchecks containers,
    manages their configuration and starts their services.
    Also manages checks, if configured.
    If there are multiple projects, each one needs a separate
    API key. You can include them in the check definitions,
    see ``healthchecks_profile`` or ``healthchecks_token``.
#}

include:
  - .package
  - .config
  - .service
  - .checks
