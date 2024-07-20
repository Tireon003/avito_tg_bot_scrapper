import pandas as pd
import datetime as dt


class Table:

    def __init__(self):
        self.__table = pd.DataFrame(
            columns=["ID", "TITLE", "DATE", "PRICE", "ADDRESS", "CATEGORIES", "DESCRIPTION","VIEWS", "SPECS"]
        )

    @staticmethod
    def verify_data(data: dict):
        if not isinstance(data, dict):
            raise TypeError("Параметр должен иметь тип данных <dict>")
        else:
            required_keys = ["ID", "TITLE", "DATE", "PRICE", "ADDRESS", "CATEGORIES", "DESCRIPTION", "VIEWS", "SPECS"]
            if len(required_keys) != len(data.keys()):
                raise ValueError("В таблице есть отсутствующие либо лишние столбцы")
            else:
                for key in required_keys:
                    if key not in data.keys():
                        raise ValueError("Данные имеют неверный формат или имена столбцов")
                else:
                    return data

    def push(self, data: dict):
        self.__table = self.__table._append(self.verify_data(data), ignore_index=True)

    def get_csv(self):
        file_path = f'./output_tables/csv_output_{dt.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.csv'
        self.__table.to_csv(file_path, sep=";")
        return file_path

