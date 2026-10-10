# ai-generated: 95% - ChatGPT prepared this local GenAI instrumentation capture script; I ran it against my local Ollama model.

import json

from openai import OpenAI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.instrumentation.genai.openai import OpenAIInstrumentor


captured = []


class JsonSpanExporter(SpanExporter):
    def export(self, spans):
        for span in spans:
            captured.append(
                {
                    "name": span.name,
                    "context": {
                        "trace_id": format(span.context.trace_id, "032x"),
                        "span_id": format(span.context.span_id, "016x"),
                    },
                    "kind": str(span.kind),
                    "attributes": dict(span.attributes or {}),
                    "status": {
                        "status_code": str(span.status.status_code),
                    },
                    "start_time": span.start_time,
                    "end_time": span.end_time,
                }
            )
        return SpanExportResult.SUCCESS


provider = TracerProvider()
processor = SimpleSpanProcessor(JsonSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

OpenAIInstrumentor().instrument()

client = OpenAI(
    base_url="http://127.0.0.1:11434/v1",
    api_key="ollama",
)

response = client.chat.completions.create(
    model="qwen3:1.7b",
    messages=[
        {
            "role": "user",
            "content": "Reply with exactly: OpenTelemetry test",
        }
    ],
)

print(response.choices[0].message.content)

provider.force_flush()

with open("genai/spans.json", "w", encoding="utf-8") as f:
    json.dump(captured, f, indent=2, ensure_ascii=False)