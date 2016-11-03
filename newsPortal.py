import fcntl
import os
import os.path
import sys
import time

FILE_PATH = "./.lock/.news"
MAX_IDLE_TIMEOUT = 10
NUM_CLIENT = 5

def consumeNews(condition, clientFeeds):
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
				#print "News reading: " + news
				if news:
					totalSleep = 0
					notifyReaders(condition, news, clientFeeds)
				else:
					if totalSleep >= MAX_IDLE_TIMEOUT and totalSleep%10 == 0:
						print "Producer is not generating news for last " + str(totalSleep) + " seconds."

			except:
				#Proper error message
				raise

		finally:
			fp.flush()
			fcntl.lockf(fp, fcntl.LOCK_UN)
			fp.close()	

		time.sleep(2)
		totalSleep += 2

def notifyReaders(condition, news, clientFeeds):
	freshNews = True
	totalWait = MAX_IDLE_TIMEOUT
	while totalWait > 0:
		try:
			condition.acquire()
			print "Portal acquired condition"	
			stillUnread = False
			if freshNews:
				freshNews = False
				stillUnread = True
				for i in range NUM_CLIENT:
					#Clean up feeds (Maintain sanity)
					for i in range NUM_CLIENT:
						while clientFeeds[i]:
							oNews = clientFeeds[i].pop()
							print "ERROR: Old news: " + str(oNews)
					clientFeeds[i].append(news)
				condition.notify_all()
				break
			else:
				stillUnread = False
				for i in range NUM_CLIENT:
					if not clientFeeds[i]:
						print "Thread " + str(i) + ", morning time, wake up and read news!(fight for your slot, BTW)"
						stillUnread = True
				if stillUnread:
					totalWait -= 2
					time.sleep(2)
		
			if totalWait <= 0 and stillUnread:
				print "Threads are not reading. Can't wait anymore. Time for new news."
				for i in range NUM_CLIENT:
					while clientFeeds[i]:
						clientFeeds[i].pop()

		except:
			print "Some error"

		finally:
			condition.release()

				
if __name__=="__main__":
	
	waitTime = MAX_IDLE_TIMEOUT
	while waitTime > 0:
		if not os.path.exists(FILE_PATH):
			waitTime -= 1
			if waitTime <=0 :
				print "Can't wait anymore."
				sys.exit(1)
			time.sleep(1)
		else:
			break	

	clientFeeds = []
	for i in range NUM_CLIENT:
		clientFeeds.append([])

	#run portal thread 
	consumeNews(condition, clientFeeds)

	#run the reader threads
