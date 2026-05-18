#
# import useful libraries
#
import feedparser
import datetime
from time import mktime
import pandas as pd
import markdown_strings
from badass_summarizer import summarize_given_text_using_ollama

#
# define function to convert RSS results to a Pandas dataframe
#
def convert_feed_to_df(feed_url, hours_cutoff = 24):
    
    #
    # Parse the RSS feed
    #
    feed = feedparser.parse(feed_url)
    
    #
    # Compute the cutoff time
    #
    dt_cutoff = datetime.datetime.now() - datetime.timedelta(hours = hours_cutoff)

    #
    # Organize feed information into a Python dictionary
    #
    list_dict_entry = []
    for entry in feed.entries:

        try:
            time_struct = entry.published_parsed
            dt = datetime.datetime.fromtimestamp(mktime(time_struct))
        except:
            continue

        if dt < dt_cutoff:
            continue

        content_values_list = []
        for content in entry.content:
            content_values_list.append(str(content['value']))
        content_full = ' '.join(content_values_list).strip()

        dict_entry = {
            'title' : str(entry.title).strip(),
            'summary_from_feed' : str(entry.summary).strip(),
            'content' : content_full.strip(),
            'link' : str(entry.link).strip(),
            'publish_date' : str(dt),
        }
        list_dict_entry.append(dict_entry)

    df = pd.DataFrame(list_dict_entry)
    return df

#
# define a function to summarize the content with an LLM
#
def add_llm_content_summary(df, model_to_use = 'llama3.2:3b', content_row_name = 'content'):
    list_llm_summaries = []
    for i, row in df.iterrows():
        list_llm_summaries.append(
            summarize_given_text_using_ollama(
                row[content_row_name],
                model_to_use = model_to_use,
            )
        )
    new_df = df.copy()
    new_df['summary_from_llm'] = list_llm_summaries
    return new_df

#
# Define a function to generate a Markdown report
#
def generate_report(report_title, df):
    report = ''
    if len(df.index) == 0:
        return report
    else:
        report = '# ' + markdown_strings.esc_format(report_title, esc = True).replace('$', r'\$') + '\n'
        for i, row in df.iterrows():
            bullet_points = [markdown_strings.esc_format(x.strip(), esc = True).replace('$', r'\$') for x in row['summary_from_llm'].split('*') if not x.strip() == '']
            report += '## [' + markdown_strings.esc_format(row['title'], esc = True).replace('$', r'\$') + '](' + row['link'] + ')\n'
            report += '* ' + '\n* '.join(bullet_points) + '\n'
            report += '\n'
            report += 'Published: ' + row['publish_date'] + '\n'
            report += '\n'
    return report

#
# Generate the report given an RSS feed URL and a report title
#
def go(
    feed_url,
    report_title,
    hours_cutoff = 24,
    model_to_use = 'llama3.2:3b',
    content_row_name = 'content',
    summary_row_name = 'summary_from_llm'
):
    df = convert_feed_to_df(feed_url, hours_cutoff = hours_cutoff)
    df = add_llm_content_summary(df, model_to_use = model_to_use, content_row_name = content_row_name)
    #df = add_llm_tags(df, model_to_use = model_to_use, content_row_name = summary_row_name)
    report = generate_report(report_title, df)
    return report








#
# define a function to tag the summaries
#
def add_llm_tags(df, model_to_use = 'llama3.2:3b', content_row_name = 'summary_from_llm'):
    list_llm_tags = []
    for i, row in df.iterrows():
        list_llm_tags.append(
            multi_tag(
                row[content_row_name],
                model_to_use = model_to_use,
            )
        )
    new_df = df.copy()
    new_df['tags_from_llm'] = list_llm_tags
    return new_df







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
