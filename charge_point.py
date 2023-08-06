import asyncio
import time
import uuid
import logging
import json
from enum import Enum

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
# [
#  3,
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


class ParseResponseResult(int, Enum):
    JSON_ERROR         = 0
    BAD_CALLRESULT_LEN = 1
    CALLRESULT         = 2
    BAD_CALLERROR_LEN  = 3
    CALLERROR          = 4
    NOT_RESPONSE       = 5
    BAD_UNIQUE_ID      = 6

class BaseJsonMessage:
    CALL       = 2 # (Client-to-server)
    CALLRESULT = 3 # (Server-to-client)
    CALLERROR  = 4 # (Server-to-client)

    CALLRESULT_LEN = 3
    CALLERROR_LEN  = 5

    def __init__(self, action: str) -> None:
        self.action = action
        self.UniqueId = ''
        self.msg_payload = None

    async def SendRequest(self, connection, callback) -> None:
        pass

    def MakeRequest(self, _uuid: str, payload: dict) -> str:
        result = ''
        self.UniqueId = _uuid
        msg = []
        msg.append(BaseJsonMessage.CALL)
        msg.append(_uuid)
        msg.append(self.action)
        msg.append(payload)
        result = json.dumps(msg)
        return result
    
    def ParseResponse(self, json_data: str) -> ParseResponseResult:
        try:
            response = json.loads(json_data)
        except:
            return ParseResponseResult.JSON_ERROR

        msg_type  = response[0]
        unique_id = response[1]
        if msg_type == BaseJsonMessage.CALLRESULT:
            if len(response) != BaseJsonMessage.CALLRESULT_LEN:
                return ParseResponseResult.BAD_CALLRESULT_LEN
            if self.UniqueId != unique_id:
                return ParseResponseResult.BAD_UNIQUE_ID
            self.msg_payload = response[2]
            return ParseResponseResult.CALLRESULT
        elif msg_type == BaseJsonMessage.CALLERROR:
            if len(response) != BaseJsonMessage.CALLERROR_LEN:
                return ParseResponseResult.BAD_CALLERROR_LEN
            error_code        = response[2]
            error_describtion = response[3]
            error_details     = response[4]
            return ParseResponseResult.CALLERROR
        else:
            return False

class BootNotification(BaseJsonMessage):
    ACTION = 'BootNotification'

    PL_KEY_STATUS = 'status'
    PL_KEY_CURRENT_TIME = 'currentTime'
    PL_KEY_INTERVAL = 'interval'
    def __init__(self) -> None:
        super().__init__(BootNotification.ACTION)
        self.chargePointVendor = 'vendor'
        self.chargePointModel = 'model'
        self.chargePointSerialNumber = 'point serial num'
        self.chargeBoxSerialNumber = 'box serial num'
        self.firmwareVersion = 'firm ver'
        self.iccid = 'iccid'
        self.imsi = 'imcid'
        self.meterType = 'meter type'
        self.meterSerialNumber = 'meter serial num'

        self.callback = None

    async def SendRequest(self, connection, callback) -> None:
        _uuid = str(uuid.uuid4())
        request = self.MakeRequest(_uuid)
        self.callback = callback
        await connection.send(request)

    def MakeRequest(self, _uuid: str) -> str:
        pl = {}
        pl['chargePointVendor']       = self.chargePointVendor
        pl['chargePointModel']        = self.chargePointModel
        pl['chargePointSerialNumber'] = self.chargePointSerialNumber
        pl['chargeBoxSerialNumber']   = self.chargeBoxSerialNumber
        pl['firmwareVersion']         = self.firmwareVersion
        pl['iccid']                   = self.iccid
        pl['imsi']                    = self.imsi
        pl['meterType']               = self.meterType
        pl['meterSerialNumber']       = self.meterSerialNumber
        return super().MakeRequest(_uuid, pl)

    async def ParseResponse(self, json_data: str) -> None:
        parse_result = super().ParseResponse(json_data)
        if parse_result == ParseResponseResult.CALLRESULT:
            if self.callback:
                payload = self.msg_payload
                status = payload.get(BootNotification.PL_KEY_STATUS)
                time = payload.get(BootNotification.PL_KEY_CURRENT_TIME)
                interval = int(payload.get(BootNotification.PL_KEY_INTERVAL))
                await self.callback(status, time, interval)

class Heartbeat(BaseJsonMessage):
    ACTION = 'Heartbeat'

    def __init__(self) -> None:
        super().__init__(Heartbeat.ACTION)
        self.callback = None

    async def Start(self, interval: int, connection, callback) -> None:
        prev_time = time.time()
        while True:
            await asyncio.sleep(1)
            if (time.time() - prev_time) >= interval:
                prev_time = time.time()
                await self.SendRequest(connection, callback)

    async def SendRequest(self, connection, callback) -> None:
        _uuid = str(uuid.uuid4())
        request = self.MakeRequest(_uuid)
        print(f'Heartbeat.req: {request}')
        self.callback = callback
        await connection.send(request)

    def MakeRequest(self, _uuid: str) -> str:
        pl = {}
        return super().MakeRequest(_uuid, pl)

    async def ParseResponse(self, json_data: str) -> None:
        parse_result = super().ParseResponse(json_data)
        if parse_result == ParseResponseResult.CALLRESULT:
            if self.callback:
                payload = self.msg_payload
                # print(payload.get('currentTime'))
                await self.callback(payload.get('currentTime'))

class StatusNotification(BaseJsonMessage):
    ACTION = 'StatusNotification'

    PL_INFO              = 'info'
    PL_TIMESTAMP         = 'timestamp'
    PL_VENDOR_ID         = 'vendorId'
    PL_VENDOR_EEROR_CODE = 'vendorErrorCode'
    PL_KEY_CURRENT_TIME  = 'currentTime'
    PL_KEY_INTERVAL      = 'interval'

# required
    PL_CONNECTOR_ID = 'connectorId'
    PL_EEROR_CODE   = 'errorCode'
    PL_KEY_STATUS   = 'status'

    def __init__(self) -> None:
        super().__init__(StatusNotification.ACTION)
        self.callback = None
        self.error_code = ''
        self.connectorId = ''
        self.status = ''

    async def Start(self, interval: int, connection, callback) -> None:
        prev_time = time.time()
        while True:
            await asyncio.sleep(1)
            if (time.time() - prev_time) >= interval:
                prev_time = time.time()
                await self.SendRequest(connection, callback)

    async def SendRequest(self, connection, callback) -> None:
        _uuid = str(uuid.uuid4())
        request = self.MakeRequest(_uuid)
        print(f'StatusNotification.req: {request}')
        self.callback = callback
        await connection.send(request)

    def MakeRequest(self, _uuid: str) -> str:
        pl = {}
        pl[StatusNotification.PL_CONNECTOR_ID] = self.connectorId
        pl[StatusNotification.PL_KEY_STATUS]   = self.status
        pl[StatusNotification.PL_EEROR_CODE]   = self.error_code
        pl[StatusNotification.PL_INFO] = 'connector info'
        return super().MakeRequest(_uuid, pl)

    async def ParseResponse(self, json_data: str) -> None:
        parse_result = super().ParseResponse(json_data)
        if parse_result == ParseResponseResult.CALLRESULT:
            if self.callback:
                payload = self.msg_payload
                # print(payload.get('currentTime'))
                print(f'StatusNotification Response OK')
                pass


class ChargePoint:

    def __init__(self, id, connection) -> None:
        
        self.id = id
        self.connection = connection
        self.uuid_generator = uuid.uuid4
        logging.basicConfig(level=logging.DEBUG, filename='ChargePoint.log', filemode='a')
        self.logger = logging.getLogger('ChargePoint_'+id)
        # logging.root.name = id
        self.CreateOcppProtocolObjects()

    def CreateOcppProtocolObjects(self):
        self.ocpp_objects_list = []

        self.boot_notification = BootNotification()
        self.ocpp_objects_list.append(self.boot_notification)
        self.heartbeat = Heartbeat()
        self.ocpp_objects_list.append(self.heartbeat)
        self.status_notification = StatusNotification()
        self.ocpp_objects_list.append(self.status_notification)

    async def BootNotificationSend(self):
        self.boot_notification.chargePointModel = self.id
        self.boot_notification.chargePointVendor = 'NSTU'
        await self.boot_notification.SendRequest(self.connection, self.BootNotificationCallback)
    async def BootNotificationCallback(self, reg_status: str, cur_date_time: str, heartbeat_interval: int) -> None:
        log = f'status: {reg_status}, date_time: {cur_date_time}, heartbeat_interval: {heartbeat_interval}'
        self.Log(log)
        if reg_status == 'Accepted':
            # asyncio.gather(self.heartbeat.Start(heartbeat_interval, self.connection, self.HeartbeatCallback))
            asyncio.gather(self.heartbeat.Start(10, self.connection, self.HeartbeatCallback))
            pass

    async def HeartbeatCallback(self, cur_time: str) -> None:
        print(f'HeartbeatCallback: {cur_time}')
        await self.StatusNotificationSend(self.connectors_id)
        self.connectors_id +=1
        if self.connectors_id > 3:
            self.connectors_id = 0
        # await self.StatusNotificationSend(1)

    async def StatusNotificationSend(self, connectorId: int):
        self.status_notification.status = 'Available'
        self.status_notification.connectorId = str(connectorId)
        self.status_notification.error_code = 'NoError'
        await self.status_notification.SendRequest(self.connection, self.StatusNotificationCallback)
    async def StatusNotificationCallback(self) -> None:
        print(f'StatusNotificationCallback')

    async def start(self):
        self.connectors_id = 0
        connection = self.connection
        await self.BootNotificationSend()
        # await self.StatusNotificationSend()
        while True:
            rx_message = await connection.recv()
            self.Log(f'{rx_message}')
            for ocpp_obj in self.ocpp_objects_list:
                await ocpp_obj.ParseResponse(rx_message)

    def Log(self, message: str) -> None:
        print(message)
        self.logger.debug(message)

def main():
    msg = BaseJsonMessage()
    request = msg.MakeRequest('_uuid', 'request_type', {'param':'val'})
    print(f'MakeRequest: {request}')
    
    response = '[3, "19223201", {"status":"Accepted","currentTime":"2013-02-01T20:53:32.486Z","heartbeatInterval":300}]'
    msg.ParseResponse(response)
    response = '[, "19223201", {"status":"Accepted","currentTime":"2013-02-01T20:53:32.486Z","heartbeatInterval":300}]'
    msg.ParseResponse(response)
    response = '[10, "19223201", {"status":"Accepted","currentTime":"2013-02-01T20:53:32.486Z","heartbeatInterval":300}]'
    msg.ParseResponse(response)
    response = '[4,"19223201","ErrorCode","ErrorDescribtion",{"ErrorDetails":"Details"}]'
    msg.ParseResponse(response)


if __name__ == '__main__':
    main()