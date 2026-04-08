# OTel Collector Configuration Examples

> observability スキル補足資料 — OpenTelemetry Collector の構成パターンとサンプル設定

## 1. デプロイメントパターン

### Agent + Gateway 構成（推奨）

```
Applications
  └── OTel SDK
        ↓ OTLP (gRPC)
OTel Collector (Agent mode, per-node DaemonSet/sidecar)
        ↓ OTLP (gRPC)
OTel Collector (Gateway mode, centralized Deployment)
  ├── → Tracing Backend
  ├── → Metrics Backend
  └── → Logging Backend
```

| 構成 | 用途 | スケーリング |
|:---|:---|:---|
| **Agent** | ノードローカル収集、初期処理 | DaemonSet or Sidecar |
| **Gateway** | 集約、ルーティング、サンプリング | HPA による水平スケール |

---

## 2. Agent 構成サンプル

```yaml
# otel-collector-agent.yaml
# Role: per-node data collection and initial processing
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  # Memory limiter to prevent OOM
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
    spike_limit_mib: 128

  # Batch for efficient export
  batch:
    timeout: 5s
    send_batch_size: 1024
    send_batch_max_size: 2048

  # Resource detection for cloud metadata
  resourcedetection:
    detectors: [env, system, docker, ec2, ecs, eks, azure, gcp]
    timeout: 5s

exporters:
  otlp:
    endpoint: otel-gateway:4317
    tls:
      insecure: false
      cert_file: /certs/client.crt
      key_file: /certs/client.key

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, resourcedetection, batch]
      exporters: [otlp]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, resourcedetection, batch]
      exporters: [otlp]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, resourcedetection, batch]
      exporters: [otlp]
```

---

## 3. Gateway 構成サンプル

```yaml
# otel-collector-gateway.yaml
# Role: centralized routing, sampling, and export
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 2048
    spike_limit_mib: 512

  batch:
    timeout: 10s
    send_batch_size: 4096

  # Tail-based sampling for error/slow traces
  tail_sampling:
    decision_wait: 30s
    num_traces: 100000
    expected_new_traces_per_sec: 1000
    policies:
      # Always keep error traces
      - name: error-policy
        type: status_code
        status_code:
          status_codes: [ERROR]
      # Always keep slow traces
      - name: latency-policy
        type: latency
        latency:
          threshold_ms: 1000
      # Sample normal traces at 10%
      - name: probabilistic-policy
        type: probabilistic
        probabilistic:
          sampling_percentage: 10

  # PII redaction
  attributes:
    actions:
      - key: user.email
        action: hash
      - key: user.ip_address
        action: delete
      - key: http.request.header.authorization
        action: delete

exporters:
  # Tracing backend
  otlp/traces:
    endpoint: jaeger-collector:4317
    tls:
      insecure: true

  # Metrics backend
  prometheusremotewrite:
    endpoint: http://prometheus:9090/api/v1/write

  # Logging backend
  elasticsearch:
    endpoints: [https://es-cluster:9200]
    logs_index: otel-logs

  # Long-term storage (data lake)
  awss3:
    s3uploader:
      region: ap-northeast-1
      s3_bucket: telemetry-archive
      s3_prefix: raw/

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, tail_sampling, attributes, batch]
      exporters: [otlp/traces, awss3]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheusremotewrite]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, attributes, batch]
      exporters: [elasticsearch]
```

---

## 4. Kubernetes マニフェスト

### Agent DaemonSet

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: otel-collector-agent
  namespace: observability
spec:
  selector:
    matchLabels:
      app: otel-collector-agent
  template:
    metadata:
      labels:
        app: otel-collector-agent
    spec:
      containers:
        - name: collector
          image: otel/opentelemetry-collector-contrib:0.96.0
          args: ["--config=/conf/otel-collector-agent.yaml"]
          ports:
            - containerPort: 4317  # OTLP gRPC
            - containerPort: 4318  # OTLP HTTP
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
          volumeMounts:
            - name: config
              mountPath: /conf
      volumes:
        - name: config
          configMap:
            name: otel-agent-config
```

### Gateway Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector-gateway
  namespace: observability
spec:
  replicas: 3
  selector:
    matchLabels:
      app: otel-collector-gateway
  template:
    metadata:
      labels:
        app: otel-collector-gateway
    spec:
      containers:
        - name: collector
          image: otel/opentelemetry-collector-contrib:0.96.0
          args: ["--config=/conf/otel-collector-gateway.yaml"]
          ports:
            - containerPort: 4317
          resources:
            requests:
              cpu: 1000m
              memory: 2Gi
            limits:
              cpu: 2000m
              memory: 4Gi
          volumeMounts:
            - name: config
              mountPath: /conf
      volumes:
        - name: config
          configMap:
            name: otel-gateway-config
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: otel-gateway-hpa
  namespace: observability
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: otel-collector-gateway
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

## 5. 移行パターン: 既存ツール → OTel

### 段階的移行（デュアルエクスポート）

```yaml
# Phase 1: dual export (existing + OTel backend)
exporters:
  # Existing backend (keep during migration)
  datadog:
    api:
      key: ${DD_API_KEY}

  # New OTel-native backend
  otlp/honeycomb:
    endpoint: api.honeycomb.io:443
    headers:
      x-honeycomb-team: ${HONEYCOMB_API_KEY}

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [datadog, otlp/honeycomb]  # Both during migration
```

### 移行フェーズ

| フェーズ | 期間 | アクション |
|:---|:---|:---|
| Phase 0 | 2 週間 | OTel SDK 導入、既存エクスポーター維持 |
| Phase 1 | 4 週間 | デュアルエクスポート開始、新バックエンド検証 |
| Phase 2 | 4 週間 | SLO アラートを新バックエンドに移行 |
| Phase 3 | 2 週間 | 旧バックエンド廃止、クリーンアップ |
