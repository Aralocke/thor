UID_DEFINITION = [4, 4, 3, 8]
UID_DELIMITER  = '-'
UID_LENGTH = 22

class Object(object):

	__uid = None

	def __init__(self):
		self.__uid = self.__generateUid()

	def getUID(self):
		return self.__uid

	# Generate a long obnoxious string to denote the object ID of the class
	# This will be a unique identifier 
	def __generateUid(self, definition=UID_DEFINITION, delimiter=UID_DELIMITER):
		# This function is not cryptographically safe
		import random
		# we save this data within an aray which will be joined
		# by a delimiter later on
		uid = ['', '', '', '']
		# loop through the definition creating random parts at the given length
		for i in range(len(definition)):
			# The array element is the actual length of this portion of the uid
			# loop through assigning a random hex digit until lengths are correct
			while (len(uid[i]) < definition[i]):
				uid[i] += str(hex(random.randint(1,16)).replace('0x', ''))
		# Return the array with the given uuid delimeter
		return delimiter.join(uid)