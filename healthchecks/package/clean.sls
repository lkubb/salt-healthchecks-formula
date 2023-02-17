# vim: ft=sls

{#-
    Removes the healthchecks containers
    and the corresponding user account and service units.
    Has a depency on `healthchecks.config.clean`_.
    If ``remove_all_data_for_sure`` was set, also removes all data.
#}

{%- set tplroot = tpldir.split("/")[0] %}
{%- set sls_config_clean = tplroot ~ ".config.clean" %}
{%- from tplroot ~ "/map.jinja" import mapdata as healthchecks with context %}

include:
  - {{ sls_config_clean }}

{%- if healthchecks.install.autoupdate_service %}

Podman autoupdate service is disabled for Healthchecks:
{%-   if healthchecks.install.rootless %}
  compose.systemd_service_disabled:
    - user: {{ healthchecks.lookup.user.name }}
{%-   else %}
  service.disabled:
{%-   endif %}
    - name: podman-auto-update.timer
{%- endif %}

Healthchecks is absent:
  compose.removed:
    - name: {{ healthchecks.lookup.paths.compose }}
    - volumes: {{ healthchecks.install.remove_all_data_for_sure }}
{%- for param in ["project_name", "container_prefix", "pod_prefix", "separator"] %}
{%-   if healthchecks.lookup.compose.get(param) is not none %}
    - {{ param }}: {{ healthchecks.lookup.compose[param] }}
{%-   endif %}
{%- endfor %}
{%- if healthchecks.install.rootless %}
    - user: {{ healthchecks.lookup.user.name }}
{%- endif %}
    - require:
      - sls: {{ sls_config_clean }}

Healthchecks compose file is absent:
  file.absent:
    - name: {{ healthchecks.lookup.paths.compose }}
    - require:
      - Healthchecks is absent

{%- if healthchecks.install.podman_api %}

Healthchecks podman API is unavailable:
  compose.systemd_service_dead:
    - name: podman
    - user: {{ healthchecks.lookup.user.name }}
    - onlyif:
      - fun: user.info
        name: {{ healthchecks.lookup.user.name }}

Healthchecks podman API is disabled:
  compose.systemd_service_disabled:
    - name: podman
    - user: {{ healthchecks.lookup.user.name }}
    - onlyif:
      - fun: user.info
        name: {{ healthchecks.lookup.user.name }}
{%- endif %}

Healthchecks user session is not initialized at boot:
  compose.lingering_managed:
    - name: {{ healthchecks.lookup.user.name }}
    - enable: false
    - onlyif:
      - fun: user.info
        name: {{ healthchecks.lookup.user.name }}

Healthchecks user account is absent:
  user.absent:
    - name: {{ healthchecks.lookup.user.name }}
    - purge: {{ healthchecks.install.remove_all_data_for_sure }}
    - require:
      - Healthchecks is absent
    - retry:
        attempts: 5
        interval: 2

{%- if healthchecks.install.remove_all_data_for_sure %}

Healthchecks paths are absent:
  file.absent:
    - names:
      - {{ healthchecks.lookup.paths.base }}
    - require:
      - Healthchecks is absent
{%- endif %}
