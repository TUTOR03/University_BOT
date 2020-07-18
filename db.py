from peewee import *

db = SqliteDatabase('bot_q.db',pragmas={
	'foreign_keys': 1
	})

class BaseModel(Model):
	class Meta:
		database = db

# MODELS

class Account(BaseModel):
	acc_id = DecimalField()
	acc_type = DecimalField()# 0-registration 1-заказчик 2-исполнитель 
	acc_status = CharField()
	# last_time = TimeField()

class Task(BaseModel):
	title = CharField(null = True)
	cost = DecimalField(null = True)
	user = ForeignKeyField(model = Account, on_delete = 'CASCADE')
	status = DecimalField()
	worker = ForeignKeyField(model = Account, on_delete = 'CASCADE', null = True)

class Img(BaseModel):
	img_url = TextField()
	task = ForeignKeyField(model = Task, on_delete = 'CASCADE')

def inicialize_db():
	db.connect()
	db.create_tables([Account, Task, Img])
	# Task.create(title = 'Tsk_1', cost='300', user=1,status=0)
	# Img.create(img_url='test_url', task = 4)
	# Task.get(Task.id == 4).delete_instance()

	# Task.create(title = 'Tsk_2', cost='400', user=1,status=0)Ы

def get_tasks_list(user_id):
	user = Account.select().where(Account.acc_id == user_id)
	if(user.exists()):
		if(user.get().acc_type == 2):
			tasks = Task.select().where(Task.status == 1)
			tasks = list(map(lambda ob:[[f'{ob.title} - {ob.cost}RUB',f'task_card_{ob.id}']],tasks))
			return({'ok':True,'tasks':tasks})
	return({'ok':False})

def create_task(user_id, files, message):
	user = Account.select().where(Account.acc_id == user_id).get()
	task = Task.get((Task.user == user)&(Task.status == -1))
	title,cost = message
	task.title = title
	task.cost = int(cost)
	task.status = 0
	task.save()
	user.acc_status = 'waiting'
	user.save()
	Img.create(task = task, img_url = files[0]['file_id'])
	return({'ok':True})

def success_task_card(task_id):
	task = Task.get(Task.id == int(task_id))
	task.status = 1
	task.save()
	return({'ok':True})

def delete_task_card(task_id):
	task =	Task.get(Task.id == int(task_id))
	task.delete_instance()
	return({'ok':True})

def add_task_card_img(user_id, task_id, files):
	user = Account.select().where(Account.acc_id == user_id).get()
	user.acc_status = 'waiting'
	user.save()
	Img.create(task = int(task_id), img_url = files[0]['file_id'])
	return({'ok':True})

def add_task_card_img_status(user_id, task_id):
	user = Account.select().where(Account.acc_id == user_id).get()
	user.acc_status = f'adding_task_card_img_{task_id}'
	user.save()
	return({'ok':True})

def get_task_card(user_id, task_id):
	user = Account.select().where(Account.acc_id == user_id).get()
	task = Task.get(Task.id == int(task_id))
	if(user.acc_type == 1):
		if(task.status == 0):
			status = 'Ожидает подтверждения'
			keyboard = [
				[['Добавить изображение',f'add_task_card_img_{task.id}'],['Удалить',f'delete_task_card_{task.id}']],
				[['Подтвердить задание',f'success_task_card_{task.id}']]
			]
		reply_mes = f'{task.title}\n{task.cost}RUB\nСтатус:{status}'
		return({
			'ok':True,
			'reply_mes':reply_mes,
			'keyboard':keyboard
		})

def create_task_model(user_id):
	user = Account.select().where(Account.acc_id == user_id)
	if(user.exists()):
		user = user.get()
		if(user.acc_type == 1):
			temp_task = Task.select().where((Task.user == user) & (Task.status == -1))
			if(not temp_task.exists()):
				Task.create(user = user, status = -1)
			user.acc_status = 'adding_task'
			user.save()
			return({'ok':True})
	return({'ok':False})

def set_user_status(user_id, user_status):
	user = Account.select().where(Account.acc_id == user_id)
	if(user.exists()):	
		user = user.get()
		user.acc_status = user_status
		user.save()

def get_user_status(user_id):
	user = Account.select().where(Account.acc_id == user_id)
	if(user.exists()):	
		return(user.get().acc_status)
	return('none')

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

def user_check(user_id):
	user = Account.select().where(Account.acc_id == user_id)
	if(user.exists() and user.get().acc_type != 0):
		return({
			'register':True,
			'acc_type':user.get().acc_type,
		})
	else:
		if(not user.exists()):
			Account.create(acc_id = user_id, acc_type = 0, acc_status = 'registration')
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

