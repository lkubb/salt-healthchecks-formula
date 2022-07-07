# -*- coding: utf-8 -*-
# vim: ft=sls

{%- set tplroot = tpldir.split('/')[0] %}
{%- from tplroot ~ "/map.jinja" import mapdata as healthchecks with context %}
{%- from tplroot ~ "/libtofs.jinja" import files_switch with context %}

Healthchecks user account is present:
  user.present:
{%- for param, val in healthchecks.lookup.user.items() %}
{%-   if val is not none and param != "groups" %}
    - {{ param }}: {{ val }}
{%-   endif %}
{%- endfor %}
    - usergroup: true
    - createhome: true
    - groups: {{ healthchecks.lookup.user.groups | json }}
    # (on Debian 11) subuid/subgid are only added automatically for non-system users
    - system: false

Healthchecks user session is initialized at boot:
  compose.lingering_managed:
    - name: {{ healthchecks.lookup.user.name }}
    - enable: {{ healthchecks.install.rootless }}

Healthchecks paths are present:
  file.directory:
    - names:
      - {{ healthchecks.lookup.paths.base }}
    - user: {{ healthchecks.lookup.user.name }}
    - group: {{ healthchecks.lookup.user.name }}
    - makedirs: true
    - require:
      - user: {{ healthchecks.lookup.user.name }}

Healthchecks compose file is managed:
  file.managed:
    - name: {{ healthchecks.lookup.paths.compose }}
    - source: {{ files_switch(['docker-compose.yml', 'docker-compose.yml.j2'],
                              lookup='Healthchecks compose file is present'
                 )
              }}
    - mode: '0644'
    - user: root
    - group: {{ healthchecks.lookup.rootgroup }}
    - makedirs: True
    - template: jinja
    - makedirs: true
    - context:
        healthchecks: {{ healthchecks | json }}

Healthchecks is installed:
  compose.installed:
    - name: {{ healthchecks.lookup.paths.compose }}
{%- for param, val in healthchecks.lookup.compose.items() %}
{%-   if val is not none and param != "service" %}
    - {{ param }}: {{ val }}
{%-   endif %}
{%- endfor %}
{%- for param, val in healthchecks.lookup.compose.service.items() %}
{%-   if val is not none %}
    - {{ param }}: {{ val }}
{%-   endif %}
{%- endfor %}
    - watch:
      - file: {{ healthchecks.lookup.paths.compose }}
{%- if healthchecks.install.rootless %}
    - user: {{ healthchecks.lookup.user.name }}
    - require:
      - user: {{ healthchecks.lookup.user.name }}
{%- endif %}
