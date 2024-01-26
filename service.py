from datetime import timedelta, datetime
from pprint import pprint
from typing import List, Dict, Any
import time


from moysklad.exceptions import ApiResponseException
from moysklad.queries import Expand, Filter, Select, Query
from moysklad.api import MoySklad

from config import accounts, my_params


class Loader:
    def __init__(self, params=None):
        self.limit = 100
        self.offset = 0
        self.scanned_id = ''
        self.time_delta_before_start = 24
        self.time_delta_before_finish = 12
        self.expand = []
        self.entity = ''
        self.client = None
        self.methods = None
        if params:
            # Установка параметров, как атрибутов
            for key, value in params.items():
                setattr(self, key, value)

    def init_ms(self, account):
        """Инициализация учетной записи Мой Склад"""

        self.offset = 0
        self.scanned_id = account['scanned_id']
        sklad = MoySklad.get_instance(
            account['moysklad_login'], account['moysklad_password'], account['moysklad_token']
        )
        self.client = sklad.get_client()
        self.methods = sklad.get_methods()

    def get_formatted_dates(self) -> (str, str):
        start_date = (datetime.now()
                      - timedelta(hours=self.time_delta_before_start)).strftime('%Y-%m-%d %H:%M')
        finish_date = (datetime.now()
                       - timedelta(hours=self.time_delta_before_finish)).strftime('%Y-%m-%d %H:%M')
        return start_date, finish_date

    def get_response(self):
        """Получения ответа от Мой Склад"""

        try:
            start_date, finish_date = self.get_formatted_dates()
            print(start_date)
            print(finish_date)
            response = self.client.get(
                method=self.methods.get_list_url(self.entity),
                query=Query(
                    Filter().gte('updated', start_date) + Filter().lte('updated', finish_date),
                    Select(limit=self.limit, offset=self.offset),
                    Expand(*self.expand)
                )
            )

            return response

        except ApiResponseException as ex:
            print(f"Error fetching orders: {ex}")
            return None

    def formation_full_dataset(self, test_iteration: bool = False) -> List[Dict[str, Any]]:
        """Формирования полного датасета с Мой Склад (обход по offset)"""
        result = []
        while True:
            response = self.get_response()
            if not response:
                break
            part_dataset = self.formation_part_dataset(response.rows)
            result.extend(part_dataset)
            self.offset += self.limit

            if not ('nextHref' in response.meta) or test_iteration:
                break

        return result

    def formation_part_dataset(self, response_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Формирование данных из одного ответа Мой Склад"""

        part_dataset = []
        for order in response_rows:
            if order['state']['name'] not in ['Ожидает сборки', 'Отменен', 'Новый', 'Подтвержден']:
                processed_order = self.process_order(order)
                part_dataset.append(processed_order)
        return part_dataset

    def process_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        order_data = {
            'order_code': order.get('name'),
            'attributes': order.get('attributes',
                                    [{'value': None, 'id': 'bb89136d-7a4f-11ed-0a80-03dc00017d69'}]),
            'sum': order['sum'] / 100,
            'scanned': None,
            'updated': order.get('updated'),
            'delivery': 0
        }

        for attribute in order_data['attributes']:
            if attribute.get('id') == self.scanned_id:
                order_data['scanned'] = attribute['value']
                break

        for position in order.get('positions', {}).get('rows', []):
            assortment = position.get('assortment', {})
            meta = assortment.get('meta', {})
            if meta.get('type') == 'service':
                price = position.get('price', 0)
                order_data['sum'] = order_data.get('sum', 0) - price / 100

        order_data.pop('attributes', None)
        return order_data

    def formation_notification_list(self):
        notification_list = []
        for account in accounts:
            self.init_ms(account)
            full_dataset = self.formation_full_dataset()
            for order in full_dataset:
                if order['scanned'] is None or order['scanned'] != order['sum']:
                    order['account'] = account['name']
                    notification_list.append(order)
        return notification_list

    def formation_text_message(self):
        notification_list = self.formation_notification_list()
        report_text = 'Заказы по которым обнаружены расхождения:\n'
        if len(notification_list) == 0:
            report_text = 'Расхождений в заказах не найдено.\n'
        for order in notification_list:
            report_text += f"\n{order['order_code']}  - {order['account']}\n"

        return report_text



start_time = time.time()

loader_order = Loader(params=my_params)
list_notification = loader_order.formation_notification_list()

pprint(list_notification, indent=4)
print(len(list_notification))

end_time = time.time()
duration = end_time - start_time
print(f'Duration: {duration} seconds')
