from peewee import *
from datetime import timedelta, datetime
from threading import Timer

db = SqliteDatabase('bot_q.db',pragmas={
	'foreign_keys': 1
	})

CALLDOWN = 1
success_timers = []
reject_timers = []
TIMER_TIME = 1
COM_PROC = 7

class BaseModel(Model):
	class Meta:
		database = db

# MODELS

class Account(BaseModel):
	acc_id = DecimalField()
	acc_type = DecimalField()# 0-registration 1-заказчик 2-исполнитель
	acc_status = CharField()
	acc_tag = CharField()
	last_time = DateTimeField(null = True)
	is_admin = BooleanField(default = False)
	can_change = BooleanField(default = False)

class Task(BaseModel):
	title = CharField(null = True)
	cost = DecimalField(null = True)
	user = ForeignKeyField(model = Account, on_delete = 'CASCADE')
	status = DecimalField()
	worker = ForeignKeyField(model = Account, on_delete = 'CASCADE', null = True)
	payed = BlobField(default = False)

class Img(BaseModel):
	img_url = TextField()
	task = ForeignKeyField(model = Task, on_delete = 'CASCADE')
	status = DecimalField()

class Payment(BaseModel):
	task = ForeignKeyField(model = Task, on_delete = 'CASCADE')
	cost = DecimalField(null = True)
	pay_data = CharField()
	closed = BooleanField(default = False)
	status = DecimalField()

class HelpRequest(BaseModel):
	user = ForeignKeyField(model = Account, on_delete = 'CASCADE')
	message = CharField()
	closed = BooleanField(default = False)

def inicialize_db():
	db.connect()
	db.create_tables([Account, Task, Img, Payment, HelpRequest])
	# Task.create(title = 'Tsk_1', cost='300', user=1,status=0)
	# Img.create(img_url='test_url', task = 4)
	# Task.get(Task.id == 4).delete_instance()

	# Task.create(title = 'Tsk_2', cost='400', user=1,status=0)Ы

def change_status(user_id):
	user = Account.select().where(Account.acc_id == user_id)
	if(user.exists()):
		user = user.get()
		if(user.can_change):
			if(user.acc_type == 1):
				user.acc_type = 2
			else:
				user.acc_type = 1
			user.save()
			return({'ok':True,'type':user.acc_type})
	return({'ok':False})

def op_worker(user_id, tag_name):
	user = Account.select().where(Account.acc_tag == tag_name)
	if(user.exists()):
		user = user.get()
		user.can_change = True
		user.save()
		set_user_status(user_id,'waiting')
		not_mes = 'Вас успешно перевели в исполнители\nДля переключения между исполнителем и заказчиком используйет команду /change'
		return({'ok':True, 'user':user.acc_id, 'not_mes':not_mes})
	return({'ok':False})

def op_worker_status(user_id):
	user = Account.get(Account.acc_id == user_id)
	if(user.is_admin):
		user.acc_status = 'op_worker'
		user.save()
		return({'ok':True})
	return({'ok':False})

def get_tasks_list(user_id):
	user = Account.select().where(Account.acc_id == user_id)
	if(user.exists()):
		if(user.get().acc_type == 2):
			tasks = Task.select().where(Task.status == 1)
			tasks = list(map(lambda ob:[[f'{ob.title} - {ob.cost}RUB',f'get_task_card_{ob.id}']],tasks))
			return({'ok':True,'tasks':tasks})
	return({'ok':False})

def get_payment_card(user_id, pay_id):
	user = Account.get(Account.acc_id == user_id)
	if(user.is_admin):
		pay = Payment.get(Payment.id == int(pay_id))
		if(pay.status == 2):
			reply_mes = f'Вывод средст\nЗакрыт: {"Да" if pay.closed else "Нет"}\nПользователь: @{Account.get(Account.id == pay.task.worker).acc_tag}\nСообщение: {pay.pay_data}\n{pay.cost}RUB'
			keyboard = [
				[['Закрыть',f'close_payment_card_{pay.id}']],
				[['Отклонить',f'reject_payment_card_{pay.id}']]
			]
			return({
				'ok':True,
				'reply_mes':reply_mes,
				'keyboard':keyboard,
			})
		elif(pay.status == 1):
			reply_mes = f'Оплата задания\nУникаьный ID: {pay.task.id}\nЗакрыт: {"Да" if pay.closed else "Нет"}\nПользователь: @{Account.get(Account.id == pay.task.worker).acc_tag}\n{pay.cost}RUB'
			if(pay.task.payed):
				keyboard = [
					[['Закрыть',f'close_payment_card_{pay.id}']],
				]
			else:
				keyboard = [
					[['Подтвердить',f'success_pay_card_{pay.task.id}']],
				]
			return({
				'ok':True,
				'reply_mes':reply_mes,
				'keyboard':keyboard,
			})
	return({'ok':False})

def reject_payment_card(user_id, pay_id, message):
	user = Account.get(Account.acc_id == user_id)
	pay = Payment.get(Payment.id == int(pay_id))
	task = Task.get(Task.id == pay.task)
	if(task.status == 5):
		task.status = 4
		task.save()
		user.acc_status = 'waiting'
		user.save()
		pay.delete_instance()
		not_mes = f'Администратор отклонил ваш запрос на оплату по заданию:\n{task.title}\nПричина:\n{message}\nОтправьте запрос повторно или обратитесь в поддержку, прописав /help'
		return({'ok':True, 'not_mes':not_mes,'user':Account.get(Account.id == task.worker).acc_id})
	else:
		return({'ok':False})

def reject_payment_card_status(user_id, pay_id):
	user = Account.get(Account.acc_id == user_id)
	if(user.is_admin):
		user.acc_status = f'adding_reject_payment_{pay_id}'
		user.save()
		return({'ok':True})
	return({'ok':False})

def success_pay_card(user_id, task_id):
	user = Account.get(Account.acc_id == user_id)
	if(user.is_admin):
		task = Task.get(Task.id == int(task_id))
		task.payed = True
		task.save()
		return({'ok':True})
	return({'ok':False})

def close_payment_card(user_id, pay_id):
	user = Account.get(Account.acc_id == user_id)
	if(user.is_admin):
		pay = Payment.get(Payment.id == int(pay_id))
		pay.closed = True
		pay.save()
		return({'ok':True})
	return({'ok':False})

def get_help_card(user_id, help_id):
	user = Account.get(Account.acc_id == user_id)
	if(user.is_admin):
		help_card = HelpRequest.get(HelpRequest.id == int(help_id))
		reply_mes = f'Закрыт: {"Да" if help_card.closed else "Нет"}\nПользователь: @{Account.get(Account.id == help_card.user).acc_tag}\nСообщение: {help_card.message}'
		keyboard = [
			[['Зыкрыть',f'close_help_card_{help_card.id}']]
		]
		return({
			'ok':True,
			'reply_mes':reply_mes,
			'keyboard':keyboard,
		})
	return({'ok':False})

def close_help_card(user_id, help_id):
	user = Account.get(Account.acc_id == user_id)
	if(user.is_admin):
		help_card = HelpRequest.get(HelpRequest.id == int(help_id))
		help_card.closed = True
		help_card.save()
		return({'ok':True})
	return({'ok':False})

def get_admin_list(user_id):
	user = Account.get(Account.acc_id == user_id)
	if(user.is_admin):
		data_payments = Payment.select().where(Payment.closed == False)
		data_requsts = HelpRequest.select().where(HelpRequest.closed == False)
		data_payments = list(map(lambda ob:[[f'💲 {ob.cost}RUB 💲',f'get_payment_card_{ob.id}']],data_payments))
		data_requsts = list(map(lambda ob:[[f'❓ {ob.message[:15]}... ❓',f'get_help_card_{ob.id}']],data_requsts))
		data = data_payments + data_requsts
		return({'ok':True,'data':data})
	return({'ok':False})

def create_admin_request(user_id, message):
	user = Account.get(Account.acc_id == user_id)
	user.acc_status = 'waiting'
	user.save()
	HelpRequest.create(user = user, message = message)
	return({'ok':True})

def create_task(user_id, files, message):
	user = Account.select().where(Account.acc_id == user_id).get()
	title,cost = message
	user.acc_status = 'waiting'
	user.save()
	task = Task.create(title = title, cost = cost, user = user, status = 0)
	Img.create(task = task, img_url = files[0]['file_id'], status = 1)
	return({'ok':True})

def create_task_status(user_id):
	user = Account.select().where(Account.acc_id == user_id)
	if(user.exists()):
		user = user.get()
		if(user.acc_type == 1):
			user.acc_status = 'adding_task'
			user.save()
			return({'ok':True})
	return({'ok':False})

def make_task_card_pay(task_id):
	task = Task.get(Task.id == int(task_id))
	if(not task.payed and (task.status == 2 or task.status == 3)):
		task.payed = True
		task.save()
		return({'ok':True})
	return({'ok':False})

def success_task_card(task_id):
	task = Task.get(Task.id == int(task_id))
	if(task.status == 0):
		task.status = 1
		task.save()
		return({'ok':True})
	return({'ok':False})

def delete_task_card(task_id):
	task = Task.get(Task.id == int(task_id))
	if(task.status == 0 or task.status == 1):
		task.delete_instance()
		return({'ok':True})
	return({'ok':False})

def delete_task_answer(task_id):
	task = Task.get(Task.id == int(task_id))
	answers = Img.select().where((Img.status == 2) & (Img.task == int(task_id)))
	if(answers.exists() and task.status == 2):
		for ob in answers:
			ob.delete_instance()
		return({'ok':True})
	return({'ok':False})

def take_task_card(user_id, task_id):
	user = Account.select().where(Account.acc_id == user_id).get()
	task = Task.get(Task.id == int(task_id))
	if(task.worker == None and task.status == 1):
		task.worker = user
		task.status = 2
		task.save()
		not_mes = f'\nLimuric взял ваш заказ\n{task.title}\n\nТеперь вы можете оплатить его'
		return({'ok':True, 'user':Account.get(Account.id == task.user).acc_id, 'not_mes':not_mes})
	return({'ok':False})

def add_task_card_img(user_id, task_id, files):
	user = Account.select().where(Account.acc_id == user_id).get()
	user.acc_status = 'waiting'
	user.save()
	Img.create(task = int(task_id), img_url = files[0]['file_id'], status = 1)
	return({'ok':True})

def add_task_answer(user_id, task_id, files):
	user = Account.select().where(Account.acc_id == user_id).get()
	user.acc_status = 'waiting'
	user.save()
	Img.create(task = int(task_id), img_url = files[0]['file_id'], status = 2)
	return({'ok':True})

def send_task_answer(task_id):
	task = Task.get(Task.id == int(task_id))
	card_files_ans = Img.select().where((Img.task == int(task_id))&(Img.status == 2))
	if(task.status == 2 and card_files_ans.exists()):
		task.status = 3
		task.save()
		not_mes = f'Limuric отправил вам решение по заданию:\n{task.title}\nТеперь вы можете оценить данную работу, если оплатили ее'
		return({'ok':True,'user':Account.get(Account.id == task.user).acc_id,'message':not_mes})
	return({'ok':False})

def add_task_card_img_status(user_id, task_id):
	user = Account.select().where(Account.acc_id == user_id).get()
	task = Task.get(Task.id == int(task_id))
	if(task.status == 0):
		user.acc_status = f'adding_task_card_img_{task_id}'
		user.save()
		return({'ok':True})
	return({'ok':False})

def get_task_card(user_id, task_id):
	user = Account.select().where(Account.acc_id == user_id).get()
	task = Task.get(Task.id == int(task_id))
	all_card_files = Img.select().where(Img.task == int(task_id))
	card_files = list(map(lambda ob:ob.img_url,filter(lambda tm:tm.status == 1,all_card_files)))
	card_files_ans = list(map(lambda ob:ob.img_url,filter(lambda tm:tm.status == 2,all_card_files)))
	if(user.acc_type == 1):
		if(task.status == 0):
			status = 'Ожидает подтверждения ⏳'
			keyboard = [
				[['Добавить изображение',f'add_task_card_img_{task_id}'],['Удалить',f'delete_task_card_{task_id}']],
				[['Подтвердить задание',f'success_task_card_{task_id}']]
			]
		elif(task.status == 1):
			status = 'Ожидает исполнителя'
			keyboard=[
				[['Удалить',f'delete_task_card_{task_id}']]
			]
		elif(task.status == 2):
			if(task.payed):
				status = 'Исполнитель назначен'
				keyboard = []
			else:
				status = 'Исполнитель назначен, ожидает оплаты'
				keyboard = [
					[['Оплатить',f'pay_task_card_{task_id}']]#,
					#[['Удалить',f'delete_task_card_{task_id}']] #joma
				]
		elif(task.status == 3):
			if(task.payed):
				status = ' Ожидает оценки'
				keyboard = [
					[['Оценить',f'show_task_answer_{task_id}_1']]
				]
			else:
				status = 'Ожидает оценки, ожидает оплаты'
				keyboard=[
					[['Оплатить',f'pay_task_card_{task_id}']]
				]
		elif(task.status == 4 or task.status == 5):
			status = 'Работа завершена'
			keyboard = [
				[['Просмотр ответов',f'show_task_answer_{task_id}_2']],
				[['Удалить',f'delete_task_card_{task_id}']] #joma
			]

	elif(user.acc_type == 2):
		if(task.status == 1):
			status = 'Ожидает исполнителя'
			keyboard=[
				[['Взять задание',f'take_task_card_{task_id}']]
			]
		elif(task.status == 2):
			if(task.payed):
				status = 'Исполнитель назначен'
			else:
				status = 'Исполнитель назначен, ожидает оплаты'
			if(len(card_files_ans) == 0):
				keyboard=[
					[['Добавить ответ',f'add_task_answer_{task_id}']]
				]
			else:
				keyboard=[
					[['Добавить ответ',f'add_task_answer_{task_id}'],['Удалить ответы',f'delete_task_answer_{task_id}']],
					[['Посмотреть ответы',f'show_task_answer_{task_id}_2'],['Отправить заказчику',f'send_task_answer_{task_id}']]
				]
		elif(task.status == 3):
			if(task.payed):
				status = 'Ожидает оценки'
			else:
				status = 'Ожидает оценки, ожидает оплаты'
			keyboard=[
				[['Посмотреть ответы',f'show_task_answer_{task_id}_2']]
			]
		elif(task.status == 4):
			status = 'Работа завершена. Доступен вывод средств'
			if(task.payed):
				keyboard = [
					[['Вывести средства',f'ask_for_payment_{task_id}']]
				]
			else:
				keyboard = []
		elif(task.status == 5):
			status = 'Работа завершена. Ожидается вывод средств'
			keyboard = []

	reply_mes = f'Уникальный ID:{task.id}\n\n🔰 Задание: {task.title}\n\n💰 Цена: {task.cost} руб\n\n🔎 Статус: {status}\n\n💎 Оплачен: {"Да ✅" if task.payed else "Нет ❌"}'
	return({
		'ok':True,
		'reply_mes':reply_mes,
		'keyboard':keyboard,
		'files':card_files
	})

def create_timer_chech_answer(user_id, task_id):
	user = Account.get(Account.acc_id == user_id)
	task = Task.get(Task.id == int(task_id))
	have_timer = False
	for ob in success_timers:
		if(ob['task'] == task_id):
			have_timer = True
			break
	if(task.status == 3):
		keyboard = [
			[['Подтвердить ✅',f'success_task_answer_{task_id}'],['Отклонить ❌',f'reject_task_answer_{task_id}']]
		]
		reply_mes = 'Данное задание уже на подтверждении'
		if(not have_timer):
			reply_mes = 'Вам необходимо подтвердить или отклонить полученную работу в течение 15 минут\nПо прошествии 15 минут работа будет подтверждена автоматически'
			success_timers.append({
				'task':task_id,
				'timer':Timer(TIMER_TIME*60,force_success_task_answer, args = [task_id, 1])
			})
			success_timers[-1]['timer'].start()
		return({
			'ok':True,
			'reply_mes':reply_mes,
			'keyboard':keyboard,
		})
	return({'ok':False})

def create_payment(user_id, task_id, message, status):
	task = Task.get(Task.id == int(task_id))
	user = Account.get(Account.acc_id == user_id)
	if(status == 2):
		if(task.status == 4):
			task.status = 5
			task.save()
			user.acc_status = 'waiting'
			user.save()
			Payment.create(task = task, pay_data = message, cost = int(task.cost)*(100-COM_PROC)//100, status = status)
			return({'ok':True})
		return({'ok':False})
	elif(status == 1):
		pay = Payment.select().where((Payment.task == task)&(Payment.status == 1))
		if(not pay.exists()):
			Payment.create(task = task, pay_data = message, cost = int(task.cost), status = status)
			reply_mes = f'Чтобы оплатить задание переведите {task.cost}RUB по номеру:\nСБЕРБАНК: +79322477131, в комментарии к платежу указав уникальный номер задания\n Ваш уникальный номер задания:{task.id}\n\nПосле оплаты ждите подтверждение Администратора.\n(Мои задания📚 => 💎Статус оплаты)\n\n⚠️ Техподдержка - /help'
			return({'ok':True,'reply_mes':reply_mes})
		reply_mes = f'Вы уже создали запрос на оплату'
		return({'ok':False,'reply_mes':reply_mes})

def create_payment_status(user_id, task_id):
	task = Task.get(Task.id == int(task_id))
	user = Account.get(Account.acc_id == user_id)
	if(task.status == 4):
		user.acc_status = f'adding_payment_{task_id}'
		user.save()
		return({'ok':True})
	return({'ok':False})

def success_task_answer(task_id):
	task = Task.get(Task.id == int(task_id))
	if(task.status == 3):
		for ob in success_timers:
			if(ob['task'] == task_id):
				success_timers[success_timers.index(ob)]['timer'].cancel()
				success_timers.remove(ob)
				break
		task.status = 4
		task.save()
		not_mes = f'Заказчик подтвердил заказ, спасибо за работу!\n Вам доступен вывод средств.\n Оставьте заявку на вывод во вкладке Мои задания📚\n{task.title}'
		return({'ok':True, 'user':Account.get(Account.id == task.worker).acc_id, 'not_mes':not_mes})
	return({'ok':False})

def reject_task_answer(task_id, user_id):
	task = Task.get(Task.id == int(task_id))
	user = Account.get(Account.acc_id == user_id)
	if(task.status == 3):
		for ob in success_timers:
			if(ob['task'] == task_id):
				success_timers[success_timers.index(ob)]['timer'].cancel()
				success_timers.remove(ob)
				break
		user.acc_status = f'adding_reject_notification_{task_id}'
		user.save()
		have_timer = False
		for ob in reject_timers:
			if(ob['task'] == task_id):
				have_timer = True
				break
		reply_mes = 'Опишите проблему в решении'
		if(not have_timer):
			reject_timers.append({
				'task':task_id,
				'timer':Timer(TIMER_TIME*60,force_success_task_answer, args = [task_id, 2])
			})
			reject_timers[-1]['timer'].start()
			reply_mes = 'Опишите проблему в решении в течение 30 минут или задание будет автоматически подтверждено'
		return({'ok':True,'reply_mes':reply_mes})
	return({'ok':False})

def create_reject_message(task_id, user_id, message):
	task = Task.get(Task.id == int(task_id))
	user = Account.get(Account.acc_id == user_id)
	if(task.status == 3):
		user.acc_status = 'waiting'
		user.save()
		task.status = 2
		task.save()
		dl = delete_task_answer(task_id)
		for ob in reject_timers:
			if(ob['task'] == task_id):
				reject_timers[reject_timers.index(ob)]['timer'].cancel()
				reject_timers.remove(ob)
				break
		not_mes = f'Заказчик отклонил ваш ответ по заданию\n{task.title}\n{message}'
		return({'ok':True,'not_mes':not_mes,'user':Account.get(Account.id == task.worker).acc_id})
	return({'ok':False})

def force_success_task_answer(task_id, type_t):
	task = Task.get(Task.id == int(task_id))
	task.status = 4
	task.save()
	set_user_status(Account.get(Account.id == task.user).acc_id,'waiting')
	if(type_t == 1):
		for ob in success_timers:
			if(ob['task'] == task_id):
				success_timers.remove(ob)
				break
	elif(type_t == 2):
		for ob in reject_timers:
			if(ob['task'] == task_id):
				reject_timers.remove(ob)
				break

def get_task_answer(user_id, task_id):
	user = Account.get(Account.acc_id == user_id)
	task = Task.get(Task.id == int(task_id))
	card_files_ans = Img.select().where((Img.status == 2)&(Img.task == int(task_id)))
	card_files_ans = list(map(lambda ob: ob.img_url,card_files_ans))
	if(len(card_files_ans)!=0):
		if((user.acc_type == 2 and task.status >= 2) or (user.acc_type == 1 and task.status >= 3)):
			return({
				'ok':True,
				'files':card_files_ans
			})
	return({'ok':False})

def get_task_card_imgs(task_id,stat):
	card_files = Img.select().where((Img.task == int(task_id)) & (Img.status == stat))
	return(len(card_files))

def check_user_last_time(user_id):
	user = Account.select().where(Account.acc_id == user_id)
	if(user.exists()):
		user = user.get()
		last = datetime.now()
		if(user.last_time != None):
			time_status = (user.last_time + timedelta(seconds=CALLDOWN))<last
		else:
			time_status = True
		if(time_status == True):
			user.last_time = last
			user.save()
		return({'ok':True,'status':time_status})
	return({'ok':True,'status':True})

def set_user_status(user_id, user_status):
	user = Account.select().where(Account.acc_id == user_id)
	if(user.exists()):
		user = user.get()
		if(user.acc_status != 'registration'):
			user.acc_status = user_status
			user.save()

def get_user_status(user_id):
	user = Account.select().where(Account.acc_id == user_id)
	if(user.exists()):
		user = user.get()
		return({'acc_status':user.acc_status, 'is_admin':user.is_admin})
	return({'acc_status':'none', 'is_admin':False})

def get_my_tasks(user_id):
	user = Account.select().where(Account.acc_id == user_id)
	if(user.exists() and user.get().acc_type != 0):
		user = user.get()
		if(user.acc_type == 1):
			tasks = Task.select().where(Task.user == user)
		elif(user.acc_type == 2):
			tasks = Task.select().where(Task.worker == user)
		tasks = list(map(lambda ob:[[f'{ob.title} - {ob.cost}RUB',f'get_task_card_{ob.id}']],tasks))
		return({'ok':True, 'tasks':tasks})
	return({'ok':False})

def user_check(user_id, user_tag):
	user = Account.select().where(Account.acc_id == user_id)
	if(user.exists() and user.get().acc_type != 0):
		return({
			'register':True,
			'acc_type':user.get().acc_type,
		})
	else:
		if(not user.exists()):
			Account.create(acc_id = user_id, acc_type = 0, acc_tag = user_tag, acc_status = 'registration')
		return({
			'register':False,
		})

def user_register(user_id, user_type):
	user = Account.select().where(Account.acc_id == user_id).get()
	if(user.acc_status == 'registration'):
		user.acc_type = user_type
		user.acc_status = 'waiting'
		user.save()
		return({'ok':True})
	return({'ok':False})
