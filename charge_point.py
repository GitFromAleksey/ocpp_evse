import asyncio
import uuid
import logging
from ocpp_protocol import BaseJsonMessage, BootNotification, Heartbeat, StatusNotification




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
        self.tx_queue = []
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
        # await self.boot_notification.SendRequest(self.connection, self.BootNotificationCallback)
        await self.SendOcppRequest(self.boot_notification, self.BootNotificationCallback)
    async def BootNotificationCallback(self, reg_status: str, cur_date_time: str, heartbeat_interval: int) -> None:
        log = f'status: {reg_status}, date_time: {cur_date_time}, heartbeat_interval: {heartbeat_interval}'
        self.Log(log)
        if reg_status == 'Accepted':
            await self.HeartbeatSendingStart(heartbeat_interval)

    async def HeartbeatSendingStart(self, heartbeat_interval: int) -> None:
        asyncio.gather(self.heartbeat.Start(heartbeat_interval, self.connection, self.HeartbeatCallback))
    async def HeartbeatCallback(self, cur_time: str) -> None:
        print(f'HeartbeatCallback: {cur_time}')
        await self.StatusNotificationSend(self.connectors_id)
        self.connectors_id += 1
        if self.connectors_id > 3:
            self.connectors_id = 0

    async def StatusNotificationSend(self, connectorId: int):
        self.status_notification.status = 'Available'
        self.status_notification.connectorId = str(connectorId)
        self.status_notification.error_code = 'NoError'
        # await self.status_notification.SendRequest(self.connection, self.StatusNotificationCallback)
        await self.SendOcppRequest(self.status_notification, self.StatusNotificationCallback)
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

    # async def DataExchange(self) -> None:
    #     if len(self.tx_queue) > 0:
    #         request = self.tx_queue.pop()
    #         await request.SendRequest(self.connection, callback)
    async def SendOcppRequest(self, request: BaseJsonMessage, callback) -> None:
        # self.tx_queue.append(request)
        await request.SendRequest(self.connection, callback)


    def Log(self, message: str) -> None:
        print(message)
        self.logger.debug(message)

def main():
    # msg = BaseJsonMessage()
    # request = msg.MakeRequest('_uuid', 'request_type', {'param':'val'})
    # print(f'MakeRequest: {request}')
    
    # response = '[3, "19223201", {"status":"Accepted","currentTime":"2013-02-01T20:53:32.486Z","heartbeatInterval":300}]'
    # msg.ParseResponse(response)
    # response = '[, "19223201", {"status":"Accepted","currentTime":"2013-02-01T20:53:32.486Z","heartbeatInterval":300}]'
    # msg.ParseResponse(response)
    # response = '[10, "19223201", {"status":"Accepted","currentTime":"2013-02-01T20:53:32.486Z","heartbeatInterval":300}]'
    # msg.ParseResponse(response)
    # response = '[4,"19223201","ErrorCode","ErrorDescribtion",{"ErrorDetails":"Details"}]'
    # msg.ParseResponse(response)
    pass

if __name__ == '__main__':
    main()