# -*- coding: utf-8 -*-
# vim: ft=sls

{%- set tplroot = tpldir.split('/')[0] %}
{%- set sls_config_clean = tplroot ~ '.config.clean' %}
{%- from tplroot ~ "/map.jinja" import mapdata as healthchecks with context %}

include:
  - {{ sls_config_clean }}

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
