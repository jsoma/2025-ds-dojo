---
title: Python Fundamentals homework
---

# Homework, Part 1: Data sources survey

Please take the [data sources survey here](https://docs.google.com/forms/d/e/1FAIpQLSeESNZJkuUXLg2W7Uf-FROW1VCZflwMGr3Dib8yPT4rvLWoSw/viewform?usp=sf_link). It will help me know what kind of data or products to focus on.

# Homework, Part 2: Basic Python

Please do some of [the Python tutorial](https://littlecolumns.com/learn/python) if you have not yet.

## Setup

Please create a new notebook named 'First Homework'.

Turn the first cell into a **Markdown cell** and add:

- The first line should be your full name
- The second line should be the date
- The third line should be "Homework: Basic Python"

They should be displayed as a **list**, with the little bullet points on the left. You can look at what we did in class, [check this reference sheet](https://www.markdownguide.org/basic-syntax/), or even ask ChatGPT. 

## Assignment

When run from top to bottom, this notebook should prompt the user for their year of birth, and display the information below. Use complete sentences (don't just print the answer), and it's okay for calculations to be approximate.

The **first cell** should use `input` to prompt the user for their year of birth. The **second cell** should do all of the rest.

1. How old the user is
1. In that time, how many times the user's heart has beaten.
1. In that time, how many times a blue whale's heart has beaten.
1. In that time, how many times a rabbit's heart has beaten. If the answer to rabbit heartbeats is more than a billion, say "XXX billion" instead of the very long raw number
1. There are several ways to calculate and format/display numbers in Python – string addition, f-strings, commas, etc etc etc. Redo one of the above questions above with another technique and briefly explain the pros and cons of each approach.
1. Whether they are the same age as you, older or younger
1. If older or younger, how many years difference
1. If they were born in an even or odd year
1. How many prime ministers have been in office since the user was born
1. If someone says they were born in the future, ask them for their year of birth again. Assume they'll do it right the second time.

## Hints and tips

> If you use ChatGPT to help with this assignment, think about the tradeoffs between the learning process vs the process of having something completed. We'll talk more about that tomorrow!

To review the basics of Python, visit [the Little Columns tutorial](https://littlecolumns.com/learn/python)

When you ask a user for information, Python always saves it as a string. But a year as a string isn't very useful! You'll need to convert it to an integer before you do anything to it (there might be some tips in the tutorial to help you with that).

How fast does a blue whale's heart beat? I don't know, I'm not a biologist - research it!

Before you write out a solution as code, write out what you want to do in words (a comment would be good for this). Breaking down the steps as "real" text can do a lot to help you organize your Python code.

`XXX billion` will involve either division, rounding, or converting to an integer.

You might need to know about...

- multiple comparisons in if
- adding one to variables (incrementing)
- else/elif
- modulo (for the even/odd one)

Anything not covered in the tutorial probably exists somewhere on the internet, or through ChatGPT!

# Homework, Part 3: Lists and dictionaries

Lists and dictionaries are always tough to figure out, and they only make sense once you've really spent some time with them. This homework and [the Little Columns tutorial](https://littlecolumns.com/learn/python) will really help you out! **Be sure to check the tips at the bottom!**

## Lists

1. Make a list of the following numbers: 22, 90, 0, -10, 3, 22, and 48
1. Display the number of elements in the list.
1. Display the 4th element of this list.
1. Display the sum of the 2nd and 4th element of the list.
1. Display the 2nd-largest value in the list.
1. Display the last element of the original unsorted list
1. Display the sum of all of the numbers divided by two.
1. Print whether the median or the mean of the numbers is higher

## Dictionaries

1. Sometimes dictionaries are used to describe multiple aspects of a single object. Like, say, a movie. Define a dictionary called movie that works with the following code.

```py
print("My favorite movie is", movie['title'], "which was released in", movie['year'], "and was directed by", movie['director'])
```

2. On the lines after that, add keys to the movie dictionary for budget and revenue (you'll use code like `movie['budget'] = 1000`), and print out the difference between the two.
3. If the movie cost more to make than it made in theaters, print "That was a bad investment". If the film's revenue was more than five times the amount it cost to make, print "That was a great investment." Otherwise print "That was an okay investment."
4. Sometimes dictionaries are used to describe the same aspects of many different objects. Make ONE dictionary that describes the population of the boroughs of NYC. Manhattan has 1.6 million residents, Brooklyn has 2.6m, Bronx has 1.4m, Queens has 2.3m and Staten Island has 470,000. (Tip: keeping it all in either millions or thousands is a good idea)
5. Display the population of Brooklyn.
6. Display the combined population of all five boroughs.
7. Display what percent of NYC's population lives in Manhattan.

## Tips

There are two ways to sort a list! One is just for display, and one sorts the list permanently. Keep an eye out for which one you're using.

Programmers are weird about counting. What number do they start with?

There might be a magic way to get the last item of a list in Python (or to start counting from the end).

When dealing with multiple numbers - population, for example - be sure to keep them all at the same level. If Brooklyn has 1.4 million people and Staten Island as 470,000, storing their population as 1.4 and 470000 isn't going to let you compare them accurately!

