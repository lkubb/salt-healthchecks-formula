# vim: ft=sls

{%- set tplroot = tpldir.split("/")[0] %}
{%- set sls_package_install = tplroot ~ ".package.install" %}
{%- from tplroot ~ "/map.jinja" import mapdata as healthchecks with context %}
{%- from tplroot ~ "/libtofsstack.jinja" import files_switch with context %}

include:
  - {{ sls_package_install }}

Healthchecks environment files are managed:
  file.managed:
    - names:
      - {{ healthchecks.lookup.paths.config_healthchecks }}:
        - source: {{ files_switch(
                        ["healthchecks.env", "healthchecks.env.j2"],
                        config=healthchecks,
                        lookup="healthchecks environment file is managed",
                        indent_width=10,
                     )
                  }}
    - mode: '0640'
    - user: root
    - group: {{ healthchecks.lookup.user.name }}
    - makedirs: true
    - template: jinja
    - require:
      - user: {{ healthchecks.lookup.user.name }}
    - require_in:
      - Healthchecks is installed
    - context:
        healthchecks: {{ healthchecks | json }}
