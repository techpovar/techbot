import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from random import randint, choices

def init():
	global mode, vkEventData
	"""
		Mode используется для удобства запуска бота, а также на случай если
	придется запустить бота в отдельной группе не вписывая каждый раз новый
	токен и адрес группы.
		VkEventData сделан для того, чтобы было удобнее в глобальной среде
	получить доступ ко всему входящему сообщению. Например получить список вложений.
	"""
	mode = 'основная_группа'
	vkEventData = None
	return None

def getTokenIdByName(obj):
	if type(obj) != type(str()): return False, 0
	modes = {
		#    НАЗВАНИЕ      АДРЕС ГРУППЫ                                          ТОКЕН
		'основная_группа': {'123456789': '123sahd123983sakd09123kh'},
	}
	if obj not in modes:
		return False, 1
	for modename in modes.keys():
		for token_obj in modes.get(modename):
			if modename == obj.lower():
				return {
					'id': token_obj,
					'token': modes.get(modename).get(token_obj),
				}

def textHandler(text):
	"""
		Это обработчик сообщения и сравнения. Дробит сообщение, сравнивает
	каждую часть и выбирает самый лучший вариант.
		Как результат работы возвращает команду для запуска и опции.
	"""
	input_layer = text
	input_layer_parts = input_layer.lower().split()
	length_of_input_layer_parts = len(input_layer_parts)
	command = None
	command_options = None
	for cortege in Commands:
		cortege = tuple(reversed(sorted(cortege, key=len)))
		for sentence in cortege:
			if sentence in [' '.join(input_layer_parts[:len(sentence.split(' '))])]:
				command = sentence.rstrip()
				if len(command.split(' ')) != len(input_layer_parts):
					command_options = input_layer_parts[len(command.split(' ')):]
				else:
					command_options = (None)
	if (command == None) and (command_options == None):
		return False
	else:
		return {
			'command': str(command),
			'options': command_options,
		}

def executeDef(id, uid, text):
	"""
		Исполнитель запроса, на вход принимает словарь с командой и опцией.
	"""
	data = textHandler(text)
	if data != False:
		for key in Commands.keys():
			if data['command'] in key:
				Commands[key](id, uid, data['options'])
	return False

def getFieldsByGroup(fields):
	"""
		Позволяет получить данные о текущей группе по полям - экранное имя, фотографию и т.д.
	"""
	result = vk_session.method('groups.getById', {
		'group_id': bot_data.get('id'),
		'fields': str(fields)
		}
	)
	result = result[0][fields]
	return result

def sendMessage(id, uid, text = None):
	"""
		Отправляет сообщение, поддерживает отправку как в личные сообщения так и в беседы,
	в последнем типе может потребоваться доступ к переписке или админка (!).
	"""
	post = {}
	if vkEventData:
		if vkEventData.from_user:
			post['user_id'] = uid
		else:
			post['chat_id'] = id
	else:
		if (str(id) == 'None') or (id == None):
			post['user_id'] = uid
		else:
			post['chat_id'] = id
	post['message'] = text
	post['random_id'] = int(generateRandomId())
	return vk_session.method('messages.send', post)

"""
Генерирует случайное число для 32bit-х систем.
"""
def generateRandomId(): return randint(-2147483648, +2147483647)

# Команды для реакции

def bot(id, uid, text):
	"""
		Отправляет сообщение со случайным текстом из переменной-списка answers.
	"""
	answers = [
		'Я тут!',
		'Здесь!',
		'Да-да?'
	]
	sendMessage(id, uid, choices(answers, k = 1)[0])

def bot_flip(id, uid, text):
	"""
		Игра "Орёл или решка"
	"""
	result = 0
	for _ in range(731):
		result = randint(0, 1)
	sendMessage(id, uid, 'Выпал %s!' % ('орёл' if result else 'решка'))

init()

"""
	Список ассоциаций и указатель для функции.
"""
Commands = {
	('бот', 'bot'): bot,
	('подкинь монетку', 'монетка'): bot_flip,
}

"""
Авторизируем бота
"""
bot_data = getTokenIdByName(mode)
vk_session = vk_api.VkApi(token = bot_data.get('token'))
longpoll = VkBotLongPoll(vk_session, bot_data.get('id'))

"""
Префикс группы. Позволяет делать отклик на обращение прямое или косвенное.
"""
group_prefix = f'[club{bot_data.get("id")}|@{getFieldsByGroup("screen_name")}]'

if __name__ == '__main__':
	for event in longpoll.listen():
		if event.type == VkBotEventType.MESSAGE_NEW:
			if event.from_chat or event.from_user:
				Message = str(event.obj.message['text'].lower())
				id, uid = event.chat_id, event.obj.message['from_id']
				if Message and uid > 1:
					# if db_editor.existsById(uid) == False:
					# 	registerNewUser(id, getUserNameById(uid), uid)
					if Message[:len(group_prefix)] == group_prefix:
						Message = Message[len(group_prefix):].lstrip(' ')
					executeDef(id, uid, Message)