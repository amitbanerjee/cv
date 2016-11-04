# File list

## README.md -- This file 
## reverseWords.py -- This is the python program to reverse the word of a string. Takes input from standard input
## newsProducer.py -- Python code for the news producer
## newsPortal.py -- Python code for News portal and readers
## testPortal.sh -- Automated unit test code for Portal program
## testProducer.sh -- Automated unit test code for Producer program

# Reverse word quiz

## Brief design highlight for the reverseWords.py
## It takes a string through standard input and reverse the words only. Everything else is unchanged.
## since string variable in python is immutable it converts it into an arrary and reverse the words in-place.
## It uses two pointer for each word and exchange the values. For each exchange left pointer forwards and right
## pointer goes backwords untill they touch or cross each other.

## To run - "python reverseWords.py". It needs pythin 2.7


# News producer and news Portal/News Readers quiz

## Brief design highlight: News Producer
## Producer and Portal exchange data through an exclusive lock to a file. It uses fcntl(2) on unix like filesystem, not designed foe windows.
## The lock file is also the news channel though which producer send the news to Portal. Producer peridically checks for exclusive lock
## (non-blocking mode to avoid dead lock). If it gets it it and the file is empty it generates news and goes back to periodic sleep
## If the file is not empty it waits for threshold time and then generates error log.

## It writes the log in standard out. So to run use "nohup python newsProducer.py > producer.log &". To live monitor, use
## python newsProducer.py. Use ctrl-c to terminate

## To test it independently use the shell code - testProducer.sh


## Brief design highlight: News Portal
## As mentioned earlier, it consumes the news by taking the exclusive lock on the shared file and reading from it.
## The program has one dedicated thread from this portal worker and "NUM_READERS" threads (a global variable in the code) for readers
## There is a global variable "readersFeed", which is an array with "NUM_READERS" size. Portal copies the news in this array and readers 
## consume it from their respective position readersFeed[threadNum].

## Portal and readers share the global variable "readersFeed" using a "condition" object. Portal thread peridically checks for new news in
## shared file. If there is a new news, it tries to acquire condition lock on readersFeed and see if all the places are empty (readers consumed
## the earlier news). There is a threshold time after which it will assume the reader has dies and clean up the respective position.
## Then the portal copies the news in readersFeed and "notify" the readers. It then releases the condition lock and the file lock. Now it would 
## periodically lock the shared file to check if there is any new news.

## Readers are always waiting for new news using "condition.wait". The wait call is not blocking, it times out that makes the thread alive.
## It also wakes up by the notify call of the Portal thread. Now it would check if new news available that it consumes it and makes it place 
## in readersFeed empty and goes back to wait call.

## It writes the log in standard out. So to run use "nohup python newsPortal.py > portal.log &". To live monitor, use
## python newsPortal.py. Use ctrl-c to terminate.

## To test it independently use the shell code - testPortal.sh
