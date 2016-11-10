all: newsProducer newsPortal

newsProducer: newsProducer.c
	gcc -o newsProducer newsProducer.c

newsPortal: newsProducer.c
	gcc -pthread -o newsPortal newsPortal.c

clean:
	rm newsProducer newsPortal	
