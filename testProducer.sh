#!/bin/bash

LOCK_FILE=".lock/.news"

#start producer

PID=`ps -ef|grep "newsProducer.py"|grep -v grep|awk '{print $2}'`

if [ "X"$PID == "X" ]; then

	nohup python  newsProducer.py > producer.log &
	ret=$?
	PID=`ps -ef|grep "newsProducer.py"|grep -v grep|awk '{print $2}'`

	if [ $ret -eq 0 -a "X"$PID != "X" ]; then
		echo "Started the newsProducer"
	else
		echo "Couldn't start newsProducer. Exiting"
		exit 1
	fi
else
	echo "newsProducer is running with PID $PID"
fi

# Test1: It's really producing news
echo "Test1: Here comes the latest news: "`cat $LOCK_FILE`

# Test2: Consume the news and check it is producing more news
echo "Test2: Reading news and consuming form channel"
for i in {1..5}; do
	news=`cat $LOCK_FILE`
	echo "Iteration $i: $news " 
	echo "" > $LOCK_FILE
	sleep 2
done

# Test3: Consume the news faster and expect producer is still sleeping sometimes.
# That sleeping param can be changed in the global section of the Producer code.
echo "Test3: Reading news little too fast"
for i in {1..5}; do
	news=`cat $LOCK_FILE`
	echo "Iteration $i: $news " 
	echo "" > $LOCK_FILE
	sleep 1
done


# Test4: Generate news in the same channel and see producer complaining. 
# Take a look in producer log
# NOTE: To see a producer log, run the program on another terminal so that the log comes on standard out.
# Redirection and kiiling doesn't flush the log for a small log.
echo "Test4: Generate news in the same channel"
echo "Extra News" >> $LOCK_FILE
news=`cat $LOCK_FILE`
echo "Now the news feed look like: "$news
sleep 3
echo "" > $LOCK_FILE


# Test5: Sit idle for some time and see producer complaining for not consuming 
# Take a look in producer log
# NOTE: To see a producer log, run the program on another terminal so that the log comes on standard out.
# Redirection and kiiling doesn't flush the log for a small log.
echo "Test5: Sitting idle for 22 sec. You should see 2 ERROR lines in the producer log" 
sleep 22

echo "Testing done. Killing prducer"
kill $PID
echo "Bye!"
