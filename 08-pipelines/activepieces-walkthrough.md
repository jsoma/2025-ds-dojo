---
title: "Activepieces walkthrough"
links:
  - name: "ActivePieces"
    url: "https://www.activepieces.com"
  - name: "Perplexity AI"
    url: "http://perplexity.ai/"
  - name: "DOJO keys"
    url: "https://jonathansoma.com/dojo-key.txt"
---

Log into [ActivePieces](https://activepieces.com) and create a new flow.

![](images/01.png)

Select the trigger of **Every Week**, then update it to be every Monday at 8am.

![](images/02.png)

![](images/03.png)

Add a new step by clicking the `+` button.

![](images/04.png)

Search for an add the **Perplexity AI** option. Update it with a new connection using my [Perplexity API key](https://jonathansoma.com/dojo-key.txt).

![](images/05.png)

![](images/06.png)

![](images/07.png)

Describe what you want Perplexity to research for you. In my case, I'm looking at AI and journalism as a weekly newsletter update. Be as specific as you want - individual sources or just "search the internet!"

![](images/08.png)

Click **Test** to see the output. *You always need to do this when you finish a step.*

![](images/09.png)

Add a new step for **Ask AI**. We will use this to convert Perplexity's research into an easy-to-read format.

![](images/10.png)

I've decided to use OpenAI's GPT-5 Mini, because all it's doing is rewriting a report, nothing fancy. To give it the content to include, I need to use the **Data selector** and click Perplexity's result.

![](images/11.png)

![](images/12.png)

Click **Test** to make sure it works.

![](images/13.png)

AI writes in Markdown, like we do in Notebooks. But we want this in HTML so we can send it in an email. Add the **Markdown to HTML** piece next.

![](images/14.png)

Insert the result of the Ask AI step, and test it.

![](images/15.png)

Now we want to send the email (or pretend to). Search for 'send email' and choose your provider - I use GMail.

![](images/16.png)

I then create a new connection to Google, and allow ActivePieces to send email from my account.

![](images/17.png)

Fill in the final few results.

![](images/18.png)
![](images/19.png)

Click **Publish** up top and you'll be ready to go!