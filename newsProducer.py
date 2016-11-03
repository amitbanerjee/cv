import fcntl
import os
import os.path
import sys
import time
import random

FILE_PATH = "./.lock/.news"
MAX_IDLE_TIMEOUT = 10

def produceNews():
	totalSleep = 0
	lastNews = ""
	while True:

		try:
			fp = open(FILE_PATH, "w+", 0)
			fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)

		except IOError, err:
			# http://docs.python.org/library/fcntl.html#fcntl.lockf
			# Any exception other the usual one (raised when it fails to get ex lock), will be raised
			if err.errno not in (errno.EACCES, errno.EAGAIN):
				raise

		else:
			try:
				news = fp.read()
				print "News reading: " + news
				if not news:
					lastNews = "News" + str(random.randint(0, 10000))
					fp.write(lastNews)
					print "News writing: " + lastNews
					totalSleep = 0
				else:
					#Sanity Check
					if news != lastNews:
						print "Somebody else if producing news in the same channel."
						#TBD: proper message
						raise "Channel Exception"

					if totalSleep >= MAX_IDLE_TIMEOUT and totalSleep%10 == 0:
						print "Portal is not consuming news for last " + totalSleep + " seconds."

			except:
				#Proper error message
				raise

		finally:
			fp.flush()
			fcntl.lockf(fp, fcntl.LOCK_UN)
			fp.close()	

		time.sleep(2)
		totalSleep += 2

if __name__=="__main__":
	
	fileName = os.path.basename(FILE_PATH)
	dirName = os.path.dirname(FILE_PATH)

	#Make sure the file directory exists:
	if not os.path.exists(dirName):
		try:
			os.makedirs(dirName)
		except:
			#Doesn't make sense to proceed
			#TBD: Proper error message	
			print "Problem in directory creation"
			sys.exit(1)
	'''	
	try:	
		produceNews()
	except:
		#TBD:
		print "Error in producing news"

	'''
	produceNews()
