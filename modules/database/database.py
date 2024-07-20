import aiosqlite


class Database:

    async def __aenter__(self):
        self.connection = await aiosqlite.connect('scrapper_users.db')
        async with self.connection.cursor() as cursor:
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    data TEXT
                )
            ''')
            await self.connection.commit()
            await cursor.execute('''
                            CREATE TABLE IF NOT EXISTS products_history (
                                product_id INTEGER PRIMARY KEY,
                                product_data TEXT
                            )
                        ''')
            await self.connection.commit()
            print("Менеджер БД начал свою работу")
            return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.connection.close()
        print("Менеджер БД завершил свою работу")

    async def add_user(self, user_id: int, data: str = "{}"):
        async with self.connection.cursor() as cursor:
            await cursor.execute('INSERT OR IGNORE INTO users (id, data) VALUES (?, ?)', (user_id, data))
            await self.connection.commit()

    async def update_user_data(self, user_id: int, new_data: str):
        async with self.connection.cursor() as cursor:
            await cursor.execute('UPDATE users SET data = ? WHERE id = ?', (new_data, user_id))
            await self.connection.commit()

    async def get_user_data(self, user_id: int):
        async with self.connection.cursor() as cursor:
            await cursor.execute('SELECT data FROM users WHERE id = ?', (user_id, ))
            user_data = await cursor.fetchone()
            aiter(cursor)
            return user_data[0]

    async def put_product_to_history(self, product_id: int, product_data: str):
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                'INSERT OR IGNORE INTO products_history (product_id, product_data) VALUES (?, ?)',
                (product_id, product_data)
            )
            await self.connection.commit()

    async def get_product_from_history(self, product_id: int):
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM products_history WHERE product_id = ?",
                (product_id, )
            )
            data = await cursor.fetchone()
            return data if data else None

    def __del__(self):
        print(f"Объект {self.__class__.__name__} Удален")
