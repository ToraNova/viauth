# form helper class

def getbool(reqform, attr):
    formval = reqform.get(attr)
    if formval is None:
        return False
    if type(formval) is bool:
        return formval
    formval = formval.lower()
    return formval == "on" or \
            formval == "1" or \
            formval == "yes" or \
            formval == "true" or \
            formval == "t"

