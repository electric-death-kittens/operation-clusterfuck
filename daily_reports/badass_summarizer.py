#
# load useful libraries
#
import ollama

#
# define a function to summarize a given text using an Ollama model
#
def summarize_given_text_using_ollama(
    text_to_summarize,
    model_to_use = 'llama3.2:3b',
    number_of_bullet_points_min = 3,
    number_of_bullet_points_max = 3,
    number_of_sentences_per_bullet_point_min = 1,
    number_of_sentences_per_bullet_point_max = 2,
):

    #
    # Ensure the number ranges are valid
    #
    assert number_of_bullet_points_min <= number_of_bullet_points_max
    assert number_of_sentences_per_bullet_point_min <= number_of_sentences_per_bullet_point_max

    #
    # Define the prompt
    #
    prompt = f"Please summarize the following text and report results in {number_of_bullet_points_min} to {number_of_bullet_points_max} bullet points of {number_of_sentences_per_bullet_point_min} to {number_of_sentences_per_bullet_point_max} sentences each. Return only the three bullet points with no header, footer, or additional content in the response. Report the response in Markdown format:"

    #
    # Ensure that the intended model is installed
    #
    installed_models = [dict(x)['model'] for x in ollama.list()['models']]
    assert model_to_use in installed_models

    #
    # Communicate with the model
    #
    response: ollama.ChatResponse = ollama.chat(
        model = model_to_use,
        messages = [
          {
            'role': 'user',
            'content': prompt + '  ' + text_to_summarize,
          },
        ]
    )

    #
    # return the results
    #
    summary = response.message.content
    return summary
