# vim: ft=sls

{%- set tplroot = tpldir.split("/")[0] %}
{%- set sls_config_file = tplroot ~ ".config.file" %}
{%- from tplroot ~ "/map.jinja" import mapdata as healthchecks with context %}

include:
  - {{ sls_config_file }}

Healthchecks service is enabled:
  compose.enabled:
    - name: {{ healthchecks.lookup.paths.compose }}
{%- for param in ["project_name", "container_prefix", "pod_prefix", "separator"] %}
{%-   if healthchecks.lookup.compose.get(param) is not none %}
    - {{ param }}: {{ healthchecks.lookup.compose[param] }}
{%-   endif %}
{%- endfor %}
    - require:
      - Healthchecks is installed
{%- if healthchecks.install.rootless %}
    - user: {{ healthchecks.lookup.user.name }}
{%- endif %}

Healthchecks service is running:
  compose.running:
    - name: {{ healthchecks.lookup.paths.compose }}
{%- for param in ["project_name", "container_prefix", "pod_prefix", "separator"] %}
{%-   if healthchecks.lookup.compose.get(param) is not none %}
    - {{ param }}: {{ healthchecks.lookup.compose[param] }}
{%-   endif %}
{%- endfor %}
{%- if healthchecks.install.rootless %}
    - user: {{ healthchecks.lookup.user.name }}
{%- endif %}
    - watch:
      - Healthchecks is installed
      - sls: {{ sls_config_file }}
