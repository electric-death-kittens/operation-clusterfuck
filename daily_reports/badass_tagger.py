import ollama

dict_refined_replacement = {
    'artificial intelligence' : 'ai',
}

def get_tags_as_json(text_to_tag, model_to_use = 'llama3.2:3b'):

    installed_models = [dict(x)['model'] for x in ollama.list()['models']]
    assert model_to_use in installed_models
    
    prompt_part_1 = """You are an advanced text analysis and semantic tagging system. Your task is to analyze the provided text and extract a list of rationalized, meaningful tags that accurately represent the core topics, themes, or entities in the content.

For each tag, you must also provide a brief, 1-2 sentence rationale explaining exactly why it applies based on the text.

Constraints:
1. Tags must be concise (1-3 words) and highly relevant.
2. The rationale must be grounded directly in the text (no hallucinations).
3. Do not include redundant tags or duplicates.
4. Output the final result in the exact JSON format specified below.
5. Do NOT include any conversational filler, introductions, explanations, or conclusions.
6. Do NOT use code block fences (like ```json or ```).
7. Ensure all keys and string values are enclosed in double quotes. 
8. Ensure arrays and objects are perfectly closed.
9. Exclude dates and years
10. Report all nouns as singular

Spaces between words are okay.

# Text to analyze:

"""

    prompt_part_2 = """
    
    # Desired Output Format (Strict JSON):
{
  "tags": [
    {
      "tag": "string",
      "rationale": "string"
    }
  ]
}
"""    

    prompt = prompt_part_1 + text_to_tag + prompt_part_2

    response: ollama.ChatResponse = ollama.chat(
        model = model_to_use,
        messages = [
          {
            'role': 'user',
            'content': prompt,
          },
        ]
    )
    return response.message.content

def get_tags_as_json_once(text_to_tag, model_to_use = 'llama3.2:3b'):
    worked = False
    dict_tags = None
    while not worked:
        try:
            json_tags = get_tags_as_json(text_to_tag, model_to_use = model_to_use)
            dict_tags = json.loads(json_tags)
            worked = True
        except:
            worked = False
    return dict_tags

def multi_tag(text_to_tag, model_to_use = 'llama3.2:3b', n = 5, space_character = ' '):
    list_tags = []
    for i in range(0, n):
        dict_tags = get_tags_as_json_once(text_to_tag, model_to_use = model_to_use)
        list_tags.extend([x['tag'].strip().lower().replace('_', space_character).replace(' ', space_character) for x in dict_tags['tags']])

    list_tags = [dict_refined_replacement[x].strip() if x in dict_refined_replacement else x.strip() for x in list_tags]
    return sorted(list(set(list_tags)))
