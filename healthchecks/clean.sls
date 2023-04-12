# vim: ft=sls

{#-
    *Meta-state*.

    Undoes everything performed in the ``healthchecks`` meta-state
    except configured checks in reverse order, i.e. stops the healthchecks services,
    removes their configuration and then removes their containers.
#}

include:
  - .service.clean
  - .config.clean
  - .package.clean
