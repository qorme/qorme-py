# Core Architecture: The Self-Healing SDK

Qorme is engineered to move beyond simple observability. It provides a feedback loop between data collection and application logic, enabling **automatic runtime optimization**.

## 🧠 The Optimization Feedback Loop

Qorme's primary innovation is the `MLStore` and its integration with tracking `Domains`.

1. **Observe**: Tracking domains (like `django.queries`) capture high-fidelity performance data.
2. **Collect**: The `Ingest` domain batches this data and sends it to the Qorme server.
3. **Analyze**: The Qorme server trains ML models based on your application's actual behavior (e.g., "Field X is never used in View Y").
4. **Optimize**: The `MLDomain` in your SDK receives these models via a real-time **Server-Sent Events (SSE)** stream.
5. **Act**: When a query is triggered, the SDK uses the local `MLStore` to predict the optimal execution path and modifies the query (e.g., adding `defer()`) before it reaches the database.

## 🧱 Key Components

### 1. TrackingManager (The Orchestrator)
A thread-safe singleton that manages the lifecycle of all domains and their shared dependencies.

### 2. Domains (The Collectors & Actors)
- **Monitoring Domains**: Simple collectors that capture timing, SQL, and tracebacks.
- **Optimization Domains**: Inherit from `MLDomain`. They are active participants that use the `MLStore` to modify application behavior at runtime.

### 3. Ingest Pipeline (The Data Engine)
- **High-Performance Serialization**: Uses `msgspec` and bitsets to minimize capture overhead.
- **Asynchronous Batching**: All I/O occurs in a dedicated background worker to ensure zero impact on application request latency.

### 4. MLStore (The Brain)
- **Real-Time Sync**: Uses SSE to stay synchronized with the Qorme cloud.
- **Atomic Operations**: Employs an immutable replacement pattern for model updates, ensuring that readers (application threads) always see a consistent state.

## 🚀 Performance Design

Qorme is built with a "Performance-First" mandate:
- **C Extensions**: critical paths like bitset operations and LRU caching are implemented in C.
- **Minimal Instrumentation**: We use `wrapt` for transparent patching that avoids the overhead of traditional class-injection or extensive decoration.
- **Adaptive Precision**: Domains can be toggled or tuned at runtime based on environment configuration.
