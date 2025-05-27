import json


def output_formatter(content):
    try:
        content = json.loads(content)

        if content['content_type'] == "markdown":
            return content['content']

        if content['content_type'] == "image":
            return content['content']

        return content['content']

    except:
        # if the content isn't json, return it as is
        pass

    return content


__all__ = ["output_formatter",]
