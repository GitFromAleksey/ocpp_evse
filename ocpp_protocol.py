
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

import asyncio
from enum import Enum
import uuid
import json
import time

# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------
class StatusNotificationErrCode(str, Enum):
    ConnectorLockFailure = "ConnectorLockFailure"
    EVCommunicationError = "EVCommunicationError"
    GroundFailure        = "GroundFailure"
    HighTemperature      = "HighTemperature"
    InternalError        = "InternalError"
    LocalListConflict    = "LocalListConflict"
    NoError              = "NoError"
    OtherError           = "OtherError"
    OverCurrentFailure   = "OverCurrentFailure"
    PowerMeterFailure    = "PowerMeterFailure"
    PowerSwitchFailure   = "PowerSwitchFailure"
    ReaderFailure        = "ReaderFailure"
    ResetFailure         = "ResetFailure"
    UnderVoltage         = "UnderVoltage"
    OverVoltage          = "OverVoltage"
    WeakSignal           = "WeakSignal"

class StatusNotificationStatus(str, Enum):
    Available     = "Available"
    Preparing     = "Preparing"
    Charging      = "Charging"
    SuspendedEVSE = "SuspendedEVSE"
    SuspendedEV   = "SuspendedEV"
    Finishing     = "Finishing"
    Reserved      = "Reserved"
    Unavailable   = "Unavailable"
    Faulted       = "Faulted"

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
        self.status = StatusNotificationStatus.Available

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
                print(f'StatusNotification Response OK: {self.UniqueId}')
                pass
