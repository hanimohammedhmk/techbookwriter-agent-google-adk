# Chapter 2: Introduction to Apache Kafka

## 2.3 Producers and Consumers in Kafka

Kafka's power lies in its ability to act as a central hub for data streams, facilitating communication between different applications. This communication is primarily managed through two types of clients: **Producers** and **Consumers**. Understanding their roles and interaction patterns is crucial for designing effective event-driven systems with Kafka.

### Producers: Writing Data to Kafka

**Producers** are applications responsible for **publishing** (writing) data to Kafka topics. They send records, which are essentially key-value pairs containing the data, to specific topics within the Kafka cluster.

**Interaction Flow:**

1.  **Record Creation:** A producer creates a record, which includes the data payload, an optional key, and an optional timestamp. The **key** is significant as it determines which partition the record will be sent to. Records with the same key are guaranteed to be written to the same partition, ensuring order for related messages.
2.  **Partitioning:** Based on the record's key (or a round-robin strategy if no key is provided), the producer or its client library determines which partition of the target topic the record should be sent to.
3.  **Sending to Broker:** The producer sends the record to the broker that acts as the leader for the chosen partition.
4.  **Acknowledgement (acks):** The producer can configure the level of acknowledgement it requires from the broker.
    *   `acks=0`: The producer doesn't wait for any acknowledgement, offering the lowest latency but also the lowest durability guarantee.
    *   `acks=1`: The producer waits for the leader broker to acknowledge receipt. This is a common default, balancing latency and durability.
    *   `acks=all` (or `-1`): The producer waits for all in-sync replicas (ISRs) to acknowledge receipt. This provides the highest durability guarantee but incurs higher latency.
5.  **Record Delivery:** Once the acknowledgement is received (or not, depending on the `acks` setting), the producer knows the record has been successfully written or has taken its chances.

**Example Producer Configuration (Conceptual Java):**

```java
Properties props = new Properties();
props.put("bootstrap.servers", "kafka-broker1:9092,kafka-broker2:9092");
props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
// Configure acks, retries, etc. for desired durability and performance

KafkaProducer<String, String> producer = new KafkaProducer<>(props);

// Send a message
ProducerRecord<String, String> record = new ProducerRecord<>("my-topic", "user-id-123", "{\"event\": \"login\", \"timestamp\": 1678886400}");
producer.send(record);

producer.close();
```

### Consumers: Reading Data from Kafka

**Consumers** are applications that **subscribe** to one or more topics and process the records published to them. Consumers read data in the order it was stored within each partition.

**Interaction Flow:**

1.  **Subscription:** A consumer subscribes to one or more topics it's interested in.
2.  **Consumer Groups:** Consumers typically operate within **consumer groups**. A group is a collection of consumers that work together to consume a topic. Kafka ensures that each partition of a topic is consumed by *exactly one* consumer within a given consumer group. This enables parallel processing and load balancing. If you have multiple consumers in the same group subscribing to a topic with multiple partitions, Kafka will distribute the partitions among those consumers.
3.  **Fetching Records:** Consumers poll Kafka brokers for new records from the partitions assigned to them. They do this periodically.
4.  **Offset Management:** For each partition, a consumer (or its group) keeps track of its position, known as the **offset**. The offset is a unique sequential ID assigned to each record within a partition. When a consumer successfully processes a batch of records, it **commits** the offset of the last processed record. This commit tells Kafka how far that consumer group has progressed in a partition. If a consumer fails and restarts, it will resume reading from the last committed offset.
5.  **Processing Records:** The consumer processes the fetched records. The processing logic is entirely up to the consumer application.
6.  **Offset Committing:** After processing, the consumer commits the offset. This can be done automatically by Kafka at configured intervals or manually by the consumer application. **Commit semantics** (e.g., at-least-once, exactly-once, at-most-once) depend heavily on how offset commits are handled in conjunction with record processing.

**Example Consumer Configuration (Conceptual Java):**

```java
Properties props = new Properties();
props.put("bootstrap.servers", "kafka-broker1:9092,kafka-broker2:9092");
props.put("group.id", "my-consumer-group");
props.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
props.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
// Configure auto.commit.enable, session.timeout.ms, etc.

KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Arrays.asList("my-topic"));

try {
    while (true) {
        ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
        for (ConsumerRecord<String, String> record : records) {
            System.out.printf("offset = %d, key = %s, value = %s%n", record.offset(), record.key(), record.value());
            // Process the record here
        }
        // If auto-commit is disabled, manually commit offsets here after processing
        // consumer.commitSync();
    }
} finally {
    consumer.close();
}
```

In summary, producers write data to Kafka topics, and consumers read data from these topics. Kafka manages the data distribution, partitioning, and offset tracking, enabling robust and scalable decoupled communication between microservices.
