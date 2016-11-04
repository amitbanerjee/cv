import fcntl
import os
import os.path
import sys
import time
from threading import Thread, Condition
import errno

#This is the shared file between producer and Portal.
FILE_PATH = "./.lock/.news"

#This is a list(array) with NUM_READERS size. Each reader is supposed to read it's news from readersFeed[thread number].
# This is a global shared datastructure shared among the portal and readers.
# Whenever a news is produced, portal takes exclusive access and copies the news in this list for each reader and notify readers.
# Readers pop the news from it's own position readersFeed[thread number]
readersFeed = []

### The following are different timer values(explained in details). To test/tune, theese numbers need to be changed.

#This is the max idle timeout in seconds for the portal. Used in the follwoing places -
#  1. News portal prints out error message if News producer doesn't generate a news
#  2. News portal deletes record from readersFeed datastructure if one/more reder doesn't consume the news.
#  3. At initialization, News Portal wait time if the FILE_PATH file doesn't exist.
PORTAL_MAX_IDLE_TIMEOUT = 10

#Portal thread wakeup interval
PORTAL_SLEEP = 2

#Number of readers. This is the single place to change reader number.
NUM_READERS = 5

#READER wait time in condition
READER_WAIT = 2

#After this time reader threads complain about no new news.
READER_MAX_IDLE_TIMEOUT = 10


class Reader(Thread):

	'''
	This is the thread to consume news from the the readersFeed datastructure.
	Each thread has a number and it only read from it's place(index) in in the readersFeed
	Total number of reader thread is defined in global variable NUM_READERS
	'''

        def __init__ (self, condition, num):
		super(Reader, self).__init__()
		self.condition = condition
		self.trNum = num
		self.kill_received = False

	def __del__(self):
		del self.condition 
		del self.trNum
		del self.kill_received

	def run(self):
		global readersFeed

		while not self.kill_received:
			try:
				self.condition.acquire()

				#If there is news waiting for you, grab it.
				if readersFeed[self.trNum]:
					news = readersFeed[self.trNum].pop()
					print "Thread " + str(self.trNum) + " got a new news " + news

				#Wait for the Portal thread to notify
				self.condition.wait(READER_WAIT)	

			except:
				print "ERROR: In reader thread. Messages follows - "	
				print sys.exc_info()[0], sys.exc_info()[1]

			finally:
				self.condition.release()


class Portal(Thread):

	'''
	This is the thread to consume news from the the readersFeed datastructure.
	Each thread has a number and it only read from it's place(index) in in the readersFeed
	Total number of reader thread is defined in global variable NUM_READERS
	'''

        def __init__ (self, condition):
		super(Portal, self).__init__()
		self.condition = condition
		self.kill_received = False

	def __del__(self):
		del self.condition 
		del self.kill_received

	def run(self):
		global readersFeed
		totalSleep = 0
		lastNews = ""

		while not self.kill_received:
			try:
				#Open the shared file and grab exclusive lock
				fp = open(FILE_PATH, "r+", 0)
				fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
	
			except IOError, err:
				# http://docs.python.org/library/fcntl.html#fcntl.lockf
				# Any exception other the usual one (raised when it fails to get ex lock), will be raised
				if err.errno not in (errno.EACCES, errno.EAGAIN):
					raise
				#Better luck next time for grabbing the exclusive lock
	
			else:
				#Acquired the exclusive lock
				try:
					print "Portal acquired exclusive access of the shared file"
					news = fp.read().strip()
					if news:
						print "Portal got a new News " + news + " from producer. Going to share with the readers."
						#Take the news off of the shared file
						fp.seek(0)
						fp.truncate(0)
						totalSleep = 0
						#Let the readers consume the news. Will not relase the exclusive lock untill all readers read the news
						self.notifyReaders(news)
					else:
						#No news, if the threshold is crossed, complain. News produces may have died. 
						if totalSleep >= PORTAL_MAX_IDLE_TIMEOUT and totalSleep%PORTAL_MAX_IDLE_TIMEOUT == 0:
							print "Producer is not generating news for last " + str(totalSleep) + " seconds."
	
				except:
					print "ERROR: In Portal thread. Messages follows - "	
					print sys.exc_info()[0], sys.exc_info()[1]
	
			finally:
				fp.flush()
				print "Portal released exclusive access of the shared file"
				fcntl.lockf(fp, fcntl.LOCK_UN)
				fp.close()	
	
			#Let the readers read the news
			time.sleep(PORTAL_SLEEP)
			totalSleep += PORTAL_SLEEP
	

	def notifyReaders(self, news):

		'''
		This function copies the news in the reader's specific placce in the readersFeed datastructure. readerFeed[thread number]
		Notify all readers thread to wake up and consume news. 
		After the threshold, if news is not conssumed, it cleans up the space.
		'''

		#Following variable indicates if the news is not yet distributed to the readers
		freshNews = True
		#Timeout for the readers to read. After this time the news is erased from the readersFeed datastructure
		totalWait = PORTAL_MAX_IDLE_TIMEOUT

		while totalWait > 0:
			try:
				self.condition.acquire()
				print "Portal acquired condition"	
				#Following variable indicates if all the readers read the news.
				stillUnread = False

				if freshNews:
					#The news is not yet read by the readers. Just got it from the Producer.
					freshNews = False
					stillUnread = True
					
					for i in range(NUM_READERS):
						#This is an error condition check. If the news is still not consumed by one/more readers, 
						#it will be reported and erased.
						while readersFeed[i]:
							oNews = readersFeed[i].pop()
							print "ERROR: Reader " + str(i) + " didn't read the old news: " + oNews
						#Supply the news for all the readers
						readersFeed[i].append(news)

					#Notify all readers 
					self.condition.notify_all()
					print "Portal appended the news to the readersFeed and notified readers"

				else:
					#Coming back to check if all readers read the news.
					stillUnread = False
					for i in range(NUM_READERS):
						if readersFeed[i]:
							print "Thread " + str(i) + ", morning time, wake up and read news!(fight for your slot, BTW)"
							stillUnread = True

					#Well, all readers read news, time for a freash news to look for
					if not stillUnread:
						break
			
				#Still some threads have not read news after the threshold time
				if totalWait <= 0 and stillUnread:
					print "Threads are not reading. Can't wait anymore. Time for new news."
					for i in range(NUM_READERS):
						while readersFeed[i]:
							readersFeed[i].pop()
	
			except:
				print "ERROR: In notify reader function. Messages follows - "	
				print sys.exc_info()[0], sys.exc_info()[1]

			finally:
				self.condition.release()

			#Sleep before checking again if the readers read the news
			totalWait -= PORTAL_SLEEP
			time.sleep(PORTAL_SLEEP)

				
def main():	

	global readersFeed
	
	#Make sure the shared file exists. If not, wait for a threhold time
	waitTime = PORTAL_MAX_IDLE_TIMEOUT
	while waitTime > 0:
		if not os.path.exists(FILE_PATH):
			waitTime -= 1
			if waitTime <=0 :
				print "Can't wait anymore."
				sys.exit(1)
			time.sleep(1)
		else:
			break	

	#Initialize the gloab; readersFeed with the num reader size
	for i in range(NUM_READERS):
		readersFeed.append([])

	threads = []
	condition = Condition()

	#start portal thread 
	portalTr = Portal(condition)
	portalTr.start()
	threads.append(portalTr)

	#Start reader threads
	for i in range(NUM_READERS):
		readerTr = Reader(condition, i)
		readerTr.start()
		threads.append(readerTr)

	while len(threads) > 0:
        	try:
            		# Join all threads using a timeout so it doesn't block
            		# Filter out threads which have been joined or are None
            		threads = [t.join(1) for t in threads if t is not None and t.isAlive()]
        	except KeyboardInterrupt:
            		print "Ctrl-c received! Sending kill to threads..."
            		for t in threads:
                		t.kill_received = True

if __name__=="__main__":
	main()
