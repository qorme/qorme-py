# ML Store: The Real-Time Optimization Engine

The **ML Store** is the core domain that powers Qorme's unique self-healing and optimization capabilities. It maintains a real-time, thread-safe cache of ML models used by other domains to modify application behavior.

## ⚙️ How it Works

- **SSE Stream**: The store connects to the Qorme server via a long-lived Server-Sent Events (SSE) stream to receive pushed updates.
- **Delta Processing**: When model updates are received, the store calculates the differences and applies them locally.
- **Atomic Swap Pattern**: To ensure high performance, the store uses an immutable replacement pattern. Readers (application threads fetching or using models) never experience locks or "dirty reads."
- **State Machine**: The store transitions through `connecting`, `connected`, `disconnected` (retry), and `dead` (terminal) states.

## 📝 Key Components

### `MLDomain`
Any domain that wishes to use ML for optimization (e.g., `defer_columns`) must inherit from `MLDomain`. It provides access to the `ml_store`.

### `MLInstance`
The data structure passed to an ML model to trigger a prediction. It includes the execution context, call stack, and historical patterns.

## 🛠️ Internal API Usage

```python
# Used by optimization domains
ml_store = manager.deps.ml_store
model = ml_store.get_model(category="defer-columns", name="product.Product")

if model:
    prediction = model.predict(MLInstance(...))
    # Act on prediction
```

## 🚀 Performance characteristics

- **Read Operations**: Constant-time dictionary lookups.
- **Update Operations**: Happens in a background worker; negligible impact on application threads.
- **Resilience**: Automatically handles SSE disconnection and session resumption using the `Last-Event-ID` header.
