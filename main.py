# -*- coding: utf-8 -*- 
from flask import Flask, request, abort
import telebot
from telebot import types
from db import *
import time
import logging
import math

app = Flask(__name__)

logger = logging.getLogger('info_logger')
logger.setLevel('INFO')
logger_handler = logging.FileHandler('logs.log', mode = 'a')
logger_handler.setLevel('INFO')
loger_formater = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger_handler.setFormatter(loger_formater)
logger.addHandler(logger_handler)

token = '1112815348:AAHHF1qdZ0XBuUoK46IFLe63pSijokeeRw4'
bot = telebot.TeleBot(token)

main_url = 'https://b4a60c61ac65.ngrok.io'

SERVER_IP = '80.240.25.179'
SERVER_PORT = '8443'

bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url = f'https://{SERVER_IP}:{SERVER_PORT}',certificate = open('YOURPUBLIC.pem') , allowed_updates=['message', 'edited_channel_post', 'callback_query','pre_checkout_query'])

logger.info('set webhook')

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
	if('callback_query' in ans.keys()):
		user_mes = ans['callback_query']['data']
		user_id = ans['callback_query']['from']['id']
		try:
			message_id = ans['callback_query']['message']['message_id']
			last_time = check_user_last_time(user_id)
			if(last_time['ok'] and last_time['status']):
				logger.info(f'CallBack user_id : {user_id} user_mes : {user_mes}')
				if('register_' in user_mes):
					# bot.delete_message(user_id, message_id)
					acc_type = int(user_mes.split('_')[1])
					if(acc_type == 1):
						ans = user_register(user_id, acc_type)
						if(ans['ok']):
							reply_mes = 'Добро пожаловать заказчик'
							keyboard = create_default_keyboard([
								['Добавить задание 📎'],
								['Мои задания 📚']
							], False)
						else:
							reply_mes = 'Вы уже зарегистрированы'
					elif(acc_type == 2):
						reply_mes = 'Чтобы стать исполнителем отправьте заявку через /help\nНеобходимо указать ФИО и почту\nВ течение 24 часов администратор рассмотрит вашу заявку'
						keyboard = create_default_keyboard([], False)
					bot.send_message(user_id, reply_mes, reply_markup = keyboard)
					return({'ok':True})

				elif('get_task_card_' in user_mes):
					bot.delete_message(user_id, message_id)
					task_id = user_mes.split('_')[3]
					ans = get_task_card(user_id, task_id)
					if(ans['ok']):
						reply_mes = ans['reply_mes']
						keyboard = create_inline_keyboard(ans['keyboard'])
						for i in range(math.ceil(len(ans['files'])/10)):
							temp_mas = ans['files'][10*i:10*(i+1)]
							if(len(temp_mas) == 1):
								bot.send_photo(user_id, photo = ans['files'][0])
							else:
								bot.send_media_group(user_id, media = list(map(lambda ob:types.InputMediaPhoto(ob),temp_mas)))
						bot.send_message(user_id, reply_mes, reply_markup = keyboard)
						return({'ok':True})

				elif('add_task_card_img_' in user_mes):
					bot.delete_message(user_id, message_id)
					task_id = user_mes.split('_')[4]
					del_prev_card_imgs(task_id, message_id, user_id, 1)
					ans = add_task_card_img_status(user_id, task_id)
					if(ans['ok']):
						reply_mes = 'Чтобы добавить изображение пришлите необходимое изображение без подписи\nЕсли вы решили не добавлять изображение, напишите /reset'
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
						reply_mes = 'Теперь задание будет отображаться в списке у Limuric \n\nОжидайте, скоро Limuric приступит к выполнению задания\n'
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
						send_notification(ans['user'],ans['not_mes'])
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
						for i in range(math.ceil(len(ans['files'])/10)):
							temp_mas = ans['files'][10*i:10*(i+1)]
							if(len(temp_mas) == 1):
								bot.send_photo(user_id, photo = ans['files'][0])
							else:
								bot.send_media_group(user_id, media = list(map(lambda ob:types.InputMediaPhoto(ob),temp_mas)))
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
						reply_mes = '✅ Теперь вы имеете полный доступ к ответам и можете удалить это задание.\n💟 Спасибо.'
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
						reply_mes = 'Укажите данные одним ответным сообщением:\n\nДанные карты или номер телефона для перевода\nНазвание Банка\nФамилия Имя\nВ течение 24 часов наши администраторы совершат перевод.\n\n'
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
					ans = close_payment_card(user_id, pay_id)
					if(ans['ok']):
						reply_mes = 'Данные об оплате успешно удалены'
						bot.send_message(user_id, reply_mes)
					return({'ok':True})

				elif('close_help_card_' in user_mes):
					bot.delete_message(user_id, message_id)
					help_id = user_mes.split('_')[3]
					ans = close_help_card(user_id, help_id)
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
					ans = create_payment(user_id, task_id, '', 1)
					reply_mes = ans['reply_mes']
					bot.send_message(user_id, reply_mes)
					return({'ok':True})

				elif('success_pay_card_' in user_mes):
					bot.delete_message(user_id, message_id)
					task_id = user_mes.split('_')[3]
					ans = success_pay_card(user_id, task_id)
					if(ans['ok']):
						reply_mes = 'Оплата задания успешно подтверждена'
						bot.send_message(user_id, reply_mes)
					return({'ok':True})
		except Exception as e:
			logger.error(f'CallBack user_id : {user_id} user_mes : {user_mes} Error : {e}')
	elif('message' in ans.keys()):
		if('photo' in ans['message'].keys() and 'caption' in ans['message'].keys()):
			user_mes = ans['message']['caption']
		elif('text' in ans['message'].keys()):
			user_mes = ans['message']['text']
		else:
			user_mes = ''
		user_id = ans['message']['from']['id']
		last_time = check_user_last_time(user_id)
		if(last_time['ok'] and last_time['status']):
			acc_data = get_user_status(user_id)
			acc_status = acc_data['acc_status']
			acc_is_admin = acc_data['is_admin']
			try:
				logger.info(f"Message user_id : {user_id} user_mes : {user_mes.replace('📎','').replace('📚','').replace('📃','').replace('💼','').replace('✅','')} user_status : {acc_status}")
				if(user_mes == '/reset'):
					set_user_status(user_id, 'waiting')
					return({'ok':True})
				if(acc_status == 'waiting' or acc_status == 'none' or acc_status == 'registration'):
					if(user_mes == '/start'):
						user_tag = ans['message']['from']['username']
						user_status = user_check(user_id, user_tag)
						if(user_status['register']):
							if(user_status['acc_type'] == 1):
								reply_mes = 'Добро пожаловать заказчик'
								if(acc_is_admin):
									keyboard = create_default_keyboard([
										['Добавить задание 📎'],
										['Мои задания 📚'],
										['Admin data']
									], False)
								else:
									keyboard = create_default_keyboard([
										['Добавить задание 📎'],
										['Мои задания 📚']
									], False)
							elif(user_status['acc_type'] == 2):
								reply_mes = 'Добро пожаловать (Limuric)'
								if(acc_is_admin):
									keyboard = create_default_keyboard([
										['Список заданий 📃'],
										['Мои задания 📚'],
										['Admin data']
									], False)
								else:
									keyboard = create_default_keyboard([
										['Список заданий 📃'],
										['Мои задания 📚']
									], False)
							set_user_status(user_id, 'waiting')
							bot.send_message(user_id, reply_mes, reply_markup = keyboard)
							return({'ok':True})
						else:
							reply_mes = 'Привет 👋\n🔰Здесь ты можешь получить ответы на любые задания! 🤘\n\n✨Расчетки✨Чертежи✨\n✨ Лабораторные работы ✨\n✨Практика✨Билеты✨ и тп✨\n\nПо вопросам и предложениям обращаться сюда: @ari_gu\nИли в техподдержку - команда /help\n\n🙀 Как это работает? \n\n1. Вы загружаете фотографию задания и выставляете цену.\n2. Ожидайте пока ваш заказ будет взят Исполнителем.\n3. Доступ к ответам будет открыть после оплаты заказа.\n4. Проверьте качество выполненой работы.\n5. Оцените работу сервиса и оставьте отзыв.\n\nДля продолжения нажмите кнопку:\n✅ НАЧАТЬ ✅\n\n_____________________\n😼 Ты Гуру в учебе и хочешь на этом заработать?\nЖми: ОСТАВИТЬ ЗАЯВКУ'
							keyboard = create_inline_keyboard([
								[['💼 Оставить заявку 💼','register_2']],
								[['✅ Начать ✅','register_1']]
							])
							bot.send_message(user_id, reply_mes, reply_markup = keyboard)
							return({'ok':True})

				if(acc_status == 'waiting'):

					if(user_mes == '/help'):
						set_user_status(user_id, 'adding_admin_request')
						reply_mes = '❣️ Техподдержка: ❣️\n\n⚠️ Отправьте запрос ОДНИМ сообщением начав его со слов:\n\nЕсли у вас возникла проблема, опишите ее, начав сообщение со слова ПРОБЛЕМА\n\nХотите пополнить ряды команды Limuric, начните сообщение со слова LIMURIC\n\nХотите оставить отзыв или предложение, начните сообщение со слова ОТЗЫВ или ПРЕДЛОЖЕНИЕ'
						bot.send_message(user_id, reply_mes)
						return({'ok':True})

					elif(user_mes == '/info'):
						reply_mes = 'INFO:\n\nПо вопросам и предложениям обращаться сюда: @ari_gu\nИли в техподдержку - команда /help\n\nЧтобы сменить роль с Заказчика на Limuric: /change\nИнфо: /info'
						bot.send_message(user_id, reply_mes)
						return({'ok':True})

					elif(user_mes == '/change'):
						ans = change_status(user_id)
						if(ans['ok']):
							if(ans['type'] == 1):
								reply_mes = 'Добро пожаловать заказчик'
								if(acc_is_admin):
									keyboard = create_default_keyboard([
										['Добавить задание 📎'],
										['Мои задания 📚'],
										['Admin data']
									], False)
								else:
									keyboard = create_default_keyboard([
										['Добавить задание 📎'],
										['Мои задания 📚']
									], False)
							elif(ans['type'] == 2):
								reply_mes = 'Добро пожаловать (Limuric)'
								if(acc_is_admin):
									keyboard = create_default_keyboard([
										['Список заданий 📃'],
										['Мои задания 📚'],
										['Admin data']
									], False)
								else:
									keyboard = create_default_keyboard([
										['Список заданий 📃'],
										['Мои задания 📚']
									], False)
							bot.send_message(user_id, reply_mes, reply_markup = keyboard)
						else:
							reply_mes = 'У вас нет доступа к этой команде\nЧтобы стать исполнителем отправьте заявку через /help\nНеобходимо указать ФИО и почту\nВ течение 24 часов администратор рассмотрит вашу заявку'
							bot.send_message(user_id, reply_mes)
						return({'ok':True})

					elif(acc_is_admin and user_mes == '/op_work'):
						ans = op_worker_status(user_id)
						if(ans['ok']):
							reply_mes = 'Введите имя пользователя'
							bot.send_message(user_id, reply_mes)
						return({'ok':True})

					elif(acc_is_admin and user_mes == '/get_log'):
						with open('logs.log','r') as file:
							bot.send_document(user_id,file)
						return({'ok':True})

					elif(acc_is_admin and user_mes == '/get_db'):
						with open('bot_q.db','r') as file:
							bot.send_document(user_id,file)
						return({'ok':True})

					elif(user_mes == 'Список заданий 📃'):
						tasks = get_tasks_list(user_id)
						if(tasks['ok']):
							reply_mes='Доступные задания:'
							keyboard = create_inline_keyboard(tasks['tasks'])
							bot.send_message(user_id, reply_mes, reply_markup = keyboard)
							return({'ok':True})
						return({'ok':True})

					elif(user_mes == 'Добавить задание 📎'):
						ans = create_task_status(user_id)
						if(ans['ok']):
							reply_mes = '➕ Чтобы добавить задание:\n\n📎 Прикрепите одну фотографию с подписью в таком формате:\n \n  Название/Стоимоть\n\n  Пример:\n\n  Расчетка номера 11 13 15 / 200\n\n\nПрикрепить больше фотографий к заданию вы можете в разделе "Мои задания 📚" \n \nДля отмены напишите /reset'
							bot.send_message(user_id, reply_mes)
							#bot.send_photo(user_id, open('photo/example.png', 'rb')); #joma
							return({'ok':True})
						return({'ok':True})

					elif(user_mes == 'Мои задания 📚'):
						tasks = get_my_tasks(user_id)
						if(tasks['ok']):
							reply_mes='Мои задания 📚:'
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
						elif(not user_mes[1].replace(' ','').isdigit()):
							error = 'Цена не является целым числом'
						else:
							if(len(user_mes[1].replace(' ',''))>5):
								error = 'Слишком большая цена'
							elif(int(user_mes[1].replace(' ',''))<80):
								error = 'Минимальная цена 80руб'
						if(not 'photo' in ans['message'].keys()):
							error = 'Фотография не найдена'
						if('media_group_id' in ans['message'].keys()):
							error = 'Больше одной фотографии'
					else:
						error = 'Отсутствует название и цена'
					if(error == 'none'):
						result = create_task(user_id,ans['message']['photo'],user_mes)
						if(result['ok']):
							reply_mes='✅ Задание успешно создано! ✅\n\n⚠️ Не забудте подтвердить задание! 👇👇👇\n⚠️ Перейдите в "Мои задания 📚" \n\n⏳ Там же отслеживайте статус заказа 😉'
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
						result = create_payment(user_id, task_id, user_mes, 2)
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
						pay_id = acc_status.split('_')[3]
						result = reject_payment_card(user_id, pay_id, user_mes)
						if(result['ok']):
							reply_mes = 'Запрос на оплату успешно отклонен'
							bot.send_message(user_id, reply_mes)
							send_notification(result['user'], result['not_mes'])
					else:
						bot.send_message(user_id, error)
					return({'ok':True})

				elif('op_worker' in acc_status):
					error = 'none'
					if(user_mes == ''):
						error = 'Имя не обноружено'
					if(error == 'none'):
						result = op_worker(user_id,user_mes.replace('@',''))
						if(result['ok']):
							reply_mes = 'Пользователь успешно одобрен'
							send_notification(result['user'], result['not_mes'])
						else:
							reply_mes = 'Данного пользователся не существует'
						bot.send_message(user_id, reply_mes)
					else:
						bot.send_message(user_id, error)
					return({'ok':True})
			except Exception as e:
				logger.error(f"Message user_id : {user_id} user_mes : {user_mes.replace('📎','').replace('📚','').replace('📃','').replace('💼','').replace('✅','')} user_status : {acc_status} Error : {e}")
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
	app.run(host = SERVER_IP, port = SERVER_PORT, debug = False, ssl_context = ('YOURPUBLIC.pem','YOURPRIVATE.key'))
