# Definition to validate uids

UID_DEFINITION = [4, 4, 3, 8]
UID_DELIMITER  = '-'
UID_LENGTH     = 22


# Class definition to act as an interface for future classes
class Identity(object):
    
    def __init__(self):
        self.__uid = generate_uid()
    
    def get_uid(self):
        return self.__uid

# Generate a long obnoxious string to denote the object ID of the class
# This will be a unique identifier 
def generate_uid():
    # This function is not cryptographically safe
    import random
    # we save this data within an aray which will be joined
    # by a delimiter later on
    uid = ['', '', '', '']
    # loop through the definition creating random parts at the given length
    for i in range(len(UID_DEFINITION)):
        # The array element is the actual length of this portion of the uid
        # loop through assigning a random hex digit until lengths are correct
        while (len(uid[i]) < UID_DEFINITION[i]):
            uid[i] += str(hex(random.randint(1,16)).replace('0x', ''))
    # Return the array with the given uuid delimeter
    return UID_DELIMITER.join(uid)