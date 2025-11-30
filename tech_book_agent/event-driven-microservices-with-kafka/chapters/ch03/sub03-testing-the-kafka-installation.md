## Testing the Kafka Installation

Now that you have Kafka installed and running, it's time to verify that everything is working correctly. In this section, we'll guide you through testing your Kafka setup by producing and consuming messages to a test topic.

### Creating a Test Topic

First, let's create a test topic that we'll use for our verification:

```bash
# Create a test topic with a single partition
kafka-topics.sh --create --topic test-topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

You should see confirmation that the topic was created successfully. To verify the topic exists, list all topics:

```bash
kafka-topics.sh --list --bootstrap-server localhost:9092
```

### Producing Test Messages

Open a new terminal window and start the Kafka console producer. This tool allows you to send messages to your topic:

```bash
kafka-console-producer.sh --topic test-topic --bootstrap-server localhost:9092
```

Once the producer starts, you'll see a prompt where you can type messages. Type a few test messages:
- `Hello Kafka!`
- `This is a test message`
- `Microservices are awesome!`

Press **Ctrl+C** to exit the producer.

### Consuming the Messages

In another terminal window, start the Kafka console consumer to read the messages you just produced:

```bash
kafka-console-consumer.sh --topic test-topic --bootstrap-server localhost:9092 --from-beginning
```

You should immediately see the messages you sent appearing in the consumer window:
- `Hello Kafka!`
- `This is a test message`
- `Microservices are awesome!`

The **`--from-beginning`** flag tells the consumer to read all messages from the start of the topic. Without this flag, the consumer would only receive new messages sent after it started.

### Real-Time Testing

To test real-time message flow, you can run both producer and consumer simultaneously:

1. Start the consumer in one terminal (without `--from-beginning`):
   ```bash
   kafka-console-consumer.sh --topic test-topic --bootstrap-server localhost:9092
   ```

2. In another terminal, start the producer and type new messages
3. Watch as messages appear instantly in the consumer terminal

### Verification Checklist

**Successful Kafka installation test includes:**
- Topic creation without errors
- Messages successfully produced to the topic
- Messages successfully consumed from the topic
- Real-time message flow working correctly
- No connection errors or timeouts

If you encounter any issues, double-check that:
- Zookeeper is running on port 2181
- Kafka broker is running on port 9092
- No firewall blocking the connections
- You're using the correct bootstrap server address

Your Kafka development environment is now ready for building event-driven microservices!