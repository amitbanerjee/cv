import fcntl
import os
import os.path
import sys
import time
import random
import errno

FILE_PATH = "./.lock/.news"

#This is a threshold timeout after which producer complains if the news is not consumed
MAX_IDLE_TIMEOUT = 10

#Portal thread wakeup interval
PRODUCER_SLEEP = 2


def produceNews():
	totalSleep = 0
	lastNews = ""
	while True:

		try:
			fp = open(FILE_PATH, "r+", 0)
			fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)

		except IOError, err:
			# http://docs.python.org/library/fcntl.html#fcntl.lockf
			# Any exception other the usual one (raised when it fails to get ex lock), will be raised
			if err.errno not in (errno.EACCES, errno.EAGAIN):
				raise

		else:
			try:
				news = fp.read().strip()
				if not news:
					lastNews = "News" + str(random.randint(0, 10000))
					fp.write(lastNews)
					totalSleep = 0
				else:
					#Sanity Check
					if news != lastNews:
						#Somebody else is producing news in the same channel
						print "ERROR: Some other news producer is generating news in the same channel"

					if totalSleep >= MAX_IDLE_TIMEOUT and totalSleep%10 == 0:
						print "Portal is not consuming news for last " + str(totalSleep) + " seconds."

			except:
				print "ERROR: In News producer thread. Messages follows - "
				print sys.exc_info()[0], sys.exc_info()[1]
				break

		finally:
			fp.flush()
			fcntl.lockf(fp, fcntl.LOCK_UN)
			fp.close()	

		#This is the time to allow the portal to grab the news and serve it to it's readers.
		time.sleep(PRODUCER_SLEEP)
		totalSleep += PRODUCER_SLEEP

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
			print "ERROR: Problem in directory creation"
			print sys.exc_info()[0], sys.exc_info()[1]
			sys.exit(1)

	if os.path.exists(FILE_PATH):
		#Truncate the file
		try:
			fp = open(FILE_PATH, "w", 0)
			fp.flush()
			fp.close()	
		except:
			print "ERROR: opening and truncating file" 
			print sys.exc_info()[0], sys.exc_info()[1]
			sys.exit(1)
			
	produceNews()
