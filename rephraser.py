# import os
# from openai import OpenAI

# # Initialize your AI client (ensure your API key is in your environment variables)
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def rephrase_markdown(original_markdown: str) -> str:
#     """Sends Markdown text to an LLM to be rephrased while preserving formatting."""
    
#     system_prompt = """
#     You are an expert copywriter. Your task is to rephrase the provided article 
#     to make it unique, engaging, and plagiarism-free.
    
#     CRITICAL RULES:
#     1. The input is in Markdown format. You MUST return valid Markdown.
#     2. Preserve all Markdown formatting, including headers (##), bold text (**text**), and links ([text](url)).
#     3. Do not add conversational filler (e.g., "Here is your rewritten text:"). Output ONLY the rephrased Markdown.
#     """

#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o-mini", # Use a fast, cheap model for bulk tasks
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": original_markdown}
#             ],
#             temperature=0.7 # Slight creativity
#         )
#         return response.choices[0].message.content.strip()
#     except Exception as e:
#         print(f"Error during rephrasing: {e}")
#         return ""




from transformers import pipeline
import torch

print("Loading local Transformer model into memory. This may take a minute...")

# Initialize the pipeline globally
# We use device_map="auto" so it automatically uses your GPU if you have one, or falls back to CPU
rephrase_pipe = pipeline(
    "text-generation",
    model="Qwen/Qwen2.5-1.5B-Instruct", 
    device_map="auto", 
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
)
print("Model successfully loaded!")

def rephrase_markdown(original_markdown: str) -> str:
    """Sends Markdown text to a local Transformer LLM to be rephrased."""
    
    # We structure the prompt exactly like we would for an API
    messages = [
        {
            "role": "system", 
            "content": (
                "You are an expert copywriter. Rewrite the provided article to make it unique. "
                "CRITICAL: You MUST preserve all Markdown formatting exactly as it is, "
                "including headers (##), bold text (**text**), and links. "
                "Output ONLY the rephrased Markdown without any conversational filler."
            )
        },
        {"role": "user", "content": original_markdown}
    ]

    try:
        # Generate the text
        result = rephrase_pipe(
            messages,
            # max_new_tokens=1500,  # Ensure it has enough room to output a full article
            temperature=0.7,      # Slight creativity
            do_sample=True
        )
        
        # The pipeline returns the full conversation history; we only want the final response
        generated_reply = result[0]["generated_text"][-1]["content"]
        
        return generated_reply.strip()
        
    except Exception as e:
        print(f"Error during local Transformer rephrasing: {e}")
        return ""