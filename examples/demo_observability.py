"""
Phase 4 proof of concept: Observability with OpenTelemetry.

Run with telemetry enabled; spans are exported to OTLP (default http://127.0.0.1:4317).
To view traces in Arize Phoenix, run in a separate terminal:

    docker run -p 6006:6006 -p 4317:4317 arizeai/phoenix

Then open http://localhost:6006 for the visual trace UI.
"""

from dotenv import load_dotenv

from aion.patterns import DurableSDR
from aion.telemetry import setup_telemetry

load_dotenv()

# Configure OTEL so spans are sent to local OTLP (Phoenix listens on 4317)
setup_telemetry(service_name="AionDemoSDR")


def main() -> None:
    agent = DurableSDR(
        name="ObservabilityDemo",
        model="openai:gpt-4o-mini",
    )
    event_id = agent.start("Find the CTO of Acme Corp and draft an outreach email.")
    print(f"✅ Dispatched! Event ID: {event_id}")
    print("👉 Run `aion worker` in another terminal to process this task.")
    print("   To view traces: docker run -p 6006:6006 -p 4317:4317 arizeai/phoenix then open http://localhost:6006")


if __name__ == "__main__":
    main()
