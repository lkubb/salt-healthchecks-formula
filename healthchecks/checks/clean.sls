# vim: ft=sls

{#-
    Removes all managed checks.
#}

{%- set tplroot = tpldir.split("/")[0] %}
{%- from tplroot ~ "/map.jinja" import mapdata as healthchecks with context %}

{%- if healthchecks.checks %}

Configured health checks are absent:
  healthchecks.check_absent:
    - names: {{ healthchecks.checks | json }}
{%- endif %}
