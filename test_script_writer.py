import os
import yaml
from section_writer import *
from RWrapperOrganiser import *
from textwrap import dedent

TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'findtransferanchors.yaml')
# TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'yo.yaml')
# TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'PercentageFeatureSet.yaml')


def test_script_writing():
    with open(file=TESTDATA_FILENAME) as f:
        script_data = yaml.full_load(f)
    to_be_writed = []
    all_opts = list()
    for command in script_data['commands']:
        all_opts.extend(command['options'])
    print("ALL OPTS = " + str(all_opts))

    shebang_w = shebang_writer(script_data)

    dep_w = RDependencies(script_data['commands'])
    print("ALLL DEPENDENCIES ")
    print(dep_w.write())

    save_w = RsaveRDS(script_data['commands'])
    print(save_w.write())

    wsc_treatment = need_wsc(all_opts)
    all_opts = wsc_treatment.corrected_options

    opt_w = ROptionsDeclarationWriter(all_opts)
    print(opt_w.write_declarations())

    prepoc_out = ""
    try:
        preproc_w = RPreprocessWriter(all_opts)
        print(preproc_w.write_preprocess())
        prepoc_out = preproc_w.write_preprocess()
    except:
        pass


    importformat_w = Ropeninglibrary(all_opts)

    for command in script_data['commands']:
        cmd_w = RCommandWriter.create_writer(command)
        print(cmd_w.write_command_call())

    with open("R_file.R", 'w+') as r_file:

        for element in to_be_writed:
            r_file.write(dedent(element))

    create_R_file(shebang_w.write(), dep_w.write(), opt_w.write_declarations(), wsc_treatment.write(), prepoc_out, cmd_w.write_command_call(), save_w.write())


test_script_writing()

