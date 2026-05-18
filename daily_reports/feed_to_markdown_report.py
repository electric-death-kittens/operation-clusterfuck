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
):
    df = convert_feed_to_df(feed_url, hours_cutoff = hours_cutoff)
    df = add_llm_content_summary(df, model_to_use = model_to_use, content_row_name = content_row_name)
    report = generate_report(report_title, df)
    return report
