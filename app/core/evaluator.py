def evaluate(result):
    if not result or len(str(result)) < 10:
        return "retry"
    return "pass"