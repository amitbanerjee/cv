import string


def main():

	inputS = raw_input("Enter string with one/more words in it: ")
	inputL = []
	for char in inputS:
		inputL.append(char) 

	#Word seperators
	seperators = [" ", "	", "\n", ".", ",", ";"]

	i = 0

	while i < len(inputL):

		#Ignore all seperators chars
		while i < len(inputL) and inputL[i] in seperators:
			i += 1

		#End of the string
		if i >= len(inputL):
			break
		
		print "i in the beginning: " + inputL[i]
		#i is pointing to a word now
		j = i
		while j < len(inputL) and (inputL[j] not in seperators):
			j += 1
		j -= 1
		print "j is at the end of word: " + inputL[j]

		start = i
		end = j

		#Reverse the word
		while start < end:
			#exchange the chars
			x = inputL[start]
			inputL[start] = inputL[end]
			inputL[end] = x
			start += 1
			end -= 1

		#point to the next word
		i = j+1

	reversedWord = "".join(inputL)
	print reversedWord

if __name__=="__main__":
	main()
