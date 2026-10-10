---
lab3_genai_diff:
  instrumentation: "opentelemetry-instrumentation-genai-openai 1.2b0"
  spec_ref: "semantic-conventions-genai@e57c543b4889619eb2a05702471937db5119165d"
  attributes:
    - name: gen_ai.operation.name
      emitted: true
      in_spec: true
      stability: development
    - name: gen_ai.provider.name
      emitted: true
      in_spec: true
      stability: development
    - name: gen_ai.request.model
      emitted: true
      in_spec: true
      stability: development
    - name: gen_ai.response.finish_reasons
      emitted: true
      in_spec: true
      stability: development
    - name: gen_ai.response.id
      emitted: true
      in_spec: true
      stability: development
    - name: gen_ai.response.model
      emitted: true
      in_spec: true
      stability: development
    - name: gen_ai.usage.input_tokens
      emitted: true
      in_spec: true
      stability: development
    - name: gen_ai.usage.output_tokens
      emitted: true
      in_spec: true
      stability: development
---
<!-- ai-generated: 90% - ChatGPT helped compare the attributes emitted by the OpenTelemetry OpenAI instrumentation with the pinned GenAI semantic conventions; I generated the spans locally using Ollama. -->

# GenAI instrumentation diff

I instrumented one local LLM request using `opentelemetry-instrumentation-genai-openai` version `1.2b0`. The OpenAI-compatible request was sent to a local Ollama instance running `qwen3:1.7b`.

The resulting span contained eight `gen_ai.*` attributes. All eight emitted attributes are represented in the front matter above so that the declared emitted set matches the keys observed in `genai/spans.json`.

The instrumentation emitted attributes covering the operation and provider, the requested and returned model, response metadata, and token usage.

The comparison uses the course-pinned `semantic-conventions-genai` commit rather than the current moving version of the conventions.
