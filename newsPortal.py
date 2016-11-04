import fcntl
import os
import os.path
import sys
import time
from threading import Thread, Condition

#This is the shared file between producer and Portal.
FILE_PATH = "./.lock/.news"

#This is a list(array) with NUM_READERS size. Each reader is supposed to read it's news from readersFeed[thread number].
# This is a global shared datastructure shared among the portal and readers.
# Whenever a news is produced, portal takes exclusive access and copies the news in this list for each reader and notify readers.
# Readers pop the news from it's own position
readersFeed = []

#This is the max idle timeout for the portal. Used in the follwoing places -
#  1. News portal prints out error message if News producer doesn't generate a news
#  2. News portal deletes record from readersFeed datastructure if one/more reder doesn't consume the news.
#  3. At initialization if News Portal wait time if the FILE_PATH file doesn't exist.
PORTAL_MAX_IDLE_TIMEOUT = 10

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
				if readersFeed[self.trNum]:
					news = readersFeed[self.trNum].pop()
					print "Thread " + str(self.trNum) + " got a new news " + news
				self.condition.wait(READER_WAIT)	

			except:
				print "Some Error"	
				print sys.exc_info()[0], sys.exc_info()[1]

			finally:
				self.condition.release()

			time.sleep(2)
				

class Portal(Thread):
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
						print "Portal got a new News " + news + " from producer. Going to share with the readers."
						fp.seek(0)
						fp.truncate(0)
						totalSleep = 0
						self.notifyReaders(news)
					else:
						if totalSleep >= PORTAL_MAX_IDLE_TIMEOUT and totalSleep%10 == 0:
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
	

	def notifyReaders(self, news):
		freshNews = True
		totalWait = PORTAL_MAX_IDLE_TIMEOUT
		while totalWait > 0:
			try:
				self.condition.acquire()
				print "Portal acquired condition"	
				stillUnread = False
				if freshNews:
					freshNews = False
					stillUnread = True
					for i in range(NUM_READERS):
						#Clean up feeds (Maintain sanity)
						while readersFeed[i]:
							oNews = readersFeed[i].pop()
							print "ERROR: Reader " + str(i) + " didn't read the old news: " + oNews
						readersFeed[i].append(news)
					self.condition.notify_all()
					print "Portal appended the news to the readersFeed and notified readers"
					break
				else:
					stillUnread = False
					for i in range(NUM_READERS):
						if not readersFeed[i]:
							print "Thread " + str(i) + ", morning time, wake up and read news!(fight for your slot, BTW)"
							stillUnread = True
					if stillUnread:
						totalWait -= 2
						time.sleep(2)
			
				if totalWait <= 0 and stillUnread:
					print "Threads are not reading. Can't wait anymore. Time for new news."
					for i in range(NUM_READERS):
						while readersFeed[i]:
							readersFeed[i].pop()
	
			except:
				print "Some error"
	
			finally:
				self.condition.release()

				
def main():	
	global readersFeed
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
