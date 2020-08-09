from flask import Flask, request, abort
import telebot
from telebot import types
import zipfile
from db import *
import time

app = Flask(__name__)

# shopId 506751

# shopArticleId 538350

# 1111 1111 1111 1026, 12/22, CVC 000.

#{'update_id': 336558998, 'pre_checkout_query': {'id': '2271760126141413696', 'from': {'id': 528935372, 'is_bot': False, 'first_name': 'Artem', 'username': 'TUTORT', 'language_code': 'ru'}, 'currency': 'RUB', 'total_amount': 250000, 'invoice_payload': 'task_card_pay_1'}}

#{'update_id': 336559096, 'message': {'message_id': 680, 'from': {'id': 528935372, 'is_bot': False, 'first_name': 'Artem', 'username': 'TUTORT', 'language_code': 'ru'}, 'chat': {'id': 528935372, 'first_name': 'Artem', 'username': 'TUTORT', 'type': 'private'}, 'date': 1596198647, 'successful_payment': {'currency': 'RUB', 'total_amount': 20000, 'invoice_payload': 'task_card_pay_3', 'telegram_payment_charge_id': '_', 'provider_payment_charge_id': '26b622b2-000f-5000-a000-18199fd120d3'}}}

token = '1112815348:AAHHF1qdZ0XBuUoK46IFLe63pSijokeeRw4'
yandex_token = '381764678:TEST:18219'
tranzzo_token = '410694247:TEST:ba144a44-10f8-4d9e-b80a-7d36495756a1'
bot = telebot.TeleBot(token)

main_url = 'https://adbdbbaf692d.ngrok.io'

bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url = main_url, allowed_updates=['message', 'edited_channel_post', 'callback_query','pre_checkout_query'])

def del_prev_card_imgs(task_id, message_id, user_id, stat):
	col = get_task_card_imgs(task_id, stat)
	for i in range(col):
		bot.delete_message(user_id, message_id-(1+i))

def send_notification(user_id, message):
	bot.send_message(user_id, message)

@app.route('/', methods=['POST'])
def get_updates():
	ans = request.json
	# print(ans)
	# return({'ok':True})
	# temp = datetime.now()
	# time.sleep(0.3)
	# print((temp+timedelta(milliseconds=500)) < datetime.now())
	# return({'ok':True})
	if('callback_query' in ans.keys()):
		user_mes = ans['callback_query']['data']
		user_id = ans['callback_query']['from']['id']
		message_id = ans['callback_query']['message']['message_id']
		last_time = check_user_last_time(user_id)
		if(last_time['ok'] and last_time['status']):
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
					if(len(ans['files']) == 1):
						bot.send_photo(user_id, photo = ans['files'][0])
					else:
						bot.send_media_group(user_id, media = list(map(lambda ob:types.InputMediaPhoto(ob),ans['files'])))
					bot.send_message(user_id, reply_mes, reply_markup = keyboard)
					return({'ok':True})

			elif('add_task_card_img_' in user_mes):
				bot.delete_message(user_id, message_id)
				task_id = user_mes.split('_')[4]
				del_prev_card_imgs(task_id, message_id, user_id, 1)
				ans = add_task_card_img_status(user_id, task_id)
				if(ans['ok']):
					reply_mes = 'Чтобы добавить изобрадение пришлите необходимое изображение без подписи\nЕсли вы решили не добавлять изображение, напишите /reset'
				else:
					reply_mes = 'Вы не можете добавить изображение'
				bot.send_message(user_id, reply_mes)
				return({'ok':True})

			elif('delete_task_card_' in user_mes):
				bot.delete_message(user_id, message_id)
				task_id = user_mes.split('_')[3]
				del_prev_card_imgs(task_id, message_id, user_id, 1)
				ans = delete_task_card(task_id)
				if(ans['ok']):
					reply_mes = 'Задание успешно удалено'
				else:
					reply_mes = 'Вы не можете удалить задание'
				bot.send_message(user_id, reply_mes)
				return({'ok':True})

			elif('success_task_card_' in user_mes):
				bot.delete_message(user_id, message_id)
				task_id = user_mes.split('_')[3]
				del_prev_card_imgs(task_id, message_id, user_id, 1)
				ans = success_task_card(task_id)
				if(ans['ok']):
					reply_mes = 'Теперь задание будет отображаться в списке у исполнителей'
				else:
					reply_mes = 'Вы не можете подтвердить это задание'
				bot.send_message(user_id, reply_mes)
				return({'ok':True})

			elif('take_task_card_' in user_mes):
				bot.delete_message(user_id, message_id)
				task_id = user_mes.split('_')[3]
				del_prev_card_imgs(task_id, message_id, user_id, 1)
				ans = take_task_card(user_id,task_id)
				if(ans['ok']):
					reply_mes = 'Вы успешно получили это задание'
				else:
					reply_mes = 'Вам не удалось получить это задание'
				bot.send_message(user_id, reply_mes)
				return({'ok':True})

			elif('add_task_answer_' in user_mes):
				bot.delete_message(user_id, message_id)
				task_id = user_mes.split('_')[3]
				del_prev_card_imgs(task_id, message_id, user_id, 1)
				set_user_status(user_id, f'adding_task_answer_{task_id}')
				reply_mes = 'Чтобы добавить ответ отправьте фото'
				bot.send_message(user_id, reply_mes)
				return({'ok':True})

			elif('delete_task_answer_' in user_mes):
				bot.delete_message(user_id, message_id)
				task_id = user_mes.split('_')[3]
				del_prev_card_imgs(task_id, message_id, user_id, 1)
				ans = delete_task_answer(task_id)
				if(ans['ok']):
					reply_mes = 'Ответы успешно удалены'
				else:
					reply_mes = 'Нечего удалять'
				bot.send_message(user_id, reply_mes)
				return({'ok':True})

			elif('show_task_answer_' in user_mes):
				bot.delete_message(user_id, message_id)
				task_id = user_mes.split('_')[3]
				user_status = user_mes.split('_')[4]
				del_prev_card_imgs(task_id, message_id, user_id, 1)
				ans = get_task_answer(user_id, task_id)
				if(ans['ok']):
					if(len(ans['files']) == 1):
						bot.send_photo(user_id, photo = ans['files'][0])
					else:
						bot.send_media_group(user_id, media = list(map(lambda ob:types.InputMediaPhoto(ob),ans['files'])))
				if(user_status == '1'):
					ans = create_timer_chech_answer(user_id, task_id)
					if(ans['ok']):
						reply_mes = ans['reply_mes']
						keyboard = create_inline_keyboard(ans['keyboard'])
						bot.send_message(user_id, reply_mes, reply_markup = keyboard)
				return({'ok':True})

			elif('success_task_answer_' in user_mes):
				bot.delete_message(user_id, message_id)
				task_id = user_mes.split('_')[3]
				del_prev_card_imgs(task_id, message_id, user_id, 2)
				ans = success_task_answer(task_id)
				if(ans['ok']):
					reply_mes = 'Теперь вы имеете полный доступ к ответам и можете удалить это задание'
					bot.send_message(user_id, reply_mes)
					send_notification(ans['user'], ans['not_mes'])
				return({'ok':True})

			elif('reject_task_answer_' in user_mes):
				bot.delete_message(user_id, message_id)
				task_id = user_mes.split('_')[3]
				del_prev_card_imgs(task_id, message_id, user_id, 2)
				ans = reject_task_answer(task_id, user_id)
				if(ans['ok']):
					reply_mes = ans['reply_mes']
					bot.send_message(user_id, reply_mes)
				return({'ok':True})

			elif('send_task_answer_' in user_mes):
				bot.delete_message(user_id, message_id)
				task_id = user_mes.split('_')[3]
				del_prev_card_imgs(task_id, message_id, user_id, 1)
				ans = send_task_answer(task_id)
				if(ans['ok']):
					reply_mes = 'Работа отправлена заказчику на оценку'
					send_notification(ans['user'],ans['message'])
				else:
					reply_mes = 'Вы не можете отправить эту работу'
				bot.send_message(user_id, reply_mes)
				return({'ok':True})

			elif('ask_for_payment_' in user_mes):
				bot.delete_message(user_id, message_id)
				task_id = user_mes.split('_')[3]
				del_prev_card_imgs(task_id, message_id, user_id, 1)
				ans = create_payment_status(user_id, task_id)
				if(ans['ok']):
					reply_mes = 'Укажите данные карты или номер телефона для перевода\nВ течение 24 часов наши администраторы совершат перевод'
					bot.send_message(user_id, reply_mes)	
				return({'ok':True})

			elif('get_payment_card_' in user_mes):
				bot.delete_message(user_id, message_id)
				pay_id = user_mes.split('_')[3]
				ans = get_payment_card(user_id, pay_id)
				if(ans['ok']):
					reply_mes = ans['reply_mes']
					keyboard = create_inline_keyboard(ans['keyboard'])
					bot.send_message(user_id, reply_mes, reply_markup = keyboard)
				return({'ok':True})

			elif('get_help_card_' in user_mes):
				bot.delete_message(user_id, message_id)
				help_id = user_mes.split('_')[3]
				ans = get_help_card(user_id, help_id)
				if(ans['ok']):
					reply_mes = ans['reply_mes']
					keyboard = create_inline_keyboard(ans['keyboard'])
					bot.send_message(user_id, reply_mes, reply_markup = keyboard)
				return({'ok':True})

			elif('close_payment_card_' in user_mes):
				bot.delete_message(user_id, message_id)
				pay_id = user_mes.split('_')[3]
				ans = close_payment_card(user_mes, pay_id)
				if(ans['ok']):
					reply_mes = 'Данные об оплате успешно удалены'
					bot.send_message(user_id, reply_mes)
				return({'ok':True})

			elif('close_help_card_' in user_mes):
				bot.delete_message(user_id, message_id)
				help_id = user_mes.split('_')[3]
				ans = close_payment_card(user_mes, help_id)
				if(ans['ok']):
					reply_mes = 'Данное клиентское обращение удалено'
					bot.send_message(user_id, reply_mes)
				return({'ok':True})

			elif('reject_payment_card_' in user_mes):
				bot.delete_message(user_id, message_id)
				pay_id = user_mes.split('_')[3]
				ans = reject_payment_card_status(user_id, pay_id)
				if(ans['ok']):
					reply_mes = 'Опишите, почему невозможно провести оплату'
					bot.send_message(user_id, reply_mes)
				return({'ok':True})

			elif('pay_task_card_' in user_mes):
				bot.delete_message(user_id, message_id)
				task_id = user_mes.split('_')[3]
				del_prev_card_imgs(task_id, message_id, user_id, 1)
				ans = can_send_pay(task_id)
				if(ans['ok']):
					bot.send_invoice(
					chat_id = user_id,
					title = ans['title'],
					description = 'Оплата услуг исполнителя',
					provider_token=yandex_token,
			    	currency='rub',
			    	prices=[types.LabeledPrice(label = 'worker_job_pay', amount = int(ans['cost'])*100)],
			    	start_parameter='worker_pay',
			    	invoice_payload=f'task_card_pay_{task_id}'
					)
				else:
					reply_mes = 'Вы не можете совершить оплату'
					bot.send_message(user_id, reply_mes)
				return({'ok':True})

	elif('message' in ans.keys()):
		payment = False
		if('photo' in ans['message'].keys() and 'caption' in ans['message'].keys()):
			user_mes = ans['message']['caption']
		elif('text' in ans['message'].keys()):
			user_mes = ans['message']['text']
		else:
			user_mes = ''
		if('successful_payment' in ans['message'].keys()):
			payment = True
		user_id = ans['message']['from']['id']
		last_time = check_user_last_time(user_id)
		if(last_time['ok'] and last_time['status']):
			if(not payment):
				acc_data = get_user_status(user_id)
				acc_status = acc_data['acc_status']
				acc_is_admin = acc_data['is_admin']
				if(acc_status == 'waiting' or acc_status == 'none'):
					if(user_mes == '/start'):
						user_status = user_check(user_id)
						if(user_status['register']):
							if(user_status['acc_type'] == 1):
								reply_mes = 'С возвращением заказчик'
								if(acc_is_admin):
									keyboard = create_default_keyboard([
										['Добавить задание'],
										['Мои задания'],
										['Admin data']
									], False)
								else:
									keyboard = create_default_keyboard([
										['Добавить задание'],
										['Мои задания']
									], False)
							elif(user_status['acc_type'] == 2):
								reply_mes = 'С возвращением исполнитель'
								if(acc_is_admin):
									keyboard = create_default_keyboard([
										['Список заданий'],
										['Мои задания'],
										['Admin data']
									], False)
								else:
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

				if(acc_status == 'waiting'):
					if(user_mes == '/reset'):
						set_user_status(user_id, 'waiting')

					elif(user_mes == '/help'):
						set_user_status(user_id, 'adding_admin_request')
						reply_mes = 'Пожалуйста опишите вашк проблему\nАдминистратор ответит в течение 24 часов'
						bot.send_message(user_id, reply_mes)
						return({'ok':True})

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

					elif(user_mes == 'Admin data' and acc_is_admin):
						data = get_admin_list(user_id)
						if(data['ok']):
							reply_mes = 'Admin list:'
							keyboard = create_inline_keyboard(data['data'])
							bot.send_message(user_id, reply_mes, reply_markup = keyboard)
							return({'ok':True})
						return({'ok':True})

				elif(acc_status == 'adding_task'):
					error = 'none'
					if(user_mes!=''):
						user_mes = user_mes.split('/')
						if(len(user_mes)!=2):
							error = 'Неправильно указаны название и стоимоть'
						try:
							int(user_mes[1])
						except:
							error = 'Стоимоть должна быть числом'
						if(len(user_mes)==2):
							if(len(user_mes[1])>5):
								error = 'Слишком большая цена'
						if(not 'photo' in ans['message'].keys()):
							error = 'Фотография не найдена'
						if('media_group_id' in ans['message'].keys()):
							error = 'Больше одной фотографии'
					else:
						error = 'Отсутствует название и цена'
					if(error == 'none'):
						result = create_task(user_id,ans['message']['photo'],user_mes)
						if(result['ok']):
							reply_mes='Задание успешно создано. Чтобы добавить изображения перейдите в "Мои задания"'
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
					else:
						bot.send_message(user_id, error)
					return({'ok':True})

				elif('adding_task_answer_' in acc_status):
					error = 'none'
					if(user_mes == ''):
						if(not 'photo' in ans['message'].keys()):
							error = 'Фотография не найдена'
						if('media_group_id' in ans['message'].keys()):
							error = 'Больше одной фотографии'
					else:
						error = 'У фотографии не должно быть подписи'
					if(error == 'none'):
						task_id = acc_status.split('_')[3]
						result = add_task_answer(user_id, task_id, ans['message']['photo'])
						if(result['ok']):
							reply_mes = 'Фотография успешно добавлена'
							bot.send_message(user_id, reply_mes)
					else:
						bot.send_message(user_id, error)
					return({'ok':True})

				elif('adding_reject_notification_' in acc_status):
					error = 'none'
					if(user_mes == ''):
						error = 'Отсутствует сообщение'
					if(error == 'none'):
						task_id = acc_status.split('_')[3]
						result = create_reject_message(task_id, user_id, user_mes)
						if(result['ok']):
							send_notification(result['user'], result['not_mes'])
					else:
						bot.send_message(user_id, error)
					return({'ok':True})

				elif('adding_payment_' in acc_status):
					error = 'none'
					if(user_mes == ''):
						error = 'Отсутствует сообщение'
					if(error == 'none'):
						task_id = acc_status.split('_')[2]
						result = create_payment(user_id, task_id, user_mes)
						if(result['ok']):
							reply_mes = 'Ожидайте ответа от администратора'
							bot.send_message(user_id, reply_mes)
					else:
						bot.send_message(user_id, error)
					return({'ok':True})

				elif('adding_admin_request' in acc_status):
					error = 'none'
					if(user_mes == ''):
						error = 'Отсутствует сообщение'
					if(error == 'none'):
						result = create_admin_request(user_id, user_mes)
						if(result['ok']):
							reply_mes = 'Запрос успешно создан, ожидайте ответа'
							bot.send_message(user_id, reply_mes)
					else:
						bot.send_message(user_id, error)
					return({'ok':True})

				elif('adding_reject_payment_' in acc_status):
					error = 'none'
					if(user_mes == ''):
						error = 'Отсутствует сообщение'
					if(error == 'none'):
						pay_id = user_mes.split('_')[3]
						result = reject_payment_card(user_id, pay_id, user_mes)
						if(result['ok']):
							reply_mes = 'Запрос на оплату успешно откланен'
							bot.send_message(user_id, reply_mes)
							send_notification(result['user'], result['not_mes'])
					else:
						bot.send_message(user_id, error)
					return({'ok':True})

			else:
				task_id = ans['message']['successful_payment']['invoice_payload'].split('_')[3]
				ans = make_task_card_pay(task_id)
				if(ans['ok']):
					reply_mes = 'Оплата успешно завершена'
				bot.send_message(user_id, reply_mes)
	
	elif('pre_checkout_query' in ans.keys()):
		pre_checkout_query_id = ans['pre_checkout_query']['id']
		user_id = ans['pre_checkout_query']['from']['id']
		task_id = ans['pre_checkout_query']['invoice_payload'].split('_')[3]
		ans = can_send_pay(task_id)
		if(ans['ok']):
			bot.answer_pre_checkout_query(pre_checkout_query_id, ok = True)
		else:
			bot.answer_pre_checkout_query(pre_checkout_query_id, ok = False, error_message = 'Вы уже оплатили это задание')
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