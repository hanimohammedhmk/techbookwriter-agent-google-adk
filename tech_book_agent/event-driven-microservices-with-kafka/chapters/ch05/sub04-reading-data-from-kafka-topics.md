# Reading Data from Kafka Topics

Now that we've configured our Kafka consumers, let's explore how to actually **read data from Kafka topics** using consumer applications. This process involves connecting to Kafka, subscribing to topics, and continuously polling for new messages.

## Consumer Polling Strategy

The fundamental pattern for reading from Kafka involves a **continuous polling loop**. Unlike traditional messaging systems where messages are pushed to consumers, Kafka uses a **pull-based model** where consumers actively request messages from the broker.

This design has several advantages:
- **Backpressure control**: Consumers can control the rate at which they process messages
- **Efficient batching**: Consumers can fetch multiple messages in a single request
- **Flexible processing**: Consumers can pause/resume consumption as needed

## Basic Consumer Implementation

Here's a Java example showing the core pattern for reading messages from a Kafka topic:

```java
import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.common.serialization.StringDeserializer;
import java.time.Duration;
import java.util.Collections;
import java.util.Properties;

public class BasicConsumer {
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(ConsumerConfig.GROUP_ID_CONFIG, "test-consumer-group");
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        
        KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
        consumer.subscribe(Collections.singletonList("user-events"));
        
        try {
            while (true) {
                ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
                
                for (ConsumerRecord<String, String> record : records) {
                    System.out.printf("Received message: key=%s, value=%s, partition=%d, offset=%d%n",
                            record.key(), record.value(), record.partition(), record.offset());
                    
                    // Process the message here
                    processMessage(record);
                }
                
                // Commit offsets after processing
                consumer.commitSync();
            }
        } finally {
            consumer.close();
        }
    }
    
    private static void processMessage(ConsumerRecord<String, String> record) {
        // Business logic for processing the message
        System.out.println("Processing: " + record.value());
    }
}
```

## Key Consumer Operations

### 1. **Topic Subscription**
```java
// Subscribe to a single topic
consumer.subscribe(Collections.singletonList("my-topic"));

// Subscribe to multiple topics
consumer.subscribe(Arrays.asList("topic1", "topic2", "topic3"));

// Subscribe using pattern matching
consumer.subscribe(Pattern.compile("user-.*"));
```

### 2. **Message Polling**
The `poll()` method is the heart of Kafka consumption:

```java
// Poll with timeout
ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));

// Check if we received any records
if (!records.isEmpty()) {
    for (ConsumerRecord<String, String> record : records) {
        // Process each record
    }
}
```

### 3. **Offset Management**
```java
// Automatic offset committing (default)
props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "true");
props.put(ConsumerConfig.AUTO_COMMIT_INTERVAL_MS_CONFIG, "5000");

// Manual offset committing
consumer.commitSync();  // Synchronous commit
consumer.commitAsync(); // Asynchronous commit
```

## Handling Different Message Scenarios

### Processing Large Message Volumes
```java
while (true) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    
    if (!records.isEmpty()) {
        // Process in batches for efficiency
        processBatch(records);
        
        // Commit after successful batch processing
        consumer.commitSync();
    }
}
```

### Graceful Shutdown
```java
// Add shutdown hook for proper cleanup
Runtime.getRuntime().addShutdownHook(new Thread(() -> {
    System.out.println("Shutting down consumer...");
    consumer.wakeup();
}));

// Modified polling loop with shutdown support
try {
    while (!shutdownRequested) {
        ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
        // Process records...
    }
} catch (WakeupException e) {
    // Ignore for shutdown
} finally {
    consumer.close();
}
```

## Consumer Group Coordination

When multiple consumers belong to the same **consumer group**, Kafka automatically distributes partitions among them:

```java
// Each consumer in the same group gets a subset of partitions
props.put(ConsumerConfig.GROUP_ID_CONFIG, "order-processing-group");

// Rebalance listener for partition assignment changes
consumer.subscribe(Arrays.asList("orders"), new ConsumerRebalanceListener() {
    @Override
    public void onPartitionsRevoked(Collection<TopicPartition> partitions) {
        // Commit offsets before partitions are reassigned
        consumer.commitSync();
    }
    
    @Override
    public void onPartitionsAssigned(Collection<TopicPartition> partitions) {
        // Seek to committed offsets for newly assigned partitions
        for (TopicPartition partition : partitions) {
            consumer.seek(partition, getCommittedOffset(partition));
        }
    }
});
```

## Error Handling and Recovery

Robust consumers should handle various error scenarios:

```java
try {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    
    for (ConsumerRecord<String, String> record : records) {
        try {
            processMessage(record);
        } catch (ProcessingException e) {
            // Handle processing errors without stopping the consumer
            log.error("Failed to process message: " + record.value(), e);
            // Optionally send to dead-letter queue
        }
    }
} catch (SerializationException e) {
    // Handle deserialization errors
    log.error("Deserialization error", e);
} catch (WakeupException e) {
    // Expected during shutdown
} catch (Exception e) {
    // Handle other unexpected errors
    log.error("Unexpected error in consumer", e);
}
```

By understanding these fundamental patterns, you can build reliable Kafka consumers that efficiently read and process messages from your event-driven system.