import os
import json
import asyncio
import websockets as ws

from charge_point import ChargePoint



class Settings:
    CHARGE_POINT_NAME = 'ChargePointName'
    CHARGE_POINT_VENDOR = 'VendorName'
    # SCHEMAS_FOLDER = '\schemas\json'
    SERVER_IP = '192.168.1.20'
    SERVER_PORT = '8180'
    SERVER_POSTFIX = '/steve/websocket/CentralSystemService/'
    SETTINGS_FILE_NAME = 'settings.json'
    SETTINGS = {
                'SERVER_IP' : SERVER_IP, 
                'SERVER_PORT' : SERVER_PORT, 
                'SERVER_POSTFIX' : SERVER_POSTFIX,
                'CHARGE_POINT_NAME' : CHARGE_POINT_NAME,

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
        addr += self.settings['SERVER_POSTFIX'] # /steve/websocket/CentralSystemService/' 
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
            # cp.BootNotificationSend()
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

# [
#   2,
#   "ad71ad42-18a2-46cf-a0f4-c9316413bf83",
#   "ChangeConfiguration",
#   {
#       "key":"MeterValueSampleInterval",
#       "value":"30"
#   }
# ]
# [
#   2,
#   "bebc8fac-1ac7-491a-a362-926eade676b8",
#   "GetConfiguration",
#   {
#       "key":[
#           "MeterValueSampleInterval",
#           "MeterValuesSampledDataMaxLength",
#           "MeterValuesSampledData",
#           "StopTxnSampledData",
#           "HeartbeatInterval",
#           "AuthorizationCacheEnabled",
#           "AuthorizeRemoteTxRequests",
#           "ConnectionTimeOut",
#           "GetConfigurationMaxKeys",
#           "ClockAlignedDataInterval"
#           ]
#   }
# ] 
if __name__ == '__main__':
    asyncio.run(main())