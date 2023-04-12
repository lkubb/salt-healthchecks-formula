# vim: ft=sls

{%- set tplroot = tpldir.split("/")[0] %}
{%- set sls_service_running = tplroot ~ ".service.running" %}
{%- from tplroot ~ "/map.jinja" import mapdata as healthchecks with context %}

include:
  - {{ sls_service_running }}

{%- if healthchecks.checks %}

Configured health checks are present:
  healthchecks.check_present:
    - names:
{%-   for name, vals in healthchecks.checks %}
        - name: {{ vals | json }}
{%-   endfor %}
    - require:
      - sls: {{ sls_service_running }}
{%- endif %}

{%- if healthchecks.checks_absent %}

Unwanted health checks are absent:
  healthchecks.check_absent:
    - names: {{ healthchecks.checks_absent | json }}
    - require:
      - sls: {{ sls_service_running }}
{%- endif %}
