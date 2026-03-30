def assemble_context(user_input, memory_manager, session_id):
    return {
        "recent": memory_manager.get_recent(session_id),
        "input": user_input,
    }