import asyncio
import uuid
import logging
from ocpp_protocol import BaseJsonMessage, BootNotification, Heartbeat, StatusNotification




class ChargePoint:

    def __init__(self, id='', chargePointVendor='', connection=None) -> None:
        
        self.id = id
        self.chargePointVendor = chargePointVendor
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
        self.boot_notification.AddCallback(self.BootNotificationCallback)
        self.ocpp_objects_list.append(self.boot_notification)
        self.heartbeat = Heartbeat()
        self.heartbeat.AddCallback(self.HeartbeatCallback)
        self.ocpp_objects_list.append(self.heartbeat)
        self.status_notifications = []
        for connectorId in range(4):
            status_notification = StatusNotification(connectorId)
            status_notification.AddCallback(self.StatusNotificationCallback)
            self.status_notifications.append(status_notification)
            self.ocpp_objects_list.append(status_notification)
        
        for ocpp_obj in self.ocpp_objects_list:
            ocpp_obj.AddCallback(self.DataAnswerCallback)

    def BootNotificationSend(self):
        self.boot_notification.chargePointModel = self.id
        self.boot_notification.chargePointVendor = self.chargePointVendor
        self.DataPutTxQueue(self.boot_notification, self.BootNotificationCallback)
    def BootNotificationCallback(self, reg_status: str, cur_date_time: str, heartbeat_interval: int) -> None:
        log = f'status: {reg_status}, date_time: {cur_date_time}, heartbeat_interval: {heartbeat_interval}'
        self.Log(log)
        if reg_status == 'Accepted':
            self.HeartbeatSendingStart(heartbeat_interval)

    def HeartbeatSendingStart(self, heartbeat_interval: int) -> None:
        asyncio.gather(self.heartbeat.Start(heartbeat_interval, self.connection, self.HeartbeatCallback))
    async def HeartbeatCallback(self, cur_time: str) -> None:
        print(f'HeartbeatCallback: {cur_time}')

    def StatusNotificationSend(self, connectorId: int):
        status_notification = self.status_notifications[connectorId]
        status_notification.status = 'Available'
        status_notification.error_code = 'NoError'
        self.DataPutTxQueue(status_notification, self.StatusNotificationCallback)
    async def StatusNotificationCallback(self) -> None:
        print(f'StatusNotificationCallback')

    async def start(self):
        # connection = self.connection

        asyncio.gather(self.DataSender())
        asyncio.gather(self.DataReceiver())

        self.BootNotificationSend()
        self.StatusNotificationSend(0)
        self.StatusNotificationSend(1)
        self.StatusNotificationSend(2)
        self.StatusNotificationSend(3)

        while True:
            await asyncio.sleep(1)

    async def DataSender(self) -> None:
        while True:
            await asyncio.sleep(1)
            if len(self.tx_queue) > 0:
                request = self.tx_queue.pop(0)
                await request.SendRequest(self.connection, None)
                continue
    async def DataReceiver(self) -> None:
        connection = self.connection
        while True:
            rx_message = await connection.recv()
            self.Log(f'{rx_message}')
            for ocpp_obj in self.ocpp_objects_list:
                await ocpp_obj.ParseResponse(rx_message)

    def DataAnswerCallback(self, *p) -> None:
        print(f'DataAnswerCallback: {p}')
    def DataPutTxQueue(self, request: BaseJsonMessage, callback) -> None:
        self.tx_queue.append(request)

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