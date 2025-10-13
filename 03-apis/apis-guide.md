---
title: Working with APIs
---

## Using APIs with Python

APIs (Application Programming Interfaces) allow you to programmatically access data from various services.

## Additional links

- [Inspect Element](https://inspectelement.org/), a series of tutorials about Undocumented APIs
- [Using paginated APIs with Python (four ways!)](https://www.youtube.com/watch?v=4Fdyft-ky0w), a video from me about going through APIs that have multiple pages of results

## AI Prompts for APIs

You can get a description of the structure of your data like this:

```py
def describe_data(data):
    if isinstance(data, dict):
        return {key: describe_data(value) for key, value in data.items()}
    elif isinstance(data, list) and data:
        return [describe_data(data[0])]
    else:
        return type(data)

describe_data(data)
```

This prompt is a little more complicated, because usually ChatGPT tries to do something *too crazy*. Feel free to adjust the prompt until it works for you.

<pre class="prompt">
I have API output that is a python dictionary, saved as data. The data structure is described as below. Provide code to convert the data into a dataframe of **______**. This probably just means pd.json_normalize with the appropriate key. Don't use meta. If you need to ask clarifying questions about the data itself, provide code snippets I can run to help answer them. You don't need to use print since I'm in a Jupyter notebook. Use functions only if absolutely necessary.

<strong>(paste description of data)</strong>
</pre>