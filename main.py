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

CHARGE_POINT_NAME = 'FMA'
CHARGE_POINT_VENDOR = 'NSTU'
SCHEMAS_FOLDER = '\schemas\json'
SERVER_IP = '192.168.1.20'
SERVER_PORT = '8180'
SERVER_WS_ADDRESS = 'ws://' + SERVER_IP + ':' + SERVER_PORT + '/steve/websocket/CentralSystemService/FMA'
#'ws://192.168.1.20:8180/steve/websocket/CentralSystemService/' + CHARGE_POINT_NAME
SETTINGS_FILE_NAME = 'settings.json'

SETTINGS = {
            'SERVER_IP' : SERVER_IP, 
            'SERVER_PORT' : SERVER_PORT, 
            'CHARGE_POINT_NAME' : CHARGE_POINT_NAME,
            # 'CHARGE_POINT_VENDOR' : CHARGE_POINT_VENDOR,
            }

def GetSettings():
    from pathlib import Path
    global SETTINGS
    file_exist = Path(SETTINGS_FILE_NAME)
    if file_exist.is_file():
        print(f'exist')
        file = open(SETTINGS_FILE_NAME, 'r', encoding = "utf-8")
    else:
        print(f'not exist')
        file = open(SETTINGS_FILE_NAME, 'w', encoding = "utf-8")
        json_settings = json.dumps(SETTINGS, indent = 2)
        file.write(json_settings)
        file.close()
        file = open(SETTINGS_FILE_NAME, 'r', encoding = "utf-8")

    try:
        load_settings = json.loads(file.read())
        SETTINGS = load_settings
    except:
        file.close()
        file = open(SETTINGS_FILE_NAME, 'w', encoding = "utf-8")
        json_settings = json.dumps(SETTINGS, indent = 2)
        file.write(json_settings)

    file.close()

class Settings:
    CHARGE_POINT_NAME = 'ChargePointName'
    CHARGE_POINT_VENDOR = 'Vendor'
    SCHEMAS_FOLDER = '\schemas\json'
    SERVER_IP = '192.168.1.20'
    SERVER_PORT = '8180'
    SETTINGS_FILE_NAME = 'settings.json'
    SETTINGS = {
                'SERVER_IP' : SERVER_IP, 
                'SERVER_PORT' : SERVER_PORT, 
                'CHARGE_POINT_NAME' : CHARGE_POINT_NAME,
                # 'CHARGE_POINT_VENDOR' : CHARGE_POINT_VENDOR,
                }

    def __init__(self, path: str = '') -> None:
        self.path = Settings.SETTINGS_FILE_NAME # path + '\\' + Settings.SETTINGS_FILE_NAME
        print(self.path)
        self.settings = Settings.SETTINGS
        if self.IsFileExist(self.path):
            if self.ReadSettingsFromFile(self.path) == False:
                self.CreateNewFile(self.path)
        else:
            self.CreateNewFile(self.path)

    def IsFileExist(self, path: str) -> bool:
        from pathlib import Path
        file_exist = Path(path)
        if file_exist.is_file():
            print(f'exist')
            return True
        else:
            print(f'not exist')
            return False

    def CreateNewFile(self,  path: str):
        file = open(path, 'w', encoding = "utf-8")
        json_settings = json.dumps(Settings.SETTINGS, indent = 2)
        file.write(json_settings)
        file.close()
        file = open(path, 'r', encoding = "utf-8")

    def ReadSettingsFromFile(self, path: str) -> bool:
        res = True
        file = open(path, 'r', encoding = "utf-8")
        try:
            load_settings = json.loads(file.read())
            self.settings = load_settings
            # self.FileDataIsValid(path)
        except:
            res = False
        file.close()
        return res

    def FileDataIsValid(self) -> bool:
        pass

    def GetChargePointName(self) -> str:
        return self.settings['CHARGE_POINT_NAME']
    def GetWsServerAddress(self) -> str:
        addr = 'ws://' 
        addr += self.settings['SERVER_IP'] 
        addr += ':' 
        addr += self.settings['SERVER_PORT']
        addr += '/steve/websocket/CentralSystemService/' 
        addr += self.GetChargePointName()
        return addr


async def main():
    # GetSettings()
    cp_settings = Settings()
    print(cp_settings.GetWsServerAddress())

    # cwd = os.getcwd()
    # schemas_dir = cwd + SCHEMAS_FOLDER
    # print(f'schemas_dir: {schemas_dir}')
    # schemas_files = [f for f in os.listdir(schemas_dir) if os.path.isfile(os.path.join(schemas_dir, f))]
    # # print(f'{schemas_files}')
    # if 'Authorize.json' in schemas_files:
    #     path = schemas_dir + '\Authorize.json'
    #     with open(path, 'rt') as f:
    #         Authorize = json.load(f)
    #         f.close()

    # print(f'{Authorize.get("properties").get("idTag")}')

    async with ws.connect(cp_settings.GetWsServerAddress(), subprotocols=['ocpp1.6']) as socket:
        cp = ChargePoint(cp_settings.GetChargePointName(), socket)
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