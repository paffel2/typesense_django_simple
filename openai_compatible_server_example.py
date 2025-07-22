from flask import Flask, request, jsonify

from transformers import AutoModel



app = Flask(__name__)
print("Model initialized")
model = AutoModel.from_pretrained("jinaai/jina-embeddings-v3", trust_remote_code=True)


@app.route('/v1/embeddings', methods=['POST'])
def embeddings():
    data = request.get_json()
    prompts = data.get('input', [])
    if isinstance(prompts, list) and len(prompts) > 0:
        prompts = prompts[0]
    outputs = model.encode(prompts,task="text-matching")
    resp = jsonify( {
        "data": [
            {
            "embedding": outputs.tolist(),
            }
            ],
  "model": "my-model",
  "usage": {
    "prompt_tokens": 8,
    "total_tokens": 8
  }
})
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)