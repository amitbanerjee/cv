#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdbool.h>

#define NUM_READERS 5
#define MAX_NEWS_SIZE 50

typedef struct {
    pthread_mutex_t mutex; 	  // needed to add/remove data from the shared_news
    pthread_cond_t cond_portal;   // Used to notify Portal when all news are read
    pthread_cond_t cond_readers;  // Used to notify readers when new news arrives
    char news_buf[MAX_NEWS_SIZE]; // Place for readers to consume news
    bool read[NUM_READERS];       // TBD: number of readers not yet read news
} news_t;

typedef struct {
    int       thread_num;       /* Application-defined thread # */
    news_t    *shared_news;      /* From command-line argument */
} thread_info;

// Portal thread
void* portal(void *arg) {
    news_t *shared_news = (news_t*)arg;
    int i;
    bool still_unread;

    printf("Production Thread Started.");
    while(1) {

        pthread_mutex_lock(&shared_news->mutex);

	still_unread = false;
	for (i=0; i<NUM_READERS; i++) { 
          if (shared_news->read[i] == false) {
            still_unread = true;
            break;
	  }
        }

	//TBD:
	// 1. socket
	// 2. no wait, timewait
	// 3. periodic wakeup
        if(still_unread) { // Some readers have not read yet
            // wait until some elements are consumed
            pthread_cond_wait(&shared_news->cond_portal, &shared_news->mutex);
        }

        // in real life it may be some data fetched from
        // sensors, the web, or just some I/O
        int t = rand();
        printf("Produced: %d\n", t);

        // append data to the shared_news
	for (i=0; i<NUM_READERS; i++) { 
          shared_news->read[i] = false;
	}
	sleep(rand() % 3);
	// TBD: Copy the new in the buffer
        //shared_news->to_read = NUM_READERS;

        // signal the fact that new items may be consumed
        pthread_cond_signal(&shared_news->cond_readers);
        pthread_mutex_unlock(&shared_news->mutex);
    }

    // never reached
    return NULL;
}

// consume random numbers
void* consumer(void *arg) {
    // news_t *shared_news = (news_t*)arg;
    thread_info *this_thread = (thread_info*)arg;
    news_t *shared_news = this_thread->shared_news;
    int thread_num = this_thread->thread_num;

    printf("Production Thread Started.");
    while(1) {
        pthread_mutex_lock(&shared_news->mutex);

        if(shared_news->read[thread_num] == true) { // empty
            // wait for new items to be appended to the shared_news
            pthread_cond_wait(&shared_news->cond_readers, &shared_news->mutex);
        }

        // TBD: grab data
        shared_news->read[thread_num] == true;
        printf("Consumed: %d\n", thread_num);

        // signal the fact that new items may be produced
        pthread_cond_signal(&shared_news->cond_portal);
        pthread_mutex_unlock(&shared_news->mutex);
    }

    // never reached
    return NULL;
}

int main(int argc, char *argv[]) {
 
    int i;
    //news_t shared_news;
    news_t shared_news =  {PTHREAD_MUTEX_INITIALIZER, PTHREAD_COND_INITIALIZER, PTHREAD_COND_INITIALIZER, "Fake News", {}};
    thread_info reader_threads[NUM_READERS];
    pthread_t threads[NUM_READERS+1];

    printf("About to create threads\n");	
    //shared_news.news_buf = "This is a constant string";
    //shared_news->mutex = PTHREAD_MUTEX_INITIALIZER;
    //shared_new->cond_portal = PTHREAD_COND_INITIALIZER;
    //shared_news->cond_readers = PTHREAD_COND_INITIALIZER;
    for (i=0; i<NUM_READERS; i++) {
      shared_news.read[i] = false;
    }
    printf("About to create threads1\n");	
    pthread_create(&threads[0], NULL, portal, (void*)&shared_news);
    printf("About to create threads2\n");	
    for (i=0; i<NUM_READERS; i++) {
      reader_threads[i].thread_num = i;
      reader_threads[i].shared_news = &shared_news;
      pthread_create(&threads[i+1], NULL, consumer, (void*)&(reader_threads[i]));
    }
    printf("About to create threads3\n");	

    for (i=0; i<=NUM_READERS; i++) {
      pthread_join(threads[i], NULL);
    }

    return 0;
}
