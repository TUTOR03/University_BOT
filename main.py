from flask import Flask, request, abort
import telebot
from telebot import types
import zipfile
from db import *
from datetime import datetime, timedelta
import time

app = Flask(__name__)

token = '1112815348:AAHHF1qdZ0XBuUoK46IFLe63pSijokeeRw4'
bot = telebot.TeleBot(token)

main_url = 'https://83e0fe32376b.ngrok.io'

bot.remove_webhook()
bot.set_webhook(url = main_url, allowed_updates=['message', 'edited_channel_post', 'callback_query'])

@app.route('/', methods=["POST"])
def get_updates():
	ans = request.json
	# # return({'ok':True})
	# temp = datetime.now()
	# time.sleep(0.3)
	# print((temp+timedelta(milliseconds=500)) < datetime.now())
	# return({'ok':True})
	if('callback_query' in ans.keys()):
		user_mes = ans['callback_query']['data']
		user_id = ans['callback_query']['from']['id']
		message_id = ans['callback_query']['message']['message_id']
		if('register_' in user_mes):
			bot.delete_message(user_id, message_id)
			acc_type = int(user_mes.split('_')[1])
			ans = user_register(user_id, acc_type)
			if(ans['ok']):
				if(acc_type == 1):
					reply_mes = 'Добропожаловать заказчик'
					keyboard = create_default_keyboard([
						['Добавить задание'],
						['Мои задания']
					], False)
				elif(acc_type == 2):
					reply_mes = 'Добропожаловать исполнитель'
					keyboard = create_default_keyboard([
						['Список заданий'],
						['Мои задания']
					], False)
				bot.send_message(user_id, reply_mes, reply_markup = keyboard)
				return({'ok':True})
			else:
				bot.send_message(user_id, 'Вы уже зарегистрированы')
				return({'ok':True})

		elif('get_task_card_' in user_mes):
			bot.delete_message(user_id, message_id)
			task_id = user_mes.split('_')[3]
			ans = get_task_card(user_id, task_id)
			if(ans['ok']):
				reply_mes = ans['reply_mes']
				keyboard = create_inline_keyboard(ans['keyboard'])
				bot.send_message(user_id, reply_mes, reply_markup = keyboard)
				return({'ok':True})

		elif('add_task_card_img_' in user_mes):
			bot.delete_message(user_id, message_id)
			task_id = user_mes.split('_')[4]
			ans = add_task_card_img_status(user_id, task_id)
			if(ans['ok']):
				reply_mes = 'Чтобы добавить изобрадение пришлите необходимое изображение без подписи\nЕсли вы решили не добавлять изображение, напишите /reset'
				bot.send_message(user_id, reply_mes)
				return({'ok':True})

		elif('delete_task_card_' in user_mes):
			bot.delete_message(user_id, message_id)
			task_id = user_mes.split('_')[3]
			ans = delete_task_card(task_id)
			if(ans['ok']):
				reply_mes = 'Задание успешно удалено'
				bot.send_message(user_id, reply_mes)
				return({'ok':True})

		elif('success_task_card_' in user_mes):
			bot.delete_message(user_id, message_id)
			task_id = user_mes.split('_')[3]
			ans = success_task_card(task_id)
			if(ans['ok']):
				reply_mes = 'Теперь задание будет отображаться в списке у исполнителей'
				bot.send_message(user_id, reply_mes)
				return({'ok':True})

	elif('message' in ans.keys()):
		try:
			if('photo' in ans['message'].keys()):
				user_mes = ans['message']['caption']
			elif('text' in ans['message'].keys()):
				user_mes = ans['message']['text']
		except:
			user_mes = ''
		user_id = ans['message']['from']['id']

		if(user_mes == '/start'):
			user_status = user_check(user_id)
			if(user_status['register']):
				if(user_status['acc_type'] == 1):
					reply_mes = 'С возвращением заказчик'
					keyboard = create_default_keyboard([
						['Добавить задание'],
						['Мои задания']
					], False)
				elif(user_status['acc_type'] == 2):
					reply_mes = 'С возвращением исполнитель'
					keyboard = create_default_keyboard([
						['Список заданий'],
						['Мои задания']
					], False)
				set_user_status(user_id, 'waiting')
				bot.send_message(user_id, reply_mes, reply_markup = keyboard)
				return({'ok':True})
			else:
				reply_mes = 'Здравствуйте, вы впервые используете этого бота.\nВыберите кем вы хотите быть:'
				keyboard = create_inline_keyboard([
					[['Исполнитель','register_2']],
					[['Заказчик','register_1']]
				])
				bot.send_message(user_id, reply_mes, reply_markup = keyboard)
				return({'ok':True})

		elif(user_mes == '/reset'):
			set_user_status(user_id, 'waiting')

		elif(user_mes == 'Список заданий'):
			tasks = get_tasks_list(user_id)
			if(tasks['ok']):
				reply_mes='Доступные задания:'
				keyboard = create_inline_keyboard(tasks['tasks'])
				bot.send_message(user_id, reply_mes, reply_markup = keyboard)
				return({'ok':True})
			return({'ok':True})

		elif(user_mes == 'Добавить задание'):
			ans = create_task_model(user_id)
			if(ans['ok']):
				reply_mes = 'Чтобы добавить задание, отправьте сообщение с прикрепленной фотографией вида:\nНазвание/Стоимоть\nЕсли вы решил не добавлять задание, то напишите /reset'
				bot.send_message(user_id, reply_mes)
				return({'ok':True})
			return({'ok':True})

		elif(user_mes == 'Мои задания'):
			tasks = get_my_tasks(user_id)
			if(tasks['ok']):
				reply_mes='Мои задания:'
				keyboard = create_inline_keyboard(tasks['tasks'])
				bot.send_message(user_id, reply_mes, reply_markup = keyboard)
				return({'ok':True})
			return({'ok':True})

		else:
			acc_status = get_user_status(user_id)
			if(acc_status == 'adding_task'):
				error = 'none'
				if(user_mes!=''):
					user_mes = user_mes.split('/')
					if(len(user_mes)!=2):
						error = 'Неправильно указаны название и стоимоть'
					try:
						int(user_mes[1])
					except:
						error = 'Стоимоть должна быть числом'
					if(not 'photo' in ans['message'].keys()):
						error = 'Фотография не найдена'
					if('media_group_id' in ans['message'].keys()):
						error = 'Больше одной фотографии'
				else:
					error = 'Отсутствует название и цена'
				if(error == 'none'):
					result = create_task(user_id,ans['message']['photo'],user_mes)
					if(result['ok']):
						reply_mes='Задание успешно сощдано. Чтобы добавить изображения перейдите в "Мои задания"'
						bot.send_message(user_id, reply_mes)
						return({'ok':True})
				else:
					bot.send_message(user_id, error)
				return({'ok':True})
			elif('adding_task_card_img_' in acc_status):
				error = 'none'
				if(user_mes == ''):
					if(not 'photo' in ans['message'].keys()):
						error = 'Фотография не найдена'
					if('media_group_id' in ans['message'].keys()):
						error = 'Больше одной фотографии'
				else:
					error = 'У фотографии не должно быть подписи'
				if(error == 'none'):
					task_id = acc_status.split('_')[4]
					result = add_task_card_img(user_id, task_id, ans['message']['photo'])
					if(result['ok']):
						reply_mes = 'Фотография успешно добавлена'
						bot.send_message(user_id, reply_mes)
						return({'ok':True})
	return({'ok':True})

def create_inline_keyboard(mas):
	markup = types.InlineKeyboardMarkup()
	for row in mas:
		new_row = []
		for btn in row:
			new_row.append(types.InlineKeyboardButton(text = btn[0], callback_data = btn[1]))
		markup.add(*new_row)
	return(markup)

def create_default_keyboard(mas, one_time):
	markup = types.ReplyKeyboardMarkup(one_time_keyboard = one_time, resize_keyboard = True)
	for row in mas:
		new_row = []
		for btn in row:
			new_row.append(types.KeyboardButton(btn))
		markup.row(*new_row)
	return markup

if(__name__ == '__main__'):
	inicialize_db()
	app.run(debug = True)