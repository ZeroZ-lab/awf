from prometheus_client import Counter, Histogram
import time

# 定义指标
WORKFLOW_EXECUTION_TIME = Histogram(
    'workflow_execution_seconds',
    'Time spent executing workflow',
    ['workflow_id']
)

WORKFLOW_EXECUTION_COUNT = Counter(
    'workflow_executions_total',
    'Number of workflow executions',
    ['workflow_id', 'status']
)

class WorkflowMonitoring:
    @staticmethod
    def record_execution(workflow_id: str, start_time: float, status: str):
        duration = time.time() - start_time
        WORKFLOW_EXECUTION_TIME.labels(workflow_id=workflow_id).observe(duration)
        WORKFLOW_EXECUTION_COUNT.labels(
            workflow_id=workflow_id,
            status=status
        ).inc() 