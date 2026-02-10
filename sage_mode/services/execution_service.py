class ExecutionService:
    def create_session_chain(self, session_id: int, feature_name: str):
        return {"session_id": session_id, "feature_name": feature_name}

    def execute_session(self, session_id: int, feature_name: str):
        return f"chain_{session_id}"
