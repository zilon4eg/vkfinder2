import sqlalchemy
import datetime


class Database:
    """Класс для работы с базой данных"""
    db_name = 'vkfinder2'
    db_user_name = 'vkfinder'
    db_user_pass = 'pass'
    db_address = 'localhost:5432'
    db_type = 'postgresql'
    db = f'{db_type}://{db_user_name}:{db_user_pass}@{db_address}/{db_name}'

    def __init__(self):
        engine = sqlalchemy.create_engine(self.db)
        self.connection = engine.connect()
        self.inspector = sqlalchemy.inspect(engine)

    def get_table_names(self):
        """возвраает список имен таблиц базы данных"""
        return self.inspector.get_table_names()

    def create_tables(self):
        """создаем таблицуы, если не существуют"""

        if 'sex' not in self.inspector.get_table_names():
            self.connection.execute('''
                CREATE TABLE sex(
                id serial PRIMARY KEY,
                title TEXT UNIQUE NOT NULL
                );
                INSERT INTO sex(title) VALUES('женский');
                INSERT INTO sex(title) VALUES('мужской');
                INSERT INTO sex(title) VALUES('любой');
            ''')

        if 'status' not in self.inspector.get_table_names():
            self.connection.execute('''
                CREATE TABLE status(
                id serial PRIMARY KEY,
                title TEXT UNIQUE NOT NULL
                );
                INSERT INTO status(title) VALUES('не женат (не замужем)');
                INSERT INTO status(title) VALUES('встречается');
                INSERT INTO status(title) VALUES('помолвлен(-а)');
                INSERT INTO status(title) VALUES('женат (замужем)');
                INSERT INTO status(title) VALUES('всё сложно');
                INSERT INTO status(title) VALUES('в активном поиске');
                INSERT INTO status(title) VALUES('влюблен(-а)');
                INSERT INTO status(title) VALUES('в гражданском браке');
                INSERT INTO status(title) VALUES('не указано');
            ''')

        if 'users' not in self.inspector.get_table_names():
            self.connection.execute('''
                CREATE TABLE users(
                id serial PRIMARY KEY,
                id_vk_user INTEGER UNIQUE NOT NULL,
                age INTEGER NOT NULL,
                sex INTEGER NOT NULL REFERENCES sex(id),
                city INTEGER NOT NULL,
                date TEXT NOT NULL
                );
            ''')

        if 'blacklist' not in self.inspector.get_table_names():
            self.connection.execute('''
                CREATE TABLE blacklist(
                id serial PRIMARY KEY,
                id_vk_user INTEGER NOT NULL REFERENCES users(id),
                id_vk_unloved INTEGER NOT NULL,
                status INTEGER REFERENCES status(id),
                date TEXT NOT NULL
                );
            ''')

        if 'favorites' not in self.inspector.get_table_names():
            self.connection.execute('''
                CREATE TABLE favorites(
                id serial PRIMARY KEY,
                id_vk_user INTEGER NOT NULL REFERENCES users(id),
                id_vk_favorite INTEGER NOT NULL,
                status INTEGER REFERENCES status(id),
                date TEXT NOT NULL
                );
            ''')

        if 'found' not in self.inspector.get_table_names():
            self.connection.execute('''
                CREATE TABLE found(
                id serial PRIMARY KEY,
                id_vk_user INTEGER NOT NULL REFERENCES users(id),
                id_vk_search INTEGER NOT NULL,
                age INTEGER NOT NULL,
                sex INTEGER NOT NULL REFERENCES sex(id),
                city INTEGER NOT NULL,
                status INTEGER NOT NULL REFERENCES status(id),
                date TEXT NOT NULL
                );
            ''')

    def find_in_users(self, id_vk_user):
        """
        проверяет, есть ли запрашиваемый пользователь в таблице 'users'
        :param id_vk_user: id пользователя
        :return: True or False
        """
        if self.connection.execute(f'SELECT id_vk_user FROM users WHERE id_vk_user = {id_vk_user};').fetchall():
            return True
        else:
            return False

    def find_in_blacklist(self, id_vk_user, id_vk_unloved):
        """
        проверяет, есть ли запрашиваемый пользователь в таблице 'blacklist'
        :param id_vk_user: id пользователя для которого ищем пару
        :param id_vk_unloved: id пользователя которого добавили в черный список
        :return: True or False
        """
        if self.connection.execute(f'''
            SELECT u.id_vk_user, b.id_vk_unloved FROM blacklist b
            JOIN users u ON u.id = b.id_vk_user
            WHERE b.id_vk_unloved = {id_vk_unloved}
            AND u.id_vk_user = {id_vk_user};
        ''').fetchall():

            return True
        else:
            return False

    def find_in_favorites(self, id_vk_user, id_vk_favorite):
        """
        проверяет, есть ли запрашиваемый пользователь в таблице 'favorites'
        :param id_vk_user: id пользователя для которого ищем пару
        :param id_vk_favorite: id пользователя которого добавили в избранное
        :return: True or False
        """
        if self.connection.execute(f'''
            SELECT u.id_vk_user, f.id_vk_favorite FROM favorites f
            JOIN users u ON u.id = f.id_vk_user
            WHERE f.id_vk_favorite = {id_vk_favorite}
            AND u.id_vk_user = {id_vk_user};
        ''').fetchall():
            return True
        else:
            return False

    def add_user(self, id_vk_user, age, sex, city):
        """
        добавляем пользователя с параметрами в db
        :param id_vk_user: id пользователя
        :param sex: пол
        :param age: год рождения
        :param city: город проживания
        """
        if not self.find_in_users(id_vk_user):
            self.connection.execute(f'INSERT INTO users(id_vk_user, age, sex, city, date) VALUES({id_vk_user}, {age}, {sex}, {city}, \'{str(datetime.datetime.today())}\');')

    def add_in_blacklist(self, id_vk_user, id_vk_unloved, id_vk_unloved_status):
        """
        добавляем пользователя в 'черный список'
        :param id_vk_user: id пользователя для кого ищем
        :param id_vk_unloved: id пользовтеля, которого нашли
        :param id_vk_unloved_status: статус пользователя
        """
        if not self.find_in_blacklist(id_vk_user, id_vk_unloved):
            id_id_vk_user = self.connection.execute(f'SELECT id FROM users WHERE id_vk_user = {id_vk_user};').fetchall()
            id_id_vk_user = list(id_id_vk_user[0])[0]
            self.connection.execute(f'INSERT INTO blacklist(id_vk_user, id_vk_unloved, status, date) VALUES({id_id_vk_user}, {id_vk_unloved}, {id_vk_unloved_status}, \'{str(datetime.datetime.today())}\');')

    def add_in_favorites(self, id_vk_user, id_vk_favorite, id_vk_favorite_status):
        """
        добавляем пользователя в 'избранное'
        :param id_vk_user: id пользователя для кого ищем
        :param id_vk_favorite: id пользовтеля, которого нашли
        :param id_vk_favorite_status: статус пользователя
        """
        if not self.find_in_favorites(id_vk_user, id_vk_favorite):
            id_id_vk_user = self.connection.execute(f'SELECT id FROM users WHERE id_vk_user = {id_vk_user};').fetchall()
            id_id_vk_user = list(id_id_vk_user[0])[0]
            self.connection.execute(f'INSERT INTO favorites(id_vk_user, id_vk_favorite, status, date) VALUES({id_id_vk_user}, {id_vk_favorite}, {id_vk_favorite_status}, \'{str(datetime.datetime.today())}\');')


if __name__ == '__main__':
    pass
