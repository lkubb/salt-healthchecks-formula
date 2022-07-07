# -*- coding: utf-8 -*-
# vim: ft=sls

{%- set tplroot = tpldir.split('/')[0] %}
{%- set sls_service_clean = tplroot ~ '.service.clean' %}
{%- from tplroot ~ "/map.jinja" import mapdata as healthchecks with context %}

include:
  - {{ sls_service_clean }}

# This does not lead to the containers/services being rebuilt
# and thus differs from the usual behavior
Healthchecks environment files are absent:
  file.absent:
    - names:
      - {{ healthchecks.lookup.paths.config_healthchecks }}
    - require:
      - sls: {{ sls_service_clean }}
