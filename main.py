from os import environ
from hashlib import md5
import json
import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.types import InlineQuery, InputTextMessageContent, InlineQueryResultArticle, InlineKeyboardMarkup,\
    InlineKeyboardButton, CallbackQuery
import requests as rq

logging.basicConfig(level=logging.INFO)

bot = Bot(environ.get('BOT_TOKEN'))
dp = Dispatcher(bot)


def get_title_info(slug):
    response = rq.post('https://anibel-be.herokuapp.com/graphql',
                       json={'query': '''{anime(slug:"''' + slug + '''"){slug,title{be,en},
                               description{be},poster,year,duraction{start,end},donation,download,genres,rating}}'''
                             })
    if response.status_code != 200:
        return False
    data_json = json.loads(response.content)
    anime = data_json['data']['anime']
    message_text = f"<a href=\"https://anibel.net{anime['poster']}\">&#8203;</a>" \
                   f"{anime['title']['be']} / {anime['title']['en']}\n"\
                   f"Год выпуску: {anime['year']}\n"\
                   f"Колькасць серый: {anime['duraction']['start']} з {anime['duraction']['end']}\n"\
                   f"Жанры: {', '.join([genre for genre in anime['genres']])}\n"\
                   f"Рэйтынг на Anibel: {anime['rating']}\n"
    return {
        'message_text': message_text,
        'slug': slug,
        'download': anime['download'],
        'donation': anime['donation'],
        'title': {
            'en': anime['title']['en'],
            'be': anime['title']['be']
        },
        'description': {
            'be': anime['description']['be']
        },
        'poster': anime['poster']
    }


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
        anime = get_title_info(search_result['url'])
        result_id: str = md5(text.encode()).hexdigest()
        input_content = InputTextMessageContent(
            message_text=anime['message_text'],
            parse_mode='html'
        )
        reply_markup = InlineKeyboardMarkup(1)
        reply_markup.add(InlineKeyboardButton(
            text="Глядзець на Anibel.net",
            url=f"https://anibel.net/{anime['slug']}"
        ))
        reply_markup.add(InlineKeyboardButton(
            text="Глядзець анлайн",
            callback_data=anime['slug']
        ))
        reply_markup.add(InlineKeyboardButton(
            text="Спампаваць",
            url=anime['download']
        ))
        if anime['donation'] != '':
            reply_markup.add(InlineKeyboardButton(
                text="Падзякваць за пераклад",
                url=anime['donation']
            ))
        item = InlineQueryResultArticle(
            id=result_id,
            title=anime['title']['be'],
            input_message_content=input_content,
            reply_markup=reply_markup,
            description=anime['description']['be'],
            thumb_url=f"https://anibel.net{anime['poster']}"
        )
        results.append(item)
    await bot.answer_inline_query(inline_query.id, results=results, cache_time=1)


@dp.callback_query_handler()
# @dp.throttled(rate=2)
async def callback(callback_query: CallbackQuery):
    if callback_query.data.split('__')[0] not in ['sub', 'dub', 'main']:
        reply_markup = InlineKeyboardMarkup(2)
        reply_markup.insert(InlineKeyboardButton(
            text='Субцітры',
            callback_data=f'sub__{callback_query.data}'
        ))
        reply_markup.insert(InlineKeyboardButton(
            text='Агучка',
            callback_data=f'dub__{callback_query.data}'
        ))
        reply_markup.add(InlineKeyboardButton(
            text='Вярнуцца назад',
            callback_data='main__' + callback_query.data
        ))
        await bot.edit_message_reply_markup(
            inline_message_id=callback_query.inline_message_id,
            reply_markup=reply_markup
        )
        return
    elif callback_query.data.split('__')[0] in ['sub', 'dub']:
        response = rq.post('https://anibel-be.herokuapp.com/graphql',
                           json={'query': '''{anime(slug:"''' + ''.join(callback_query.data.split('__')[1:]) + '''")
                           {episodes{type,episode,resource,url}}}'''
                                 })
        if response.status_code != 200:
            await callback_query.answer('Error')
            return
        all_episodes = json.loads(response.content)['data']['anime']['episodes']
        episodes = list()
        for episode in all_episodes:
            if episode['type'] == callback_query.data.split('__')[0] and episode['resource'] == 1:
                episodes.append(episode)
        episodes.sort(key=lambda e: e['episode'])
        reply_markup = InlineKeyboardMarkup(8)
        for episode in episodes:
            reply_markup.insert(InlineKeyboardButton(
                text=str(episode['episode']),
                url=episode['url']
            ))
        reply_markup.add(InlineKeyboardButton(
            text='Вярнуцца назад',
            callback_data=''.join(callback_query.data.split('__')[1:])
        ))
        await bot.edit_message_reply_markup(
            inline_message_id=callback_query.inline_message_id,
            reply_markup=reply_markup
        )
        return
    elif callback_query.data.split('__')[0] == 'main':
        anime = get_title_info(''.join(callback_query.data.split('__')[1:]))
        reply_markup = InlineKeyboardMarkup(1)
        reply_markup.add(InlineKeyboardButton(
            text="Глядзець на Anibel.net",
            url=f"https://anibel.net/{anime['slug']}"
        ))
        reply_markup.add(InlineKeyboardButton(
            text="Глядзець анлайн",
            callback_data=anime['slug']
        ))
        reply_markup.add(InlineKeyboardButton(
            text="Спампаваць",
            url=anime['download']
        ))
        if anime['donation'] != '':
            reply_markup.add(InlineKeyboardButton(
                text="Падзякваць за пераклад",
                url=anime['donation']
            ))
        await bot.edit_message_reply_markup(
            inline_message_id=callback_query.inline_message_id,
            reply_markup=reply_markup
        )
        return
    await callback_query.answer('Hi')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
