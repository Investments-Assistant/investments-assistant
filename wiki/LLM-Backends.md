# LLM Backends

The agent runs inference entirely in-process — no HTTP call to an external AI API.
Two backends are available, controlled by `LLM_BACKEND` in `.env`.

---

## Why local inference?

Running a cloud AI (OpenAI, Anthropic, Google) would:
1. Send your portfolio data, brokerage balances, and trade reasoning to a third-party server
2. Create a recurring API cost proportional to usage
3. Break the "offline-capable" goal — the assistant should work even if your ISP is down

A local 7B parameter model quantised to 4-bit runs at ~5–8 tokens/sec on the Pi 5, which
is fast enough for a conversational assistant. The trade-off is lower reasoning quality
compared to frontier models like Claude or GPT-4, but the structured tool-calling workflow
(ReAct loop) compensates: the model doesn't need to know facts from memory, it calls
tools that fetch real data.

---

## `llama_cpp` — recommended for Pi 5

**Library**: `llama-cpp-python` (Python bindings for `llama.cpp`)

**Why llama.cpp?**
- Written in pure C/C++ with zero external runtime dependencies
- Ships hand-optimised SIMD kernels for **ARM NEON** (the instruction set on Pi 5's
  Cortex-A76 cores), which gives 2–3× higher throughput than naive float32 operations
- The Docker build compiles llama-cpp-python with **OpenBLAS** (`CMAKE_ARGS="-DGGML_BLAS=ON
  -DGGML_BLAS_VENDOR=OpenBLAS"`) for an additional speedup on matrix multiplications
- Supports the **GGUF** file format (see below)
- Supports the **OpenAI-compatible Chat Completions API** with native tool calling

**What is GGUF?**
GGUF (GGML Unified Format) is a binary format for quantised LLM weights. The key
properties that make it ideal for the Pi:
- **Quantisation**: instead of storing each weight as a 16-bit float (~2 bytes), Q4_K_M
  stores it in ~4 bits. A 7B parameter model weighs ~14 GB in fp16 but only ~4.7 GB in Q4_K_M
- **K-quants** (the K in Q4_K_M): the weights are grouped into "blocks", and the scaling
  factor per block is itself quantised. This achieves better quality-per-byte than older
  formats like GPTQ
- **Memory-mapped I/O**: GGUF files can be mmap'd directly — the OS pages weights in from
  disk on demand rather than loading the full file into RAM upfront. On first use some
  pages fault in; after warm-up the model runs fully from RAM

**Tool calling**
`llama.cpp`'s `create_chat_completion` accepts an `tools` parameter (OpenAI format) and
sets `finish_reason = "tool_calls"` when the model wants to call a function. The
`LlamaCppClient` loops on this, dispatching each tool and feeding results back as
`{"role": "tool", ...}` messages, until the model stops calling tools and produces text.

**Singleton pattern**
Loading a 4.7 GB model takes ~30–60 seconds and uses most of the Pi's RAM. The client
is instantiated once (`_instance` module-level variable) and reused across all sessions.
Concurrent requests serialise on the GIL and the thread pool executor — inference is
single-threaded, so there's no speedup from parallel requests anyway.

---

## `transformers` — for GPU or desktop use

**Libraries**: HuggingFace `transformers` + `torch`

**Why it exists**
The `transformers` backend lets you run the assistant on a machine with a CUDA GPU
(e.g. a desktop with an RTX card) or Apple Silicon (MPS). A 7B model on a GPU with 8 GB
VRAM runs at 60–100 tokens/sec — a 10–15× speedup over the Pi.

**Why llama_cpp is preferred on the Pi**
- `transformers` loads models in `float32` on CPU (or `float16` on CUDA), using 2–4×
  more RAM than GGUF Q4_K_M for the same model
- PyTorch's CPU kernels are not as optimised for ARM as llama.cpp's hand-written NEON code
- The HuggingFace format downloads multi-GB safetensors shards from the Hub on first run
  (requires internet); GGUF files are self-contained

**Tool calling**
HuggingFace tokenizers support tool calling via `apply_chat_template(tools=...)` for
models trained with function-calling (Qwen 2.5, Llama 3.1, Mistral v3, Gemma 3, Phi-4).
The model embeds tool calls as XML-like markup in its text output. The
`TransformersClient` parses two common patterns:
- `<tool_call>{"name": "...", "arguments": {...}}</tool_call>` — used by Qwen 2.5 and
  many Hermes-tuned models
- `<|python_tag|>...<|eom_id|>` — used by Llama 3.1

This is less reliable than llama.cpp's native tool-use support. If your model uses a
different markup pattern, add a new entry to `_TOOL_CALL_PATTERNS` in
`src/agent/clients/transformers_client.py`.

---

## Model selection

### Tested on Pi 5 (8 GB RAM)

| Key | Model | Format | RAM | Notes |
|---|---|---|---|---|
| `qwen2.5-7b` | Qwen 2.5 7B Instruct | Q4_K_M GGUF | ~4.7 GB | **Recommended** — best quality/speed balance, native tool calling |
| `qwen2.5-3b` | Qwen 2.5 3B Instruct | Q8_0 GGUF | ~3.3 GB | Lighter and faster; noticeably lower reasoning quality |
| `llama3.2-3b` | Llama 3.2 3B Instruct | Q8_0 GGUF | ~3.4 GB | Good for testing; limited financial domain knowledge |
| `llama3.1-8b` | Llama 3.1 8B Instruct | Q4_K_M GGUF | ~4.9 GB | Strong tool use; needs all 8 GB, leaves little headroom |
| `mistral-7b` | Mistral 7B Instruct v0.3 | Q4_K_M GGUF | ~4.4 GB | Solid all-rounder; good function calling |
| `phi4-14b` | Microsoft Phi-4 | Q4_K_M GGUF | ~8.9 GB | Excellent reasoning; **requires GPU or 16+ GB RAM** |

### Why Qwen 2.5 7B is the default

1. **Native tool calling**: Alibaba trained Qwen 2.5 with multi-turn function calling and
   it reliably produces valid JSON tool calls. Some other 7B models hallucinate tool
   argument names or values.
2. **Financial domain**: Qwen was trained on a large multilingual corpus including
   financial text, which helps with ticker recognition, market terminology, and Portuguese
   financial news (the user is based in Portugal).
3. **Q4_K_M quality**: the K-quant at 4-bit strikes the best quality/RAM balance.
   Going to Q8_0 would use ~7 GB and leave almost no RAM for the OS and services.

---

## Adding a new backend

1. Create `src/agent/clients/<name>_client.py` implementing `BaseLLMClient`
2. Add a singleton getter `get_<name>_client()` in that module
3. Add a branch in `create_llm_client()` in `src/agent/clients/__init__.py`
4. Optionally expose tool definitions in the new backend's format

The `BaseLLMClient` interface is intentionally minimal — one abstract method:

```python
async def stream_response(
    self,
    messages: list[dict],
    system: str,
) -> AsyncGenerator[dict, None]:
    ...
```

Events yielded:
| Event type | Fields | Meaning |
|---|---|---|
| `text_delta` | `text: str` | A chunk of assistant text |
| `tool_call` | `name`, `input`, `id` | The model wants to call a tool |
| `tool_result` | `name`, `result`, `id` | The tool call result |
| `done` | — | Turn is complete |

---

## Downloading models

```bash
# List available presets
python scripts/download_model.py --list

# Download by key (saves to ./models/)
python scripts/download_model.py qwen2.5-7b --output-dir ./models

# Then set in .env:
LLM_MODEL_PATH=/app/models/qwen2.5-7b-instruct-q4_k_m.gguf
```

The script downloads directly from HuggingFace Hub using Python's standard
`urllib.request.urlretrieve` (no extra deps). A progress bar shows download status.
If a file already exists at the target path, the download is skipped.

The models directory is **bind-mounted read-only** into the container:
```yaml
volumes:
  - ./models:/app/models:ro
```
This means you download once on the host and the container sees the file immediately,
without rebuilding the Docker image.
