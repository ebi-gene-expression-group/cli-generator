import inspect

def create_R_file(*args,**kwargs):
    with open("R_file.R", 'w+') as r_file:
        to_write = ""
        a = []
        all_args = inspect.getargspec(create_R_file)
        a.extend(locals()[all_args[1]])
        a.extend(locals()[all_args[2]])
        all_args = inspect.getargspec(create_R_file)
        for element in a:
            to_write += element
        r_file.write(to_write)
            

def write_R_file(path, *sections):
    with open(path, "w+") as r_file:
        for section in sections:
            r_file.write(str(section))

        
    
    
