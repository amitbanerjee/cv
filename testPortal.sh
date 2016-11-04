#!/bin/bash

LOCK_FILE=".lock/.news"

echo "Please make sure the Producer is not running and the Portal is running"

PID=`ps -ef|grep "newsPortal"|grep -v grep|awk '{print $2}'`
if [ "X"$PID == "X" ]; then
	echo "Please start the newsPortal.py on another terminal."
	echo "python newsPortal.py"
	exit 1
fi

# Test1: Produce News and check portal if that is consumed
echo "Test2: Produce News and check portal log if that is consumed"
for i in {1..5}; do
	news="TestNews$RANDOM"
	echo $news > $LOCK_FILE
	echo "New News generated: $news"
	sleep 5
done

# Test2: Sit idle for some time and see Portal complaining for no news
echo "Test2 Sitting idle for 22 sec. You should see 2 ERROR lines in the Portal log" 
sleep 22

echo "Testing done. Killing prducer"
echo "Bye!"
