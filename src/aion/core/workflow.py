from hatchet_sdk import Hatchet, Context
from .memory import MetaMemory
from pydantic_ai import Agent

hatchet = Hatchet(debug=True)
memory = MetaMemory()


@hatchet.workflow(on_events=["aion:agent_task"])
class AionRuntimeWorkflow:

    @hatchet.step(retries=3)  # Hatchet handles exponential backoff automatically
    async def run_agent_step(self, context: Context):
        task_payload = context.workflow_input()
        user_task = task_payload.get("task", "")
        system_prompt = task_payload.get("system_prompt", "You are a helpful AI.")
        model_name = task_payload.get("model", "openai:gpt-4o-mini")

        # 1. Pre-Hook: Meta-Memory retrieval
        past_mistakes = memory.find_similar_mistakes(user_task)
        if past_mistakes:
            system_prompt += "\n\nWARNING - AVOID THESE PAST MISTAKES:\n"
            system_prompt += "\n".join(past_mistakes)
            print(f"🧠 [Memory] Injected {len(past_mistakes)} past lessons into prompt.")

        # 2. Setup Agent
        agent = Agent(model_name, system_prompt=system_prompt)

        # 3. Execution & Post-Hook (Catching)
        try:
            print(f"🚀 [Aion Worker] Executing task: {user_task}")
            # Note: In a full implementation, tools are serialized and passed here
            result = await agent.run(user_task)
            return {"result": result.data}

        except Exception as e:
            error_msg = str(e)
            print(f"❌ [Aion Worker] Task failed: {error_msg}")

            # Save to memory to learn from it
            memory.record_mistake(
                task=user_task,
                error=error_msg,
                correction=f"Do not repeat the action that caused: {error_msg}",
            )

            # Re-raise so Hatchet marks the step as failed and retries durably!
            raise e
