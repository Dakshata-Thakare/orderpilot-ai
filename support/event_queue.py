import queue

subscribers = {}
#when in dashboard on particular order admin click view then that admin is subscribed i.e added that admin in queue for that order details and he started seeing that live data their
#when click the back button or close the window he gets unsubscribed and remove from the queue
'''
{
#order_id:[no of subscriber those are watching those real time conversations it can be one two ,more]
# [] this is list of queues===in that agents will publish to all of the queues
25:[[subscriber1],[subscriber2]]
8:[subscriber1]
}
'''

def subscribe(conversation_id):
    q = queue.Queue() # create and empty queue for this browser

    if conversation_id not in subscribers:
        subscribers[conversation_id] = []

    subscribers[conversation_id].append(q)
    return q

# we are unsubscribing from this queue
def unsubscribe(conversation_id,q):
    if conversation_id in subscribers:
        subscribers[conversation_id].remove(q)

        if not subscribers[conversation_id]:
            del subscribers[conversation_id]

#the events are going to publish for this particular conversation_id
def publish(conversation_id,event):
    print("conversation_id=====> ",conversation_id)
    print("event====> ",event)
    if conversation_id in subscribers:
        for q in subscribers[conversation_id]:
            q.put(event)


#sentinel value - it tells SSE stream to stop
DONE = {"type":"done"}