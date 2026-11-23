"""space_app.py: the ZeroGPU Space that runs make_vectors.py (issue #38). Uploaded as app.py beside make_vectors.py and
replies.jsonl, with requirements.txt (transformers, accelerate) and a README.md front matter (README.md here says how).
The button builds the three vectors, then gauges every reply on every layer. Each GPU call stays under 120 seconds.
"""

import json
import pathlib

import gradio as gr
import spaces

import make_vectors as mv

mv.load_model()  # at module scope on purpose: ZeroGPU claims the card for this model here
HERE = pathlib.Path(__file__).parent


@spaces.GPU(duration=120)
def vectors_for(trait):
    return mv.make_vectors((trait,))["traits"][trait]


@spaces.GPU(duration=120)
def gauge_chunk(flattery, rows):
    return mv.gauge_replies({"layers": len(flattery), "traits": {"flattery": flattery}}, rows)


def run():
    traits = {t: vectors_for(t) for t in mv.TRAITS}
    rows = mv.read_jsonl(HERE / "replies.jsonl")
    out = []
    for i in range(0, len(rows), 8):
        out += gauge_chunk(traits["flattery"], rows[i:i + 8])
    # The gap between the two persona means, per trait and layer: a near-zero gap marks a layer with no signal.
    gaps = {t: [round(v["gap"], 2) for v in traits[t]] for t in traits}
    return json.dumps({"model": mv.MODEL_ID, "layers": len(traits["flattery"]), "gauge": out, "gaps": gaps})


with gr.Blocks() as demo:
    btn = gr.Button("Run the trial")
    box = gr.Textbox(label="result", lines=10)
    btn.click(run, None, box, api_name="run")

demo.queue().launch()
