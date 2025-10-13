---
title: Data Analysis with Pandas
---

[Pandas](https://pandas.pydata.org/) is Python's equivalent to Excel. According to the official documentation:

> pandas is a fast, powerful, flexible and easy to use open source data analysis and manipulation tool,
built on top of the Python programming language.

## Session content

Working with structured data using pandas DataFrames.

## Setup

Pandas is installed using `pip`. You can run the code below in a Jupyterlab Desktop notebook cell:

```bash
%pip install pandas
```

To use pandas you need to be running a Jupyter Notebook.

## Additional links

- [Real-world data analysis with pandas and Python](https://www.youtube.com/playlist?list=PLewNEVDy7gq08UYzhKO3VwthH6KLx1sZD), a video series I produced within the past few years
- [First Python Notebook](https://palewi.re/docs/first-python-notebook/index.html), a Jupyter/pandas tutorial by data journalist Ben Welsh

## AI Prompts

When asking questions to your AI tool, it is usually useful to give an example of your data. You can automatically copy part of your dataframe to the clipboard with the code below

```py
df.sample(5).to_clipboard()
```

<pre class="prompt">
I have a dataframe that looks like the below. I want to _____.

<strong>(paste sample of dataframe)</strong>
</pre>

It can sometimes be useful to ask "is there a simpler approach?" after you ask a question.