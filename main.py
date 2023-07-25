import os
import json
import asyncio
import websockets as ws

from charge_point import ChargePoint

#   2 - CALL       (Client-to-server)
#   3 - CALLRESULT (Server-to-client)
#   4 - CALLERROR  (Server-to-client)

# Структура сообщения CALL
# [<MessageTypeId>,"<UniqueId>","<Action>",{<Payload>}]
# MessageTypeId=2 - идентификатор типа сообщения
# UniqueId - уникальный идентификатор максимум 36 символов
# Action - текстовое имя типа сообщения
# Payload - полезная нагрузка (данные сообщения)
# Пример сообщения:
# [
#   2,
#   "7a3621e6-2c72-42fc-afce-4c7f2c23248b",
#   "BootNotification",
#   {
#       "chargePointModel":"FMA",
#       "chargePointVendor":"NSTU"
#   }
# ]

# Структура сообщения CALLRESULT
# [<MessageTypeId>,"<UniqueId>",{<Payload>}]
# MessageTypeId=3 - идентификатор типа сообщения
# UniqueId - уникальный идентификатор максимум 36 символов
# Payload - полезная нагрузка (данные сообщения)
# Пример сообщения ответа ("BootNotification"):
# [3,
#  "19223201",
#  {
#   "status":"Accepted",
#   "currentTime":"2013-02-01T20:53:32.486Z",
#   "heartbeatInterval":300}
# ]

# Структура сообщения CALLERROR
# [<MessageTypeId>,"<UniqueId>","<ErrorCode>","<ErrorDescribtion>"{<ErrorDetails>}]
# MessageTypeId=3 - идентификатор типа сообщения
# UniqueId - уникальный идентификатор максимум 36 символов
# ErrorCode - код(номер) ошибки
# ErrorDescribtion - описание ошибки
# ErrorDetails - (данные сообщения) поле может быть пустым
# Сообщение отправляется в 2-х случаях:
#  - Ошибка во время передачи сообщений. 
#  - Сообщение было получено, но формат был неправильным.

SCHEMAS_FOLDER = '\schemas\json'
SERVER_IP = '192.168.1.20'
SERVER_PORT = '8180'
SERVER_WS_ADDRESS = 'ws://' + SERVER_IP + ':' + SERVER_PORT + '/steve/websocket/CentralSystemService/FMA'
#'ws://192.168.1.20:8180/steve/websocket/CentralSystemService/' + CHARGE_POINT_NAME

async def main():
    cwd = os.getcwd()
    schemas_dir = cwd + SCHEMAS_FOLDER
    print(f'schemas_dir: {schemas_dir}')
    schemas_files = [f for f in os.listdir(schemas_dir) if os.path.isfile(os.path.join(schemas_dir, f))]
    # print(f'{schemas_files}')
    if 'Authorize.json' in schemas_files:
        path = schemas_dir + '\Authorize.json'
        with open(path, 'rt') as f:
            Authorize = json.load(f)
            f.close()

    print(f'{Authorize.get("properties").get("idTag")}')

    async with ws.connect(SERVER_WS_ADDRESS, subprotocols=['ocpp1.6']) as socket:
        cp = ChargePoint('FMA', socket)
        await asyncio.gather(
            cp.start(),
            cp.BootNotificationSend()
        )


# [
#   2,
#   "7a3621e6-2c72-42fc-afce-4c7f2c23248b",
#   "BootNotification",
#   {
#       "chargePointModel":"FMA",
#       "chargePointVendor":"NSTU"
#   }
# ]


# [ 
#   3,
#   "4c6db77f-4785-4baa-9aab-c776033ad5fe",
#   {
#       "status":"Accepted",
#       "currentTime":"2023-07-22T02:16:40.694Z",
#       "interval":14400
#   }
# ]
if __name__ == '__main__':
    asyncio.run(main())