import sys

class Fetch():
 	
 	"""docstring for Fetch_Plus"""
 	
 	def __init__(self, *args):
 		self.args = args
 		
	def int_hex(self):
		list_hex = []
		for arg in self.args:
			list_hex.append(self.format_hex(arg))
		hex_value = "#%s" % "".join(list_hex)
		print "the hex value of html color code is " + hex_value

	def format_hex(self, val): return hex(val)[2:].zfill(2).upper()

   	def file_content(self):
   		fname = "fetch.txt"
		num_lines = num_words = num_chars = 0
		with open(fname, 'r') as f:
			for line in f:
				words = line.split()
				num_lines += 1
				num_words += len(words)
				num_chars += len(line)

		print "The file contains..."
		print "total lines: " + str(num_lines)	
		print "total words: " + str(num_words)
		print "total characters: " + str(num_chars)

if "__main__" == __name__:
	
	## improvement: use commandline argument(using getopt module) to choose with proces to use
	## -hex option for decimal to hex conversion
	## -count to get the file content

	fp = Fetch(0, 255, 255)
	fp.int_hex()
	fp.file_content()
