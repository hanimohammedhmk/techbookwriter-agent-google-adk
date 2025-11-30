# Configuring Kafka Consumers

Configuring Kafka consumers properly is essential for building reliable, scalable event-driven microservices. Consumer configuration determines how your application connects to Kafka, processes messages, and handles failures.

## Essential Consumer Properties

The Kafka consumer API requires several fundamental properties to be configured:

- **`bootstrap.servers`**: The list of Kafka brokers to connect to
- **`key.deserializer`**: The class used to deserialize message keys
- **`value.deserializer`**: The class used to deserialize message values
- **`group.id`**: The consumer group identifier for coordinating consumers

## Basic Consumer Configuration

Here's a minimal consumer configuration example:

```java
Properties props = new Properties();
props.put("bootstrap.servers", "localhost:9092");
props.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
props.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
props.put("group.id", "order-processing-group");

KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
```

## Understanding Consumer Groups

Consumer groups are one of Kafka's most powerful features:

- **Partition Distribution**: Partitions are distributed among consumers in the same group
- **Load Balancing**: Kafka automatically balances partitions across available consumers
- **Fault Tolerance**: When a consumer fails, its partitions are reassigned to other consumers

Each consumer group maintains its own offset tracking, allowing multiple applications to read the same topic independently.

## Common Configuration Options

### Performance and Reliability

- **`fetch.min.bytes`**: Minimum amount of data to fetch per request (default: 1)
- **`fetch.max.wait.ms`**: Maximum time to wait for data to become available (default: 500)
- **`max.poll.records`**: Maximum number of records returned in a single poll (default: 500)
- **`session.timeout.ms`**: Timeout for detecting consumer failures (default: 10000)

### Offset Management

- **`auto.offset.reset`**: What to do when no initial offset exists (earliest, latest, none)
- **`enable.auto.commit`**: Whether to automatically commit offsets (default: true)
- **`auto.commit.interval.ms`**: Frequency of auto-committing offsets (default: 5000)

### Advanced Settings

- **`max.partition.fetch.bytes`**: Maximum data returned per partition (default: 1MB)
- **`heartbeat.interval.ms`**: Frequency of heartbeats to coordinator (default: 3000)
- **`request.timeout.ms`**: Maximum time to wait for a response (default: 30000)

## Complete Consumer Configuration Example

```java
Properties props = new Properties();
props.put("bootstrap.servers", "kafka1:9092,kafka2:9092,kafka3:9092");
props.put("group.id", "payment-processing-service");
props.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
props.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");

// Performance configuration
props.put("fetch.min.bytes", 1024);
props.put("fetch.max.wait.ms", 100);
props.put("max.poll.records", 1000);

// Reliability configuration
props.put("session.timeout.ms", 30000);
props.put("heartbeat.interval.ms", 10000);
props.put("max.partition.fetch.bytes", 1048576);

// Offset management
props.put("auto.offset.reset", "earliest");
props.put("enable.auto.commit", false);

KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
```

## Configuration Best Practices

1. **Set appropriate timeouts**: Balance between responsiveness and reliability
2. **Disable auto-commit for critical applications**: Use manual offset commits
3. **Configure appropriate fetch sizes**: Balance latency and throughput
4. **Use descriptive group IDs**: Make debugging and monitoring easier
5. **Monitor consumer lag**: Ensure your consumers can keep up with producers

Proper consumer configuration is crucial for building resilient microservices that can handle varying workloads and gracefully recover from failures.