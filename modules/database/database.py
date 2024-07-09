import aiosqlite


class Database:

    async def __aenter__(self):
        self.connection = await aiosqlite.connect('scrapper_users.db')
        self.cursor = await self.connection.cursor()
        await self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                data TEXT
            )
        ''')
        await self.connection.commit()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.cursor.close()
        await self.connection.close()

    async def add_user(self, user_id, data=""):
        await self.cursor.execute('INSERT OR IGNORE INTO users (id, data) VALUES (?, ?)', (user_id, data))
        await self.connection.commit()

    async def update_user_data(self, user_id, new_data):
        await self.cursor.execute('UPDATE users SET data = ? WHERE id = ?', (new_data, user_id))
        await self.connection.commit()

    async def get_user_data(self, user_id):
        async with self.connection.cursor() as cursor:
            await cursor.execute('SELECT data FROM users WHERE id = ?', (user_id, ))
            user_data = await cursor.fetchone()
            print(user_data[0], "в геттере БД")
            return user_data[0]
