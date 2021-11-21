import random
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import vk
import database


class VKfinder:
    """Класс для работы с ботом VK VKfinder"""
    def __init__(self):
        self.g_token = get_group_token()
        self.s_token = get_user_token()
        self.vk1 = vk_api.VkApi(token=self.g_token)
        self.vk2 = vk.VK(s_token=self.s_token)
        self.db_status = self.db_status()
        if self.db_status:
            self.db = database.Database()
        self.longpoll = VkLongPoll(self.vk1)

    def db_status(self):
        """Проверяет доступность базы данных"""
        try:
            db = database.Database()
            db.get_table_names()
            return True
        except:
            return False

    def write_msg(self, user_id, message, photos=None):
        """
        отправка сообщения пользователю в чат
        :param user_id: id пользователя
        :param message: сообщение для пользователя
        :param photos: фотографии для пользователя
        """
        if photos == None:
            self.vk1.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': random.randrange(10 ** 7)})
        else:
            self.vk1.method('messages.send', {'peer_id': user_id, 'message': message, 'attachment': photos, 'random_id': random.randrange(10 ** 7)})

    def start(self):
        """
        слушает чат, приветствует пользователя и инициирует поиск ему пары
        """
        if self.db_status:
            self.db.create_tables()
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    request = event.text.lower().strip()
                    if request in ['start', 'начать', 'привет']:
                        user_info = self.vk2.get_user_info(event.user_id)
                        user_firstname = user_info['response'][0]['first_name']
                        self.write_msg(event.user_id, f'Привет, {user_firstname}! Хочешь, найду тебе пару?')
                        self.find_a_pair()

    def find_a_pair(self):
        """
        основная логика программы, связывающая воедино большую часть методов и функций
        """
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    request = event.text.lower().strip()
                    if request in ['хочу', 'найди', 'да', 'валяй', 'найди мне пару']:
                        user_info = self.vk2.get_user_info(event.user_id)
                        id_vk_user = user_info['response'][0]['id']
                        vk_user_params = [id_vk_user]
                        print('db_status =', self.db_status)
                        if not self.db_status:
                            self.write_msg(event.user_id, f'Упс! Что-то пошло не так и наша база данных недоступна. Результаты поиска могут повторяться.')

                        try:
                            sex_vk_user = user_info['response'][0]['sex']
                            vk_user_params.append(sex_vk_user)
                        except:
                            self.write_msg(event.user_id, f'Вы мужчина или женщина?')
                            self.req_sex(vk_user_params)

                        try:
                            age_vk_user = user_info['response'][0]['bdate'][-4:]
                            vk_user_params.append(age_vk_user)
                        except:
                            message = 'В каком году ты родилась?' if vk_user_params[1] == 1 else 'В каком году ты родился?'
                            self.write_msg(event.user_id, f'{message}')
                            self.req_age(vk_user_params)

                        try:
                            city_vk_user = user_info['response'][0]['city']['id']
                            vk_user_params.append(city_vk_user)
                        except:
                            self.write_msg(event.user_id, f'В каком городе ты живешь?')
                            self.req_city(vk_user_params)

                        if self.db_status:
                            if not self.db.find_in_users(vk_user_params[0]):
                                self.db.add_user(vk_user_params[0], vk_user_params[2], vk_user_params[1], vk_user_params[3])

                        vk_user_params = [vk_user_params[0], 1 if vk_user_params[1] == 2 else 2, vk_user_params[2], vk_user_params[3]]
                        photos = self.get_photos_random_id_found(vk_user_params)
                        if photos == 'Список пуст! Не удалось никого найти.':
                            self.write_msg(event.user_id, f'Не удалось никого найти. Попробуй позднее.')
                        else:
                            id_vk_found = photos[0]
                            photos = photos[1]
                            found_info = self.vk2.get_user_info(id_vk_found)
                            found_firstname = found_info['response'][0]['first_name']
                            if 'relation' in found_info['response'][0].keys():
                                found_status = found_info['response'][0]['relation']
                            else:
                                found_status = 9
                            self.write_msg(event.user_id, f'Знакомься, это {found_firstname} (https://vk.com/id{id_vk_found})', photos)
                            self.write_msg(event.user_id, f'Похоже на твою половинку, как считаешь?')
                            self.yes_or_no(vk_user_params[0], id_vk_found, found_status)
                        break

    def req_sex(self, vk_user_params):
        """
        добавляет пол в список параметров пользователя
        :param vk_user_params: список параметров
        """
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    request = event.text.lower().strip()
                    if request in ['мужчина', 'м', 'муж']:
                        vk_user_params.append(2)
                    elif request in ['женщина', 'ж', 'жен']:
                        vk_user_params.append(1)
                        break

    def req_age(self, vk_user_params):
        """
        добавляет год рождения в список параметров пользователя
        :param vk_user_params: список параметров
        """
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    request = event.text.lower().strip()
                    vk_user_params.append(int(request))
                    break

    def req_city(self, vk_user_params):
        """
        добавляет город в список параметров пользователя
        :param vk_user_params: список параметров
        """
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    request = event.text.lower().strip()
                    vk_user_params.append(self.vk2.get_city_id(request))
                    break

    def get_photos_random_id_found(self, vk_user_params):
        """
        Ищет случайного пользователя VK по параметрам и 3 его фотографии
        :param vk_user_params: параметры пользователя, по которым осуществляется поисковый запрос
        :return: список с id найденного случайного пользователя и 3 его фотографии в формате photo<owner.id>_<photo_id>
        """
        founds = self.vk2.search_users(vk_user_params[1], vk_user_params[2], vk_user_params[3])
        count = len(founds)
        for i in range(count):

            if not founds:
                return 'Список пуст! Не удалось никого найти.'

            found = founds[random.randint(0, len(founds) - 1)]
            if self.db_status:
                if self.db.find_in_blacklist(vk_user_params[0], found):
                    founds.remove(found)
                    print('УДАЛЕНА анкета из ЧС')
                else:
                    if 'error' not in self.get_photos_id_found(found, founds):
                        return self.get_photos_id_found(found, founds)
            else:
                if 'error' not in self.get_photos_id_found(found, founds):
                    return self.get_photos_id_found(found, founds)

    def get_photos_id_found(self, id_vk_found, founds):
        """
        ищет, упаковывает фотографии пользователя. если при поиске вернулась ошибка, удаляет id из списка.
        :param id_vk_found: id пользователя
        :param founds: список id пользователей
        :return: error или список с id пользователя и 3 его фотографии в формате photo<owner.id>_<photo_id>
        """
        photos = self.vk2.find_user_photos(id_vk_found)
        if 'error' in photos:
            founds.remove(id_vk_found)
        else:
            photos = list(f'photo{photo["owner_id"]}_{photo["id"]}' for photo in photos)
            photos = ','.join(photos)
            return [id_vk_found, str(photos)]

    def yes_or_no(self, id_vk_user, id_vk_found, id_vk_found_status):
        """
        На основании ответа пользователя добавляем найденный профиль в избранное или черный список
        :param id_vk_user: пользователь для которого ищем
        :param id_vk_found: пользователь которого нашли
        :param id_vk_found_status: семейное положение найденного пользователя
        """
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    request = event.text.lower().strip()
                    if request in ['нет', 'не похоже']:
                        if self.db_status:
                            if not self.db.find_in_blacklist(id_vk_user, id_vk_found):
                                self.db.add_in_blacklist(id_vk_user, id_vk_found, id_vk_found_status)
                        self.write_msg(event.user_id, f'Не отчаивайся! Просто, попробуй еще разок)')
                        self.write_msg(event.user_id, f'P.S. Если хочешь повторить поиск, напиши: Привет')
                        break
                    elif request in ['да', 'похоже']:
                        if self.db_status:
                            if not self.db.find_in_favorites(id_vk_user, id_vk_found):
                                self.db.add_in_favorites(id_vk_user, id_vk_found, id_vk_found_status)
                        self.write_msg(event.user_id, f'Поздравляю, дальше все в твоих руках!')
                        self.write_msg(event.user_id, f'P.S. Если хочешь повторить поиск, напиши: Привет')
                        break


def get_group_token():
    """
    считываем токен группы из файла
    :return: токен группы
    """
    with open('vk_group_token.txt', "r") as file:
        for line in file:
            token = line
    return token


def get_user_token():
    """
    считываем токен пользователя из файла
    :return: токен пользователя
    """
    with open('vk_standalone_token.txt', "r") as file:
        for line in file:
            token = line
    return token


if __name__ == '__main__':
    stop = False
    while stop == False:
        finder = VKfinder()
        finder.start()
        stop = True
