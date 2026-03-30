from app.core.classifier import classify_intent
from app.core.context import assemble_context
from app.core.planner import create_plan
from app.core.executor import execute_step
from app.core.evaluator import evaluate
from app.state.task_state import TaskState


class OrchestrationEngine:
    def __init__(self, model_router, memory_manager, settings):
        self.model_router = model_router
        self.memory_manager = memory_manager
        self.settings = settings

    def handle(self, user_input, session_id):
        task_type = classify_intent(user_input)
        context = assemble_context(user_input, self.memory_manager, session_id)

        plan = create_plan(task_type.value, user_input)
        state = TaskState.from_plan(user_input, task_type.value, plan)

        for step in state.steps:
            result = execute_step(step, state, context, self.model_router)
            status = evaluate(result)

            if status == "retry" and step.retries < self.settings.max_retries:
                step.retries += 1
                result = execute_step(step, state, context, self.model_router)

            state.record(step, result)

        final = "\n\n".join(str(x) for x in state.outputs)
        self.memory_manager.store(session_id, user_input)
        self.memory_manager.store(session_id, final)

        return final