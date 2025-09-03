#!/bin/bash

# Load the necessary module
ml load cuda/12

# Set the environment variables
export HF_HUB_CACHE=/sc/arion/projects/hpims-hpi/user/janssm02/vllm/hub
export LLAMA_CACHE=/sc/arion/projects/hpims-hpi/user/janssm02/llama

# Parse port argument (default: 5912)
PORT=5912
while [[ $# -gt 0 ]]; do
  case $1 in
    --port)
      PORT="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

# Function to handle SIGTERM
forward_sigterm() {
  echo "Caught SIGTERM signal! Forwarding to child process..."
  kill -TERM "$child" 2>/dev/null
}

# Trap SIGTERM and call forward_sigterm
trap forward_sigterm SIGTERM

# Start your process in the background
../llama.cpp/build/bin/llama-server \
  -hf unsloth/Llama-3.3-70B-Instruct-GGUF:Q4_K_M \
  -c 16384 -ngl 100 --no-mmap --device CUDA0 --flash-attn --port "$PORT" --host 0.0.0.0 &

# Save the PID of the background process
child=$!

# Wait for the process to finish
wait "$child"
