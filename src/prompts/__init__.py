import importlib

def get_prompt_builder(prompt_name):
    prompt_lib = f"prompts.{prompt_name}"
    prompt_builder = getattr(importlib.import_module(prompt_lib), "build_prompts")
    return prompt_builder
                        
