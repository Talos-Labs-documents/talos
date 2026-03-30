def execute_step(step, state, context, model_router):
    if step.action_type == "generate":
        return model_router.generate(context, state.user_goal, step.description)

    if step.action_type == "analyze":
        return f"Analyzing: {state.user_goal}"

    if step.action_type == "plan":
        return "Creating structured outline..."

    return "Unknown step"