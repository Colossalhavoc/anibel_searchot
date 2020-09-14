from os import environ
from hashlib import md5
import json
import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.types import InlineQuery, InputTextMessageContent, InlineQueryResultArticle, InlineKeyboardMarkup, InlineKeyboardButton
import requests as rq

logging.basicConfig(level=logging.INFO)

bot = Bot(environ.get('BOT_TOKEN'))
dp = Dispatcher(bot)


@dp.inline_handler()
async def inline(inline_query: InlineQuery):
    if len(inline_query.query) < 3:
        return
    text = inline_query.query
    response = rq.post('https://anibel-be.herokuapp.com/graphql',
                       json={'query': '''{search(query:"''' + text + '''"){url}}'''})
    if response.status_code != 200:
        return
    data_json = json.loads(response.content)
    results = list()
    for search_result in data_json['data']['search']:
        response = rq.post('https://anibel-be.herokuapp.com/graphql',
                           json={'query': '''{anime(slug:"''' + search_result['url'] + '''"){slug,title{be,en},
                           description{be},poster,year,duraction{start,end},donation,download,genres,rating}}'''
                                 })
        if response.status_code != 200:
            return
        data_json = json.loads(response.content)
        anime = data_json['data']['anime']
        result_id: str = md5(text.encode()).hexdigest()
        input_content = InputTextMessageContent(
            message_text=f"<a href=\"https://anibel.net{anime['poster']}\">&#8203;</a>"
                         f"{anime['title']['be']} / {anime['title']['en']}\n"
                         f"Год выпуску: {anime['year']}\n"
                         f"Колькасць серый: {anime['duraction']['start']} з {anime['duraction']['end']}\n"
                         f"Жанры: {', '.join([genre for genre in anime['genres']])}\n"
                         f"Рэйтынг на Anibel: {anime['rating']}\n",
            parse_mode='html'
        )
        buttons = [
            [InlineKeyboardButton(
                text="Глядзець на Anibel.net",
                url=f"https://anibel.net/{anime['slug']}"
            )],
            [InlineKeyboardButton(
                text="Спампаваць",
                url=anime['download']
            )]
        ]
        if anime['donation'] != '':
            buttons.append(
                [InlineKeyboardButton(
                    text="Падзякваць за пераклад",
                    url=anime['donation']
                )]
            )
        item = InlineQueryResultArticle(
            id=result_id,
            title=anime['title']['be'],
            input_message_content=input_content,
            reply_markup=InlineKeyboardMarkup(
                row_width=1,
                inline_keyboard=buttons
            ),
            description=anime['description']['be'],
            thumb_url=f"https://anibel.net{anime['poster']}"
        )
        results.append(item)
    # don't forget to set cache_time=1 for testing (default is 300s or 5m)
    await bot.answer_inline_query(inline_query.id, results=results)#, cache_time=1)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
