# Writing Data to Kafka Topics

Having configured your Kafka producer, the next logical step is to send data to your Kafka topics. This involves creating producer instances, constructing messages (records), and sending them to the appropriate topics. We'll illustrate this process using Java, a common language for Kafka development, but the core concepts apply across different programming languages and Kafka client libraries.

## Creating a Kafka Producer Instance

Before you can send messages, you need to instantiate a `KafkaProducer` object. This is typically done by providing the configuration properties we discussed in the previous section.

```java
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.StringSerializer;

import java.util.Properties;

public class SimpleProducer {

    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092"); // Replace with your broker list
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        // Add other configurations as needed (acks, linger.ms, etc.)
        props.put(ProducerConfig.ACKS_CONFIG, "all"); 
        props.put(ProducerConfig.RETRIES_CONFIG, 0); // Example: no retries for simplicity here
        props.put(ProducerConfig.LINGER_MS_CONFIG, 10); // Example: wait 10ms for more messages

        KafkaProducer<String, String> producer = new KafkaProducer<>(props);

        // ... sending messages ...

        producer.close(); // Important to close the producer to flush remaining messages
    }
}
```

In this example:

1.  We create a `Properties` object to hold our configuration.
2.  We set the `bootstrap.servers` and the `key.serializer` and `value.serializer` to `StringSerializer`.
3.  We also include `acks`, `retries`, and `linger.ms` for demonstration.
4.  We instantiate `KafkaProducer` with our properties. The generic types `<String, String>` indicate that both our message keys and values will be strings.
5.  Crucially, we call `producer.close()` at the end. This ensures that any buffered records are flushed and sent before the application exits.

## Sending Messages (Records)

Kafka messages are formally known as **records**. A `ProducerRecord` contains the topic name, and optionally, a partition number, a key, and the value.

There are a few ways to send records:

### 1. Send Asynchronously with Callback

This is the most common and recommended approach. You send a record and provide a callback function that will be executed when the send operation completes (either successfully or with an error).

```java
// Inside the main method of SimpleProducer, after creating the producer:

String topic = "my-topic"; // The topic to send messages to
String key = "user123";
String value = "{\"event\": \"login\", \"timestamp\": " + System.currentTimeMillis() + "}";

ProducerRecord<String, String> record = new ProducerRecord<>(topic, key, value);

producer.send(record, (metadata, exception) -> {
    if (exception == null) {
        // The record was successfully sent
        System.out.println("Successfully sent record to partition " + metadata.partition() +
                           " offset " + metadata.offset());
    } else {
        // An error occurred during sending
        System.err.println("Error sending record: " + exception.getMessage());
        exception.printStackTrace();
    }
});

// Note: producer.send() is asynchronous. To ensure all messages are sent before closing,
// you might want to use producer.flush() or keep the application running for a while.
// For simplicity in this example, we'll add a small sleep.
try {
    Thread.sleep(1000); // Give the producer some time to send
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
}
```

The callback provides `RecordMetadata` (containing topic, partition, offset) on success or an `Exception` on failure. This allows for fine-grained error handling and confirmation.

### 2. Send Synchronously

While less common in high-throughput scenarios due to blocking, you can also send records synchronously by calling `.get()` on the `Future` returned by `send()`.

```java
// Inside the main method of SimpleProducer, after creating the producer:

String topic = "my-topic";
String key = "product456";
String value = "{\"event\": \"update_price\", \"new_price\": 99.99}";

ProducerRecord<String, String> record = new ProducerRecord<>(topic, key, value);

try {
    RecordMetadata metadata = producer.send(record).get(); // .get() blocks until completion
    System.out.println("Sent record synchronously to partition " + metadata.partition() +
                       " offset " + metadata.offset());
} catch (Exception e) {
    System.err.println("Error sending record synchronously: " + e.getMessage());
    e.printStackTrace();
}
```

Be cautious with `get()`, as it can block your application thread, potentially becoming a bottleneck.

## Key Concepts Recap

*   **`ProducerRecord`**: The fundamental unit of data sent to Kafka, containing topic, key, and value.
*   **Asynchronous Sending**: The preferred method, using callbacks for non-blocking I/O and explicit handling of send outcomes.
*   **`producer.close()` / `producer.flush()`**: Essential methods to ensure all buffered messages are sent before the producer is shut down.

By mastering these techniques, you can reliably and efficiently write data into your Kafka topics, forming the backbone of your event-driven systems.
