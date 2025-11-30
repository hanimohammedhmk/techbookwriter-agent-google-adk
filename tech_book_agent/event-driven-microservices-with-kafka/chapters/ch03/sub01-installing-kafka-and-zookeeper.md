# Installing Kafka and Zookeeper

Welcome to Chapter 3! In this chapter, we'll set up a local development environment for Kafka. This will allow you to experiment with Kafka's features without needing to deploy to a complex cloud infrastructure. We'll start by installing **Apache Kafka** and its essential dependency, **Apache ZooKeeper**.

## Prerequisites

Before we begin, ensure you have the following installed on your system:

*   **Java Development Kit (JDK)**: Kafka is built on Java, so you'll need a compatible JDK installed. Kafka 3.x and later versions require **JDK 11 or higher**. You can download it from Oracle's website or use an open-source distribution like OpenJDK. Verify your installation by running `java -version` in your terminal.
*   **Download Kafka**: Navigate to the official Apache Kafka downloads page ([https://kafka.apache.org/downloads](https://kafka.apache.org/downloads)). Choose a recent stable release (e.g., 3.6.1). Download the pre-built binaries for your operating system. Look for a file named something like `kafka_2.13-3.6.1.tgz`. The `2.13` indicates the Scala version Kafka was built with; for general use, this choice typically doesn't impact Kafka functionality.

## Step 1: Download and Extract Kafka

1.  **Download the Archive**: Once you've downloaded the Kafka binary archive (e.g., `kafka_2.13-3.6.1.tgz`), you'll need to extract it.
2.  **Extract**: Open your terminal or command prompt, navigate to the directory where you downloaded the file, and run the following command:

    ```bash
    tar -xzf kafka_2.13-3.6.1.tgz
    ```
    *Replace `kafka_2.13-3.6.1.tgz` with the actual filename you downloaded.*

3.  **Move to a Convenient Location**: It's good practice to move the extracted Kafka directory to a more permanent and accessible location. For example, you might move it to `/opt/kafka` on Linux/macOS or `C:\kafka` on Windows. Let's assume you move it to a directory named `kafka_2.13-3.6.1` within your home directory for this guide.

    ```bash
    # Example for Linux/macOS
    mv kafka_2.13-3.6.1 ~/kafka
    cd ~/kafka
    ```

## Step 2: Understanding Kafka's Architecture (ZooKeeper)

Kafka relies on **ZooKeeper** for managing cluster state, leader election, topic configuration, and more. While Kafka is introducing alternatives (like KRaft) for future versions, ZooKeeper is still the standard for most current deployments and essential for understanding Kafka's operational basics.

For development purposes, Kafka bundles a convenient **development ZooKeeper instance**. This means you don't need to install and configure ZooKeeper separately if you're just running Kafka locally.

## Step 3: Start the ZooKeeper Server

Kafka includes a script to start a single ZooKeeper node.

1.  **Navigate to Kafka Directory**: Ensure you are in the root directory of your Kafka installation (e.g., `~/kafka/kafka_2.13-3.6.1`).
2.  **Start ZooKeeper**: Run the following command:

    ```bash
    bin/zookeeper-server-start.sh config/zookeeper.properties
    ```

    You should see output indicating that ZooKeeper has started successfully. It will typically bind to port `2181`. Keep this terminal window open, as stopping ZooKeeper will also stop Kafka.

## Step 4: Start the Kafka Broker

Now that ZooKeeper is running, you can start the Kafka broker (the server that handles messages).

1.  **Open a New Terminal**: Since the first terminal is occupied by ZooKeeper, open a *new* terminal window.
2.  **Navigate to Kafka Directory**: Navigate to the same Kafka installation directory as before.
3.  **Start Kafka Broker**: Run the following command:

    ```bash
    bin/kafka-server-start.sh config/server.properties
    ```

    This command starts a Kafka broker using the default configuration. The broker will connect to the ZooKeeper instance we started earlier. You should see output indicating the broker has started, usually listening on port `9092`.

## Step 5: Verification (Optional but Recommended)

To confirm that Kafka is running, you can create a topic, produce a message, and consume it.

1.  **Create a Topic**: In the *same terminal* where you started the Kafka broker, run:

    ```bash
    bin/kafka-topics.sh --create --topic quickstart-topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
    ```

    You should see a success message.

2.  **Produce Messages**: Start a console producer in a *new terminal*:

    ```bash
    bin/kafka-console-producer.sh --topic quickstart-topic --bootstrap-server localhost:9092
    ```

    Type a few messages, pressing Enter after each one (e.g., `Hello Kafka!`, `This is message 1.`). Press `Ctrl+C` to exit the producer when done.

3.  **Consume Messages**: Start a console consumer in *another new terminal*:

    ```bash
    bin/kafka-console-consumer.sh --topic quickstart-topic --from-beginning --bootstrap-server localhost:9092
    ```

    You should see the messages you typed earlier appear in this terminal. Press `Ctrl+C` to exit the consumer.

## Stopping Kafka and ZooKeeper

To stop your Kafka environment:

1.  **Stop Kafka Broker**: In the terminal where the Kafka broker is running, press `Ctrl+C`.
2.  **Stop ZooKeeper**: In the terminal where ZooKeeper is running, press `Ctrl+C`.

Congratulations! You have successfully installed and run Kafka and ZooKeeper locally. You're now ready to explore Kafka's capabilities in the next sections.
