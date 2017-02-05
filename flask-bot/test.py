from Queue import Queue
from threading import Thread
# A thread that produces data
def producer(out_q):
    data = "R"
    out_q.put(data)


# A thread that consumes data
def consumer(in_q):
    data = in_q.get()
    # Process the data
    print data

# Create the shared queue and launch both threads
q = Queue()
t1 = Thread(target=consumer, args=(q,))
t2 = Thread(target=producer, args=(q,))
t1.start()
t2.start()