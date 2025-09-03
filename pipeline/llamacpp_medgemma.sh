# HF_HUB_CACHE=/sc/arion/projects/hpims-hpi/user/janssm02/vllm/hub LLAMA_CACHE=/sc/arion/projects/hpims-hpi/user/janssm02/llama \
# ./llama-server -m llama-server -m /models/gemma-3-27b-it-q4_0.gguf \
# -fa --temp 1.0 --top-k 64 --min-p 0.0 --top-p 0.95 -sm row --no-mmap -ngl 99 \
# -c 5000 --cache-type-k q8_0 --cache-type-v q8_0 --device CUDA0 --tensor-split \
#  1,0,0,0 --slots --metrics --numa distribute -t 40 --no-warmup --port 8800 --host 0.0.0.0


ml load cuda/12
HF_HUB_CACHE=/sc/arion/projects/hpims-hpi/user/janssm02/vllm/hub LLAMA_CACHE=/sc/arion/projects/hpims-hpi/user/janssm02/llama \
../llama.cpp/build/bin/llama-cli -hf unsloth/medgemma-27b-text-it-GGUF:Q8_0 \
-c 8192 -ngl 100 --temp 1.0 --device CUDA0 --flash-attn --cache-type-v q8_0 --cache-type-k q8_0 
# --port 5912 --host 0.0.0.0 