import inspect


def create_R_file(*args, **kwargs):
    """
    This function simply print every thing you give to it into a R file named R_file.R

    """
    with open("R_file.R", 'r+') as r_file:
        to_write = r_file.read()
        all_args = inspect.getfullargspec(create_R_file)
        a = (locals()[all_args[1]])
        gafa = ' '.join(str(k) for k in a)
        r_file.write(to_write)
            

def write_R_file(path, *sections):
    with open(path, "w+") as r_file:
        r_file.write("#!/usr/bin/env Rscript")
        for section in sections:
            r_file.write(str(section))

        
    
    
