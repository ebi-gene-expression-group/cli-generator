import os
import yaml
from section_writer import *

GALAXY_FILENAME = os.path.join(os.path.dirname(__file__), "..", "tools_yaml", 'monocle3_markers.yaml')


def test_galaxy_writing():
    with open(file=GALAXY_FILENAME) as f:
        script_data = yaml.load(f)

    all_opts = list()
    for command in script_data['commands']:
        all_opts.extend(command['options'])

    opt_c = GalaxyCommandWriter(all_opts)
    print(opt_c.write_command())

    opt_w = GalaxyOptionsDeclarationWriter(all_opts)
    print(opt_w.write_declarations())