import requests
import telebot
from bs4 import BeautifulSoup
import time
import textwrap
from telebot import types

TOKEN = "6693848707:AAH7JEb3QP-bXSsZBmifXBq5NVk_zg_7spM"
chat_id = "418140655"
bot = telebot.TeleBot(TOKEN)

sent_urls = []  # List to store the URLs of the sent articles


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Get 5 articles')
    item2 = types.KeyboardButton('Get 10 articles')
    item3 = types.KeyboardButton('Get 15 articles')
    item4 = types.KeyboardButton('Get 20 articles')
    item5 = types.KeyboardButton('Get 25 articles')
    item6 = types.KeyboardButton('Get 30 articles')
    markup.add(item1, item2, item3, item4, item5, item6)
    bot.send_message(
        message.chat.id, "Welcome! Choose an option to get started:", reply_markup=markup)


@bot.message_handler(func=lambda message: True)
def get_articles(message):
    # Check if the message text matches the expected format
    if message.text.startswith('Get ') and message.text.endswith(' articles'):
        try:
            # Get the number from the button text
            num_articles = int(message.text.split()[1])
            url = "https://zehabesha.com/topics/get-the-latest-ethiopian-news-analysis-and-opinions-on-zehabesha-stay-informed-about-history-politics-business-health-sports-science-and-entertainment/page/{}/"
            # Start from page 1 and keep fetching articles until we have enough
            page_num = 1
            global sent_urls
            while num_articles > 0:
                try:
                    response = requests.get(url.format(page_num))
                    response.raise_for_status()
                except requests.exceptions.RequestException as err:
                    print(f"Error: {err}")
                    page_num += 1
                    continue

                soup = BeautifulSoup(response.content, "html.parser")

                articles = soup.find_all(
                    name="h2", class_="entry-title ast-blog-single-element")
                news_date = soup.find_all(name="span", class_="published")
                for i in range(min(len(articles), num_articles)):
                    article = articles[i]
                    heading = article.getText()
                    link = article.find(name="a").get("href")
                    # Skip the article if it has been sent before
                    if link in sent_urls:
                        continue
                    try:
                        response2 = requests.get(link)
                        response2.raise_for_status()
                    except requests.exceptions.RequestException as err:
                        print(f"Error: {err}")
                        continue
                    soup2 = BeautifulSoup(response2.content, "html.parser")
                    story_divs = soup2.find_all(
                        name="div", class_="entry-content clear")
                    story_paragraphs = [
                        p.getText() for story_div in story_divs for p in story_div.find_all(name="p")]
                    story = ' '.join(story_paragraphs)
                    date = news_date[i].getText()
                    other_parts_length = len(heading) + len(date) + len(link) + \
                        len("<b>\n\nDate: </b>\n\n \n\n") + len("\\read more")
                    story_max_length = 4096 - other_parts_length
                    message = f"<b>{heading}</b>\n\nDate: <b>{date}</b>\n\n{textwrap.shorten(
                        story, width=story_max_length, placeholder='...')}\n\n<b>read more: {link}</b>"
                    bot.send_message(chat_id, message, parse_mode='HTML')
                    # Add the URL to the list of sent URLs
                    sent_urls.append(link)
                    num_articles -= 1
                    if num_articles == 0:
                        return
                    # Move to the next page after processing all articles on the current page
                    page_num += 1

        except ValueError:
            # The second word in the message text is not a number
            bot.send_message(
                message.chat.id, "Please choose an option from the custom keyboard.")
    else:
        # The message text does not match the expected format
        bot.send_message(
            message.chat.id, "Please choose an option from the custom keyboard.")


bot.polling()
