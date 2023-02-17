# vim: ft=sls


{#-
    Stops the healthchecks container services
    and disables them at boot time.
#}

{%- set tplroot = tpldir.split("/")[0] %}
{%- from tplroot ~ "/map.jinja" import mapdata as healthchecks with context %}

healthchecks service is dead:
  compose.dead:
    - name: {{ healthchecks.lookup.paths.compose }}
{%- for param in ["project_name", "container_prefix", "pod_prefix", "separator"] %}
{%-   if healthchecks.lookup.compose.get(param) is not none %}
    - {{ param }}: {{ healthchecks.lookup.compose[param] }}
{%-   endif %}
{%- endfor %}
{%- if healthchecks.install.rootless %}
    - user: {{ healthchecks.lookup.user.name }}
{%- endif %}

healthchecks service is disabled:
  compose.disabled:
    - name: {{ healthchecks.lookup.paths.compose }}
{%- for param in ["project_name", "container_prefix", "pod_prefix", "separator"] %}
{%-   if healthchecks.lookup.compose.get(param) is not none %}
    - {{ param }}: {{ healthchecks.lookup.compose[param] }}
{%-   endif %}
{%- endfor %}
{%- if healthchecks.install.rootless %}
    - user: {{ healthchecks.lookup.user.name }}
{%- endif %}
